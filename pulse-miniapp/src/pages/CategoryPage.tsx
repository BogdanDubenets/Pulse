import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { useCatalogStore } from '../store/catalogStore';
import { API_ORIGIN } from '../api/client';
import { getUserId } from '../utils/telegram';
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
    UserCog,
    ChevronRight,
    Sparkles
} from 'lucide-react';

// Допоміжний компонент для слотів
const PromotionSlot: React.FC<{
    type: 'auction' | 'premium' | 'pinned';
    title: string;
    channel?: any;
    onDetail: () => void;
}> = ({ type, title, channel, onDetail }) => {
    return (
        <div className="space-y-1.5">
            <h3 className="text-[9px] font-black uppercase tracking-wider text-text-muted px-1 flex items-center gap-1.5 opacity-70">
                {type === 'auction' && <Trophy className="w-2.5 h-2.5 text-accent" />}
                {type === 'premium' && <Sparkles className="w-2.5 h-2.5 text-primary" />}
                {type === 'pinned' && <Pin className="w-2.5 h-2.5 text-secondary" />}
                {title}
            </h3>

            {channel ? (
                <div className={`p-2.5 bg-surface border rounded-xl flex items-center justify-between transition-all ${type === 'auction' ? 'border-accent/40 bg-gradient-to-r from-surface to-accent/5 shadow-sm shadow-accent/5' :
                    type === 'premium' ? 'border-primary/40 bg-gradient-to-r from-surface to-primary/5 shadow-sm shadow-primary/5' :
                        'border-secondary/20 bg-gradient-to-r from-surface to-secondary/5'
                    }`}>
                    <div className="flex items-center space-x-3">
                        <div className="relative">
                            <div className="w-9 h-9 rounded-full overflow-hidden bg-surface-secondary border border-border flex items-center justify-center font-bold text-xs">
                                {channel.avatar_url ? (
                                    <img src={`${API_ORIGIN}${channel.avatar_url}`} alt={channel.title} className="w-full h-full object-cover" />
                                ) : channel.title.charAt(0)}
                            </div>
                            <div className={`absolute -top-0.5 -right-0.5 p-0.5 rounded-full border border-surface ${type === 'auction' ? 'bg-accent' : type === 'premium' ? 'bg-primary' : 'bg-secondary'
                                }`}>
                                {type === 'auction' && <Trophy className="w-1.5 h-1.5 text-background fill-current" />}
                                {type === 'premium' && <Zap className="w-1.5 h-1.5 text-white fill-current" />}
                                {type === 'pinned' && <Pin className="w-1.5 h-1.5 text-white" />}
                            </div>
                        </div>
                        <div className="min-w-0">
                            <p className="font-bold text-xs truncate max-w-[100px] leading-tight">{channel.title}</p>
                            <p className="text-[8px] text-text-muted">@{channel.username}</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-1.5">
                        <a
                            href={`https://t.me/${channel.username}`}
                            target="_blank"
                            rel="noreferrer"
                            className="p-1.5 bg-surface/50 border border-border rounded-lg"
                        >
                            <ExternalLink size={12} className="text-text-muted" />
                        </a>
                        <button
                            onClick={onDetail}
                            className={`px-2 py-1.5 text-[9px] font-black uppercase tracking-widest rounded-lg transition-all ${type === 'auction' ? 'bg-accent/10 text-accent' :
                                type === 'premium' ? 'bg-primary/10 text-primary' :
                                    'bg-secondary/10 text-secondary'
                                }`}
                        >
                            Інфо
                        </button>
                    </div>
                </div>
            ) : (
                <div
                    onClick={onDetail}
                    className="p-2.5 bg-surface/10 border border-dashed border-border/50 rounded-xl flex items-center justify-between cursor-pointer active:scale-[0.98] transition-all"
                >
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full border border-dashed border-border/50 flex items-center justify-center opacity-40">
                            <Plus size={14} className="text-text-muted" />
                        </div>
                        <div className="text-left">
                            <p className="text-[9px] font-bold text-text-muted uppercase">Вільний слот</p>
                            <p className="text-[8px] text-text-muted opacity-60">Станьте першим тут</p>
                        </div>
                    </div>
                    <ChevronRight size={12} className="text-text-muted opacity-30" />
                </div>
            )}
        </div>
    );
};

export const CategoryPage: React.FC = () => {
    const { category } = useParams<{ category: string }>();
    const navigate = useNavigate();
    const { channels, isLoading, error, fetchChannels, subscribeToChannel, unsubscribeFromChannel } = useCatalogStore();
    const [isAuctionOpen, setIsAuctionOpen] = useState(false);
    const [imgErrors, setImgErrors] = useState<Record<number, boolean>>({});
    const [submittingIds, setSubmittingIds] = useState<Record<number, boolean>>({});

    const userId = getUserId();

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

                {/* Promotion Slots Section */}
                <div className="grid grid-cols-1 gap-4 mb-8">
                    {/* 1. Auction Slot */}
                    <PromotionSlot
                        type="auction"
                        title="🏆 Аукціон: Top-1 Категорії"
                        channel={channels.find(c => c.partner_status === 'auction')}
                        onDetail={() => navigate('/cabinet', { state: { tab: 'auctions', category } })}
                    />

                    {/* 2. Premium Slot */}
                    <PromotionSlot
                        type="premium"
                        title="💎 Premium Карусель"
                        channel={channels.find(c => c.partner_status === 'premium')}
                        onDetail={() => navigate('/cabinet', { state: { tab: 'promote', section: 'premium' } })}
                    />

                    {/* 3. Partner Slot */}
                    <PromotionSlot
                        type="pinned"
                        title="🤝 Партнерська мережа"
                        channel={channels.find(c => c.partner_status === 'pinned')}
                        onDetail={() => navigate('/cabinet', { state: { tab: 'promote', section: 'partner' } })}
                    />
                </div>

                <div className="h-px bg-border/50 mx-2" />

                <h2 className="text-sm font-bold uppercase tracking-wider text-text-muted px-1">Усі канали</h2>

                {/* Channels List */}
                <div className="space-y-3">
                    {channels.map((ch, index) => (
                        <motion.div
                            key={ch.id}
                            initial={{ x: -20, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            transition={{ delay: index * 0.05 }}
                            className={`p-4 bg-surface border rounded-2xl flex items-center justify-between transition-all ${ch.partner_status === 'auction'
                                ? 'border-accent shadow-lg shadow-accent/10 bg-gradient-to-br from-surface to-accent/5'
                                : (ch.partner_status === 'premium' ? 'border-primary shadow-lg shadow-primary/5' : 'border-border')
                                }`}
                        >
                            <div className="flex items-center space-x-4 flex-1 min-w-0">
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
                                    {ch.partner_status === 'auction' ? (
                                        <div className="absolute -top-1 -right-1 bg-accent p-1 rounded-full border-2 border-surface animate-bounce-subtle">
                                            <Trophy className="w-3 h-3 text-background fill-current" />
                                        </div>
                                    ) : ch.partner_status === 'premium' && (
                                        <div className="absolute -top-1 -right-1 bg-primary p-1 rounded-full border-2 border-surface">
                                            <Zap className="w-3 h-3 text-white fill-current" />
                                        </div>
                                    )}
                                </div>
                                <div className="space-y-1">
                                    <div className="flex items-center space-x-2">
                                        <h3 className="font-bold leading-tight truncate">{ch.title}</h3>
                                        {ch.partner_status === 'pinned' && <Pin className="w-3 h-3 text-secondary" />}
                                    </div>
                                    <div className="flex items-center space-x-3 text-xs text-text-muted">
                                        <span className="flex items-center space-x-1">
                                            <BarChart3 className="w-3 h-3" />
                                            <span>{ch.posts_count_24h} постів/24г</span>
                                        </span>
                                        {ch.username && (
                                            <span className="text-secondary truncate">@{ch.username}</span>
                                        )}
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center space-x-2 sm:space-x-3 flex-shrink-0 ml-2">
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
                                                    // Миттєвий редирект без зайвих запитань
                                                    navigate('/catalog/my');
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
