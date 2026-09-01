"""
Inventory Service — product catalog, categories, stock adjustments, and low-stock alerts.
"""
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import assert_business_access
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.inventory import Product, ProductCategory, StockMovement, StockMovementType
from app.models.user import User
from app.schemas.inventory import (
    ProductCategoryCreate,
    ProductCreate,
    ProductUpdate,
    StockMovementCreate,
)


class InventoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Product Categories ───────────────────────────────────────────────────

    async def list_categories(self, business_id: UUID) -> List[ProductCategory]:
        result = await self.db.execute(
            select(ProductCategory)
            .where(
                ProductCategory.business_id == business_id,
                ProductCategory.deleted_at.is_(None),
            )
            .order_by(ProductCategory.name)
        )
        return list(result.scalars().all())

    async def create_category(
        self, business_id: UUID, data: ProductCategoryCreate, user: User
    ) -> ProductCategory:
        assert_business_access(user, business_id)
        cat = ProductCategory(
            business_id=business_id,
            name=data.name.strip(),
            description=data.description,
        )
        self.db.add(cat)
        await self.db.flush()
        await self.db.refresh(cat)
        return cat

    # ── Products ─────────────────────────────────────────────────────────────

    async def list_products(
        self,
        business_id: UUID,
        category_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        low_stock_only: bool = False,
    ) -> List[Product]:
        q = (
            select(Product)
            .options(selectinload(Product.category))
            .where(
                Product.business_id == business_id,
                Product.deleted_at.is_(None),
            )
        )
        if category_id:
            q = q.where(Product.category_id == category_id)
        if is_active is not None:
            q = q.where(Product.is_active == is_active)
        if low_stock_only:
            q = q.where(Product.stock_quantity <= Product.low_stock_threshold)

        q = q.order_by(Product.name)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_product(self, product_id: UUID, business_id: UUID) -> Product:
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.category))
            .where(
                Product.id == product_id,
                Product.business_id == business_id,
                Product.deleted_at.is_(None),
            )
        )
        product = result.scalar_one_or_none()
        if not product:
            raise NotFoundError("Product", product_id)
        return product

    async def create_product(
        self, business_id: UUID, data: ProductCreate, user: User
    ) -> Product:
        assert_business_access(user, business_id)

        product = Product(
            business_id=business_id,
            category_id=data.category_id,
            name=data.name.strip(),
            sku=data.sku,
            barcode=data.barcode,
            description=data.description,
            brand=data.brand,
            cost_price=data.cost_price,
            retail_price=data.retail_price,
            tax_rate=data.tax_rate,
            stock_quantity=data.stock_quantity,
            low_stock_threshold=data.low_stock_threshold,
            is_active=data.is_active,
        )
        self.db.add(product)
        await self.db.flush()

        # If initial stock > 0, record initial movement
        if data.stock_quantity > 0:
            mov = StockMovement(
                business_id=business_id,
                product_id=product.id,
                movement_type=StockMovementType.IN,
                quantity=data.stock_quantity,
                unit_cost=data.cost_price,
                notes="Initial opening stock",
                created_by_id=user.id,
            )
            self.db.add(mov)
            await self.db.flush()

        await self.db.refresh(product)
        return product

    async def update_product(
        self, product_id: UUID, business_id: UUID, data: ProductUpdate, user: User
    ) -> Product:
        assert_business_access(user, business_id)
        product = await self.get_product(product_id, business_id)

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(product, key, value)

        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product)
        return product

    # ── Stock Movements ──────────────────────────────────────────────────────

    async def record_stock_movement(
        self, business_id: UUID, data: StockMovementCreate, user: User
    ) -> StockMovement:
        assert_business_access(user, business_id)
        product = await self.get_product(data.product_id, business_id)

        qty_change = data.quantity
        if data.movement_type in [StockMovementType.OUT, StockMovementType.SALE]:
            qty_change = -abs(data.quantity)
        elif data.movement_type in [StockMovementType.IN, StockMovementType.RETURN]:
            qty_change = abs(data.quantity)

        new_stock = product.stock_quantity + qty_change
        if new_stock < 0:
            raise BusinessRuleError(
                f"Insufficient stock for product '{product.name}'. Available: {product.stock_quantity}, requested reduction: {abs(qty_change)}"
            )

        product.stock_quantity = new_stock
        self.db.add(product)

        mov = StockMovement(
            business_id=business_id,
            product_id=product.id,
            movement_type=StockMovementType(data.movement_type),
            quantity=qty_change,
            unit_cost=data.unit_cost or product.cost_price,
            notes=data.notes,
            created_by_id=user.id,
        )
        self.db.add(mov)
        await self.db.flush()
        await self.db.refresh(mov)
        return mov

    async def list_movements(
        self, business_id: UUID, product_id: Optional[UUID] = None
    ) -> List[StockMovement]:
        q = (
            select(StockMovement)
            .where(
                StockMovement.business_id == business_id,
                StockMovement.deleted_at.is_(None),
            )
        )
        if product_id:
            q = q.where(StockMovement.product_id == product_id)
        q = q.order_by(StockMovement.created_at.desc())
        result = await self.db.execute(q)
        return list(result.scalars().all())
