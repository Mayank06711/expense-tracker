import type { CategorySummary } from "../types/expense";

interface Props {
  summary: CategorySummary[];
  total: string;
}

function formatRupees(amount: string): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
  }).format(parseFloat(amount));
}

export function ExpenseSummary({ summary, total }: Props) {
  if (summary.length === 0) return null;

  const maxAmount = Math.max(...summary.map((s) => parseFloat(s.total)));

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-sm font-semibold opacity-70">Spending by Category</h2>
        <span className="text-sm font-semibold font-mono tabular-nums">
          Total: {formatRupees(total)}
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {summary.map((row) => {
          const pct =
            maxAmount > 0 ? (parseFloat(row.total) / maxAmount) * 100 : 0;
          return (
            <div
              key={row.category}
              className="p-3 rounded-md border"
              style={{ borderColor: "var(--border)" }}
            >
              <div className="flex justify-between text-sm mb-1.5">
                <span className="capitalize font-medium">{row.category}</span>
                <span className="font-mono tabular-nums text-xs">
                  {formatRupees(row.total)}
                </span>
              </div>
              <div
                className="w-full h-1.5 rounded-full overflow-hidden"
                style={{ backgroundColor: "var(--bg-muted)" }}
              >
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${pct}%`,
                    backgroundColor: "var(--text)",
                    opacity: 0.5,
                  }}
                />
              </div>
              <p className="text-xs mt-1 opacity-40">
                {row.count} expense{row.count !== 1 ? "s" : ""}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
