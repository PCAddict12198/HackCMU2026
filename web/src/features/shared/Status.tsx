import { ApiError } from "../../api/client";
import { friendlyError } from "./copy";

export function Loading({ label }: { label: string }) {
  return (
    <p className="muted loading" role="status">
      {label}
    </p>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const code = error instanceof ApiError ? error.code : "internal";
  const { title, hint, retry } = friendlyError(code);
  const detail = error instanceof Error ? error.message : String(error);
  return (
    <div className="error-card" role="alert">
      <strong>{title}</strong>
      <p className="small">{hint}</p>
      <p className="small muted">{detail}</p>
      {retry && onRetry && (
        <button type="button" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}
