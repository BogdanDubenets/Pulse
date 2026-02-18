import React from 'react';
import type { Story, BriefNews } from '../types';
import { ChevronRight } from 'lucide-react';

interface DigestListItemProps {
    item: Story | BriefNews;
    time?: string;
    onClick: () => void;
}

export const DigestListItem: React.FC<DigestListItemProps> = ({
    item,
    time,
    onClick,
}) => {
    return (
        <div
            onClick={onClick}
            className="px-4 py-3 flex items-center justify-between gap-4 cursor-pointer hover:bg-surface/80 transition-all active:scale-[0.99] border-b border-border/50 last:border-0"
        >
            <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-2">
                    {time && (
                        <span className="text-xs font-medium text-primary shrink-0">
                            {time}
                        </span>
                    )}
                    <h3 className="text-sm font-medium text-text-primary leading-snug line-clamp-2">
                        {item.title}
                    </h3>
                </div>
            </div>

            <ChevronRight size={16} className="text-text-secondary flex-shrink-0" />
        </div>
    );
};
