interface Segment {
  label: string;
  value: number;
}

// A single stacked bar splitting a total into named parts, with a legend.
export default function ProportionBar({ segments }: { segments: Segment[] }) {
  const total = segments.reduce((sum, s) => sum + s.value, 0);

  return (
    <div className="proportion">
      <div className="proportion-bar" aria-hidden="true">
        {segments.map((segment, index) => (
          <span
            key={segment.label}
            className={`proportion-segment proportion-segment-${index}`}
            style={{ width: total ? `${(segment.value / total) * 100}%` : "0%" }}
          />
        ))}
      </div>
      <ul className="proportion-legend">
        {segments.map((segment, index) => (
          <li key={segment.label}>
            <span className={`proportion-dot proportion-segment-${index}`} />
            {segment.label}: <strong>{segment.value}</strong>
            {total > 0 && ` (${Math.round((segment.value / total) * 100)}%)`}
          </li>
        ))}
      </ul>
    </div>
  );
}
