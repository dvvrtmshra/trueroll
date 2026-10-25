interface WizardStepProps {
  steps: string[];
  current: number;
}

export default function WizardStep({ steps, current }: WizardStepProps) {
  return (
    <div className="flex items-center gap-0 mb-6">
      {steps.map((label, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <div key={i} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                  done
                    ? "bg-green-500 text-white"
                    : active
                    ? "bg-[#0B2545] text-white"
                    : "bg-gray-200 text-gray-500"
                }`}
              >
                {done ? "✓" : i + 1}
              </div>
              <span className={`text-xs mt-1 ${active ? "text-[#0B2545] font-semibold" : "text-gray-400"}`}>
                {label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div className={`w-12 h-0.5 mx-1 mb-4 ${done ? "bg-green-400" : "bg-gray-200"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
