import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { useCatalogStore } from '../store/catalogStore';
import {
    ArrowLeft,
    Zap,
    Check,
    Star,
    Crown,
    Loader2,
    ShieldCheck,
    Clock
} from 'lucide-react';

const PLANS = [
    {
        id: 'basic',
        name: 'Basic',
        price: 50,
        limit: 6,
        icon: <Zap className="w-6 h-6" />,
        color: 'from-blue-500 to-cyan-500',
        features: ['До 6 власних каналів', 'Щоденний дайджест', 'Базова підтримка']
    },
    {
        id: 'standard',
        name: 'Standard',
        price: 90,
        limit: 10,
        icon: <Star className="w-6 h-6" />,
        color: 'from-purple-500 to-pink-500',
        popular: true,
        features: ['До 10 власних каналів', 'Пріоритетний аналіз AI', 'Архів за 48 годин']
    },
    {
        id: 'premium',
        name: 'Premium',
        price: 120,
        limit: 15,
        icon: <Crown className="w-6 h-6" />,
        color: 'from-amber-400 to-orange-500',
        features: ['До 15 власних каналів', 'Ultra-fast AI аналіз', 'Персональний менеджер']
    }
];

export const BillingPage: React.FC = () => {
    const navigate = useNavigate();
    const { userStatus, createInvoice, isLoading } = useCatalogStore();
    const [selectedTier, setSelectedTier] = useState<string>('standard');
    const [isProcessing, setIsProcessing] = useState(false);

    const userId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || 461874849;

    const handleSubscribe = async () => {
        setIsProcessing(true);
        const invoiceLink = await createInvoice(userId, selectedTier);

        if (invoiceLink) {
            (window.Telegram?.WebApp as any).openInvoice(invoiceLink, (status: string) => {
                if (status === 'paid') {
                    navigate('/catalog/my');
                } else {
                    setIsProcessing(false);
                }
            });
        } else {
            setIsProcessing(false);
        }
    };

    return (
        <Layout>
            <div className="p-4 pb-24 space-y-8">
                {/* Header */}
                <div className="flex items-center space-x-4">
                    <button
                        onClick={() => navigate(-1)}
                        className="p-2 hover:bg-surface rounded-full transition-colors"
                    >
                        <ArrowLeft className="w-6 h-6" />
                    </button>
                    <div>
                        <h1 className="text-2xl font-bold">Оновити план</h1>
                        <p className="text-text-secondary text-sm">Оберіть рівень доступу до Pulse</p>
                    </div>
                </div>

                {/* Current Status Card */}
                {userStatus && (
                    <div className="p-5 bg-surface/40 border border-border backdrop-blur-xl rounded-[24px] flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <div className="p-3 bg-primary/10 rounded-2xl">
                                <ShieldCheck className="w-6 h-6 text-primary" />
                            </div>
                            <div>
                                <p className="text-[10px] uppercase font-bold tracking-widest text-text-muted">Поточний План</p>
                                <p className="font-bold text-lg capitalize">{userStatus.tier}</p>
                            </div>
                        </div>
                        <div className="text-right">
                            <div className="flex items-center space-x-1 text-text-muted text-xs font-medium">
                                <Clock className="w-3 h-3" />
                                <span>30 днів</span>
                            </div>
                        </div>
                    </div>
                )}

                {/* Plans List */}
                <div className="space-y-4">
                    {PLANS.map((plan) => (
                        <motion.div
                            key={plan.id}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => setSelectedTier(plan.id)}
                            className={`relative p-5 rounded-[32px] border-2 transition-all cursor-pointer overflow-hidden ${selectedTier === plan.id
                                ? 'border-primary bg-surface shadow-xl shadow-primary/5'
                                : 'border-border bg-surface/20'
                                }`}
                        >
                            {plan.popular && (
                                <div className="absolute top-0 right-0 bg-primary text-white px-4 py-1 rounded-bl-2xl text-[10px] font-black uppercase tracking-tighter">
                                    Популярний
                                </div>
                            )}

                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center space-x-4">
                                    <div className={`p-3 rounded-2xl bg-gradient-to-br ${plan.color} text-white shadow-lg`}>
                                        {plan.icon}
                                    </div>
                                    <div>
                                        <h3 className="text-xl font-black">{plan.name}</h3>
                                        <div className="flex items-baseline space-x-1">
                                            <span className="text-2xl font-black">{plan.price}</span>
                                            <span className="text-xs font-bold text-text-secondary">Stars / міс</span>
                                        </div>
                                    </div>
                                </div>
                                <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors ${selectedTier === plan.id ? 'border-primary bg-primary' : 'border-border'
                                    }`}>
                                    {selectedTier === plan.id && <Check className="w-4 h-4 text-white" />}
                                </div>
                            </div>

                            <div className="grid grid-cols-1 gap-2">
                                {plan.features.map((feature, i) => (
                                    <div key={i} className="flex items-center space-x-2 text-sm text-text-secondary">
                                        <div className="w-1 h-1 rounded-full bg-primary" />
                                        <span>{feature}</span>
                                    </div>
                                ))}
                            </div>

                            {/* Background decoration */}
                            <div className={`absolute -bottom-6 -right-6 w-24 h-24 bg-gradient-to-br ${plan.color} opacity-[0.03] rounded-full blur-2xl`} />
                        </motion.div>
                    ))}
                </div>

                {/* Submit Action */}
                <div className="fixed bottom-0 left-0 w-full p-4 bg-gradient-to-t from-background via-background/95 to-transparent backdrop-blur-sm">
                    <button
                        onClick={handleSubscribe}
                        disabled={isProcessing || isLoading}
                        className="w-full py-5 bg-primary text-white rounded-[24px] font-black text-xl shadow-2xl shadow-primary/30 active:scale-95 transition-all flex items-center justify-center space-x-3"
                    >
                        {isProcessing || isLoading ? (
                            <Loader2 className="w-7 h-7 animate-spin" />
                        ) : (
                            <>
                                <span>Активувати за</span>
                                <span>{PLANS.find(p => p.id === selectedTier)?.price}</span>
                                <Star className="w-6 h-6 fill-current" />
                            </>
                        )}
                    </button>
                    <p className="text-center text-[10px] text-text-muted mt-3 uppercase font-bold tracking-widest px-4">
                        Оплата здійснюється через офіційну платформу Telegram Stars
                    </p>
                </div>
            </div>
        </Layout>
    );
};
