import React from 'react';
import type { Story } from '../types';
import { ChevronRight } from 'lucide-react';

interface CategorySectionProps {
    title: string;
    stories: Story[];
    onStoryClick: (story: Story) => void;
}

export const CategorySection: React.FC<CategorySectionProps> = ({ title, stories, onStoryClick }) => {
    if (stories.length === 0) return null;

    return (
        <section className="mb-8">
            <h2 className="text-lg font-bold text-white mb-3 px-1 flex items-center justify-between">
                {title}
                <span className="text-[10px] font-normal text-text-secondary bg-white/5 px-2 py-0.5 rounded-full">
                    {stories.length}
                </span>
            </h2>

            <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl overflow-hidden shadow-xl">
                {stories.map((story, index) => (
                    <div
                        key={story.id}
                        onClick={() => onStoryClick(story)}
                        className={`
                            px-4 py-4 flex items-center justify-between gap-4 cursor-pointer 
                            hover:bg-white/5 transition-all active:scale-[0.99]
                            ${index !== stories.length - 1 ? 'border-b border-white/5' : ''}
                        `}
                    >
                        <div className="flex-1 min-w-0">
                            <h3 className="text-sm font-medium text-slate-200 leading-snug line-clamp-2">
                                {story.title}
                            </h3>
                            <div className="flex items-center gap-2 mt-1.5">
                                <span className="text-[10px] text-text-secondary">
                                    {story.sources.join(', ')}
                                </span>
                            </div>
                        </div>
                        <ChevronRight size={16} className="text-text-secondary flex-shrink-0" />
                    </div>
                ))}
            </div>

            <button className="mt-3 text-xs font-medium text-primary/80 hover:text-primary px-1 transition-colors">
                всі новини у розділі "{title.toLowerCase()}"
            </button>
        </section>
    );
};
