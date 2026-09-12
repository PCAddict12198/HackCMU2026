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
  const injected = error instanceof ApiError && error.message.startsWith("[mock]");
  const { title, hint, retry } = friendlyError(code);
  const detail = error instanceof Error ? error.message : String(error);
  return (
    <div className="error-card" role="alert">
      <strong>{injected ? `Mock debug: ${code}` : title}</strong>
      <p className="small">
        {injected
          ? "This is ?mockError= in the URL, not missing dish data. The mock catalog still has 16 dishes."
          : hint}
      </p>
      <p className="small muted">{detail}</p>
      {injected && (
        <a className="chip-btn" href="/">
          Open mock catalog
        </a>
      )}
      {!injected && retry && onRetry && (
        <button type="button" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}
