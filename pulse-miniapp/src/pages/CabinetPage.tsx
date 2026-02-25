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
    UserCog,
    Users,
    Share2,
    Copy,
    Gift
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
        verifyPin,
        affiliateStats,
        fetchAffiliateStats
    } = useCatalogStore();

    const [auctions, setAuctions] = useState<any[]>([]);
    const [selectedChannel, setSelectedChannel] = useState<any>(null);
    const [activeTab, setActiveTab] = useState<'auctions' | 'promote' | 'affiliate'>('affiliate');
    const [isProcessing, setIsProcessing] = useState(false);
    const [feedback, setFeedback] = useState<{ type: 'success' | 'error', message: string } | null>(null);
    const [imgErrors, setImgErrors] = useState<Record<number, boolean>>({});

    const userId = getUserId();

    const location = useLocation();

    useEffect(() => {
        fetchMyChannels(userId);
        loadAuctions();
        fetchAffiliateStats(userId);

        // Обробка вхідного стану для перемикання табів та скролу
        const state = location.state as any;
        if (state?.tab) {
            setActiveTab(state.tab);

            if (state.section) {
                setTimeout(() => {
                    const el = document.getElementById(`section-${state.section}`);
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

    const handleCopyLink = () => {
        if (affiliateStats?.referral_link) {
            navigator.clipboard.writeText(affiliateStats.referral_link);
            setFeedback({ type: 'success', message: 'Посилання скопійовано!' });
            (window.Telegram?.WebApp as any).HapticFeedback.notificationOccurred('success');
        }
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
                            className={`p-4 rounded-2xl flex items-center space-x-3 shadow-lg border ${feedback.type === 'success' ? 'bg-success/10 border-success/20 text-success' : 'bg-error/10 border-error/20 text-error'
                                }`}
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
                                className={`flex-shrink-0 w-48 p-4 rounded-2xl border transition-all text-left relative overflow-hidden ${selectedChannel?.id === ch.id
                                    ? 'border-primary bg-primary/5 ring-1 ring-primary/20'
                                    : 'border-white/5 bg-surface/40'
                                    }`}
                            >
                                <div className="flex items-center space-x-3 relative z-10">
                                    <div className="w-10 h-10 rounded-xl bg-surface-secondary border border-border flex items-center justify-center overflow-hidden font-bold text-primary">
                                        {ch.avatar_url && !imgErrors[ch.id] ? (
                                            <img
                                                src={ch.avatar_url.startsWith('http') ? ch.avatar_url : `${API_ORIGIN}${ch.avatar_url}`}
                                                alt={ch.title}
                                                className="w-full h-full object-cover"
                                                loading="lazy"
                                                onError={() => setImgErrors(prev => ({ ...prev, [ch.id]: true }))}
                                            />
                                        ) : (
                                            ch.title[0]
                                        )}
                                    </div>
                                    <div className="min-w-0">
                                        <div className="text-sm font-bold truncate">{ch.title}</div>
                                        <div className="text-[10px] text-text-muted">@{ch.username}</div>
                                    </div>
                                </div>
                                {selectedChannel?.id === ch.id && (
                                    <div className="absolute top-2 right-2 z-20">
                                        <CheckCircle2 size={14} className="text-primary" />
                                    </div>
                                )}
                            </button>
                        ))}
                    </div>
                </section>

                <div className="grid grid-cols-3 gap-2">
                    <button
                        onClick={() => setActiveTab('affiliate')}
                        className={`py-3 px-1 rounded-xl font-bold transition-all border text-xs ${activeTab === 'affiliate' ? 'bg-primary text-white border-primary shadow-lg shadow-primary/20' : 'bg-surface/40 border-border text-text-muted'
                            }`}
                    >
                        Партнерка
                    </button>
                    <button
                        onClick={() => setActiveTab('auctions')}
                        className={`py-3 px-1 rounded-xl font-bold transition-all border text-xs ${activeTab === 'auctions' ? 'bg-primary text-white border-primary shadow-lg shadow-primary/20' : 'bg-surface/40 border-border text-text-muted'
                            }`}
                    >
                        Аукціони
                    </button>
                    <button
                        onClick={() => setActiveTab('promote')}
                        className={`py-3 px-1 rounded-xl font-bold transition-all border text-xs ${activeTab === 'promote' ? 'bg-primary text-white border-primary shadow-lg shadow-primary/20' : 'bg-surface/40 border-border text-text-muted'
                            }`}
                    >
                        Слоти
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
                    ) : activeTab === 'promote' ? (
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
                    ) : (
                        <motion.div
                            key="affiliate"
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            className="space-y-6"
                        >
                            <div className="p-6 bg-gradient-to-br from-primary/20 to-accent/10 border border-primary/20 rounded-[2.5rem] relative overflow-hidden">
                                <div className="absolute top-0 right-0 p-6 opacity-10">
                                    <Gift size={80} className="text-primary rotate-12" />
                                </div>

                                <div className="relative z-10 space-y-6">
                                    <div className="space-y-1">
                                        <h3 className="text-2xl font-black">Заробляй Stars</h3>
                                        <p className="text-sm text-text-secondary font-medium italic">Отримуй {affiliateStats?.commission_percent || 10}% від кожної оплати запрошених друзів</p>
                                        <div className="mt-2 p-2 bg-primary/10 border border-primary/20 rounded-xl">
                                            <p className="text-[10px] text-primary font-bold leading-tight">
                                                🚀 Ми підтримуємо офіційну партнерку Telegram! Виплати приходять миттєво на ваш баланс Stars.
                                            </p>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-4 bg-white/5 rounded-3xl border border-white/10 backdrop-blur-md">
                                            <p className="text-[10px] font-black text-primary uppercase tracking-widest mb-1">Зароблено</p>
                                            <div className="flex items-center gap-1.5">
                                                <Star className="w-4 h-4 text-primary fill-current" />
                                                <span className="text-xl font-black">{Math.floor(affiliateStats?.earned_stars || 0)}</span>
                                            </div>
                                        </div>
                                        <div className="p-4 bg-white/5 rounded-3xl border border-white/10 backdrop-blur-md">
                                            <p className="text-[10px] font-black text-secondary uppercase tracking-widest mb-1">Друзі</p>
                                            <div className="flex items-center gap-1.5">
                                                <Users className="w-4 h-4 text-secondary" />
                                                <span className="text-xl font-black">{affiliateStats?.referrals_count || 0}</span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="space-y-3">
                                        <p className="text-xs font-bold text-text-muted px-1">Твоє реферальне посилання:</p>
                                        <div className="flex items-center gap-2 p-2 pl-4 bg-surface/80 border border-border rounded-2xl">
                                            <span className="text-[10px] font-mono truncate text-text-muted flex-1">
                                                {affiliateStats?.referral_link || 'Завантаження...'}
                                            </span>
                                            <button
                                                onClick={handleCopyLink}
                                                className="p-3 bg-primary text-white rounded-xl active:scale-90 transition-transform"
                                            >
                                                <Copy size={16} />
                                            </button>
                                        </div>
                                    </div>

                                    <button
                                        onClick={() => (window.Telegram?.WebApp as any).openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(affiliateStats?.referral_link || '')}&text=${encodeURIComponent('🔥 Pulse — найкращий агрегатор новин України! Приєднуйся та будь у курсі подій.')}`)}
                                        className="w-full py-4 bg-white text-background font-black rounded-2xl flex items-center justify-center gap-2 shadow-xl active:scale-95 transition-all"
                                    >
                                        <Share2 size={20} />
                                        <span>Запросити друзів</span>
                                    </button>
                                </div>
                            </div>

                            <div className="px-2 space-y-4">
                                <h4 className="text-xs font-black text-text-muted uppercase tracking-[0.2em]">Як це працює?</h4>
                                <div className="space-y-4">
                                    {[
                                        { icon: <Share2 className="text-primary" />, title: 'Поділись посиланням', desc: 'Надішли своє посилання друзям або розмісти в соцмережах' },
                                        { icon: <Users className="text-secondary" />, title: 'Друзі реєструються', desc: 'Вони стають твоїми рефералами назавжди' },
                                        { icon: <Star className="text-accent fill-current" />, title: 'Отримуй бонуси', desc: 'За кожну куплену ними підписку ти отримуєш Stars на свій баланс' },
                                    ].map((step, i) => (
                                        <div key={i} className="flex gap-4 items-start">
                                            <div className="p-3 bg-surface/50 border border-border rounded-2xl">
                                                {step.icon}
                                            </div>
                                            <div className="space-y-0.5">
                                                <p className="font-bold text-sm">{step.title}</p>
                                                <p className="text-xs text-text-muted leading-relaxed">{step.desc}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </Layout>
    );
};
