interface SegmentedFilterOption<T extends string> {
  value: T;
  label: string;
}

interface SegmentedFilterProps<T extends string> {
  value: T;
  options: SegmentedFilterOption<T>[];
  ariaLabel: string;
  onChange: (value: T) => void;
}

export default function SegmentedFilter<T extends string>({
  value,
  options,
  ariaLabel,
  onChange,
}: SegmentedFilterProps<T>) {
  return (
    <div className="segmented-filter" role="group" aria-label={ariaLabel}>
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={value === option.value}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
