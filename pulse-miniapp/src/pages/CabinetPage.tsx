import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Layout } from '../components/Layout';
import { useCatalogStore } from '../store/catalogStore';
import { API_ORIGIN } from '../api/client';
import { getUserId } from '../utils/telegram';
import {
    Trophy,
    Zap,
    Pin,
    ArrowRight,
    Loader2,
    CheckCircle2,
    AlertCircle,
    Star,
    Crown,
    Clock,
    UserCog
} from 'lucide-react';
import { useLocation } from 'react-router-dom';

const PREMIUM_PLANS = [
    { days: 7, price: 1, label: '7 днів' },
    { days: 14, price: 1, label: '14 днів', popular: true },
    { days: 30, price: 1, label: '30 днів' }
];

export const CabinetPage: React.FC = () => {
    const {
        channels: myChannels,
        fetchMyChannels,
        fetchAuctions,
        placeBid,
        buyPremium,
        verifyPin
    } = useCatalogStore();

    const [auctions, setAuctions] = useState<any[]>([]);
    const [selectedChannel, setSelectedChannel] = useState<any>(null);
    const [activeTab, setActiveTab] = useState<'auctions' | 'promote'>('auctions');
    const [isProcessing, setIsProcessing] = useState(false);
    const [feedback, setFeedback] = useState<{ type: 'success' | 'error', message: string } | null>(null);

    const userId = getUserId();

    const location = useLocation();

    useEffect(() => {
        fetchMyChannels(userId);
        loadAuctions();

        // Обробка вхідного стану для перемикання табів та скролу
        const state = location.state as any;
        if (state?.tab) {
            setActiveTab(state.tab);

            if (state.section) {
                setTimeout(() => {
                    const el = document.getElementById(`section - ${state.section} `);
                    if (el) el.scrollIntoView({ behavior: 'smooth' });
                }, 300);
            }
        }
    }, [userId, location.state]);

    const loadAuctions = async () => {
        const data = await fetchAuctions();
        setAuctions(data);
    };

    const handleBid = async (auction: any) => {
        if (!selectedChannel) {
            setFeedback({ type: 'error', message: 'Спочатку виберіть канал для просування' });
            return;
        }
        setIsProcessing(true);
        const amount = auction.current_bid ? auction.current_bid + 1 : 1;
        const success = await placeBid(userId, selectedChannel.id, auction.category, amount);

        if (success) {
            setFeedback({ type: 'success', message: `Ставку ${amount} Stars прийнято!` });
            loadAuctions();
        } else {
            setFeedback({ type: 'error', message: 'Помилка розміщення ставки' });
        }
        setIsProcessing(false);
    };

    const handleBuyPremium = async (plan: any) => {
        if (!selectedChannel) return;
        setIsProcessing(true);
        const result = await buyPremium(userId, selectedChannel.id, selectedChannel.category, plan.days);
        if (result.success) {
            setFeedback({ type: 'success', message: result.message });
        } else {
            setFeedback({ type: 'error', message: result.message });
        }
        setIsProcessing(false);
    };

    const handleVerifyPin = async () => {
        if (!selectedChannel) return;
        setIsProcessing(true);
        const result = await verifyPin(userId, selectedChannel.id);
        if (result.success) {
            setFeedback({ type: 'success', message: result.message });
        } else {
            setFeedback({ type: 'error', message: result.message });
        }
        setIsProcessing(false);
    };

    return (
        <Layout>
            <div className="pb-24 space-y-6 p-4">
                {/* Header */}
                <header className="flex items-center justify-between mb-8">
                    <div className="space-y-1">
                        <h1 className="text-3xl font-black flex items-center gap-3">
                            <span className="p-2 bg-primary/10 rounded-2xl">
                                <UserCog className="text-primary w-8 h-8" />
                            </span>
                            Кабінет
                        </h1>
                        <p className="text-sm text-text-muted font-medium ml-1">Керування просуванням каналів</p>
                    </div>
                </header>

                {/* Feedback Toast */}
                <AnimatePresence>
                    {feedback && (
                        <motion.div
                            initial={{ opacity: 0, y: -20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            className={`p - 4 rounded - 2xl flex items - center space - x - 3 shadow - lg border ${feedback.type === 'success' ? 'bg-success/10 border-success/20 text-success' : 'bg-error/10 border-error/20 text-error'
                                } `}
                        >
                            {feedback.type === 'success' ? <CheckCircle2 className="w-5 h-5 flex-shrink-0" /> : <AlertCircle className="w-5 h-5 flex-shrink-0" />}
                            <span className="text-sm font-bold">{feedback.message}</span>
                            <button onClick={() => setFeedback(null)} className="ml-auto opacity-50">×</button>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Section 1: Channel Selector */}
                <section className="space-y-4">
                    <div className="flex items-center justify-between px-1">
                        <h2 className="text-sm font-bold uppercase tracking-wider text-text-muted">Мій канал для просування</h2>
                    </div>

                    <div className="flex overflow-x-auto pb-2 -mx-1 px-1 space-x-3 no-scrollbar">
                        {myChannels.filter(ch => !ch.is_placeholder).map(ch => (
                            <button
                                key={ch.id}
                                onClick={() => setSelectedChannel(ch)}
                                className={`flex - shrink - 0 w - 48 p - 4 rounded - 2xl border transition - all text - left relative overflow - hidden ${selectedChannel?.id === ch.id
                                        ? 'border-primary bg-primary/5 ring-1 ring-primary/20'
                                        : 'border-white/5 bg-surface/40'
                                    } `}
                            >
                                <div className="flex items-center space-x-3 relative z-10">
                                    <div className="w-10 h-10 rounded-xl bg-surface-secondary border border-border flex items-center justify-center overflow-hidden font-bold text-primary">
                                        {ch.avatar_url ? (
                                            <img src={`${API_ORIGIN}${ch.avatar_url} `} alt={ch.title} className="w-full h-full object-cover" />
                                        ) : ch.title.charAt(0)}
                                    </div>
                                    <div className="min-w-0">
                                        <p className="font-bold text-sm truncate">{ch.title}</p>
                                        <p className="text-[10px] text-text-muted truncate">{ch.category}</p>
                                    </div>
                                </div>
                                {selectedChannel?.id === ch.id && (
                                    <div className="absolute top-2 right-2">
                                        <CheckCircle2 size={14} className="text-primary" />
                                    </div>
                                )}
                            </button>
                        ))}
                    </div>
                </section>

                {/* Section 2: Tiers */}
                <div className="grid grid-cols-2 gap-3">
                    <button
                        onClick={() => setActiveTab('auctions')}
                        className={`py - 3 rounded - xl font - bold transition - all border ${activeTab === 'auctions' ? 'bg-primary text-white border-primary shadow-lg shadow-primary/20' : 'bg-surface/40 border-border text-text-muted'
                            } `}
                    >
                        Аукціони (Top-1)
                    </button>
                    <button
                        onClick={() => setActiveTab('promote')}
                        className={`py - 3 rounded - xl font - bold transition - all border ${activeTab === 'promote' ? 'bg-primary text-white border-primary shadow-lg shadow-primary/20' : 'bg-surface/40 border-border text-text-muted'
                            } `}
                    >
                        Постійні слоти
                    </button>
                </div>

                <AnimatePresence mode="wait">
                    {activeTab === 'auctions' ? (
                        <motion.div
                            key="auctions"
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 10 }}
                            className="space-y-4"
                        >
                            {auctions.map((auc) => (
                                <div key={auc.category} className="p-5 bg-surface/50 border border-border rounded-2xl relative overflow-hidden group">
                                    <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                                        <Trophy size={60} />
                                    </div>
                                    <div className="relative z-10 space-y-4">
                                        <div className="flex items-center justify-between">
                                            <div className="space-y-0.5">
                                                <p className="text-xs font-black text-accent uppercase tracking-widest">Категорія</p>
                                                <h3 className="text-xl font-bold">{auc.category}</h3>
                                            </div>
                                            <div className="text-right">
                                                <p className="text-[10px] text-text-muted font-bold uppercase">Поточна ставка</p>
                                                <div className="flex items-center justify-end text-lg font-black text-primary">
                                                    <Zap className="w-4 h-4 mr-1 fill-current" />
                                                    {auc.current_bid || 50}
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex items-center justify-between pt-2 border-t border-border/50">
                                            <div className="flex items-center space-x-2 text-xs text-text-muted">
                                                <Clock className="w-3 h-3" />
                                                <span>{auc.ends_at ? `До ${new Date(auc.ends_at).toLocaleTimeString()} ` : '24г залишилось'}</span>
                                            </div>
                                            <button
                                                onClick={() => handleBid(auc)}
                                                disabled={isProcessing}
                                                className="px-6 py-2 bg-accent text-background font-bold rounded-xl active:scale-95 transition-all shadow-md shadow-accent/20"
                                            >
                                                {isProcessing ? <Loader2 size={18} className="animate-spin" /> : 'Ставка'}
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </motion.div>
                    ) : (
                        <motion.div
                            key="promote"
                            initial={{ opacity: 0, x: 10 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -10 }}
                            className="space-y-6"
                        >
                            {/* Premium Carousel Section */}
                            <div className="space-y-4" id="section-premium">
                                <div className="flex items-center space-x-2">
                                    <Crown className="w-5 h-5 text-primary" />
                                    <h3 className="font-bold">Premium Карусель (Tier 2)</h3>
                                </div>
                                <div className="grid grid-cols-3 gap-3">
                                    {PREMIUM_PLANS.map(plan => (
                                        <button
                                            key={plan.days}
                                            onClick={() => handleBuyPremium(plan)}
                                            className="p-4 bg-surface/40 border border-border rounded-2xl text-center space-y-2 relative group hover:border-primary/50 transition-all"
                                        >
                                            {plan.popular && (
                                                <div className="absolute -top-2 left-1/2 -translate-x-1/2 bg-primary text-white text-[8px] px-2 py-0.5 rounded-full font-black uppercase">
                                                    Hit
                                                </div>
                                            )}
                                            <p className="text-xs font-bold text-text-muted">{plan.label}</p>
                                            <p className="text-lg font-black flex items-center justify-center">
                                                {plan.price}
                                                <Star className="w-3 h-3 ml-1 fill-current text-amber-400" />
                                            </p>
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Partner Network Section */}
                            <div className="space-y-4" id="section-partner">
                                <div className="flex items-center space-x-2">
                                    <Pin className="w-5 h-5 text-secondary" />
                                    <h3 className="font-bold">Партнерська мережа (Tier 3)</h3>
                                </div>
                                <div className="p-5 bg-gradient-to-br from-secondary/10 to-primary/5 border border-secondary/20 rounded-2xl space-y-4">
                                    <p className="text-sm text-text-secondary leading-relaxed">
                                        Закріпіть пост про Pulse у своєму каналі та отримуйте <b>бесплатне</b> місце у каруселі партнерів на 7 днів.
                                    </p>
                                    <button
                                        onClick={handleVerifyPin}
                                        className="w-full py-3 bg-secondary text-white font-bold rounded-xl active:scale-95 transition-all flex items-center justify-center gap-2"
                                    >
                                        {isProcessing ? <Loader2 size={20} className="animate-spin" /> : <>
                                            <span>Перевірити закреп</span>
                                            <ArrowRight size={18} />
                                        </>}
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </Layout>
    );
};
