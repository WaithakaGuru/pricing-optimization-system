import { useState } from "react";
import { productsApi } from "../../api/client";

interface ProductFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

export default function ProductForm({ onSuccess, onCancel }: ProductFormProps) {
  const [formData, setFormData] = useState({
    id: "",
    name: "",
    cost_price: "",
    min_price: "",
    max_price: "",
    current_price: "",
    initial_quantity: "0",
    reorder_point: "50",
    reorder_quantity: "100",
    warehouse_location: "Main Warehouse",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Basic validation
      if (!formData.id || !formData.name) {
        throw new Error("Product ID and Name are required");
      }

      const costPrice = parseFloat(formData.cost_price);
      const minPrice = parseFloat(formData.min_price);
      const maxPrice = parseFloat(formData.max_price);
      const currentPrice = parseFloat(formData.current_price);
      const quantity = parseInt(formData.initial_quantity);
      const reorderPoint = parseInt(formData.reorder_point);
      const reorderQty = parseInt(formData.reorder_quantity);

      if (
        isNaN(costPrice) ||
        isNaN(minPrice) ||
        isNaN(maxPrice) ||
        isNaN(currentPrice)
      ) {
        throw new Error("All prices must be valid numbers");
      }

      if (isNaN(quantity) || isNaN(reorderPoint) || isNaN(reorderQty)) {
        throw new Error("Quantities must be valid numbers");
      }

      if (costPrice < 0 || minPrice < 0 || maxPrice < 0 || currentPrice < 0) {
        throw new Error("Prices cannot be negative");
      }

      if (minPrice > maxPrice) {
        throw new Error("Min price cannot exceed max price");
      }

      if (!(minPrice <= currentPrice && currentPrice <= maxPrice)) {
        throw new Error("Current price must be between min and max price");
      }

      // Call API to create product
      await productsApi.create({
        id: formData.id,
        name: formData.name,
        cost_price: costPrice,
        min_price: minPrice,
        max_price: maxPrice,
        current_price: currentPrice,
        initial_quantity: quantity,
        reorder_point: reorderPoint,
        reorder_quantity: reorderQty,
        warehouse_location: formData.warehouse_location,
      });

      setSuccess(true);
      setFormData({
        id: "",
        name: "",
        cost_price: "",
        min_price: "",
        max_price: "",
        current_price: "",
        initial_quantity: "0",
        reorder_point: "50",
        reorder_quantity: "100",
        warehouse_location: "Main Warehouse",
      });

      setTimeout(() => {
        setSuccess(false);
        onSuccess?.();
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create product");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">Add New Product</h2>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
          Product created successfully!
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Product ID */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Product ID *
          </label>
          <input
            type="text"
            name="id"
            value={formData.id}
            onChange={handleChange}
            placeholder="e.g., PROD-001"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            required
            disabled={loading}
          />
        </div>

        {/* Product Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Product Name *
          </label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="e.g., Cabbage"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            required
            disabled={loading}
          />
        </div>

        {/* Cost Price */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Cost Price ($) *
          </label>
          <input
            type="number"
            name="cost_price"
            value={formData.cost_price}
            onChange={handleChange}
            placeholder="0.00"
            step="0.01"
            min="0"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            required
            disabled={loading}
          />
        </div>

        {/* Min Price */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Min Price ($) *
          </label>
          <input
            type="number"
            name="min_price"
            value={formData.min_price}
            onChange={handleChange}
            placeholder="0.00"
            step="0.01"
            min="0"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            required
            disabled={loading}
          />
        </div>

        {/* Max Price */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Max Price ($) *
          </label>
          <input
            type="number"
            name="max_price"
            value={formData.max_price}
            onChange={handleChange}
            placeholder="0.00"
            step="0.01"
            min="0"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            required
            disabled={loading}
          />
        </div>

        {/* Current Price */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Current Price ($) *
          </label>
          <input
            type="number"
            name="current_price"
            value={formData.current_price}
            onChange={handleChange}
            placeholder="0.00"
            step="0.01"
            min="0"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            required
            disabled={loading}
          />
        </div>

        {/* Initial Quantity */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Initial Quantity
          </label>
          <input
            type="number"
            name="initial_quantity"
            value={formData.initial_quantity}
            onChange={handleChange}
            placeholder="0"
            min="0"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            disabled={loading}
          />
        </div>

        {/* Reorder Point */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Reorder Point
          </label>
          <input
            type="number"
            name="reorder_point"
            value={formData.reorder_point}
            onChange={handleChange}
            placeholder="50"
            min="0"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            disabled={loading}
          />
        </div>

        {/* Reorder Quantity */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Reorder Quantity
          </label>
          <input
            type="number"
            name="reorder_quantity"
            value={formData.reorder_quantity}
            onChange={handleChange}
            placeholder="100"
            min="0"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            disabled={loading}
          />
        </div>

        {/* Warehouse Location */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Warehouse Location
          </label>
          <input
            type="text"
            name="warehouse_location"
            value={formData.warehouse_location}
            onChange={handleChange}
            placeholder="Main Warehouse"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            disabled={loading}
          />
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          type="submit"
          className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors disabled:bg-blue-400"
          disabled={loading}
        >
          {loading ? "Creating..." : "Create Product"}
        </button>

        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 bg-gray-300 text-gray-800 py-2 px-4 rounded-md hover:bg-gray-400 transition-colors disabled:bg-gray-200"
            disabled={loading}
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
