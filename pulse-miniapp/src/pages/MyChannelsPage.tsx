import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { useCatalogStore } from '../store/catalogStore';
import {
    ArrowLeft,
    ExternalLink,
    Zap,
    Pin,
    BarChart3,
    Loader2,
    Plus,
    X,
    Lock,
    CheckCircle2,
    AlertCircle
} from 'lucide-react';

export const MyChannelsPage: React.FC = () => {
    const navigate = useNavigate();
    const {
        channels,
        userStatus,
        isLoading,
        error,
        fetchMyChannels,
        fetchUserStatus,
        addCustomChannel
    } = useCatalogStore();

    const [isAddModalOpen, setIsAddModalOpen] = useState(false);
    const [isPaywallOpen, setIsPaywallOpen] = useState(false);
    const [channelUrl, setChannelUrl] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [feedback, setFeedback] = useState<{ type: 'success' | 'error', message: string } | null>(null);

    const userId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || 461874849;

    useEffect(() => {
        fetchMyChannels(userId);
        fetchUserStatus(userId);
    }, [userId, fetchMyChannels, fetchUserStatus]);

    const handleAddClick = () => {
        if (userStatus && !userStatus.can_add) {
            setIsPaywallOpen(true);
        } else {
            setIsAddModalOpen(true);
        }
    };

    const handleAddChannel = async () => {
        if (!channelUrl) return;
        setIsSubmitting(true);
        setFeedback(null);

        const result = await addCustomChannel(userId, channelUrl);

        if (result.success) {
            setFeedback({ type: 'success', message: result.message });
            setChannelUrl('');
            setTimeout(() => {
                setIsAddModalOpen(false);
                setFeedback(null);
            }, 2000);
        } else {
            setFeedback({ type: 'error', message: result.message });
        }
        setIsSubmitting(false);
    };

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
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <button
                            onClick={() => navigate('/catalog')}
                            className="p-2 hover:bg-surface rounded-full transition-colors"
                        >
                            <ArrowLeft className="w-6 h-6" />
                        </button>
                        <h1 className="text-2xl font-bold">Мої канали</h1>
                    </div>

                    <button
                        onClick={handleAddClick}
                        className="p-3 bg-primary text-white rounded-2xl shadow-lg shadow-primary/20 hover:scale-105 active:scale-95 transition-all"
                    >
                        <Plus className="w-6 h-6" />
                    </button>
                </div>

                {/* Status Bar */}
                {userStatus && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-4 bg-surface/50 border border-border backdrop-blur-md rounded-2xl flex items-center justify-between"
                    >
                        <div className="flex items-center space-x-3">
                            <div className={`p-2 rounded-xl border ${userStatus.tier === 'premium' ? 'bg-primary/10 border-primary text-primary' : 'bg-surface border-border text-text-secondary'}`}>
                                <Zap className="w-5 h-5" />
                            </div>
                            <div>
                                <p className="text-[10px] uppercase font-bold tracking-wider text-text-muted">Мій План</p>
                                <p className="font-bold capitalize">{userStatus.tier}</p>
                            </div>
                        </div>
                        <div className="text-right">
                            <p className="text-[10px] uppercase font-bold tracking-wider text-text-muted">Ліміт каналів</p>
                            <p className="font-bold">
                                <span className="text-primary">{userStatus.sub_count}</span>
                                <span className="text-text-muted"> / {userStatus.limit}</span>
                            </p>
                        </div>
                    </motion.div>
                )}

                {/* Channels List */}
                <div className="space-y-3">
                    {channels.length === 0 && !isLoading && (
                        <div className="py-12 text-center space-y-4">
                            <div className="w-16 h-16 bg-surface border border-dashed border-border rounded-full flex items-center justify-center mx-auto text-text-muted">
                                <Pin className="w-8 h-8 opacity-20" />
                            </div>
                            <p className="text-text-secondary">Тут будуть ваші підписки.</p>
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
                            transition={{ delay: index * 0.05 }}
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
                    <div className="p-4 bg-error/10 border border-error/20 rounded-xl text-error text-center text-sm">
                        {error}
                    </div>
                )}
            </div>

            {/* Add Channel Modal */}
            <AnimatePresence>
                {isAddModalOpen && (
                    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setIsAddModalOpen(false)}
                            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                        />
                        <motion.div
                            initial={{ y: "100%" }}
                            animate={{ y: 0 }}
                            exit={{ y: "100%" }}
                            className="relative w-full max-w-md bg-surface border-t sm:border border-border rounded-t-[32px] sm:rounded-[32px] p-6 shadow-2xl overflow-hidden"
                        >
                            <div className="flex justify-between items-center mb-6">
                                <h2 className="text-xl font-bold">Додати власний канал</h2>
                                <button onClick={() => setIsAddModalOpen(false)} className="p-2 hover:bg-surface-secondary rounded-full">
                                    <X className="w-6 h-6" />
                                </button>
                            </div>

                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-text-secondary px-1">Посилання або @username</label>
                                    <input
                                        type="text"
                                        value={channelUrl}
                                        onChange={(e) => setChannelUrl(e.target.value)}
                                        placeholder="t.me/example або @example"
                                        className="w-full p-4 bg-surface-secondary border border-border rounded-2xl outline-none focus:border-primary transition-colors font-medium"
                                    />
                                </div>

                                <AnimatePresence mode="wait">
                                    {feedback && (
                                        <motion.div
                                            initial={{ opacity: 0, height: 0 }}
                                            animate={{ opacity: 1, height: 'auto' }}
                                            exit={{ opacity: 0, height: 0 }}
                                            className={`p-4 rounded-xl flex items-center space-x-3 ${feedback.type === 'success' ? 'bg-success/10 text-success border border-success/20' : 'bg-error/10 text-error border border-error/20'
                                                }`}
                                        >
                                            {feedback.type === 'success' ? <CheckCircle2 className="w-5 h-5 shrink-0" /> : <AlertCircle className="w-5 h-5 shrink-0" />}
                                            <span className="text-sm font-medium">{feedback.message}</span>
                                        </motion.div>
                                    )}
                                </AnimatePresence>

                                <button
                                    onClick={handleAddChannel}
                                    disabled={isSubmitting || !channelUrl}
                                    className="w-full py-4 bg-primary text-white rounded-2xl font-bold text-lg shadow-lg shadow-primary/20 disabled:opacity-50 disabled:grayscale transition-all flex items-center justify-center space-x-3"
                                >
                                    {isSubmitting ? (
                                        <Loader2 className="w-6 h-6 animate-spin" />
                                    ) : (
                                        <>
                                            <Plus className="w-6 h-6" />
                                            <span>Додати до Pulse</span>
                                        </>
                                    )}
                                </button>

                                <p className="text-center text-xs text-text-muted px-4">
                                    Ми автоматично проаналізуємо контент каналу та додамо його до вашого персонального дайджесту.
                                </p>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>

            {/* Paywall Modal */}
            <AnimatePresence>
                {isPaywallOpen && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setIsPaywallOpen(false)}
                            className="absolute inset-0 bg-black/80 backdrop-blur-md"
                        />
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            className="relative w-full max-w-sm bg-gradient-to-b from-surface to-surface-secondary border border-primary/30 rounded-[32px] p-8 shadow-2xl text-center space-y-6 overflow-hidden"
                        >
                            {/* Decorative Background */}
                            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-primary to-transparent" />
                            <div className="absolute -top-24 -right-24 w-48 h-48 bg-primary/10 rounded-full blur-3xl" />
                            <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-secondary/10 rounded-full blur-3xl" />

                            <div className="w-20 h-20 bg-primary/10 rounded-3xl flex items-center justify-center mx-auto border border-primary/20">
                                <Lock className="w-10 h-10 text-primary" />
                            </div>

                            <div className="space-y-2">
                                <h2 className="text-2xl font-bold">Ліміт вичерпано</h2>
                                <p className="text-text-secondary text-sm">
                                    На безкоштовному плані ви можете додати максимум <span className="text-primary font-bold">3 канали</span>.
                                </p>
                            </div>

                            <div className="space-y-3">
                                <div className="p-4 bg-surface border border-border rounded-2xl flex items-center space-x-4 text-left group hover:border-primary/30 transition-colors">
                                    <div className="p-2 bg-primary/10 rounded-lg group-hover:scale-110 transition-transform">
                                        <Zap className="w-5 h-5 text-primary" />
                                    </div>
                                    <div>
                                        <p className="font-bold text-sm">Pulse Premium</p>
                                        <p className="text-xs text-text-muted">Необмежено власних каналів</p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => navigate('/billing')}
                                    className="w-full py-4 bg-primary text-white rounded-2xl font-bold shadow-lg shadow-primary/30 hover:shadow-primary/40 active:scale-95 transition-all text-lg"
                                >
                                    Оновити за 50 Stars
                                </button>
                                <button
                                    onClick={() => setIsPaywallOpen(false)}
                                    className="w-full py-3 text-text-secondary font-medium hover:text-text transition-colors"
                                >
                                    Пізніше
                                </button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </Layout>
    );
};
