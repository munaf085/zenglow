"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { api } from "@/lib/api";
import { toast } from "sonner";
import {
  Package, Plus, Search, AlertTriangle, ArrowDownRight, ArrowUpRight,
  Filter, History, X, Check, Tag, Barcode,
} from "lucide-react";
import { cn, formatPrice } from "@/lib/utils";

export default function InventoryPage() {
  const { business } = useAuth();
  const [products, setProducts] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [lowStockOnly, setLowStockOnly] = useState(false);

  // Modals
  const [isAddProductOpen, setIsAddProductOpen] = useState(false);
  const [isStockAdjustOpen, setIsStockAdjustOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<any | null>(null);

  // Forms
  const [newProduct, setNewProduct] = useState({
    name: "",
    category_id: "",
    sku: "",
    barcode: "",
    brand: "",
    cost_price: 0,
    retail_price: 0,
    tax_rate: 18,
    stock_quantity: 0,
    low_stock_threshold: 5,
  });

  const [stockAdjustment, setStockAdjustment] = useState({
    movement_type: "IN",
    quantity: 1,
    unit_cost: 0,
    notes: "",
  });

  useEffect(() => {
    if (!business?.id) return;
    loadData();
  }, [business?.id, lowStockOnly, selectedCategory]);

  const loadData = async () => {
    try {
      setLoading(true);
      let url = `/businesses/${business?.id}/inventory/products?`;
      if (lowStockOnly) url += "low_stock_only=true&";
      if (selectedCategory) url += `category_id=${selectedCategory}&`;

      const [prodRes, catRes] = await Promise.allSettled([
        api.get<any[]>(url),
        api.get<any[]>(`/businesses/${business?.id}/inventory/categories`),
      ]);

      if (prodRes.status === "fulfilled") setProducts(prodRes.value ?? []);
      if (catRes.status === "fulfilled") setCategories(catRes.value ?? []);
    } catch (e) {
      toast.error("Failed to load inventory");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!business?.id || !newProduct.name || newProduct.retail_price <= 0) {
      toast.error("Please fill in required fields");
      return;
    }

    try {
      await api.post(`/businesses/${business.id}/inventory/products`, {
        ...newProduct,
        category_id: newProduct.category_id || null,
        cost_price: Number(newProduct.cost_price),
        retail_price: Number(newProduct.retail_price),
        stock_quantity: Number(newProduct.stock_quantity),
        low_stock_threshold: Number(newProduct.low_stock_threshold),
      });
      toast.success("Product created successfully!");
      setIsAddProductOpen(false);
      setNewProduct({
        name: "",
        category_id: "",
        sku: "",
        barcode: "",
        brand: "",
        cost_price: 0,
        retail_price: 0,
        tax_rate: 18,
        stock_quantity: 0,
        low_stock_threshold: 5,
      });
      loadData();
    } catch (e: any) {
      toast.error(e?.message || "Failed to create product");
    }
  };

  const handleStockAdjustment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!business?.id || !selectedProduct) return;

    try {
      await api.post(`/businesses/${business.id}/inventory/movements`, {
        product_id: selectedProduct.id,
        movement_type: stockAdjustment.movement_type,
        quantity: Number(stockAdjustment.quantity),
        unit_cost: Number(stockAdjustment.unit_cost) || undefined,
        notes: stockAdjustment.notes || undefined,
      });
      toast.success("Stock updated successfully!");
      setIsStockAdjustOpen(false);
      setSelectedProduct(null);
      loadData();
    } catch (e: any) {
      toast.error(e?.message || "Stock adjustment failed");
    }
  };

  const filtered = products.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    (p.sku && p.sku.toLowerCase().includes(search.toLowerCase())) ||
    (p.brand && p.brand.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Package className="w-7 h-7 text-brand-600" /> Inventory & Stock Management
          </h1>
          <p className="text-sm text-gray-500">Track retail stock, restock supplies, and set low-stock thresholds</p>
        </div>
        <button
          onClick={() => setIsAddProductOpen(true)}
          className="px-4 py-2.5 bg-brand-600 text-white rounded-xl font-semibold shadow hover:bg-brand-700 flex items-center gap-2 text-sm w-fit"
        >
          <Plus className="w-4 h-4" /> Add Product
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="flex flex-wrap gap-2 w-full md:w-auto items-center">
          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by name, SKU, brand..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:outline-none"
            />
          </div>

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:outline-none"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>

          <button
            onClick={() => setLowStockOnly(!lowStockOnly)}
            className={cn(
              "px-3 py-2 rounded-lg text-sm font-medium border flex items-center gap-1.5 transition-colors",
              lowStockOnly
                ? "bg-red-50 text-red-700 border-red-200"
                : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
            )}
          >
            <AlertTriangle className="w-4 h-4 text-red-500" /> Low Stock Alerts
          </button>
        </div>

        <span className="text-xs text-gray-500 font-medium">
          Showing {filtered.length} products
        </span>
      </div>

      {/* Products Table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-700 font-semibold border-b border-gray-200">
              <tr>
                <th className="py-3.5 px-4">Product Name</th>
                <th className="py-3.5 px-4">SKU / Brand</th>
                <th className="py-3.5 px-4 text-right">Cost Price</th>
                <th className="py-3.5 px-4 text-right">Retail Price</th>
                <th className="py-3.5 px-4 text-center">Stock Level</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-gray-400">
                    Loading inventory...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-10 text-gray-400">
                    No products found. Add your first retail item above!
                  </td>
                </tr>
              ) : (
                filtered.map((product) => {
                  const isLow = product.stock_quantity <= product.low_stock_threshold;
                  return (
                    <tr key={product.id} className="hover:bg-gray-50/75 transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-gray-900">{product.name}</div>
                        {product.category && (
                          <span className="inline-block mt-0.5 px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                            {product.category.name}
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-gray-600">
                        <div>{product.sku || "—"}</div>
                        <div className="text-xs text-gray-400">{product.brand}</div>
                      </td>
                      <td className="py-3.5 px-4 text-right text-gray-600 font-medium">
                        {formatPrice(product.cost_price)}
                      </td>
                      <td className="py-3.5 px-4 text-right text-gray-900 font-bold">
                        {formatPrice(product.retail_price)}
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <div className="inline-flex items-center gap-1.5">
                          <span
                            className={cn(
                              "px-2.5 py-1 rounded-full text-xs font-bold",
                              product.stock_quantity === 0
                                ? "bg-red-100 text-red-800"
                                : isLow
                                ? "bg-amber-100 text-amber-800"
                                : "bg-green-100 text-green-800"
                            )}
                          >
                            {product.stock_quantity} units
                          </span>
                          {isLow && (
                            <span title="Low stock threshold reached">
                              <AlertTriangle className="w-4 h-4 text-amber-500" />
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => {
                            setSelectedProduct(product);
                            setStockAdjustment({
                              movement_type: "IN",
                              quantity: 5,
                              unit_cost: Number(product.cost_price),
                              notes: "",
                            });
                            setIsStockAdjustOpen(true);
                          }}
                          className="px-3 py-1.5 bg-gray-100 text-gray-700 hover:bg-brand-50 hover:text-brand-700 rounded-lg text-xs font-semibold transition-colors"
                        >
                          Adjust Stock
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Product Modal */}
      {isAddProductOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <h3 className="font-bold text-gray-900 text-lg">Add New Product</h3>
              <button onClick={() => setIsAddProductOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateProduct} className="space-y-3 text-sm">
              <div>
                <label className="font-medium text-gray-700">Product Name *</label>
                <input
                  type="text"
                  required
                  value={newProduct.name}
                  onChange={(e) => setNewProduct({ ...newProduct, name: e.target.value })}
                  placeholder="e.g. Keratin Therapy Shampoo 500ml"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-medium text-gray-700">Brand</label>
                  <input
                    type="text"
                    value={newProduct.brand}
                    onChange={(e) => setNewProduct({ ...newProduct, brand: e.target.value })}
                    placeholder="e.g. L'Oreal"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                  />
                </div>
                <div>
                  <label className="font-medium text-gray-700">Category</label>
                  <select
                    value={newProduct.category_id}
                    onChange={(e) => setNewProduct({ ...newProduct, category_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                  >
                    <option value="">Select Category</option>
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-medium text-gray-700">SKU Code</label>
                  <input
                    type="text"
                    value={newProduct.sku}
                    onChange={(e) => setNewProduct({ ...newProduct, sku: e.target.value })}
                    placeholder="e.g. SHM-001"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                  />
                </div>
                <div>
                  <label className="font-medium text-gray-700">Barcode</label>
                  <input
                    type="text"
                    value={newProduct.barcode}
                    onChange={(e) => setNewProduct({ ...newProduct, barcode: e.target.value })}
                    placeholder="e.g. 890123456789"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-medium text-gray-700">Cost Price (₹)</label>
                  <input
                    type="number"
                    min="0"
                    value={newProduct.cost_price}
                    onChange={(e) => setNewProduct({ ...newProduct, cost_price: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                  />
                </div>
                <div>
                  <label className="font-medium text-gray-700">Retail Price (₹) *</label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={newProduct.retail_price}
                    onChange={(e) => setNewProduct({ ...newProduct, retail_price: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-medium text-gray-700">Initial Stock</label>
                  <input
                    type="number"
                    min="0"
                    value={newProduct.stock_quantity}
                    onChange={(e) => setNewProduct({ ...newProduct, stock_quantity: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                  />
                </div>
                <div>
                  <label className="font-medium text-gray-700">Low Stock Alert Level</label>
                  <input
                    type="number"
                    min="1"
                    value={newProduct.low_stock_threshold}
                    onChange={(e) => setNewProduct({ ...newProduct, low_stock_threshold: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                  />
                </div>
              </div>

              <div className="pt-3 flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setIsAddProductOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-brand-600 text-white rounded-lg font-semibold hover:bg-brand-700"
                >
                  Create Product
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Adjust Stock Modal */}
      {isStockAdjustOpen && selectedProduct && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <div>
                <h3 className="font-bold text-gray-900 text-lg">Adjust Stock</h3>
                <p className="text-xs text-gray-500">{selectedProduct.name}</p>
              </div>
              <button onClick={() => setIsStockAdjustOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleStockAdjustment} className="space-y-3 text-sm">
              <div>
                <label className="font-medium text-gray-700">Adjustment Type</label>
                <select
                  value={stockAdjustment.movement_type}
                  onChange={(e) => setStockAdjustment({ ...stockAdjustment, movement_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                >
                  <option value="IN">Restock / Received from Supplier (+)</option>
                  <option value="OUT">Internal Salon Use / Damaged (-)</option>
                  <option value="ADJUSTMENT">Inventory Audit Correction</option>
                  <option value="RETURN">Customer Return (+)</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-medium text-gray-700">Quantity</label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={stockAdjustment.quantity}
                    onChange={(e) => setStockAdjustment({ ...stockAdjustment, quantity: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                  />
                </div>
                <div>
                  <label className="font-medium text-gray-700">Unit Cost (₹)</label>
                  <input
                    type="number"
                    min="0"
                    value={stockAdjustment.unit_cost}
                    onChange={(e) => setStockAdjustment({ ...stockAdjustment, unit_cost: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                  />
                </div>
              </div>

              <div>
                <label className="font-medium text-gray-700">Notes / Supplier Invoice #</label>
                <input
                  type="text"
                  value={stockAdjustment.notes}
                  onChange={(e) => setStockAdjustment({ ...stockAdjustment, notes: e.target.value })}
                  placeholder="e.g. Invoice #SUP-2026-88"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg mt-1"
                />
              </div>

              <div className="pt-3 flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setIsStockAdjustOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-brand-600 text-white rounded-lg font-semibold hover:bg-brand-700"
                >
                  Confirm Adjustment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
