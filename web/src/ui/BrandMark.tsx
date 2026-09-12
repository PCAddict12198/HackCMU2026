export function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <span className="brand-mark">
      <svg className="brand-mark-icon" viewBox="0 0 28 28" aria-hidden="true">
        <circle cx="11" cy="13" r="7" fill="#D8F25A" />
        <circle cx="18.5" cy="11" r="6" fill="#C45C3E" fillOpacity="0.82" />
        <circle cx="15.5" cy="18" r="5.4" fill="#6F8F5A" fillOpacity="0.88" />
      </svg>
      {compact ? null : <span className="brand-word">TasteSpace</span>}
    </span>
  );
}
