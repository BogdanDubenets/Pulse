import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { useCatalogStore } from '../store/catalogStore';
import {
    ArrowLeft,
    ExternalLink,
    Zap,
    Pin,
    BarChart3,
    Loader2
} from 'lucide-react';

export const MyChannelsPage: React.FC = () => {
    const navigate = useNavigate();
    const { channels, isLoading, error, fetchMyChannels } = useCatalogStore();

    // В реальному додатку ми беремо user_id з WebApp initData
    const userId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || 461874849;

    useEffect(() => {
        fetchMyChannels(userId);
    }, [userId, fetchMyChannels]);

    if (isLoading && channels.length === 0) {
        return (
            <Layout className="flex items-center justify-center">
                <Loader2 className="w-10 h-10 animate-spin text-primary" />
            </Layout>
        );
    }

    return (
        <Layout>
            <div className="p-4 pb-24 space-y-6">
                {/* Back Button & Title */}
                <div className="flex items-center space-x-4">
                    <button
                        onClick={() => navigate('/catalog')}
                        className="p-2 hover:bg-surface rounded-full transition-colors"
                    >
                        <ArrowLeft className="w-6 h-6" />
                    </button>
                    <h1 className="text-2xl font-bold">Мої канали</h1>
                </div>

                {/* Subscriptions Count */}
                <div className="px-1 text-sm text-text-secondary">
                    Ви підписані на <span className="text-primary font-bold">{channels.length}</span> каналів у Pulse
                </div>

                {/* Channels List */}
                <div className="space-y-3">
                    {channels.length === 0 && !isLoading && (
                        <div className="py-12 text-center space-y-4">
                            <div className="w-16 h-16 bg-surface border border-dashed border-border rounded-full flex items-center justify-center mx-auto text-text-muted">
                                <Pin className="w-8 h-8 opacity-20" />
                            </div>
                            <p className="text-text-secondary">Ви ще не підписалися на жоден канал у каталозі.</p>
                            <button
                                onClick={() => navigate('/catalog')}
                                className="text-primary font-semibold"
                            >
                                Перейти до каталогу
                            </button>
                        </div>
                    )}

                    {channels.map((ch, index) => (
                        <motion.div
                            key={ch.id}
                            initial={{ x: -20, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            transition={{ delay: index * 1.05 }}
                            className={`p-4 bg-surface border rounded-2xl flex items-center justify-between ${ch.partner_status === 'premium' ? 'border-primary shadow-lg shadow-primary/5' : 'border-border'
                                }`}
                        >
                            <div className="flex items-center space-x-4">
                                <div className="relative">
                                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-border to-surface flex items-center justify-center text-xl font-bold border border-border">
                                        {ch.title.charAt(0)}
                                    </div>
                                    {ch.partner_status === 'premium' && (
                                        <div className="absolute -top-1 -right-1 bg-primary p-1 rounded-full border-2 border-surface">
                                            <Zap className="w-3 h-3 text-white fill-current" />
                                        </div>
                                    )}
                                </div>
                                <div className="space-y-1">
                                    <div className="flex items-center space-x-2">
                                        <h3 className="font-bold leading-tight">{ch.title}</h3>
                                        {ch.partner_status === 'pinned' && <Pin className="w-3 h-3 text-secondary" />}
                                    </div>
                                    <div className="flex items-center space-x-3 text-xs text-text-muted">
                                        <span className="flex items-center space-x-1">
                                            <BarChart3 className="w-3 h-3" />
                                            <span>{ch.posts_count_24h} постів/24г</span>
                                        </span>
                                        <span className="bg-surface-secondary px-2 py-0.5 rounded text-[10px] uppercase font-bold text-text-muted border border-border">
                                            {ch.category || 'Без категорії'}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            <a
                                href={ch.username ? `https://t.me/${ch.username}` : '#'}
                                target="_blank"
                                rel="noreferrer"
                                className="p-2 bg-surface border border-border rounded-xl hover:bg-border transition-colors outline-none"
                            >
                                <ExternalLink className="w-5 h-5 text-text-muted" />
                            </a>
                        </motion.div>
                    ))}
                </div>

                {error && (
                    <div className="p-4 bg-error/10 border border-error/20 rounded-xl text-error text-center">
                        {error}
                    </div>
                )}
            </div>
        </Layout>
    );
};
