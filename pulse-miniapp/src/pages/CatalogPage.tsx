import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { useCatalogStore } from '../store/catalogStore';
import {
    LayoutGrid,
    ChevronRight,
    Zap,
    ShieldCheck,
    TrendingUp,
    Globe,
    Cpu,
    Gamepad2,
    Music,
    Newspaper,
    Loader2,
    Bookmark,
    Landmark,
    ShieldAlert,
    Theater,
    ExternalLink,
    Users
} from 'lucide-react';
import { API_ORIGIN } from '../api/client';

const categoryIcons: Record<string, any> = {
    '⚽ Спорт': TrendingUp,
    '🧪 Наука': Cpu,
    '🎮 Ігри': Gamepad2,
    '🎵 Музика': Music,
    '📰 Новини': Newspaper,
    '📰 Події': Newspaper,
    '🌍 Світ': Globe,
    '💎 Premium': Zap,
    '🛡️ Крипта': ShieldCheck,
    '🎩 Політика': Landmark,
    '🪖 Війна': ShieldAlert,
    '🎭 Культура': Theater,
    'Мої канали': Bookmark,
};

const getCategoryIcon = (name: string) => {
    if (categoryIcons[name]) return categoryIcons[name];
    const n = name.toLowerCase();
    if (n.includes('події') || n.includes('новини')) return Newspaper;
    if (n.includes('політика')) return Landmark;
    if (n.includes('війна')) return ShieldAlert;
    if (n.includes('культура')) return Theater;
    if (n.includes('спорт')) return TrendingUp;
    if (n.includes('наука')) return Cpu;
    if (n.includes('крипта')) return ShieldCheck;
    if (n.includes('світ')) return Globe;
    return LayoutGrid;
};

export const CatalogPage: React.FC = () => {
    const navigate = useNavigate();
    const { categories, channels, isLoading, error, fetchCategories, fetchChannels, subscribeToChannel, unsubscribeFromChannel } = useCatalogStore();
    const [viewMode, setViewMode] = React.useState<'categories' | 'popular'>('categories');

    useEffect(() => {
        if (viewMode === 'categories') {
            fetchCategories();
        } else if (viewMode === 'popular') {
            fetchChannels(undefined, 'popularity');
        }
    }, [viewMode, fetchCategories, fetchChannels]);

    const container = {
        hidden: { opacity: 0 },
        show: {
            opacity: 1,
            transition: {
                staggerChildren: 0.1
            }
        }
    };

    const item = {
        hidden: { y: 20, opacity: 0 },
        show: { y: 0, opacity: 1 }
    };

    if (isLoading && categories.length === 0) {
        return (
            <Layout className="flex items-center justify-center">
                <Loader2 className="w-10 h-10 animate-spin text-primary" />
            </Layout>
        );
    }

    return (
        <Layout>
            <div className="pb-24 space-y-8">
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
                                Каталог
                            </motion.h1>
                            <motion.p
                                initial={{ x: -20, opacity: 0 }}
                                animate={{ x: 0, opacity: 1 }}
                                transition={{ delay: 0.1 }}
                                className="text-sm text-text-secondary font-medium pl-11"
                            >
                                Найкращі Telegram-канали, відібрані для вас
                            </motion.p>
                        </div>

                        <div className="flex p-1 bg-surface/40 backdrop-blur-md rounded-xl border border-border/50 shadow-sm">
                            <button
                                onClick={() => setViewMode('categories')}
                                className={`p-2 rounded-lg transition-all ${viewMode === 'categories' ? 'bg-primary text-text-primary shadow-lg shadow-primary/20' : 'text-text-secondary hover:text-text-primary'}`}
                                title="Категорії"
                            >
                                <LayoutGrid size={18} />
                            </button>
                            <button
                                onClick={() => setViewMode('popular')}
                                className={`p-2 rounded-lg transition-all ${viewMode === 'popular' ? 'bg-primary text-text-primary shadow-lg shadow-primary/20' : 'text-text-secondary hover:text-text-primary'}`}
                                title="Популярні"
                            >
                                <TrendingUp size={18} />
                            </button>
                            <button
                                onClick={() => navigate('/catalog/my')}
                                className="p-2 rounded-lg transition-all text-text-secondary hover:text-text-primary"
                                title="Мої канали"
                            >
                                <Bookmark size={18} />
                            </button>
                        </div>
                    </div>
                </header>

                {/* Content Area */}
                <motion.div
                    variants={container}
                    initial="hidden"
                    animate="show"
                    className="grid grid-cols-1 gap-4"
                >
                    {viewMode === 'categories' ? (
                        <>
                            {/* Prepend My Channels if user wants it first */}
                            <motion.div
                                variants={item}
                                whileHover={{ scale: 1.01 }}
                                whileTap={{ scale: 0.99 }}
                                onClick={() => navigate('/catalog/my')}
                                className="group relative p-5 bg-primary/10 backdrop-blur-xl border border-primary/30 rounded-2xl cursor-pointer hover:border-primary transition-all shadow-sm"
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center space-x-4">
                                        <div className="p-3 bg-primary/20 rounded-xl group-hover:bg-primary/30 transition-colors">
                                            <Bookmark className="w-6 h-6 text-primary" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold text-lg">Мої канали</h3>
                                            <p className="text-sm text-text-muted">Канали, на які ви підписані</p>
                                        </div>
                                    </div>
                                    <ChevronRight className="w-5 h-5 text-text-muted group-hover:text-primary transform group-hover:translate-x-1 transition-all" />
                                </div>
                            </motion.div>

                            {categories.map((cat) => {
                                const Icon = getCategoryIcon(cat.name);
                                return (
                                    <motion.div
                                        key={cat.name}
                                        variants={item}
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        onClick={() => navigate(`/catalog/${cat.name}`)}
                                        className="group relative p-5 bg-surface/50 backdrop-blur-xl border border-border rounded-2xl cursor-pointer hover:border-primary/50 transition-all shadow-sm"
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center space-x-4">
                                                <div className="p-3 bg-primary/10 rounded-xl group-hover:bg-primary/20 transition-colors">
                                                    <Icon className="w-6 h-6 text-primary" />
                                                </div>
                                                <div>
                                                    <h3 className="font-semibold text-lg">{cat.name}</h3>
                                                    <p className="text-sm text-text-muted">{cat.channels_count} каналів</p>
                                                </div>
                                            </div>
                                            <ChevronRight className="w-5 h-5 text-text-muted group-hover:text-primary transform group-hover:translate-x-1 transition-all" />
                                        </div>
                                        <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent opacity-0 group-hover:opacity-100 rounded-2xl transition-opacity" />
                                    </motion.div>
                                );
                            })}
                        </>
                    ) : (
                        <div className="space-y-4">
                            {isLoading && channels.length === 0 ? (
                                <div className="flex justify-center py-12">
                                    <Loader2 className="w-8 h-8 animate-spin text-primary" />
                                </div>
                            ) : channels.map((ch) => (
                                <motion.div
                                    key={ch.id}
                                    variants={item}
                                    className="bg-surface/50 backdrop-blur-xl border border-border rounded-2xl p-4 flex items-center gap-4"
                                >
                                    <div className="w-14 h-14 rounded-xl bg-surface-secondary overflow-hidden flex-shrink-0 border border-border">
                                        {ch.avatar_url ? (
                                            <img
                                                src={ch.avatar_url.startsWith('http') ? ch.avatar_url : `${API_ORIGIN}${ch.avatar_url}`}
                                                alt={ch.title}
                                                className="w-full h-full object-cover"
                                            />
                                        ) : (
                                            <div className="w-full h-full flex items-center justify-center font-bold text-lg text-primary bg-primary/10 text-primary">
                                                {ch.title.charAt(0)}
                                            </div>
                                        )}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <h3 className="font-bold text-lg leading-tight truncate">{ch.title}</h3>
                                        <div className="flex items-center gap-3 mt-1">
                                            <p className="text-xs text-text-muted flex items-center gap-1">
                                                <Users className="w-3 h-3 text-primary" />
                                                {ch.subs_total || 0} підписників
                                            </p>
                                            <p className="text-xs text-text-muted flex items-center gap-1">
                                                <Zap className="w-3 h-3 text-amber-500" />
                                                {ch.posts_count_24h} постів/добу
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex flex-col gap-2">
                                        <a
                                            href={ch.username ? `https://t.me/${ch.username}` : '#'}
                                            target="_blank"
                                            rel="noreferrer"
                                            className="p-2 rounded-xl bg-surface-secondary border border-border text-text-muted hover:text-primary transition-colors flex items-center justify-center"
                                        >
                                            <ExternalLink size={18} />
                                        </a>
                                        <button
                                            onClick={async () => {
                                                const userId = (window as any).Telegram?.WebApp?.initDataUnsafe?.user?.id;
                                                if (!userId) return;

                                                if (ch.is_subscribed) {
                                                    await unsubscribeFromChannel(userId, ch.id);
                                                } else {
                                                    const res = await subscribeToChannel(userId, ch.id);
                                                    if (!res.success && res.errorCode === 403) {
                                                        (window as any).Telegram?.WebApp?.showPopup?.({
                                                            title: 'Ліміт',
                                                            message: 'Ви досягли ліміту каналів для вашого плану.',
                                                            buttons: [{ type: 'ok', text: 'Окей' }]
                                                        });
                                                    }
                                                }
                                            }}
                                            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${ch.is_subscribed
                                                ? 'bg-surface-secondary text-text-muted'
                                                : 'bg-primary text-white shadow-lg shadow-primary/20'
                                                }`}
                                        >
                                            {ch.is_subscribed ? 'Підписано' : 'Додати'}
                                        </button>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    )}
                </motion.div>

                {error && (
                    <div className="p-4 bg-error/10 border border-error/20 rounded-xl text-error text-center">
                        {error}
                    </div>
                )}
            </div>
        </Layout>
    );
};
