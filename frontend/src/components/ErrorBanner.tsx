interface ErrorBannerProps {
  message?: string;
  onRetry?: () => void;
}

export default function ErrorBanner({ message = "Something went wrong. Please try again.", onRetry }: ErrorBannerProps) {
  return (
    <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-lg px-4 py-3" role="alert">
      <span className="text-red-500 mt-0.5 flex-shrink-0" aria-hidden="true">⚠</span>
      <div className="flex-1">
        <p className="text-sm text-red-700">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-1 text-xs text-red-600 underline hover:text-red-800 focus:outline-none focus:ring-2 focus:ring-red-400 rounded"
          >
            Try again
          </button>
        )}
      </div>
    </div>
  );
}
