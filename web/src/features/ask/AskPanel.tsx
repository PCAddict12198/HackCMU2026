import { useEffect, useMemo, useRef, useState } from "react";
import { api, ApiError } from "../../api/client";
import type { AskResponse } from "../../contract";
import { useDish, useStore } from "../../state/store";
import { formatToolCall, formatToolStory } from "../shared/copy";
import { AskReply } from "./AskReply";
import { recommendedDishIds } from "./recommendedDishes";
import { DishVisual } from "../dish/DishVisual";
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
  const space = useStore((s) => s.space);
  const [picks, setPicks] = useState<Record<number, string[]>>({});
  const [last, setLast] = useState<AskResponse | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const [showTrace, setShowTrace] = useState(false);

  const suggestions = useMemo(() => {
    const n = selected?.name ?? "this dish";
    return [`like pho bo but spicier`, `I love ${n} but want something lighter`, `flavor twin of ${n}`];
  }, [selected?.name]);

  const lastSeedSent = useRef("");

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
      const known = new Set(useStore.getState().space?.dishes.map((d) => d.id) ?? []);
      const dishIds = recommendedDishIds(res, known);
      const idx = useStore.getState().chat.length - 1;
      if (dishIds.length) setPicks((p) => ({ ...p, [idx]: dishIds }));
      applyUiActions(res.ui_actions);
      onUsedEngine?.();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    if (!seed?.trim()) return;
    const text = seed.trim();
    if (lastSeedSent.current === text) {
      onConsumedSeed?.();
      return;
    }
    lastSeedSent.current = text;
    setInput(text);
    onConsumedSeed?.();
    void send(text);
    // Seed is consumed immediately so this should not re-fire.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seed]);

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
          <div key={i} className={`chat-turn ${m.role}`}>
            {m.role === "assistant" ? <AskReply text={m.content} /> : <p className="user">{m.content}</p>}
            {m.role === "assistant" && picks[i]?.length ? (
              <div className="ask-picks">
                {picks[i].map((id) => {
                  const dish = space?.dishes.find((d) => d.id === id);
                  if (!dish) return null;
                  return (
                    <button
                      key={id}
                      type="button"
                      className="ask-pick"
                      onClick={() => {
                        useStore.getState().select(id);
                        useStore.getState().setPanel("twins");
                        window.dispatchEvent(new Event("tastespace:show-map"));
                      }}
                    >
                      <DishVisual dish={dish} className="mini" />
                      <span>{dish.name}</span>
                    </button>
                  );
                })}
              </div>
            ) : null}
          </div>
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
