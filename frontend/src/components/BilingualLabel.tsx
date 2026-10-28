interface BilingualLabelProps {
  en: string;
  hi: string;
  className?: string;
}

export default function BilingualLabel({ en, hi, className = "" }: BilingualLabelProps) {
  return (
    <span className={className}>
      {en}
      <span className="ml-1.5 text-gray-400 font-normal" lang="hi" aria-label={hi}>
        {hi}
      </span>
    </span>
  );
}
