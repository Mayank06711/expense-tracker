import type {
  ApiResponse,
  ApiError,
  ExpenseCreate,
  Expense,
  ExpenseListData,
  SummaryData,
} from "../types/expense";

const API_BASE = import.meta.env.VITE_API_URL || "/api";

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });

    const body = await res.json();

    if (!res.ok) {
      const err = body as ApiError;
      throw new Error(err.error || `Request failed (${res.status})`);
    }

    return body as ApiResponse<T>;
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("Request timed out. Please try again.");
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

export async function createExpense(
  data: ExpenseCreate
): Promise<ApiResponse<Expense>> {
  return request<Expense>("/expenses", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getExpenses(
  category?: string,
  sort: string = "date_desc",
  fromDate?: string,
  toDate?: string
): Promise<ApiResponse<ExpenseListData>> {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  params.set("sort", sort);
  if (fromDate) params.set("from_date", fromDate);
  if (toDate) params.set("to_date", toDate);
  const qs = params.toString();
  return request<ExpenseListData>(`/expenses${qs ? `?${qs}` : ""}`);
}

export async function deleteExpense(
  id: string
): Promise<ApiResponse<{ id: string }>> {
  return request<{ id: string }>(`/expenses/${id}`, { method: "DELETE" });
}

export async function getSummary(): Promise<ApiResponse<SummaryData>> {
  return request<SummaryData>("/expenses/summary");
}
