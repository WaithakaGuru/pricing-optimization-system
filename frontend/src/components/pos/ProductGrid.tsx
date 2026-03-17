import { useState } from 'react';
import { MOCK_PRODUCTS } from '../../api/mock';
import type { Product } from '../../types';

const CATEGORIES = ['All', 'Coffee', 'Tea', 'Cold Brew', 'Matcha'];

function getEmoji(name: string) {
  if (/coffee|espresso/i.test(name)) return '☕';
  if (/matcha/i.test(name))          return '🍃';
  if (/tea/i.test(name))             return '🍵';
  if (/cold|brew/i.test(name))       return '🧊';
  return '📦';
}

export default function ProductGrid({ onAdd }: { onAdd: (p: Product) => void }) {
  const [cat, setCat] = useState('All');
  const [search, setSearch] = useState('');

  const filtered = MOCK_PRODUCTS.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase()) &&
    (cat === 'All' || p.name.toLowerCase().includes(cat.toLowerCase()))
  );

  return (
    <div className="flex flex-col gap-3 h-full min-h-0">
      {/* Search */}
      <div className="relative">
        <svg className="absolute left-3 top-1/2 -translate-y-1/2 text-[--color-text-tertiary]" width="13" height="13" viewBox="0 0 16 16" fill="none">
          <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5"/>
          <path d="M11 11l3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search products…"
          className="w-full h-10 pl-8 pr-3 border border-[--color-border] rounded-lg bg-[--color-surface] text-sm text-[--color-text-primary] placeholder:text-[--color-text-tertiary] outline-none focus:border-[--color-accent] transition-colors"
        />
      </div>

      {/* Category pills */}
      <div className="flex gap-1.5 flex-wrap">
        {CATEGORIES.map((c) => (
          <button key={c} onClick={() => setCat(c)}
            className={`px-3 py-1 rounded-full border text-xs font-medium transition-all ${
              cat === c
                ? 'bg-[--color-accent] border-[--color-accent] text-white'
                : 'bg-[--color-surface] border-[--color-border] text-[--color-text-secondary] hover:border-[--color-accent] hover:text-[--color-accent]'
            }`}>
            {c}
          </button>
        ))}
      </div>

      {/* Grid */}
      <div className="grid gap-2.5 overflow-y-auto flex-1 pb-1" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(148px, 1fr))' }}>
        {filtered.map((p, i) => (
          <button key={p.id} onClick={() => onAdd(p)}
            className="bg-[--color-surface] border-[1.5px] border-[--color-border] rounded-xl p-3.5 flex flex-col gap-2 text-left transition-all duration-150 hover:border-[--color-accent] hover:shadow-md hover:-translate-y-px active:scale-95 animate-fade-up"
            style={{ animationDelay: `${i * 30}ms` }}>
            <span className="text-3xl leading-none">{getEmoji(p.name)}</span>
            <span className="text-xs font-medium text-[--color-text-primary] leading-snug flex-1">{p.name}</span>
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-[--color-text-primary] font-mono">${p.current_price.toFixed(2)}</span>
              <span className="w-5 h-5 rounded-full bg-[--color-accent] text-white text-base flex items-center justify-center leading-none flex-shrink-0">+</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
