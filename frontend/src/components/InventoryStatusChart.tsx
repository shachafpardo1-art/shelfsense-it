interface InventoryStatusChartProps {
  inStockCount: number;
  lowStockCount: number;
  outOfStockCount: number;
}

const chartSegments = [
  { key: "in-stock", label: "In stock", className: "chart-in-stock" },
  { key: "low-stock", label: "Low stock", className: "chart-low-stock" },
  { key: "out-of-stock", label: "Out of stock", className: "chart-out-of-stock" },
] as const;

export function InventoryStatusChart({
  inStockCount,
  lowStockCount,
  outOfStockCount,
}: InventoryStatusChartProps): JSX.Element {
  const total = inStockCount + lowStockCount + outOfStockCount;

  if (total === 0) {
    return (
      <section className="chart-card">
        <div className="chart-header">
          <div>
            <span className="chart-kicker">Status distribution</span>
            <h3>Inventory health</h3>
          </div>
        </div>
        <div className="chart-empty">No active products are available yet.</div>
      </section>
    );
  }

  const values = [inStockCount, lowStockCount, outOfStockCount];
  const gradientStops = values.reduce<string[]>((stops, value, index) => {
    const previous = values.slice(0, index).reduce((sum, current) => sum + current, 0);
    const start = (previous / total) * 100;
    const end = ((previous + value) / total) * 100;
    const segment = chartSegments[index];
    stops.push(`var(--${segment.key}) ${start}%`, `var(--${segment.key}) ${end}%`);
    return stops;
  }, []);

  return (
    <section className="chart-card">
      <div className="chart-header">
        <div>
          <span className="chart-kicker">Status distribution</span>
          <h3>Inventory health</h3>
        </div>
        <strong className="chart-total">{total} products</strong>
      </div>

      <div className="chart-layout">
        <div
          className="donut-chart"
          role="img"
          aria-label={`Inventory status distribution: ${inStockCount} in stock, ${lowStockCount} low stock, ${outOfStockCount} out of stock`}
          style={{
            background: `conic-gradient(${gradientStops.join(", ")})`,
          }}
        >
          <div className="donut-hole">
            <span>Tracked</span>
            <strong>{total}</strong>
          </div>
        </div>

        <div className="chart-legend">
          {chartSegments.map((segment, index) => {
            const value = values[index];
            const percentage = Math.round((value / total) * 100);
            return (
              <div key={segment.key} className="legend-row">
                <div className="legend-label">
                  <span className={`legend-dot ${segment.className}`} aria-hidden="true" />
                  <span>{segment.label}</span>
                </div>
                <div className="legend-metrics">
                  <strong>{value}</strong>
                  <span>{percentage}%</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
