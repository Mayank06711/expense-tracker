export interface Expense {
  id: string;
  amount: string;
  category: string;
  description: string;
  date: string;
  created_at: string;
}

export interface ExpenseCreate {
  id: string;
  amount: string;
  category: string;
  description: string;
  date: string;
}

export interface ExpenseListData {
  expenses: Expense[];
  total_amount: string;
  count: number;
}

export interface CategorySummary {
  category: string;
  total: string;
  count: number;
}

export interface SummaryData {
  total: string;
  by_category: CategorySummary[];
}

export interface ApiResponse<T> {
  success: boolean;
  status: number;
  message: string;
  data: T;
  metadata: Record<string, unknown>;
}

export interface ApiError {
  success: false;
  error: string;
  error_code: string;
  metadata: Record<string, unknown>;
}
