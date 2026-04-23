import { useState, useRef } from "react";
import { createExpense } from "../api/expenses";
import { generateId } from "../utils/idempotency";
import type { Expense } from "../types/expense";

interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  onOptimisticAdd: (expense: Expense) => void;
  onOptimisticRemove: (id: string) => void;
  onOptimisticConfirm: (id: string) => void;
  existingCategories: string[];
}

const SUGGESTED_CATEGORIES = [
  "food", "transport", "groceries", "entertainment",
  "utilities", "health", "shopping", "rent", "education", "other",
];

const LARGE_AMOUNT_THRESHOLD = 100000;
const THROTTLE_MS = 200;

export function ExpenseForm({
  open, onClose, onSuccess,
  onOptimisticAdd, onOptimisticRemove, onOptimisticConfirm,
  existingCategories,
}: Props) {
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState("");
  const [description, setDescription] = useState("");
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showLargeWarning, setShowLargeWarning] = useState(false);
  const lastSubmitTime = useRef(0);
  const idempotencyId = useRef(generateId());

  const allCategories = [
    ...new Set([...SUGGESTED_CATEGORIES, ...existingCategories]),
  ].sort();

  const resetForm = () => {
    setAmount("");
    setCategory("");
    setDescription("");
    setDate(new Date().toISOString().split("T")[0]);
    setError(null);
    setShowLargeWarning(false);
    idempotencyId.current = generateId();
  };

  const doSubmit = async () => {
    const numAmount = parseFloat(amount);
    setSubmitting(true);
    setError(null);
    setShowLargeWarning(false);
    lastSubmitTime.current = Date.now();

    const currentId = idempotencyId.current;
    const catNormalized = category.trim().toLowerCase();

    const optimisticExpense: Expense = {
      id: currentId,
      amount: numAmount.toFixed(2),
      category: catNormalized,
      description: description.trim(),
      date,
      created_at: new Date().toISOString(),
    };
    onOptimisticAdd(optimisticExpense);
    onClose();

    try {
      await createExpense({
        id: currentId,
        amount: numAmount.toFixed(2),
        category: catNormalized,
        description: description.trim(),
        date,
      });
      onOptimisticConfirm(currentId);
      resetForm();
      onSuccess();
    } catch (err) {
      onOptimisticRemove(currentId);
      setError(err instanceof Error ? err.message : "Failed to create expense");
    } finally {
      setTimeout(() => setSubmitting(false), THROTTLE_MS);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const now = Date.now();
    if (now - lastSubmitTime.current < THROTTLE_MS || submitting) return;

    const numAmount = parseFloat(amount);
    if (!amount || isNaN(numAmount) || numAmount <= 0) {
      setError("Amount must be a positive number");
      return;
    }
    if (!category.trim()) {
      setError("Please enter or select a category");
      return;
    }
    if (!date) {
      setError("Date is required");
      return;
    }

    // Inline warning for large amounts
    if (numAmount >= LARGE_AMOUNT_THRESHOLD && !showLargeWarning) {
      setShowLargeWarning(true);
      return;
    }

    // Validate on client before optimistic add — catch what we can
    const numStr = numAmount.toFixed(2);
    if (parseFloat(numStr) > 9999999.99) {
      setError("Amount exceeds maximum allowed");
      return;
    }

    await doSubmit();
  };

  if (!open) return null;

  const inputClass = "w-full px-3 py-2.5 border rounded-md outline-none transition-colors";
  const inputStyle = {
    backgroundColor: "var(--bg-input)",
    color: "var(--text)",
    borderColor: "var(--border)",
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/50" />
      <div
        className="relative w-full max-w-md rounded-lg border p-5 sm:p-6"
        style={{ backgroundColor: "var(--bg)", borderColor: "var(--border)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-5">
          <h2 className="text-lg font-semibold">New Expense</h2>
          <button onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-md border cursor-pointer"
            style={{ borderColor: "var(--border)", color: "var(--text)" }}
          >&times;</button>
        </div>

        {error && (
          <div className="p-3 mb-4 text-sm rounded-md border"
            style={{ color: "var(--error)", borderColor: "var(--error)" }}
          >{error}</div>
        )}

        {/* Large amount inline confirmation */}
        {showLargeWarning && (
          <div className="p-3 mb-4 rounded-md border text-sm"
            style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-muted)" }}
          >
            <p className="mb-2">
              You're adding <strong>{"\u20B9"}{parseFloat(amount).toLocaleString("en-IN")}</strong> as a single expense. Are you sure?
            </p>
            <div className="flex gap-2">
              <button onClick={() => setShowLargeWarning(false)}
                className="px-3 py-1 text-xs rounded border cursor-pointer"
                style={{ borderColor: "var(--border)" }}
              >Go back</button>
              <button onClick={doSubmit}
                className="px-3 py-1 text-xs rounded border cursor-pointer font-medium"
                style={{ backgroundColor: "var(--bg-btn)", color: "var(--text-btn)", borderColor: "var(--border)" }}
              >Yes, add it</button>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm mb-1.5 opacity-70">Amount</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm opacity-50">&#8377;</span>
              <input type="number" step="0.01" min="0.01" value={amount}
                onChange={(e) => { setAmount(e.target.value); setShowLargeWarning(false); }}
                placeholder="0.00" required
                className={`${inputClass} pl-7`} style={inputStyle} />
            </div>
          </div>

          <div>
            <label className="block text-sm mb-1.5 opacity-70">Category</label>
            <input type="text" list="category-suggestions" value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="Type or select a category" required
              className={inputClass} style={inputStyle} />
            <datalist id="category-suggestions">
              {allCategories.map((cat) => (<option key={cat} value={cat} />))}
            </datalist>
          </div>

          <div>
            <label className="block text-sm mb-1.5 opacity-70">Date</label>
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
              max={new Date().toISOString().split("T")[0]} required
              className={inputClass} style={inputStyle} />
          </div>

          <div>
            <label className="block text-sm mb-1.5 opacity-70">
              Description <span className="opacity-50">(optional)</span>
            </label>
            <input type="text" value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What was this for?" className={inputClass} style={inputStyle} />
          </div>

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose}
              className="flex-1 py-2.5 rounded-md border cursor-pointer text-sm"
              style={{ borderColor: "var(--border)", color: "var(--text)" }}
            >Cancel</button>
            <button type="submit" disabled={submitting}
              className="flex-1 py-2.5 rounded-md border cursor-pointer text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed"
              style={{ backgroundColor: "var(--bg-btn)", color: "var(--text-btn)", borderColor: "var(--border)" }}
            >{submitting ? "Adding..." : "Add Expense"}</button>
          </div>
        </form>
      </div>
    </div>
  );
}
