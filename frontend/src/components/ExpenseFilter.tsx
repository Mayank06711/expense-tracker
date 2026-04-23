interface Props {
  categories: string[];
  filter: string;
  onFilterChange: (v: string) => void;
  sort: string;
  onSortChange: (v: string) => void;
  fromDate: string;
  onFromDateChange: (v: string) => void;
  toDate: string;
  onToDateChange: (v: string) => void;
}

export function ExpenseFilter({
  categories,
  filter,
  onFilterChange,
  sort,
  onSortChange,
  fromDate,
  onFromDateChange,
  toDate,
  onToDateChange,
}: Props) {
  const controlClass =
    "px-2.5 py-1.5 border rounded-md outline-none cursor-pointer text-xs";
  const controlStyle = {
    backgroundColor: "var(--bg-input)",
    color: "var(--text)",
    borderColor: "var(--border)",
  };

  const hasActiveFilters = filter || fromDate || toDate;

  return (
    <div className="flex flex-wrap gap-2 items-end">
      <select
        value={filter}
        onChange={(e) => onFilterChange(e.target.value)}
        className={controlClass}
        style={controlStyle}
      >
        <option value="">All Categories</option>
        {categories.map((cat) => (
          <option key={cat} value={cat}>
            {cat.charAt(0).toUpperCase() + cat.slice(1)}
          </option>
        ))}
      </select>

      <select
        value={sort}
        onChange={(e) => onSortChange(e.target.value)}
        className={controlClass}
        style={controlStyle}
      >
        <option value="date_desc">Newest</option>
        <option value="date_asc">Oldest</option>
      </select>

      <input
        type="date"
        value={fromDate}
        onChange={(e) => onFromDateChange(e.target.value)}
        className={controlClass}
        style={controlStyle}
        title="From date"
      />

      <input
        type="date"
        value={toDate}
        onChange={(e) => onToDateChange(e.target.value)}
        className={controlClass}
        style={controlStyle}
        title="To date"
      />

      {hasActiveFilters && (
        <button
          onClick={() => {
            onFilterChange("");
            onFromDateChange("");
            onToDateChange("");
          }}
          className="px-2.5 py-1.5 text-xs rounded-md border cursor-pointer"
          style={{ borderColor: "var(--border)", color: "var(--text)", opacity: 0.6 }}
        >
          Clear
        </button>
      )}
    </div>
  );
}
