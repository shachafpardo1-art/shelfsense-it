import { useEffect, useMemo, useState, type FormEvent } from "react";

import { ConfirmDialog } from "../components/ConfirmDialog";
import { ItemFormModal } from "../components/ItemFormModal";
import { StatusBadge } from "../components/StatusBadge";
import { ApiError, createItem, deleteItem, fetchItems, updateItem } from "../lib/api";
import type { Item, ItemCreateInput, ItemUpdateInput } from "../types/api";

interface InventoryPageProps {
  onInventoryChanged: () => void;
  refreshToken: number;
}

function formatCurrency(value: number | string): string {
  const numericValue = typeof value === "number" ? value : Number(value);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(numericValue);
}

export function InventoryPage({ onInventoryChanged, refreshToken }: InventoryPageProps): JSX.Element {
  const [items, setItems] = useState<Item[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [formMode, setFormMode] = useState<"create" | "edit" | null>(null);
  const [selectedItem, setSelectedItem] = useState<Item | null>(null);
  const [formBusy, setFormBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Item | null>(null);
  const [deleteBusy, setDeleteBusy] = useState(false);

  async function loadItems(currentSearch = search, currentCategory = category): Promise<void> {
    setLoading(true);
    setError(null);

    try {
      const response = await fetchItems({
        search: currentSearch.trim() || undefined,
        category: currentCategory || undefined,
      });
      setItems(response);
    } catch (caughtError) {
      setError(caughtError instanceof ApiError ? caughtError.detail : "Unable to load inventory items");
    } finally {
      setLoading(false);
    }
  }

  async function loadCategories(): Promise<void> {
    try {
      const response = await fetchItems();
      const uniqueCategories = [...new Set(response.map((item) => item.category))].sort((left, right) =>
        left.localeCompare(right),
      );
      setCategories(uniqueCategories);
    } catch {
      setCategories([]);
    }
  }

  useEffect(() => {
    void loadItems();
    void loadCategories();
  }, [refreshToken]);

  const activeFilters = useMemo(
    () => ({
      hasSearch: search.trim().length > 0,
      hasCategory: category.length > 0,
    }),
    [search, category],
  );

  async function handleApplyFilters(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setFeedback(null);
    await loadItems();
  }

  async function handleClearFilters(): Promise<void> {
    setSearch("");
    setCategory("");
    setFeedback(null);
    await loadItems("", "");
  }

  async function refreshAfterMutation(message: string): Promise<void> {
    setFeedback(message);
    await Promise.all([loadItems(), loadCategories()]);
    onInventoryChanged();
  }

  async function handleCreate(payload: ItemCreateInput | ItemUpdateInput): Promise<void> {
    setFormBusy(true);
    setFormError(null);

    try {
      await createItem(payload as ItemCreateInput);
      setFormMode(null);
      await refreshAfterMutation("Item created successfully.");
    } catch (caughtError) {
      setFormError(caughtError instanceof ApiError ? caughtError.detail : "Unable to create item");
    } finally {
      setFormBusy(false);
    }
  }

  async function handleUpdate(payload: ItemCreateInput | ItemUpdateInput): Promise<void> {
    if (!selectedItem) {
      return;
    }

    setFormBusy(true);
    setFormError(null);

    try {
      await updateItem(selectedItem.id, payload);
      setFormMode(null);
      setSelectedItem(null);
      await refreshAfterMutation("Item updated successfully.");
    } catch (caughtError) {
      setFormError(caughtError instanceof ApiError ? caughtError.detail : "Unable to update item");
    } finally {
      setFormBusy(false);
    }
  }

  async function handleDelete(): Promise<void> {
    if (!deleteTarget) {
      return;
    }

    setDeleteBusy(true);

    try {
      await deleteItem(deleteTarget.id);
      setDeleteTarget(null);
      await refreshAfterMutation("Item deleted successfully.");
    } catch (caughtError) {
      setError(caughtError instanceof ApiError ? caughtError.detail : "Unable to delete item");
    } finally {
      setDeleteBusy(false);
    }
  }

  return (
    <section className="page-section">
      <div className="page-header page-header-split">
        <div>
          <span className="eyebrow">Asset tracking</span>
          <h2>Inventory catalogue</h2>
          <p className="page-copy">Track stock levels, reorder thresholds, and hardware pricing in one place.</p>
        </div>
        <button
          type="button"
          className="button button-primary"
          onClick={() => {
            setSelectedItem(null);
            setFormError(null);
            setFormMode("create");
          }}
        >
          Create item
        </button>
      </div>

      <form className="filter-bar" onSubmit={handleApplyFilters}>
        <label className="field">
          <span>Search</span>
          <input
            type="search"
            placeholder="Search by item name or SKU"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>

        <label className="field">
          <span>Category</span>
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="">All categories</option>
            {categories.map((categoryOption) => (
              <option key={categoryOption} value={categoryOption}>
                {categoryOption}
              </option>
            ))}
          </select>
        </label>

        <div className="filter-actions">
          <button type="submit" className="button button-primary" disabled={loading}>
            Apply filters
          </button>
          <button
            type="button"
            className="button button-secondary"
            onClick={() => {
              void handleClearFilters();
            }}
            disabled={loading || (!activeFilters.hasSearch && !activeFilters.hasCategory)}
          >
            Clear filters
          </button>
        </div>
      </form>

      {feedback && <div className="inline-message inline-success">{feedback}</div>}
      {error && <div className="panel-state panel-error">{error}</div>}
      {loading && <div className="panel-state">Loading inventory items...</div>}

      {!loading && !error && items.length === 0 && (
        <div className="panel-state panel-empty">
          <strong>No matching inventory items</strong>
          <span>
            Adjust the search or category filter, or create a new item to populate the catalogue.
          </span>
        </div>
      )}

      {!loading && !error && items.length > 0 && (
        <div className="table-panel">
          <div className="table-toolbar">
            <div>
              <span className="table-kicker">Active inventory</span>
              <strong>{items.length} item{items.length === 1 ? "" : "s"}</strong>
            </div>
            <span className="table-hint">Filters are applied on the server using the existing API.</span>
          </div>
          <table className="inventory-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Category</th>
                <th>SKU</th>
                <th>Quantity</th>
                <th>Reorder level</th>
                <th>Unit price</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td data-label="Name">
                    <div className="item-name-cell">
                      <strong>{item.name}</strong>
                      <span>Updated {new Date(item.updated_at).toLocaleDateString()}</span>
                    </div>
                  </td>
                  <td data-label="Category">
                    <span className="category-pill">{item.category}</span>
                  </td>
                  <td data-label="SKU">{item.sku}</td>
                  <td data-label="Quantity">{item.quantity}</td>
                  <td data-label="Reorder level">{item.reorder_level}</td>
                  <td data-label="Unit price">{formatCurrency(item.unit_price)}</td>
                  <td data-label="Status">
                    <StatusBadge status={item.status} />
                  </td>
                  <td data-label="Actions">
                    <div className="table-actions">
                      <button
                        type="button"
                        className="button button-secondary button-small"
                        onClick={() => {
                          setSelectedItem(item);
                          setFormError(null);
                          setFormMode("edit");
                        }}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        className="button button-danger button-small"
                        onClick={() => {
                          setDeleteTarget(item);
                          setFeedback(null);
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {formMode && (
        <ItemFormModal
          mode={formMode}
          item={formMode === "edit" ? selectedItem : null}
          busy={formBusy}
          apiError={formError}
          onClose={() => {
            if (!formBusy) {
              setFormMode(null);
              setSelectedItem(null);
            }
          }}
          onSubmit={formMode === "create" ? handleCreate : handleUpdate}
        />
      )}

      {deleteTarget && (
        <ConfirmDialog
          title="Delete inventory item"
          message={`Soft delete ${deleteTarget.name} (${deleteTarget.sku})? This removes it from active inventory views.`}
          confirmLabel="Delete item"
          busy={deleteBusy}
          onCancel={() => {
            if (!deleteBusy) {
              setDeleteTarget(null);
            }
          }}
          onConfirm={() => {
            void handleDelete();
          }}
        />
      )}
    </section>
  );
}
