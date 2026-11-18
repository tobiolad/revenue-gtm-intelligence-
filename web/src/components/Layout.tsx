import { useEffect, useState, type ReactNode } from "react";
import { NavLink } from "react-router-dom";

const NAV = [
  { to: "/", label: "Revenue Overview" },
  { to: "/funnel", label: "Pipeline Funnel" },
  { to: "/forecast", label: "Forecast" },
  { to: "/reps", label: "Rep Performance" },
  { to: "/deals", label: "Deals & Lost Reasons" },
];

type Theme = "light" | "dark";

function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => (localStorage.getItem("theme") as Theme | null) ?? "light");

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("theme", theme);
  }, [theme]);

  return { theme, toggle: () => setTheme((t) => (t === "light" ? "dark" : "light")) };
}

export function Layout({ children }: { children: ReactNode }) {
  const { theme, toggle } = useTheme();

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <aside
        style={{
          width: 230,
          flexShrink: 0,
          borderRight: "1px solid var(--border)",
          padding: "24px 16px",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div style={{ fontSize: 15, fontWeight: 600, padding: "0 8px 24px", lineHeight: 1.3 }}>
          Revenue & GTM Intelligence
        </div>
        <nav style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              style={({ isActive }) => ({
                padding: "8px 10px",
                borderRadius: 6,
                fontSize: 13,
                textDecoration: "none",
                color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
                background: isActive ? "var(--surface)" : "transparent",
                fontWeight: isActive ? 600 : 400,
              })}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <button
          onClick={toggle}
          style={{
            marginTop: "auto",
            alignSelf: "flex-start",
            background: "none",
            border: "1px solid var(--border)",
            borderRadius: 6,
            color: "var(--text-secondary)",
            fontSize: 12,
            padding: "6px 10px",
            cursor: "pointer",
          }}
        >
          {theme === "light" ? "Dark mode" : "Light mode"}
        </button>
      </aside>
      <main style={{ flex: 1, padding: "28px 32px", maxWidth: 1150 }}>{children}</main>
    </div>
  );
}
