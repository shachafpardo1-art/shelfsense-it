import { NavLink, Outlet, useLocation } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/inventory", label: "Inventory" },
];

export function Layout(): JSX.Element {
  const location = useLocation();
  const pageMeta =
    location.pathname === "/inventory"
      ? {
          label: "Inventory",
          title: "Warehouse inventory",
          description: "Search, adjust, and review active hardware stock across the current catalogue.",
        }
      : {
          label: "Dashboard",
          title: "Operational inventory overview",
          description: "Monitor inventory value, reorder pressure, and stock availability in real time.",
        };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-panel">
          <div className="brand-mark">
            <span className="brand-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" focusable="false">
                <path d="M4.75 6.5 12 3l7.25 3.5v11L12 21l-7.25-3.5v-11Z" />
                <path d="M4.75 6.5 12 10l7.25-3.5M12 10v11" />
              </svg>
            </span>
            <div className="brand-copy">
              <span className="brand-kicker">Hardware inventory visibility</span>
              <h1>ShelfSense IT</h1>
            </div>
          </div>
          <p>Monitor stock movement, reorder pressure, and asset availability across your active inventory.</p>
        </div>

        <nav className="nav-list" aria-label="Primary">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) => `nav-link${isActive ? " nav-link-active" : ""}`}
            >
              <span className="nav-link-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="content-shell">
        <header className="content-header">
          <div>
            <span className="header-kicker">{pageMeta.label}</span>
            <h2>{pageMeta.title}</h2>
            <p>{pageMeta.description}</p>
          </div>
          <div className="header-meta">
            <span className="header-chip">Live API data</span>
            <span className="header-chip header-chip-muted">ShelfSense IT</span>
          </div>
        </header>

        <div className="content-panel">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
