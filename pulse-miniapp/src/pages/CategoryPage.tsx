import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { useCatalogStore } from '../store/catalogStore';
import { API_ORIGIN } from '../api/client';
import {
    ArrowLeft,
    ExternalLink,
    Zap,
    Pin,
    BarChart3,
    Loader2,
    Trophy,
    Plus,
    Check,
    LayoutGrid,
    Bookmark,
    UserCog
} from 'lucide-react';

export const CategoryPage: React.FC = () => {
    const { category } = useParams<{ category: string }>();
    const navigate = useNavigate();
    const { channels, isLoading, error, fetchChannels, subscribeToChannel, unsubscribeFromChannel } = useCatalogStore();
    const [isAuctionOpen, setIsAuctionOpen] = useState(false);
    const [imgErrors, setImgErrors] = useState<Record<number, boolean>>({});
    const [submittingIds, setSubmittingIds] = useState<Record<number, boolean>>({});

    const userId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || 461874849;

    useEffect(() => {
        if (category) {
            fetchChannels(category);
        }
    }, [category, fetchChannels]);

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
                {/* Header Section */}
                <header className="mb-6 mt-2 px-1">
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <motion.h1
                                initial={{ x: -20, opacity: 0 }}
                                animate={{ x: 0, opacity: 1 }}
                                className="text-3xl font-black text-text-primary flex items-center gap-2"
                            >
                                <img src="/pulse-logo.svg" alt="Pulse" className="w-9 h-9" />
                                {category}
                            </motion.h1>
                            <div className="flex items-center space-x-2 pl-11">
                                <button
                                    onClick={() => navigate('/catalog')}
                                    className="p-1 hover:bg-surface rounded-full transition-colors text-text-muted"
                                >
                                    <ArrowLeft size={16} />
                                </button>
                                <p className="text-sm text-text-secondary font-medium">Канали категорії</p>
                            </div>
                        </div>

                        <div className="flex p-1 bg-surface/40 backdrop-blur-md rounded-xl border border-border/50 shadow-sm">
                            <button
                                onClick={() => navigate('/catalog')}
                                className="p-2 rounded-lg transition-all text-text-secondary hover:text-text-primary"
                                title="Каталог"
                            >
                                <LayoutGrid size={18} />
                            </button>
                            <button
                                onClick={() => navigate('/catalog/my')}
                                className="p-2 rounded-lg transition-all text-text-secondary hover:text-text-primary"
                                title="Мої канали"
                            >
                                <Bookmark size={18} />
                            </button>
                            <button
                                onClick={() => navigate('/cabinet')}
                                className="p-2 rounded-lg transition-all text-text-secondary hover:text-text-primary"
                                title="Кабінет"
                            >
                                <UserCog size={18} />
                            </button>
                        </div>
                    </div>
                </header>

                {/* Auction Banner */}
                <motion.div
                    initial={{ scale: 0.95, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="p-5 bg-gradient-to-br from-accent/20 to-primary/10 border border-accent/30 rounded-2xl relative overflow-hidden"
                >
                    <div className="relative z-10 space-y-3">
                        <div className="flex items-center space-x-2 text-accent">
                            <Trophy className="w-5 h-5" />
                            <span className="font-bold text-sm uppercase tracking-wider">Аукціон Top-1</span>
                        </div>
                        <h2 className="text-xl font-bold">Будьте першим у розділі!</h2>
                        <p className="text-sm text-text-secondary pr-12">
                            Ваш канал побачать тисячі користувачів щодня. Ставка від 50 Stars.
                        </p>
                        <button
                            onClick={() => setIsAuctionOpen(true)}
                            className="w-full py-2 bg-accent text-background font-bold rounded-xl active:scale-95 transition-transform"
                        >
                            Зробити ставку
                        </button>
                    </div>
                    <Zap className="absolute -right-4 -top-4 w-24 h-24 text-accent/10 rotate-12" />
                </motion.div>

                {/* Channels List */}
                <div className="space-y-3">
                    {channels.map((ch, index) => (
                        <motion.div
                            key={ch.id}
                            initial={{ x: -20, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            transition={{ delay: index * 0.05 }}
                            className={`p-4 bg-surface border rounded-2xl flex items-center justify-between ${ch.partner_status === 'premium' ? 'border-primary shadow-lg shadow-primary/5' : 'border-border'
                                }`}
                        >
                            <div className="flex items-center space-x-4">
                                <div className="relative">
                                    <div className="w-12 h-12 rounded-full overflow-hidden bg-gradient-to-br from-border to-surface flex items-center justify-center text-xl font-bold border border-border">
                                        {ch.avatar_url && !imgErrors[ch.id] ? (
                                            <motion.img
                                                initial={{ opacity: 0 }}
                                                animate={{ opacity: 1 }}
                                                transition={{ duration: 0.3 }}
                                                src={`${API_ORIGIN}${ch.avatar_url}`}
                                                alt={ch.title}
                                                className="w-full h-full object-cover"
                                                loading="lazy"
                                                onError={() => {
                                                    setImgErrors(prev => ({ ...prev, [ch.id]: true }));
                                                }}
                                            />
                                        ) : (
                                            ch.title.charAt(0)
                                        )}
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
                                        {ch.username && (
                                            <span className="text-secondary">@{ch.username}</span>
                                        )}
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center space-x-3">
                                <a
                                    href={ch.username ? `https://t.me/${ch.username}` : '#'}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="p-2.5 bg-surface/50 backdrop-blur-md border border-border rounded-xl hover:bg-border transition-colors outline-none"
                                >
                                    <ExternalLink className="w-5 h-5 text-text-muted" />
                                </a>

                                <button
                                    onClick={async () => {
                                        setSubmittingIds(prev => ({ ...prev, [ch.id]: true }));
                                        try {
                                            if (ch.is_subscribed) {
                                                await unsubscribeFromChannel(userId, ch.id);
                                            } else {
                                                const result = await subscribeToChannel(userId, ch.id);
                                                if (!result.success && result.errorCode === 403) {
                                                    if (window.Telegram?.WebApp) {
                                                        const webApp = window.Telegram.WebApp as any;
                                                        if (webApp.isVersionAtLeast && webApp.isVersionAtLeast('6.2')) {
                                                            webApp.showAlert(
                                                                'Ліміт підписок вичерпано. Перейдіть до керування планом для розширення ліміту.',
                                                                () => navigate('/catalog/my')
                                                            );
                                                        } else {
                                                            alert('Ліміт підписок вичерпано. Перейдіть до керування планом.');
                                                            navigate('/catalog/my');
                                                        }
                                                    } else {
                                                        navigate('/catalog/my');
                                                    }
                                                    return;
                                                }
                                            }
                                        } catch (err) {
                                            console.error('Subscription error:', err);
                                        } finally {
                                            setSubmittingIds(prev => ({ ...prev, [ch.id]: false }));
                                        }
                                    }}
                                    disabled={submittingIds[ch.id]}
                                    className={`p-2.5 rounded-xl transition-all flex items-center justify-center min-w-[44px] ${ch.is_subscribed
                                        ? 'bg-success/10 text-success border border-success/20'
                                        : 'bg-primary text-white shadow-lg shadow-primary/20 active:scale-90'
                                        }`}
                                >
                                    {submittingIds[ch.id] ? (
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                    ) : ch.is_subscribed ? (
                                        <Check className="w-5 h-5" />
                                    ) : (
                                        <Plus className="w-5 h-5" />
                                    )}
                                </button>
                            </div>
                        </motion.div>
                    ))}
                </div>

                {error && (
                    <div className="p-4 bg-error/10 border border-error/20 rounded-xl text-error text-center">
                        {error}
                    </div>
                )}
            </div>

            {/* Auction Modal Overlay (Simple version) */}
            <AnimatePresence>
                {isAuctionOpen && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 backdrop-blur-sm p-4"
                        onClick={() => setIsAuctionOpen(false)}
                    >
                        <motion.div
                            initial={{ y: "100%" }}
                            animate={{ y: 0 }}
                            exit={{ y: "100%" }}
                            className="w-full max-w-lg bg-surface rounded-t-3xl p-6 space-y-6"
                            onClick={e => e.stopPropagation()}
                        >
                            <div className="w-12 h-1.5 bg-border rounded-full mx-auto" />
                            <div className="space-y-2 text-center">
                                <h3 className="text-2xl font-bold">Аукціон за Top-1</h3>
                                <p className="text-text-secondary">Категорія: {category}</p>
                            </div>

                            <div className="p-4 bg-background border border-border rounded-2xl flex items-center justify-between">
                                <span className="text-text-secondary font-medium">Поточна ставка:</span>
                                <span className="text-xl font-bold flex items-center text-accent">
                                    <Zap className="w-5 h-5 mr-1 fill-current" /> 50 Stars
                                </span>
                            </div>

                            <button
                                className="w-full py-4 bg-primary text-white font-bold rounded-2xl shadow-lg shadow-primary/20 active:scale-95 transition-transform"
                                onClick={() => {
                                    alert("Платежі будуть доступні незабаром!");
                                    setIsAuctionOpen(false);
                                }}
                            >
                                Підняти до 60 Stars
                            </button>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </Layout>
    );
};
