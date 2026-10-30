export default function Header() {
  return (
    <header className="sticky top-0 z-20 bg-white/86 backdrop-blur-md border-b border-gray-200">
      <div className="max-w-4xl mx-auto px-6 py-4 flex items-center gap-3">
        <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-white flex-shrink-0">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2l1.9 6.3L20 10l-6.1 1.7L12 18l-1.9-6.3L4 10l6.1-1.7z"/>
          </svg>
        </div>
        <div className="flex flex-col leading-tight">
          <span className="text-sm font-bold text-gray-900">아침 시장 전망</span>
          <span className="text-xs font-semibold text-gray-500">AI 시장 요약 · Daily Market Brief</span>
        </div>
        <div className="flex-1"></div>
        <button type="button" disabled aria-label="알림 (준비 중)" className="w-9 h-9 rounded-full border border-gray-200 bg-white flex items-center justify-center text-gray-400 disabled:cursor-not-allowed">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
            <path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.7 21a2 2 0 0 1-3.4 0"/>
          </svg>
        </button>
      </div>
    </header>
  );
}
