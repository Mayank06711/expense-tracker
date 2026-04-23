import { useState } from "react";
import type { Expense } from "../types/expense";

interface Props {
  expenses: Expense[];
  pendingIds: Set<string>;
  totalAmount: string;
  loading: boolean;
  onDelete: (id: string) => void;
}

function formatRupees(amount: string): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
  }).format(parseFloat(amount));
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function ExpenseTable({ expenses, pendingIds, totalAmount, loading, onDelete }: Props) {
  const [confirmId, setConfirmId] = useState<string | null>(null);

  if (loading) {
    return (
      <div className="py-16 text-center opacity-50">
        <div className="inline-block w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin mb-2" />
        <p className="text-sm">Loading expenses...</p>
      </div>
    );
  }

  if (expenses.length === 0) {
    return (
      <div className="py-16 text-center opacity-40">
        <p className="text-lg mb-1">No expenses yet</p>
        <p className="text-sm">Click "+ Add Expense" to get started</p>
      </div>
    );
  }

  const handleDelete = (id: string) => {
    if (confirmId === id) {
      onDelete(id);
      setConfirmId(null);
    } else {
      setConfirmId(id);
      // Auto-cancel after 3s
      setTimeout(() => setConfirmId((prev) => (prev === id ? null : prev)), 3000);
    }
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr
            className="border-b"
            style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-muted)" }}
          >
            <th className="text-left px-3 sm:px-4 py-3 font-medium opacity-70">Date</th>
            <th className="text-left px-3 sm:px-4 py-3 font-medium opacity-70">Category</th>
            <th className="text-left px-3 sm:px-4 py-3 font-medium opacity-70 hidden sm:table-cell">Description</th>
            <th className="text-right px-3 sm:px-4 py-3 font-medium opacity-70">Amount</th>
            <th className="w-10 px-2 py-3"></th>
          </tr>
        </thead>
        <tbody>
          {expenses.map((exp, i) => {
            const isPending = pendingIds.has(exp.id);
            return (
              <tr
                key={exp.id}
                className="border-b transition-all"
                style={{
                  borderColor: "var(--border)",
                  backgroundColor: i % 2 === 1 ? "var(--bg-muted)" : "transparent",
                  opacity: isPending ? 0.4 : 1,
                }}
              >
                <td className="px-3 sm:px-4 py-3 whitespace-nowrap">{formatDate(exp.date)}</td>
                <td className="px-3 sm:px-4 py-3 capitalize">{exp.category}</td>
                <td className="px-3 sm:px-4 py-3 opacity-70 hidden sm:table-cell">
                  {exp.description || "\u2014"}
                </td>
                <td className="px-3 sm:px-4 py-3 text-right font-mono tabular-nums">
                  {formatRupees(exp.amount)}
                </td>
                <td className="px-2 py-3 text-center">
                  {!isPending && (
                    <button
                      onClick={() => handleDelete(exp.id)}
                      className="opacity-30 hover:opacity-100 cursor-pointer transition-opacity text-xs"
                      style={{ color: confirmId === exp.id ? "var(--error)" : "var(--text)" }}
                      title={confirmId === exp.id ? "Click again to confirm" : "Delete"}
                    >
                      {confirmId === exp.id ? "Sure?" : "\u2715"}
                    </button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
        <tfoot>
          <tr
            className="border-t-2"
            style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-muted)" }}
          >
            <td colSpan={3} className="px-3 sm:px-4 py-3 font-semibold text-right hidden sm:table-cell">
              Total ({expenses.length} expense{expenses.length !== 1 ? "s" : ""})
            </td>
            <td colSpan={1} className="px-3 py-3 font-semibold text-right sm:hidden">
              Total
            </td>
            <td className="px-3 sm:px-4 py-3 font-semibold text-right font-mono tabular-nums">
              {formatRupees(totalAmount)}
            </td>
            <td></td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
