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
    Bookmark
} from 'lucide-react';

const categoryIcons: Record<string, any> = {
    '⚽ Спорт': TrendingUp,
    '🧪 Наука': Cpu,
    '🎮 Ігри': Gamepad2,
    '🎵 Музика': Music,
    '📰 Новини': Newspaper,
    '🌍 Світ': Globe,
    '💎 Premium': Zap,
    '🛡️ Крипта': ShieldCheck,
    'Мої канали': Bookmark,
};

export const CatalogPage: React.FC = () => {
    const navigate = useNavigate();
    const { categories, isLoading, error, fetchCategories } = useCatalogStore();

    useEffect(() => {
        fetchCategories();
    }, [fetchCategories]);

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
            <div className="p-6 pb-24 space-y-8">
                {/* Header Section */}
                <div className="space-y-2">
                    <motion.h1
                        initial={{ x: -20, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        className="text-3xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent"
                    >
                        Каталог Pulse
                    </motion.h1>
                    <motion.p
                        initial={{ x: -20, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ delay: 0.1 }}
                        className="text-text-secondary"
                    >
                        Найкращі Telegram-канали, відібрані для вас
                    </motion.p>
                </div>

                {/* Categories Grid */}
                <motion.div
                    variants={container}
                    initial="hidden"
                    animate="show"
                    className="grid grid-cols-1 gap-4"
                >
                    {/* Prepend My Channels if user wants it first */}
                    <motion.div
                        variants={item}
                        whileHover={{ scale: 1.01 }}
                        whileTap={{ scale: 0.99 }}
                        onClick={() => navigate('/channels')}
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
                        const Icon = categoryIcons[cat.name] || LayoutGrid;
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
