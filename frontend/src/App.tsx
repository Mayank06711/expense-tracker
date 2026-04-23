import { useState } from "react";
import { useTheme } from "./hooks/useTheme";
import { useExpenses } from "./hooks/useExpenses";
import { ThemeToggle } from "./components/ThemeToggle";
import { ExpenseForm } from "./components/ExpenseForm";
import { ExpenseFilter } from "./components/ExpenseFilter";
import { ExpenseTable } from "./components/ExpenseTable";
import { ExpenseSummary } from "./components/ExpenseSummary";

function App() {
  const { theme, toggle } = useTheme();
  const [formOpen, setFormOpen] = useState(false);
  const {
    expenses,
    pendingIds,
    totalAmount,
    categories,
    summary,
    summaryTotal,
    filter,
    setFilter,
    sort,
    setSort,
    fromDate,
    setFromDate,
    toDate,
    setToDate,
    loading,
    error,
    refetch,
    addOptimistic,
    removeOptimistic,
    confirmOptimistic,
    deleteExpense,
  } = useExpenses();

  return (
    <div
      className="min-h-screen transition-colors"
      style={{ backgroundColor: "var(--bg)", color: "var(--text)" }}
    >
      <div className="max-w-6xl mx-auto px-3 sm:px-6 py-4 sm:py-6">
        {/* Header */}
        <header className="flex justify-between items-center mb-5">
          <div>
            <h1 className="text-lg sm:text-xl font-bold tracking-tight">
              Expense Tracker
            </h1>
            <p className="text-xs opacity-40 mt-0.5 hidden sm:block">
              Track where your money goes
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setFormOpen(true)}
              className="px-3 sm:px-4 py-2 rounded-md border cursor-pointer transition-colors text-sm font-medium"
              style={{
                backgroundColor: "var(--bg-btn)",
                color: "var(--text-btn)",
                borderColor: "var(--border)",
              }}
            >
              + Add Expense
            </button>
            <ThemeToggle theme={theme} onToggle={toggle} />
          </div>
        </header>

        {/* Error banner */}
        {error && (
          <div
            className="p-3 mb-4 rounded-md border text-sm"
            style={{ color: "var(--error)", borderColor: "var(--error)" }}
          >
            {error}
          </div>
        )}

        {/* Filters bar */}
        <div
          className="rounded-t-lg border border-b-0 px-3 sm:px-4 py-3 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2"
          style={{
            borderColor: "var(--border)",
            backgroundColor: "var(--bg-muted)",
          }}
        >
          <h2 className="text-sm font-semibold opacity-70">Expenses</h2>
          <ExpenseFilter
            categories={categories}
            filter={filter}
            onFilterChange={setFilter}
            sort={sort}
            onSortChange={setSort}
            fromDate={fromDate}
            onFromDateChange={setFromDate}
            toDate={toDate}
            onToDateChange={setToDate}
          />
        </div>

        {/* Expense table */}
        <div
          className="border rounded-b-lg overflow-hidden mb-5"
          style={{ borderColor: "var(--border)" }}
        >
          <ExpenseTable
            expenses={expenses}
            pendingIds={pendingIds}
            totalAmount={totalAmount}
            loading={loading}
            onDelete={deleteExpense}
          />
        </div>

        {/* Summary below table */}
        {summary.length > 0 && (
          <div
            className="rounded-lg border p-4 sm:p-5"
            style={{ borderColor: "var(--border)" }}
          >
            <ExpenseSummary summary={summary} total={summaryTotal} />
          </div>
        )}
      </div>

      {/* Add Expense Modal */}
      <ExpenseForm
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSuccess={refetch}
        onOptimisticAdd={addOptimistic}
        onOptimisticRemove={removeOptimistic}
        onOptimisticConfirm={confirmOptimistic}
        existingCategories={categories}
      />
    </div>
  );
}

export default App;
