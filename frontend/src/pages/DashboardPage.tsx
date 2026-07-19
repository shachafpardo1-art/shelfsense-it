import { useEffect, useState } from "react";

import { InventoryStatusChart } from "../components/InventoryStatusChart";
import { SummaryCard } from "../components/SummaryCard";
import { ApiError, fetchDashboardSummary } from "../lib/api";
import type { DashboardSummary } from "../types/api";

interface DashboardPageProps {
  refreshToken: number;
}

function formatCurrency(value: number | string): string {
  const numericValue = typeof value === "number" ? value : Number(value);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(numericValue);
}

export function DashboardPage({ refreshToken }: DashboardPageProps): JSX.Element {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadSummary(): Promise<void> {
      setLoading(true);
      setError(null);

      try {
        const response = await fetchDashboardSummary();
        if (!cancelled) {
          setSummary(response);
        }
      } catch (caughtError) {
        if (!cancelled) {
          setError(caughtError instanceof ApiError ? caughtError.detail : "Unable to load dashboard summary");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadSummary();

    return () => {
      cancelled = true;
    };
  }, [refreshToken]);

  const inStockCount = summary
    ? Math.max(0, summary.total_products - summary.low_stock_count - summary.out_of_stock_count)
    : 0;

  return (
    <section className="page-section">
      <div className="page-header">
        <div>
          <span className="eyebrow">Inventory visibility</span>
          <h2>Inventory dashboard</h2>
          <p className="page-copy">Track live stock posture, reorder pressure, and total inventory value from one operational view.</p>
        </div>
      </div>

      {loading && <div className="panel-state">Loading dashboard metrics...</div>}

      {!loading && error && <div className="panel-state panel-error">{error}</div>}

      {!loading && !error && summary && (
        <>
          <div className="summary-grid">
            <SummaryCard
              label="Total products"
              value={String(summary.total_products)}
              accent="neutral"
              helper="Active hardware items"
            />
            <SummaryCard
              label="Total units"
              value={String(summary.total_units)}
              accent="success"
              helper="Combined quantity on hand"
            />
            <SummaryCard
              label="Inventory value"
              value={formatCurrency(summary.total_inventory_value)}
              accent="neutral"
              helper="Current stock value"
            />
            <SummaryCard
              label="Low-stock count"
              value={String(summary.low_stock_count)}
              accent="warning"
              helper="Needs attention soon"
            />
            <SummaryCard
              label="Out-of-stock count"
              value={String(summary.out_of_stock_count)}
              accent="danger"
              helper="Unavailable right now"
            />
          </div>

          <div className="dashboard-grid">
            <InventoryStatusChart
              inStockCount={inStockCount}
              lowStockCount={summary.low_stock_count}
              outOfStockCount={summary.out_of_stock_count}
            />

            <section className="insight-card">
              <span className="chart-kicker">Operational notes</span>
              <h3>Reorder awareness</h3>
              <ul className="insight-list">
                <li>{summary.low_stock_count} products are currently at or below their reorder level.</li>
                <li>{summary.out_of_stock_count} products are unavailable for fulfillment or deployment.</li>
                <li>{inStockCount} products remain comfortably above their reorder threshold.</li>
              </ul>
            </section>
          </div>
        </>
      )}
    </section>
  );
}
