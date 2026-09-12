import { type ReactNode } from "react";

function inline(text: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const re = /\*\*(.+?)\*\*|\*(.+?)\*|`([^`]+)`/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let k = 0;
  while ((m = re.exec(text))) {
    if (m.index > last) nodes.push(text.slice(last, m.index));
    if (m[1] != null) nodes.push(<strong key={k++}>{m[1]}</strong>);
    else if (m[2] != null) nodes.push(<em key={k++}>{m[2]}</em>);
    else nodes.push(<code key={k++}>{m[3]}</code>);
    last = m.index + m[0].length;
  }
  if (last < text.length) nodes.push(text.slice(last));
  return nodes;
}

export function AskReply({ text }: { text: string }) {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let list: { ordered: boolean; items: string[] } | null = null;
  let k = 0;

  const flushList = () => {
    if (!list) return;
    const Tag = list.ordered ? "ol" : "ul";
    blocks.push(
      <Tag key={k++}>
        {list.items.map((item, i) => (
          <li key={i}>{inline(item)}</li>
        ))}
      </Tag>,
    );
    list = null;
  };

  for (const raw of lines) {
    const line = raw.trimEnd();
    const bullet = line.match(/^\s*[-*]\s+(.+)/);
    const numbered = line.match(/^\s*\d+[.)]\s+(.+)/);
    const heading = line.match(/^\s*#{1,3}\s+(.+)/);
    if (bullet) {
      if (list && list.ordered) flushList();
      list = list ?? { ordered: false, items: [] };
      list.items.push(bullet[1]);
      continue;
    }
    if (numbered) {
      if (list && !list.ordered) flushList();
      list = list ?? { ordered: true, items: [] };
      list.items.push(numbered[1]);
      continue;
    }
    flushList();
    if (!line.trim()) continue;
    if (heading) {
      blocks.push(<h4 key={k++}>{inline(heading[1])}</h4>);
      continue;
    }
    blocks.push(<p key={k++}>{inline(line)}</p>);
  }
  flushList();

  return <div className="ask-reply">{blocks.length ? blocks : <p>{inline(text)}</p>}</div>;
}

export function flattenAskReply(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/^#+\s+/gm, "")
    .replace(/^\s*[-*]\s+/gm, "• ");
}
