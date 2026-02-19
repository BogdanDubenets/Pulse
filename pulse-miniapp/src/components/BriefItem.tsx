import React from 'react';
import type { BriefNews } from '../types';
import { ExternalLink } from 'lucide-react';
import Markdown from 'react-markdown';

interface BriefItemProps {
    item: BriefNews;
}

export const BriefItem: React.FC<BriefItemProps> = ({ item }) => {
    return (
        <div className="py-3 border-b border-white/5 last:border-0 hover:bg-white/5 px-2 -mx-2 rounded-lg transition-colors group">
            <div className="flex justify-between items-start gap-3">
                <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-medium text-primary">
                            {item.channel}
                        </span>
                        <span className="text-[10px] text-text-secondary">
                            {item.time}
                        </span>
                    </div>
                    <div className="text-sm text-slate-300 group-hover:text-slate-200 leading-snug prose prose-invert prose-sm max-w-none prose-a:text-primary prose-a:no-underline hover:prose-a:underline prose-p:my-1 prose-strong:text-white">
                        <Markdown
                            components={{
                                a: ({ node, ...props }) => (
                                    <a target="_blank" rel="noopener noreferrer" {...props} />
                                )
                            }}
                            {item.summary || ''}
                    </div>
                </div>
                {item.url && (
                    <a href={item.url} target="_blank" rel="noopener noreferrer" className="mt-1 text-text-secondary hover:text-primary transition-colors flex-shrink-0">
                        <ExternalLink size={16} />
                    </a>
                )}
            </div>
        </div>
    );
};
