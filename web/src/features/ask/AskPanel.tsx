import { useMemo, useState } from "react";
import { api, ApiError } from "../../api/client";
import type { AskResponse } from "../../contract";
import { useDish, useStore } from "../../state/store";
import { formatToolCall } from "../shared/copy";
import { ErrorState } from "../shared/Status";

export function AskPanel() {
  const { chat, pushChat, applyUiActions, selectedId, panel } = useStore();
  const selected = useDish(selectedId);
  const [input, setInput] = useState("Like tonkotsu ramen but lighter and more acidic?");
  const [last, setLast] = useState<AskResponse | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const suggestions = useMemo(() => {
    const n = selected?.name ?? "this dish";
    return [`flavor twin of ${n}`, `like ${n} but lighter`, `why is ${n} so rich?`];
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
            {last.grounded ? "grounded in engine results" : "summary generated from engine results"}
          </span>
          {last.tool_trace.length > 0 && (
            <ul className="trace">
              {last.tool_trace.map((t) => (
                <li key={t.call_id} className="small muted">
                  Grok called {formatToolCall(t)}
                  {!t.ok && t.error ? ` — ${t.error}` : ""}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
      {error != null && (
        <ErrorState
          error={error}
          onRetry={retryable ? () => void send([...chat].reverse().find((m) => m.role === "user")?.content) : undefined}
        />
      )}
      <div className="row">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && void send()}
          placeholder="Ask about flavor, not names"
        />
        <button type="button" onClick={() => void send()} disabled={busy}>
          {busy ? "..." : "Ask"}
        </button>
      </div>
    </div>
  );
}
