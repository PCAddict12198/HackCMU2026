import { useEffect, useState } from "react";

type Source = { artist?: string; licence?: string; page?: string };

let cached: Record<string, Source> | null = null;

export function DishPhoto({ id, name }: { id: string; name: string }) {
  const [failed, setFailed] = useState(false);
  const [meta, setMeta] = useState<Source | undefined>(cached?.[id]);

  useEffect(() => {
    setFailed(false);
    if (cached) {
      setMeta(cached[id]);
      return;
    }
    void fetch("/dishes/sources.json")
      .then((r) => (r.ok ? r.json() : {}))
      .then((data: Record<string, Source>) => {
        cached = data;
        setMeta(data[id]);
      })
      .catch(() => undefined);
  }, [id]);

  if (failed) return null;
  const credit = [meta?.artist || "Wikimedia Commons", meta?.licence].filter(Boolean).join(" · ");
  return (
    <figure className="dish-photo">
      <img src={`/dishes/${id}.jpg`} alt={name} onError={() => setFailed(true)} />
      {credit && (
        <figcaption>
          {meta?.page ? (
            <a href={meta.page} target="_blank" rel="noreferrer">
              {credit}
            </a>
          ) : (
            credit
          )}
        </figcaption>
      )}
    </figure>
  );
}
