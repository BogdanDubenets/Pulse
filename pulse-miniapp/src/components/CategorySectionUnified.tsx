import React from 'react';
import type { DigestItem, Story, BriefNews } from '../types';
import { ArrowRight } from 'lucide-react';
import { DigestListItem } from './DigestListItem';

interface CategorySectionUnifiedProps {
    title: string;
    items: DigestItem[];
    hasMore: boolean;
    totalCount: number;
    onItemClick: (item: Story | BriefNews) => void;
    onMoreClick: (title: string) => void;
}

export const CategorySectionUnified: React.FC<CategorySectionUnifiedProps> = ({
    title,
    items,
    hasMore,
    totalCount,
    onItemClick,
    onMoreClick
}) => {
    if (items.length === 0) return null;

    return (
        <section className="mb-8">
            <h2 className="text-lg font-bold text-text-primary mb-3 px-1 flex items-center justify-between">
                <span className="flex items-center gap-2">
                    {title}
                    {title.toLowerCase().includes('автор') && (
                        <span className="text-[10px] bg-primary/20 text-primary px-1.5 py-0.5 rounded border border-primary/30 uppercase tracking-tighter">
                            Ексклюзив
                        </span>
                    )}
                </span>
                <span className="text-[10px] font-normal text-text-secondary bg-surface px-2 py-0.5 rounded-full">
                    {totalCount}
                </span>
            </h2>

            <div className="bg-surface backdrop-blur-md border border-border rounded-2xl overflow-hidden shadow-xl">
                {items.map((item) => (
                    <DigestListItem
                        key={item.data.uid}
                        item={item.data}
                        time={item.time}
                        onClick={() => onItemClick(item.data)}
                    />
                ))}
            </div>

            {hasMore && (
                <button
                    onClick={() => onMoreClick(title)}
                    className="mt-3 w-full py-2.5 flex items-center justify-center gap-2 text-xs font-semibold text-primary bg-primary/5 hover:bg-primary/10 rounded-xl border border-primary/10 transition-all active:scale-[0.98]"
                >
                    Більше у розділі "{title}"
                    <ArrowRight size={14} />
                </button>
            )}
        </section>
    );
};
