interface EmptyStateProps {
  title: string;
  body?: string;
  action?: React.ReactNode;
}

export default function EmptyState({ title, body, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
      <div className="w-12 h-12 rounded-full bg-[#F1F5F9] flex items-center justify-center text-2xl" aria-hidden="true">
        📭
      </div>
      <p className="font-semibold text-[#0B2545]">{title}</p>
      {body && <p className="text-sm text-gray-500 max-w-xs">{body}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
