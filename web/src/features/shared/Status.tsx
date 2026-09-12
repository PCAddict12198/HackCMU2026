import { ApiError } from "../../api/client";
import { friendlyError } from "./copy";

export function Loading({ label }: { label: string }) {
  return (
    <div className="loading-block" role="status">
      <p className="muted">{label}</p>
      <div className="skeleton" />
      <div className="skeleton short" />
      <div className="skeleton" />
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const code = error instanceof ApiError ? error.code : "internal";
  const injected = error instanceof ApiError && error.message.startsWith("[mock]");
  const { title, hint, retry } = friendlyError(code);
  const detail = error instanceof Error ? error.message : String(error);
  return (
    <div className="error-card" role="alert">
      <strong>{injected ? `Panel error (${code})` : title}</strong>
      <p className="small">
        {injected
          ? "Debug query is forcing this panel to fail. The galaxy is still the mock catalog."
          : hint}
      </p>
      {!injected && <p className="small muted">{detail}</p>}
      {injected && (
        <a className="chip-btn" href="/">
          Clear ?mockError=
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
