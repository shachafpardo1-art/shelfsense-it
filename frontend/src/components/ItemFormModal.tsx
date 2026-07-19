import { useEffect, useState, type FormEvent } from "react";

import type { Item, ItemCreateInput, ItemUpdateInput } from "../types/api";

interface ItemFormModalProps {
  mode: "create" | "edit";
  item?: Item | null;
  busy: boolean;
  apiError: string | null;
  onClose: () => void;
  onSubmit: (payload: ItemCreateInput | ItemUpdateInput) => Promise<void>;
}

interface FormValues {
  name: string;
  category: string;
  sku: string;
  quantity: string;
  reorderLevel: string;
  unitPrice: string;
}

function toFormValues(item?: Item | null): FormValues {
  if (!item) {
    return {
      name: "",
      category: "",
      sku: "",
      quantity: "0",
      reorderLevel: "5",
      unitPrice: "0.00",
    };
  }

  return {
    name: item.name,
    category: item.category,
    sku: item.sku,
    quantity: String(item.quantity),
    reorderLevel: String(item.reorder_level),
    unitPrice: String(item.unit_price),
  };
}

function validateForm(values: FormValues): string | null {
  const requiredText = [
    ["Name", values.name],
    ["Category", values.category],
    ["SKU", values.sku],
  ] as const;

  for (const [label, value] of requiredText) {
    if (!value.trim()) {
      return `${label} is required`;
    }
  }

  const quantity = Number(values.quantity);
  const reorderLevel = Number(values.reorderLevel);
  const unitPrice = Number(values.unitPrice);

  if (!Number.isInteger(quantity) || quantity < 0) {
    return "Quantity must be a non-negative integer";
  }

  if (!Number.isInteger(reorderLevel) || reorderLevel < 0) {
    return "Reorder level must be a non-negative integer";
  }

  if (!Number.isFinite(unitPrice) || unitPrice < 0) {
    return "Unit price must be a non-negative number";
  }

  return null;
}

export function ItemFormModal({
  mode,
  item,
  busy,
  apiError,
  onClose,
  onSubmit,
}: ItemFormModalProps): JSX.Element {
  const [values, setValues] = useState<FormValues>(toFormValues(item));
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    setValues(toFormValues(item));
    setFormError(null);
  }, [item, mode]);

  function updateValue(field: keyof FormValues, value: string): void {
    setValues((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    const error = validateForm(values);
    if (error) {
      setFormError(error);
      return;
    }

    setFormError(null);

    const payload = {
      name: values.name.trim(),
      category: values.category.trim(),
      sku: values.sku.trim(),
      quantity: Number(values.quantity),
      reorder_level: Number(values.reorderLevel),
      unit_price: Number(values.unitPrice).toFixed(2),
    };

    await onSubmit(payload);
  }

  const title = mode === "create" ? "Create inventory item" : "Edit inventory item";
  const submitLabel = mode === "create" ? "Create item" : "Save changes";

  return (
    <div className="overlay" role="presentation">
      <div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="item-form-title">
        <div className="modal-header">
          <h2 id="item-form-title">{title}</h2>
          <button type="button" className="icon-button" onClick={onClose} disabled={busy} aria-label="Close form">
            ×
          </button>
        </div>

        <form className="form-grid" onSubmit={handleSubmit}>
          <label className="field field-required">
            <span>Name</span>
            <input
              type="text"
              placeholder="Example: NVIDIA GeForce RTX 5070"
              value={values.name}
              onChange={(event) => updateValue("name", event.target.value)}
              disabled={busy}
              required
            />
          </label>

          <label className="field field-required">
            <span>Category</span>
            <input
              type="text"
              placeholder="Example: GPU"
              value={values.category}
              onChange={(event) => updateValue("category", event.target.value)}
              disabled={busy}
              required
            />
          </label>

          <label className="field field-required">
            <span>SKU</span>
            <input
              type="text"
              placeholder="Example: GPU-RTX5070-001"
              value={values.sku}
              onChange={(event) => updateValue("sku", event.target.value)}
              disabled={busy}
              required
            />
          </label>

          <label className="field field-required">
            <span>Quantity</span>
            <input
              type="number"
              min="0"
              step="1"
              placeholder="0"
              value={values.quantity}
              onChange={(event) => updateValue("quantity", event.target.value)}
              disabled={busy}
              required
            />
          </label>

          <label className="field field-required">
            <span>Reorder level</span>
            <input
              type="number"
              min="0"
              step="1"
              placeholder="5"
              value={values.reorderLevel}
              onChange={(event) => updateValue("reorderLevel", event.target.value)}
              disabled={busy}
              required
            />
          </label>

          <label className="field field-required">
            <span>Unit price</span>
            <input
              type="number"
              min="0"
              step="0.01"
              placeholder="0.00"
              value={values.unitPrice}
              onChange={(event) => updateValue("unitPrice", event.target.value)}
              disabled={busy}
              required
            />
          </label>

          {(formError || apiError) && (
            <div className="inline-message inline-error" role="alert">
              {formError ?? apiError}
            </div>
          )}

          <div className="form-note">Fields marked with * are required.</div>

          <div className="modal-actions">
            <button type="button" className="button button-secondary" onClick={onClose} disabled={busy}>
              Cancel
            </button>
            <button type="submit" className="button button-primary" disabled={busy}>
              {busy ? (mode === "create" ? "Creating..." : "Saving...") : submitLabel}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
