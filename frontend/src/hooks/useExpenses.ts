import { useState, useEffect, useCallback } from "react";
import { getExpenses, getSummary, deleteExpense as apiDelete } from "../api/expenses";
import type { Expense, CategorySummary } from "../types/expense";

export function useExpenses() {
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [totalAmount, setTotalAmount] = useState("0.00");
  const [count, setCount] = useState(0);
  const [categories, setCategories] = useState<string[]>([]);
  const [summary, setSummary] = useState<CategorySummary[]>([]);
  const [summaryTotal, setSummaryTotal] = useState("0.00");

  // Optimistic: IDs of expenses pending server confirmation
  const [pendingIds, setPendingIds] = useState<Set<string>>(new Set());

  const [filter, setFilter] = useState<string>("");
  const [sort, setSort] = useState<string>("date_desc");
  const [fromDate, setFromDate] = useState<string>("");
  const [toDate, setToDate] = useState<string>("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchExpenses = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getExpenses(
        filter || undefined,
        sort,
        fromDate || undefined,
        toDate || undefined
      );
      setExpenses(res.data.expenses);
      setTotalAmount(res.data.total_amount);
      setCount(res.data.count);
      setPendingIds(new Set()); // Clear pending, server is source of truth now
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load expenses");
    } finally {
      setLoading(false);
    }
  }, [filter, sort, fromDate, toDate]);

  const fetchSummary = useCallback(async () => {
    try {
      const res = await getSummary();
      setSummary(res.data.by_category);
      setSummaryTotal(res.data.total);
      const cats = res.data.by_category.map((c) => c.category).sort();
      setCategories(cats);
    } catch {
      // non-critical
    }
  }, []);

  // Optimistic add: inject expense into list before server confirms
  const addOptimistic = useCallback((expense: Expense) => {
    setPendingIds((prev) => new Set(prev).add(expense.id));
    setExpenses((prev) => [expense, ...prev]);
  }, []);

  // Remove optimistic expense on failure
  const removeOptimistic = useCallback((id: string) => {
    setPendingIds((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
    setExpenses((prev) => prev.filter((e) => e.id !== id));
  }, []);

  // Confirm optimistic expense succeeded
  const confirmOptimistic = useCallback((id: string) => {
    setPendingIds((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
  }, []);

  const deleteExpense = useCallback(async (id: string) => {
    // Optimistic: remove immediately
    const removed = expenses.find((e) => e.id === id);
    setExpenses((prev) => prev.filter((e) => e.id !== id));
    try {
      await apiDelete(id);
      fetchSummary();
    } catch {
      // Rollback: put it back
      if (removed) setExpenses((prev) => [...prev, removed]);
      setError("Failed to delete expense");
    }
  }, [expenses, fetchSummary]);

  const refetch = useCallback(() => {
    fetchExpenses();
    fetchSummary();
  }, [fetchExpenses, fetchSummary]);

  useEffect(() => {
    fetchExpenses();
  }, [fetchExpenses]);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  return {
    expenses,
    pendingIds,
    totalAmount,
    count,
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
  };
}
