interface Props {
  theme: "light" | "dark";
  onToggle: () => void;
}

export function ThemeToggle({ theme, onToggle }: Props) {
  return (
    <button
      onClick={onToggle}
      className="relative w-14 h-7 rounded-full border cursor-pointer transition-colors"
      style={{
        backgroundColor: theme === "dark" ? "#fafafa" : "#000000",
        borderColor: "var(--border)",
      }}
      aria-label="Toggle theme"
    >
      <span
        className="absolute top-0.5 w-6 h-6 rounded-full transition-all flex items-center justify-center text-xs"
        style={{
          left: theme === "dark" ? "calc(100% - 1.6rem)" : "0.1rem",
          backgroundColor: theme === "dark" ? "#0a0a0a" : "#ffffff",
        }}
      >
        {theme === "dark" ? "☀" : "☾"}
      </span>
    </button>
  );
}
