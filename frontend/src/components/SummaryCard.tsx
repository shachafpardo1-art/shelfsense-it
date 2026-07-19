interface SummaryCardProps {
  label: string;
  value: string;
  accent: "neutral" | "success" | "warning" | "danger";
  helper?: string;
}

export function SummaryCard({ label, value, accent, helper }: SummaryCardProps): JSX.Element {
  return (
    <article className={`summary-card summary-${accent}`}>
      <span className="summary-label">{label}</span>
      <strong className="summary-value">{value}</strong>
      {helper ? <span className="summary-helper">{helper}</span> : null}
    </article>
  );
}
