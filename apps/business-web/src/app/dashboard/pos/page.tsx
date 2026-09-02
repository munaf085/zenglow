"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { api } from "@/lib/api";
import { toast } from "sonner";
import {
  ShoppingCart, Plus, Trash2, CreditCard, Banknote, QrCode, Gift,
  Search, CheckCircle2, User, Printer, X, ShieldAlert, Sparkles,
} from "lucide-react";
import { cn, formatPrice } from "@/lib/utils";

interface CartItem {
  item_type: "SERVICE" | "PRODUCT";
  item_id: string;
  name: string;
  quantity: number;
  unit_price: number;
  tax_rate: number;
  discount_amount: number;
}

export default function POSPage() {
  const { business } = useAuth();
  const [services, setServices] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<"services" | "products">("services");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  // Cart state
  const [cart, setCart] = useState<CartItem[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<any | null>(null);
  const [discountAmount, setDiscountAmount] = useState<number>(0);
  const [tipAmount, setTipAmount] = useState<number>(0);

  // Payment modal state
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState<"CASH" | "CARD" | "UPI" | "GIFT_CARD">("CASH");
  const [giftCardCode, setGiftCardCode] = useState("");
  const [completedOrder, setCompletedOrder] = useState<any | null>(null);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    if (!business?.id) return;
    loadData();
  }, [business?.id]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [svcRes, prodRes, custRes] = await Promise.allSettled([
        api.get<any>(`/businesses/${business?.id}/services`),
        api.get<any[]>(`/businesses/${business?.id}/inventory/products?is_active=true`),
        api.get<any>(`/customers`),
      ]);

      if (svcRes.status === "fulfilled") setServices(svcRes.value?.items ?? svcRes.value ?? []);
      if (prodRes.status === "fulfilled") setProducts(prodRes.value ?? []);
      if (custRes.status === "fulfilled") setCustomers(custRes.value?.items ?? custRes.value ?? []);
    } catch (e) {
      toast.error("Failed to load catalog items");
    } finally {
      setLoading(false);
    }
  };

  const addToCart = (item: any, type: "SERVICE" | "PRODUCT") => {
    setCart((prev) => {
      const existing = prev.find((i) => i.item_id === item.id && i.item_type === type);
      if (existing) {
        if (type === "PRODUCT" && existing.quantity >= (item.stock_quantity ?? 999)) {
          toast.error(`Only ${item.stock_quantity} available in stock!`);
          return prev;
        }
        return prev.map((i) =>
          i.item_id === item.id && i.item_type === type ? { ...i, quantity: i.quantity + 1 } : i
        );
      }
      return [
        ...prev,
        {
          item_type: type,
          item_id: item.id,
          name: item.name,
          quantity: 1,
          unit_price: Number(item.retail_price ?? item.price ?? 0),
          tax_rate: Number(item.tax_rate ?? 18),
          discount_amount: 0,
        },
      ];
    });
  };

  const updateQuantity = (itemId: string, delta: number) => {
    setCart((prev) =>
      prev
        .map((i) => {
          if (i.item_id === itemId) {
            const nextQty = i.quantity + delta;
            return nextQty > 0 ? { ...i, quantity: nextQty } : null;
          }
          return i;
        })
        .filter(Boolean) as CartItem[]
    );
  };

  const removeItem = (itemId: string) => {
    setCart((prev) => prev.filter((i) => i.item_id !== itemId));
  };

  // Calculations
  const subtotal = cart.reduce((sum, i) => sum + i.unit_price * i.quantity, 0);
  const taxTotal = cart.reduce((sum, i) => sum + (i.unit_price * i.quantity * (i.tax_rate / 100)), 0);
  const totalAmount = Math.max(0, subtotal - discountAmount + taxTotal + tipAmount);

  const handleCheckout = async () => {
    if (!business?.id || cart.length === 0) return;
    const branchId = business.branches?.[0]?.id;
    if (!branchId) {
      toast.error("Business has no active branch");
      return;
    }

    try {
      setProcessing(true);
      const payload = {
        branch_id: branchId,
        customer_id: selectedCustomer?.id || null,
        items: cart,
        payments: [
          {
            payment_method: paymentMethod,
            amount: totalAmount,
            reference_code: paymentMethod === "GIFT_CARD" ? giftCardCode : undefined,
          },
        ],
        discount_amount: Number(discountAmount),
        tip_amount: Number(tipAmount),
        notes: "Front-desk POS sale",
      };

      const res = await api.post<any>(`/businesses/${business.id}/pos/checkout`, payload);
      setCompletedOrder(res);
      toast.success(`Order #${res.order_number} completed successfully!`);
      setCart([]);
      setSelectedCustomer(null);
      setDiscountAmount(0);
      setTipAmount(0);
      setIsCheckoutOpen(false);
    } catch (e: any) {
      toast.error(e?.message || "Checkout failed");
    } finally {
      setProcessing(false);
    }
  };

  const filteredCatalog = (activeTab === "services" ? services : products).filter((item) =>
    item.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <ShoppingCart className="w-7 h-7 text-brand-600" /> POS & Checkout Terminal
          </h1>
          <p className="text-sm text-gray-500">Sell services, retail products, apply split tenders, and issue receipts</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Catalog Search & Quick-Add */}
        <div className="lg:col-span-2 space-y-4">
          {/* Tabs & Search */}
          <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex flex-col sm:flex-row gap-3 items-center justify-between">
            <div className="flex gap-2 w-full sm:w-auto">
              <button
                onClick={() => setActiveTab("services")}
                className={cn(
                  "flex-1 sm:flex-initial px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                  activeTab === "services" ? "bg-brand-600 text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                )}
              >
                Services ({services.length})
              </button>
              <button
                onClick={() => setActiveTab("products")}
                className={cn(
                  "flex-1 sm:flex-initial px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                  activeTab === "products" ? "bg-brand-600 text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                )}
              >
                Retail Products ({products.length})
              </button>
            </div>

            <div className="relative w-full sm:w-64">
              <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder={`Search ${activeTab}...`}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Catalog Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {filteredCatalog.map((item) => {
              const isProd = activeTab === "products";
              const price = Number(item.retail_price ?? item.price ?? 0);
              const outOfStock = isProd && item.stock_quantity <= 0;

              return (
                <div
                  key={item.id}
                  onClick={() => !outOfStock && addToCart(item, isProd ? "PRODUCT" : "SERVICE")}
                  className={cn(
                    "bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between cursor-pointer transition-all hover:border-brand-500 hover:shadow-md",
                    outOfStock && "opacity-50 cursor-not-allowed bg-gray-50 hover:border-gray-200 hover:shadow-none"
                  )}
                >
                  <div>
                    <h3 className="font-semibold text-gray-900 text-sm">{item.name}</h3>
                    {isProd && (
                      <p className="text-xs text-gray-500 mt-1">
                        Stock: <span className={cn("font-medium", item.stock_quantity <= 3 ? "text-red-600" : "text-gray-700")}>{item.stock_quantity}</span>
                      </p>
                    )}
                  </div>
                  <div className="flex items-center justify-between mt-3 pt-2 border-t border-gray-100">
                    <span className="font-bold text-gray-900 text-sm">{formatPrice(price)}</span>
                    <button
                      disabled={outOfStock}
                      className="p-1.5 bg-brand-50 text-brand-600 rounded-lg hover:bg-brand-100 transition-colors"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Interactive Cart & Tender Panel */}
        <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between h-fit space-y-4">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <h2 className="font-bold text-gray-900 flex items-center gap-2 text-base">
                <ShoppingCart className="w-5 h-5 text-brand-600" /> Current Cart ({cart.reduce((s, i) => s + i.quantity, 0)})
              </h2>
              {cart.length > 0 && (
                <button onClick={() => setCart([])} className="text-xs text-red-600 hover:underline">
                  Clear
                </button>
              )}
            </div>

            {/* Customer Picker */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-700 flex items-center gap-1">
                <User className="w-3.5 h-3.5" /> Customer (Optional)
              </label>
              <select
                value={selectedCustomer?.id ?? ""}
                onChange={(e) => setSelectedCustomer(customers.find((c) => c.id === e.target.value) || null)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:outline-none"
              >
                <option value="">Walk-in Customer</option>
                {customers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.first_name || c.user?.first_name} {c.last_name || c.user?.last_name} ({c.email || c.user?.email})
                  </option>
                ))}
              </select>
            </div>

            {/* Cart Items List */}
            <div className="divide-y divide-gray-100 max-h-64 overflow-y-auto space-y-2">
              {cart.length === 0 ? (
                <div className="text-center py-8 text-gray-400 text-sm">
                  Cart is empty. Tap items on the left to add.
                </div>
              ) : (
                cart.map((item) => (
                  <div key={item.item_id} className="pt-2 flex items-center justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 truncate">{item.name}</p>
                      <p className="text-xs text-gray-500">{formatPrice(item.unit_price)} each</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex items-center border border-gray-300 rounded-lg overflow-hidden">
                        <button
                          onClick={() => updateQuantity(item.item_id, -1)}
                          className="px-2 py-0.5 text-gray-600 hover:bg-gray-100 text-xs font-bold"
                        >
                          -
                        </button>
                        <span className="px-2 text-xs font-semibold text-gray-800">{item.quantity}</span>
                        <button
                          onClick={() => updateQuantity(item.item_id, 1)}
                          className="px-2 py-0.5 text-gray-600 hover:bg-gray-100 text-xs font-bold"
                        >
                          +
                        </button>
                      </div>
                      <span className="text-sm font-semibold text-gray-900 w-16 text-right">
                        {formatPrice(item.unit_price * item.quantity)}
                      </span>
                      <button
                        onClick={() => removeItem(item.item_id)}
                        className="text-gray-400 hover:text-red-600 p-1"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Discounts & Tips */}
            {cart.length > 0 && (
              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-gray-100">
                <div>
                  <label className="text-xs text-gray-600">Discount (₹)</label>
                  <input
                    type="number"
                    min="0"
                    value={discountAmount || ""}
                    onChange={(e) => setDiscountAmount(Number(e.target.value))}
                    placeholder="0"
                    className="w-full px-2 py-1.5 border border-gray-300 rounded-md text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-600">Tip (₹)</label>
                  <input
                    type="number"
                    min="0"
                    value={tipAmount || ""}
                    onChange={(e) => setTipAmount(Number(e.target.value))}
                    placeholder="0"
                    className="w-full px-2 py-1.5 border border-gray-300 rounded-md text-sm"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Pricing Summary & Checkout Button */}
          <div className="space-y-3 pt-3 border-t border-gray-200">
            <div className="space-y-1 text-sm">
              <div className="flex justify-between text-gray-600">
                <span>Subtotal</span>
                <span>{formatPrice(subtotal)}</span>
              </div>
              {taxTotal > 0 && (
                <div className="flex justify-between text-gray-600">
                  <span>Taxes (18%)</span>
                  <span>{formatPrice(taxTotal)}</span>
                </div>
              )}
              {discountAmount > 0 && (
                <div className="flex justify-between text-green-600">
                  <span>Discount</span>
                  <span>-{formatPrice(discountAmount)}</span>
                </div>
              )}
              {tipAmount > 0 && (
                <div className="flex justify-between text-gray-600">
                  <span>Tip</span>
                  <span>+{formatPrice(tipAmount)}</span>
                </div>
              )}
              <div className="flex justify-between font-bold text-gray-900 text-base pt-2 border-t border-gray-200">
                <span>Total Payable</span>
                <span className="text-brand-600">{formatPrice(totalAmount)}</span>
              </div>
            </div>

            <button
              disabled={cart.length === 0}
              onClick={() => setIsCheckoutOpen(true)}
              className="w-full py-3 bg-brand-600 text-white rounded-xl font-bold shadow-md hover:bg-brand-700 transition-colors disabled:opacity-50"
            >
              Pay {formatPrice(totalAmount)}
            </button>
          </div>
        </div>
      </div>

      {/* Tender Modal */}
      {isCheckoutOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-start sm:items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl my-8 sm:my-0">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <h3 className="font-bold text-gray-900 text-lg">Select Payment Tender</h3>
              <button onClick={() => setIsCheckoutOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="text-center py-2">
              <p className="text-xs text-gray-500">Total Amount to Collect</p>
              <p className="text-3xl font-extrabold text-brand-600 mt-1">{formatPrice(totalAmount)}</p>
            </div>

            <div className="grid grid-cols-2 gap-2">
              {[
                { id: "CASH", label: "Cash", icon: Banknote },
                { id: "CARD", label: "Card Swipe", icon: CreditCard },
                { id: "UPI", label: "UPI / QR", icon: QrCode },
                { id: "GIFT_CARD", label: "Gift Card", icon: Gift },
              ].map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setPaymentMethod(id as any)}
                  className={cn(
                    "p-3 rounded-xl border flex flex-col items-center justify-center gap-2 font-medium text-sm transition-all",
                    paymentMethod === id
                      ? "border-brand-600 bg-brand-50 text-brand-700 ring-2 ring-brand-500"
                      : "border-gray-200 hover:bg-gray-50 text-gray-700"
                  )}
                >
                  <Icon className="w-5 h-5" />
                  {label}
                </button>
              ))}
            </div>

            {paymentMethod === "GIFT_CARD" && (
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-700">Gift Card Code (e.g. GC-XXXX-XXXX)</label>
                <input
                  type="text"
                  placeholder="GC-1234-5678"
                  value={giftCardCode}
                  onChange={(e) => setGiftCardCode(e.target.value.toUpperCase())}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
            )}

            <button
              onClick={handleCheckout}
              disabled={processing || (paymentMethod === "GIFT_CARD" && !giftCardCode)}
              className="w-full py-3 bg-brand-600 text-white rounded-xl font-bold shadow-md hover:bg-brand-700 transition-colors disabled:opacity-50"
            >
              {processing ? "Processing Sale..." : "Complete & Print Receipt"}
            </button>
          </div>
        </div>
      )}

      {/* Completed Order Receipt Modal */}
      {completedOrder && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-start sm:items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-xl text-center">
            <CheckCircle2 className="w-12 h-12 text-green-600 mx-auto" />
            <h3 className="font-bold text-gray-900 text-lg">Sale Successful!</h3>
            <p className="text-xs text-gray-500">Order #{completedOrder.order_number}</p>

            <div className="bg-gray-50 p-3 rounded-lg text-left text-xs space-y-1">
              <div className="flex justify-between font-medium">
                <span>Subtotal:</span>
                <span>{formatPrice(completedOrder.subtotal)}</span>
              </div>
              <div className="flex justify-between font-medium">
                <span>Tax:</span>
                <span>{formatPrice(completedOrder.tax_amount)}</span>
              </div>
              <div className="flex justify-between font-bold border-t border-gray-200 pt-1 text-sm">
                <span>Total Paid:</span>
                <span className="text-brand-600">{formatPrice(completedOrder.total_amount)}</span>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => window.print()}
                className="flex-1 py-2 border border-gray-300 rounded-lg text-sm font-medium flex items-center justify-center gap-1 hover:bg-gray-50"
              >
                <Printer className="w-4 h-4" /> Print
              </button>
              <button
                onClick={() => setCompletedOrder(null)}
                className="flex-1 py-2 bg-brand-600 text-white rounded-lg text-sm font-semibold hover:bg-brand-700"
              >
                New Sale
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
