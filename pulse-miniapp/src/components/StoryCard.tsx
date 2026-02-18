import React from 'react';
import type { Story } from '../types';
import { motion } from 'framer-motion';
import { ChevronRight, TrendingUp } from 'lucide-react';
import { Link } from 'react-router-dom';
import Markdown from 'react-markdown';

interface StoryCardProps {
    story: Story;
    index: number;
}

export const StoryCard: React.FC<StoryCardProps> = ({ story, index }) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
        >
            <Link to={`/story/${story.id}`} className="block group">
                <div className="bg-surface/50 backdrop-blur-md border border-white/5 rounded-2xl p-4 hover:bg-surface/80 transition-all duration-300 relative overflow-hidden">
                    {/* Highlight Indicator */}
                    <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-primary to-accent opacity-0 group-hover:opacity-100 transition-opacity" />

                    <div className="flex justify-between items-start mb-2">
                        <span className="text-xs font-semibold uppercase tracking-wider text-primary/90 bg-primary/10 px-2 py-0.5 rounded-full">
                            {story.category}
                        </span>
                        {story.score > 80 && (
                            <div className="flex items-center text-xs text-accent font-medium">
                                <TrendingUp size={12} className="mr-1" />
                                Trending
                            </div>
                        )}
                    </div>

                    <h3 className="text-lg font-bold leading-tight mb-2 text-slate-100 group-hover:text-primary transition-colors">
                        {story.title}
                    </h3>

                    <div className="text-sm text-slate-400 line-clamp-3 mb-4 prose prose-invert prose-sm max-w-none prose-p:my-0">
                        <Markdown>{story.summary || ''}</Markdown>
                    </div>

                    <div className="flex items-center justify-between text-xs text-slate-500">
                        <div className="flex items-center gap-2">
                            <div className="flex -space-x-2">
                                {[...Array(Math.min(3, story.sources.length))].map((_, i) => (
                                    <div key={i} className="w-5 h-5 rounded-full bg-slate-700 border border-surface flex items-center justify-center text-[10px] text-slate-300 uppercase">
                                        {story.sources[i][0]}
                                    </div>
                                ))}
                            </div>
                            <span>{story.publications_count} джерел</span>
                        </div>
                        <div className="flex items-center text-primary group-hover:translate-x-1 transition-transform">
                            Читати <ChevronRight size={14} />
                        </div>
                    </div>
                </div>
            </Link>
        </motion.div>
    );
};
