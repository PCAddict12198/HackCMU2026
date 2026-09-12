import { useEffect, useMemo, useState } from "react";
import { api, ApiError } from "../../api/client";
import type { AskResponse } from "../../contract";
import { useDish, useStore } from "../../state/store";
import { formatToolCall, formatToolStory } from "../shared/copy";
import { ErrorState, Loading } from "../shared/Status";

export function AskPanel({
  seed,
  onConsumedSeed,
  onUsedEngine,
}: {
  seed?: string | null;
  onConsumedSeed?: () => void;
  onUsedEngine?: () => void;
}) {
  const { chat, pushChat, applyUiActions, selectedId, panel } = useStore();
  const selected = useDish(selectedId);
  const [input, setInput] = useState("like pho bo but spicier");
  const [last, setLast] = useState<AskResponse | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const [showTrace, setShowTrace] = useState(false);

  useEffect(() => {
    if (seed) {
      setInput(seed);
      onConsumedSeed?.();
    }
  }, [seed, onConsumedSeed]);

  const suggestions = useMemo(() => {
    const n = selected?.name ?? "this dish";
    return [`like pho bo but spicier`, `I love ${n} but want something lighter`, `flavor twin of ${n}`];
  }, [selected?.name]);

  const send = async (text = input) => {
    if (!text.trim()) return;
    const messages = [...chat, { role: "user" as const, content: text.trim() }];
    pushChat(messages[messages.length - 1]);
    setInput("");
    setBusy(true);
    setError(null);
    try {
      const res = await api.ask({ messages, context: { selected_dish_id: selectedId, active_panel: panel } });
      setLast(res);
      pushChat({ role: "assistant", content: res.reply });
      applyUiActions(res.ui_actions);
      onUsedEngine?.();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  const retryable = error instanceof ApiError && (error.code === "grok_failed" || error.code === "network" || error.code === "internal");

  return (
    <div>
      <h3>Ask TasteSpace</h3>
      <p className="lede-sm">Ask TasteSpace what you’re craving…</p>
      <div className="chips">
        {suggestions.map((s) => (
          <button key={s} type="button" className="chip-btn" onClick={() => void send(s)}>
            {s}
          </button>
        ))}
      </div>
      <div className="chat">
        {chat.map((m, i) => (
          <p key={i} className={m.role}>
            {m.content}
          </p>
        ))}
      </div>
      {last && (
        <>
          <span className={`badge ${last.grounded ? "real" : "mock"}`}>
            {last.grounded ? "grounded in TasteSpace" : "from TasteSpace results"}
          </span>
          {last.tool_trace.length > 0 && (
            <>
              <button type="button" className="linkish" onClick={() => setShowTrace((v) => !v)}>
                {showTrace ? "Hide how Grok used TasteSpace" : "See how Grok used TasteSpace →"}
              </button>
              {showTrace && (
                <ol className="trace">
                  {last.tool_trace.map((t) => (
                    <li key={t.call_id} className="small muted">
                      {formatToolStory(t)}
                      {!t.ok && t.error ? ` — ${t.error}` : ""}
                      <details>
                        <summary>detail</summary>
                        <code>{formatToolCall(t)}</code>
                      </details>
                    </li>
                  ))}
                </ol>
              )}
            </>
          )}
        </>
      )}
      {busy && <Loading label="TasteSpace is looking…" />}
      {error != null && (
        <ErrorState
          error={error}
          onRetry={retryable ? () => void send([...chat].reverse().find((m) => m.role === "user")?.content) : undefined}
        />
      )}
      <div className="row" style={{ marginTop: 12 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && void send()}
          placeholder="I love ramen but want something lighter and more sour."
        />
        <button type="button" className="primary" onClick={() => void send()} disabled={busy}>
          {busy ? "…" : "Ask"}
        </button>
      </div>
    </div>
  );
}
