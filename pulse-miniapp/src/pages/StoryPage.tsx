import React, { useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useStoryStore } from '../store';
import { Layout } from '../components/Layout';
import { Loader2, ArrowLeft, Clock, Eye } from 'lucide-react';

export const StoryPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const { currentStory, isLoading, error, fetchStory } = useStoryStore();

    useEffect(() => {
        if (id) {
            fetchStory(Number(id));
        }
    }, [fetchStory, id]);

    if (isLoading) {
        return (
            <Layout className="flex items-center justify-center">
                <Loader2 className="w-10 h-10 animate-spin text-primary" />
            </Layout>
        );
    }

    if (error || !currentStory) {
        return (
            <Layout className="flex items-center justify-center text-center">
                <div>
                    <p className="text-red-400 mb-4">{error || "Історію не знайдено"}</p>
                    <Link to="/" className="text-primary hover:underline">Повернутися</Link>
                </div>
            </Layout>
        );
    }

    return (
        <Layout>
            <Link to="/" className="inline-flex items-center text-slate-400 hover:text-white mb-6 transition-colors">
                <ArrowLeft size={20} className="mr-1" /> Назад
            </Link>

            <article>
                <div className="mb-6">
                    <span className="text-xs uppercase tracking-wider text-primary font-bold mb-2 block">
                        {currentStory.category}
                    </span>
                    <h1 className="text-2xl font-bold leading-tight mb-4">
                        {currentStory.title}
                    </h1>
                    <div className="bg-surface/50 p-4 rounded-xl border border-white/5 text-slate-300 text-sm leading-relaxed">
                        {currentStory.summary}
                    </div>
                </div>

                <div className="relative border-l-2 border-white/10 ml-3 space-y-8 pb-10">
                    {currentStory.timeline?.map((pub) => (
                        <div key={pub.id} className="relative pl-8">
                            {/* Timeline Dot */}
                            <div className="absolute left-[-9px] top-0 w-4 h-4 rounded-full bg-slate-900 border-2 border-primary" />

                            <div className="mb-1 flex items-center justify-between">
                                <span className="text-xs font-bold text-slate-400">
                                    {pub.channel_title}
                                </span>
                                <span className="text-[10px] text-slate-600 flex items-center gap-1">
                                    <Clock size={10} />
                                    {new Date(pub.published_at).toLocaleString('uk-UA', {
                                        day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
                                    })}
                                </span>
                            </div>

                            <div className="bg-white/5 rounded-lg p-3 hover:bg-white/10 transition-colors">
                                <p className="text-sm text-slate-300 mb-2 line-clamp-4">
                                    {pub.content}
                                </p>
                                <div className="flex justify-between items-center mt-2">
                                    <span className="text-[10px] text-slate-500 flex items-center gap-1">
                                        <Eye size={12} /> {pub.views}
                                    </span>
                                    <a
                                        href={pub.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-xs text-primary hover:underline"
                                    >
                                        Читати оригінал
                                    </a>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </article>
        </Layout>
    );
};
