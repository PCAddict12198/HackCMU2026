// Ask TasteSpace (baseline): Grok tool-calls the engine; its ui_actions drive the app via the reducer.
// P3 TODO: show the tool trace as "Grok called find_twins(...)", grounded badge styling, suggestions.
import { useState } from "react";
import { api, ApiError, errorMessage } from "../../api/client";
import type { AskResponse } from "../../contract";
import { useStore } from "../../state/store";

export function AskPanel() {
  const { chat, pushChat, applyUiActions, selectedId, panel } = useStore();
  const [input, setInput] = useState("Like tonkotsu ramen but lighter and more acidic?");
  const [last, setLast] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const send = async () => {
    if (!input.trim()) return;
    const messages = [...chat, { role: "user" as const, content: input.trim() }];
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
      setError(e instanceof ApiError && e.code === "grok_unavailable" ? "Grok is not configured on the server." : errorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <h3>Ask TasteSpace</h3>
      <div className="chat">
        {chat.map((m, i) => (
          <p key={i} className={m.role}>
            {m.content}
          </p>
        ))}
      </div>
      {last && (
        <p className="small muted">
          {last.grounded ? "grounded in engine results" : "reply replaced by engine summary"} - tools:{" "}
          {last.tool_trace.map((t) => t.tool).join(", ") || "none"}
        </p>
      )}
      {error && <p className="error">{error}</p>}
      <div className="row">
        <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()} />
        <button onClick={send} disabled={busy}>
          {busy ? "..." : "Ask"}
        </button>
      </div>
    </div>
  );
}
