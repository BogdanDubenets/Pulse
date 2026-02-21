import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useDigestStore } from '../store';
import { Layout } from '../components/Layout';
import { Loader2, X, ExternalLink, LayoutGrid, Clock, Pin, Hash } from 'lucide-react';
import type { Story, BriefNews } from '../types';
import Markdown from 'react-markdown';
import { CategorySectionUnified } from '../components/CategorySectionUnified';
import { DigestListItem } from '../components/DigestListItem';

export const DigestPage: React.FC = () => {
    // Отримуємо userId з Telegram WebApp або використовуємо fallback для розробки
    const webApp = window.Telegram?.WebApp;
    const tgUserId = webApp?.initDataUnsafe?.user?.id;
    const userId = tgUserId || 461874849; // Fallback на ID Богдана, якщо не в Telegram

    const { digest, isLoading, isRefreshing, error, fetchDigest } = useDigestStore();
    const [selectedItem, setSelectedItem] = useState<Story | BriefNews | null>(null);
    const [offset, setOffset] = useState(0);
    const observer = useRef<IntersectionObserver | null>(null);

    // UI State: 'category', 'time', or 'channel'
    const [groupBy, setGroupBy] = useState<'category' | 'time' | 'channel'>(
        (localStorage.getItem('pulse_group_by') as any) || 'category'
    );
    const [pinnedCats, setPinnedCats] = useState<string[]>(
        JSON.parse(localStorage.getItem('pulse_pinned_cats') || '["⚽ Спорт", "🧪 Наука"]')
    );

    useEffect(() => {
        setOffset(0); // Скидаємо офсет при зміні фільтрів
        fetchDigest(userId, groupBy, pinnedCats.join(','));
        localStorage.setItem('pulse_group_by', groupBy);
    }, [fetchDigest, userId, groupBy, pinnedCats]);

    // Функція для завантаження наступної порції
    const loadMore = useCallback(() => {
        if (!digest?.has_more || isLoading || isRefreshing) return;

        const nextOffset = offset + 20;
        setOffset(nextOffset);
        fetchDigest(userId, groupBy, pinnedCats.join(','), nextOffset);
    }, [digest?.has_more, isLoading, isRefreshing, offset, fetchDigest, userId, groupBy, pinnedCats]);

    // Налаштування Observer
    const lastElementRef = useCallback((node: HTMLDivElement | null) => {
        if (isLoading || isRefreshing) return;
        if (observer.current) observer.current.disconnect();

        observer.current = new IntersectionObserver(entries => {
            if (entries[0].isIntersecting && digest?.has_more) {
                loadMore();
            }
        });

        if (node) observer.current.observe(node);
    }, [isLoading, isRefreshing, digest?.has_more, loadMore]);

    const togglePin = (cat: string) => {
        const newPinned = pinnedCats.includes(cat)
            ? pinnedCats.filter(c => c !== cat)
            : [...pinnedCats, cat];
        setPinnedCats(newPinned);
        localStorage.setItem('pulse_pinned_cats', JSON.stringify(newPinned));
    };

    const handleMoreClick = () => {
        setGroupBy('time');
    };

    if (isLoading && !digest) {
        return (
            <Layout className="flex items-center justify-center">
                <Loader2 className="w-10 h-10 animate-spin text-primary" />
            </Layout>
        );
    }

    if (error) {
        return (
            <Layout className="flex items-center justify-center text-center">
                <div className="p-6 bg-surface rounded-2xl border border-border backdrop-blur-xl">
                    <p className="text-error mb-4">{error}</p>
                    <button
                        onClick={() => fetchDigest(userId, groupBy, pinnedCats.join(','))}
                        className="px-6 py-2 bg-primary rounded-full text-sm font-medium hover:bg-primary/90 transition-colors"
                    >
                        Спробувати знову
                    </button>
                </div>
            </Layout>
        );
    }

    const categories = digest?.categories || {};
    const channels = digest?.channels || {};
    const items = digest?.items || [];

    return (
        <Layout>
            <header className="mb-6 mt-2 px-1">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-[10px] text-primary font-bold uppercase tracking-widest mb-1">
                            {new Date().toLocaleDateString('uk-UA', { day: 'numeric', month: 'long' })}
                        </p>
                        <h1 className="text-3xl font-black text-text-primary flex items-center gap-2">
                            <img src="/pulse-logo.svg" alt="Pulse" className="w-9 h-9" />
                            Pulse
                        </h1>
                    </div>

                    <div className="flex p-1 bg-surface backdrop-blur-md rounded-xl border border-border">
                        <button
                            onClick={() => setGroupBy('category')}
                            className={`p-2 rounded-lg transition-all ${groupBy === 'category' ? 'bg-primary text-text-primary shadow-lg' : 'text-text-secondary hover:text-text-primary'}`}
                            title="За категоріями"
                        >
                            <LayoutGrid size={18} />
                        </button>
                        <button
                            onClick={() => setGroupBy('channel')}
                            className={`p-2 rounded-lg transition-all ${groupBy === 'channel' ? 'bg-primary text-text-primary shadow-lg' : 'text-text-secondary hover:text-text-primary'}`}
                            title="За каналами"
                        >
                            <Hash size={18} />
                        </button>
                        <button
                            onClick={() => setGroupBy('time')}
                            className={`p-2 rounded-lg transition-all ${groupBy === 'time' ? 'bg-primary text-text-primary shadow-lg' : 'text-text-secondary hover:text-text-primary'}`}
                            title="За часом"
                        >
                            <Clock size={18} />
                        </button>
                    </div>
                </div>
            </header>

            {groupBy === 'category' ? (
                <div className="pb-4">
                    {Object.entries(categories).map(([name, data]) => (
                        <div key={name} className="relative group">
                            <button
                                onClick={() => togglePin(name)}
                                className={`absolute right-2 top-2 z-10 p-2 rounded-full transition-all ${pinnedCats.includes(name) ? 'text-primary' : 'text-text-secondary/30 opacity-0 group-hover:opacity-100'}`}
                            >
                                <Pin size={14} fill={pinnedCats.includes(name) ? "currentColor" : "none"} />
                            </button>
                            <CategorySectionUnified
                                title={name}
                                items={data.items}
                                hasMore={data.has_more}
                                totalCount={data.total_count}
                                onItemClick={setSelectedItem}
                                onMoreClick={handleMoreClick}
                            />
                        </div>
                    ))}
                </div>
            ) : groupBy === 'channel' ? (
                <div className="pb-4">
                    {Object.entries(channels).map(([name, data]) => (
                        <CategorySectionUnified
                            key={name}
                            title={name}
                            items={data.items}
                            hasMore={data.has_more}
                            totalCount={data.total_count}
                            onItemClick={setSelectedItem}
                            onMoreClick={handleMoreClick}
                        />
                    ))}
                </div>
            ) : (
                <section className="mb-4">
                    <div className="bg-surface backdrop-blur-md border border-border rounded-2xl overflow-hidden shadow-xl">
                        {items.map((item) => (
                            <DigestListItem
                                key={item.data.uid}
                                item={item.data}
                                time={item.time}
                                onClick={() => setSelectedItem(item.data)}
                            />
                        ))}
                    </div>

                </section>
            )}

            {/* Загальний елемент для Infinite Scroll */}
            <div ref={lastElementRef} className="h-24 flex items-center justify-center mb-24">
                {isRefreshing && (
                    <div className="flex flex-col items-center gap-2">
                        <Loader2 className="w-8 h-8 animate-spin text-primary" />
                        <span className="text-[10px] text-text-muted font-bold uppercase tracking-widest">Завантаження...</span>
                    </div>
                )}
                {!digest?.has_more && (items.length > 0 || Object.keys(categories).length > 0) && (
                    <p className="text-[10px] text-text-muted uppercase tracking-widest font-bold bg-surface/50 px-4 py-2 rounded-full border border-border">
                        ✨ Це всі новини на сьогодні
                    </p>
                )}
            </div>

            {selectedItem && (
                <div className="fixed inset-0 z-50 flex items-end justify-center px-4 pb-4 animate-in fade-in duration-300">
                    <div
                        className="absolute inset-0 bg-background/90 backdrop-blur-sm"
                        onClick={() => setSelectedItem(null)}
                    />
                    <div className="relative w-full max-w-lg bg-surface border border-border rounded-3xl shadow-2xl overflow-hidden animate-in slide-in-from-bottom duration-300">
                        <div className="max-h-[85vh] overflow-y-auto custom-scrollbar">
                            <div className="p-6">
                                <div className="flex justify-between items-start mb-6">
                                    <div className="flex gap-2">
                                        <span className="text-[10px] font-bold text-primary uppercase tracking-widest bg-primary/10 px-2 py-0.5 rounded border border-primary/20">
                                            {selectedItem.category}
                                        </span>
                                    </div>
                                    <button
                                        onClick={() => setSelectedItem(null)}
                                        className="p-1 hover:bg-border/50 rounded-full text-text-secondary transition-colors"
                                    >
                                        <X size={20} />
                                    </button>
                                </div>

                                <h2 className="text-xl font-bold text-text-primary mb-6 leading-tight">
                                    {selectedItem.title}
                                </h2>

                                <div className="prose prose-invert prose-sm max-w-none text-text-secondary mb-8 leading-relaxed">
                                    <Markdown>
                                        {selectedItem.summary}
                                    </Markdown>
                                </div>

                                <div className="space-y-4 mb-8">
                                    <h4 className="text-[10px] font-black text-text-muted uppercase tracking-widest">Джерела інформації</h4>
                                    <div className="flex flex-wrap gap-2">
                                        {selectedItem.sources.map((source, i) => (
                                            <button
                                                key={i}
                                                onClick={() => source.url && window.open(source.url, '_blank')}
                                                className="flex items-center gap-2 px-3 py-2 bg-background hover:bg-border/30 rounded-xl border border-border text-xs text-text-primary transition-all active:scale-95"
                                            >
                                                <span className="bg-primary/20 text-primary w-5 h-5 flex items-center justify-center rounded-md font-bold">
                                                    {source.name.charAt(0)}
                                                </span>
                                                {source.name}
                                                <ExternalLink size={10} className="text-text-muted" />
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <button
                                    className="w-full bg-primary text-text-primary py-4 rounded-2xl font-bold text-sm hover:bg-primary/90 transition-all active:scale-[0.98] shadow-lg shadow-primary/20"
                                    onClick={() => setSelectedItem(null)}
                                >
                                    Назад до дайджесту
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </Layout>
    );
};
