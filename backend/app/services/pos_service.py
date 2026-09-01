"""
POS Service — cart calculations, inventory integration, multi-tender split payments, and receipt generation.
"""
import random
import string
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import assert_business_access
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.appointment import Appointment, AppointmentStatus
from app.models.gift_card import GiftCard, GiftCardTransaction, GiftCardTransactionType
from app.models.inventory import Product, StockMovement, StockMovementType
from app.models.payment import Invoice, Payment, PaymentProvider, PaymentStatus
from app.models.pos import (
    Order,
    OrderItem,
    OrderItemType,
    OrderPayment,
    OrderStatus,
    PaymentTenderType,
)
from app.models.user import User
from app.schemas.pos import POSCheckoutRequest


def _generate_order_number() -> str:
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    rand_suffix = "".join(random.choices(string.digits, k=5))
    return f"ORD-{now_str}-{rand_suffix}"


def _generate_invoice_number() -> str:
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    rand_suffix = "".join(random.choices(string.digits, k=5))
    return f"INV-{now_str}-{rand_suffix}"


class POSService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def checkout(
        self, business_id: UUID, data: POSCheckoutRequest, user: User
    ) -> Order:
        assert_business_access(user, business_id)

        # 1. Calculate items subtotal, taxes, discounts
        subtotal = 0.0
        tax_total = 0.0
        discount_items_total = 0.0
        calculated_items = []

        for item_in in data.items:
            unit_total = item_in.unit_price * item_in.quantity
            item_tax = (unit_total - item_in.discount_amount) * (item_in.tax_rate / 100.0)
            item_total = (unit_total - item_in.discount_amount) + item_tax

            subtotal += unit_total
            tax_total += item_tax
            discount_items_total += item_in.discount_amount

            calculated_items.append({
                "item_type": OrderItemType(item_in.item_type),
                "item_id": item_in.item_id,
                "name": item_in.name,
                "quantity": item_in.quantity,
                "unit_price": item_in.unit_price,
                "tax_rate": item_in.tax_rate,
                "discount_amount": item_in.discount_amount,
                "total_price": round(item_total, 2),
            })

            # If item is a PRODUCT, decrement inventory stock
            if item_in.item_type == OrderItemType.PRODUCT and item_in.item_id:
                prod_res = await self.db.execute(
                    select(Product).where(
                        Product.id == item_in.item_id,
                        Product.business_id == business_id,
                        Product.deleted_at.is_(None),
                    )
                )
                product = prod_res.scalar_one_or_none()
                if product:
                    if product.stock_quantity < item_in.quantity:
                        raise BusinessRuleError(
                            f"Insufficient stock for product '{product.name}'. Available: {product.stock_quantity}, requested: {item_in.quantity}"
                        )
                    product.stock_quantity -= item_in.quantity
                    self.db.add(product)

                    # Record stock movement
                    mov = StockMovement(
                        business_id=business_id,
                        product_id=product.id,
                        movement_type=StockMovementType.SALE,
                        quantity=-item_in.quantity,
                        unit_cost=product.cost_price,
                        notes="Sold via POS",
                        created_by_id=user.id,
                    )
                    self.db.add(mov)

        # 2. Total order calculation with overall discounts and tips
        total_discount = discount_items_total + data.discount_amount
        total_amount = round(
            max(0.0, subtotal - total_discount + tax_total + data.tip_amount), 2
        )

        # 3. Validate payment tenders sum matches total amount
        tenders_sum = round(sum(p.amount for p in data.payments), 2)
        if abs(tenders_sum - total_amount) > 0.05:
            raise BusinessRuleError(
                f"Tendered payment sum (₹{tenders_sum:.2f}) does not match order total (₹{total_amount:.2f})"
            )

        # 4. Handle gift card tenders if present
        for tender in data.payments:
            if tender.payment_method == PaymentTenderType.GIFT_CARD and tender.reference_code:
                gc_res = await self.db.execute(
                    select(GiftCard).where(
                        GiftCard.code == tender.reference_code.strip().upper(),
                        GiftCard.business_id == business_id,
                        GiftCard.deleted_at.is_(None),
                    )
                )
                gc = gc_res.scalar_one_or_none()
                if not gc:
                    raise NotFoundError("GiftCard", tender.reference_code)
                gc_bal = float(gc.current_balance)
                t_amt = float(tender.amount)
                if gc_bal < t_amt:
                    raise BusinessRuleError(
                        f"Gift card balance insufficient (₹{gc_bal:.2f} available, required ₹{t_amt:.2f})"
                    )
                new_gc_bal = round(gc_bal - t_amt, 2)
                gc.current_balance = new_gc_bal
                self.db.add(gc)

                gc_tx = GiftCardTransaction(
                    gift_card_id=gc.id,
                    transaction_type=GiftCardTransactionType.REDEEM,
                    amount=-t_amt,
                    balance_after=new_gc_bal,
                    notes="POS Checkout payment",
                )
                self.db.add(gc_tx)

        resolved_cust_id = await self._resolve_customer_id(data.customer_id)

        # 5. Create Order record
        order = Order(
            business_id=business_id,
            branch_id=data.branch_id,
            customer_id=resolved_cust_id,
            staff_id=data.staff_id,
            appointment_id=data.appointment_id,
            order_number=_generate_order_number(),
            status=OrderStatus.COMPLETED,
            subtotal=round(subtotal, 2),
            discount_amount=round(total_discount, 2),
            tax_amount=round(tax_total, 2),
            tip_amount=round(data.tip_amount, 2),
            total_amount=total_amount,
            notes=data.notes,
        )
        self.db.add(order)
        await self.db.flush()

        # Add items
        for ci in calculated_items:
            item = OrderItem(
                order_id=order.id,
                item_type=ci["item_type"],
                item_id=ci["item_id"],
                name=ci["name"],
                quantity=ci["quantity"],
                unit_price=ci["unit_price"],
                tax_rate=ci["tax_rate"],
                discount_amount=ci["discount_amount"],
                total_price=ci["total_price"],
            )
            self.db.add(item)

        # Add payments
        for tender in data.payments:
            pm = OrderPayment(
                order_id=order.id,
                payment_method=PaymentTenderType(tender.payment_method),
                amount=tender.amount,
                reference_code=tender.reference_code,
            )
            self.db.add(pm)

        # 6. If linked to an appointment, update appointment status to COMPLETED
        if data.appointment_id:
            appt_res = await self.db.execute(
                select(Appointment).where(
                    Appointment.id == data.appointment_id,
                    Appointment.business_id == business_id,
                )
            )
            appointment = appt_res.scalar_one_or_none()
            if appointment:
                appointment.status = AppointmentStatus.COMPLETED
                self.db.add(appointment)

        # 7. Generate Invoice if customer is attached
        if resolved_cust_id:
            # Create payment record for invoice
            pm_prov = PaymentProvider.CASH
            if data.payments and data.payments[0].payment_method == PaymentTenderType.CARD:
                pm_prov = PaymentProvider.MOCK
            elif data.payments and data.payments[0].payment_method == PaymentTenderType.UPI:
                pm_prov = PaymentProvider.MOCK

            payment_rec = Payment(
                business_id=business_id,
                customer_id=resolved_cust_id,
                appointment_id=data.appointment_id,
                amount=total_amount,
                provider=pm_prov,
                status=PaymentStatus.CAPTURED,
                paid_at=datetime.now(timezone.utc),
            )
            self.db.add(payment_rec)
            await self.db.flush()

            invoice = Invoice(
                payment_id=payment_rec.id,
                business_id=business_id,
                customer_id=resolved_cust_id,
                invoice_number=_generate_invoice_number(),
                subtotal=subtotal,
                tax_amount=tax_total,
                discount_amount=total_discount,
                total_amount=total_amount,
                issued_at=datetime.now(timezone.utc),
            )
            self.db.add(invoice)

        await self.db.flush()
        await self.db.refresh(order, ["items", "payments"])
        return order

    async def list_orders(
        self,
        business_id: UUID,
        branch_id: Optional[UUID] = None,
        customer_id: Optional[UUID] = None,
    ) -> List[Order]:
        q = (
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.payments),
                selectinload(Order.customer),
                selectinload(Order.staff),
            )
            .where(
                Order.business_id == business_id,
                Order.deleted_at.is_(None),
            )
        )
        if branch_id:
            q = q.where(Order.branch_id == branch_id)
        if customer_id:
            q = q.where(Order.customer_id == customer_id)
        q = q.order_by(Order.created_at.desc())
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_order(self, order_id: UUID, business_id: UUID) -> Order:
        result = await self.db.execute(
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.payments),
                selectinload(Order.customer),
                selectinload(Order.staff),
            )
            .where(
                Order.id == order_id,
                Order.business_id == business_id,
                Order.deleted_at.is_(None),
            )
        )
        order = result.scalar_one_or_none()
        if not order:
            raise NotFoundError("Order", order_id)
        return order

    async def _resolve_customer_id(self, id_val: Optional[UUID]) -> Optional[UUID]:
        if not id_val:
            return None
        from app.models.customer import Customer
        from sqlalchemy import or_
        res = await self.db.execute(
            select(Customer.id).where(
                or_(Customer.id == id_val, Customer.user_id == id_val)
            )
        )
        found_id = res.scalar_one_or_none()
        return found_id or id_val
