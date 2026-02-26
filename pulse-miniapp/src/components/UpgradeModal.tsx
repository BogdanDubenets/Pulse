import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Star, Loader2 } from 'lucide-react';
import { useCatalogStore } from '../store/catalogStore';
import { getUserId } from '../utils/telegram';

import { PLANS } from '../constants/plans';

export const UpgradeModal: React.FC = () => {
    const {
        isPaywallOpen,
        paywallReason,
        setIsPaywallOpen,
        userStatus,
        isLoading,
        createInvoice,
        fetchUserStatus
    } = useCatalogStore();

    const [selectedTier, setSelectedTier] = useState('standard');
    const [isSubscribing, setIsSubscribing] = useState(false);
    const userId = getUserId();

    console.log('[DEBUG] UpgradeModal render:', { isPaywallOpen, paywallReason, userId });

    const handleSubscribe = async () => {
        setIsSubscribing(true);
        try {
            const invoiceLink = await createInvoice(userId, selectedTier);

            if (invoiceLink) {
                (window.Telegram?.WebApp as any).openInvoice(invoiceLink, (status: string) => {
                    if (status === 'paid') {
                        fetchUserStatus(userId);
                        setIsPaywallOpen(false);
                    }
                    setIsSubscribing(false);
                });
            } else {
                setIsSubscribing(false);
            }
        } catch (err) {
            console.error('Invoice error:', err);
            setIsSubscribing(false);
        }
    };

    if (!isPaywallOpen) return null;

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
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

                    <div className="w-20 h-20 bg-primary/5 rounded-3xl flex items-center justify-center mx-auto border border-primary/10">
                        <img src="/pulse-logo.svg" alt="Pulse" className="w-12 h-12" />
                    </div>

                    <div className="space-y-2">
                        <h2 className="text-2xl font-bold">
                            {paywallReason === 'upsell' ? 'Розкрийте потенціал Pulse' : 'Час для апгрейду'}
                        </h2>
                        <p className="text-text-secondary text-sm">
                            {paywallReason === 'upsell'
                                ? 'Отримайте більше місця для каналів та преміальну AI-аналітику вже зараз.'
                                : `Ви досягли ліміту (${userStatus?.limit} каналів). Перейдіть на наступний рівень, щоб додати більше.`
                            }
                        </p>
                    </div>

                    <div className="space-y-3">
                        {PLANS.map((plan) => (
                            <div
                                key={plan.id}
                                onClick={() => setSelectedTier(plan.id)}
                                className={`p-4 bg-surface border rounded-2xl flex items-center justify-between transition-all cursor-pointer ${selectedTier === plan.id ? 'border-primary ring-1 ring-primary/20 bg-primary/5' : 'border-border'
                                    }`}
                            >
                                <div className="flex items-center space-x-3">
                                    <div className={`p-2 rounded-lg bg-gradient-to-br ${plan.color} text-white`}>
                                        {plan.icon}
                                    </div>
                                    <div className="text-left">
                                        <div className="flex items-center space-x-2">
                                            <p className="font-bold text-sm">{plan.name}</p>
                                            {plan.popular && <span className="text-[8px] bg-primary text-white px-1.5 py-0.5 rounded-full uppercase font-black">Hit</span>}
                                        </div>
                                        <p className="text-[10px] text-text-muted">{plan.features}</p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="flex items-center space-x-1 justify-end">
                                        <span className="font-black text-sm">{plan.price}</span>
                                        <Star className="w-3 h-3 fill-current text-amber-400" />
                                    </div>
                                    <p className="text-[8px] text-text-muted uppercase font-bold">на 30 днів</p>
                                </div>
                            </div>
                        ))}

                        <button
                            onClick={handleSubscribe}
                            disabled={isSubscribing || isLoading}
                            className="w-full py-4 bg-primary text-white rounded-2xl font-bold shadow-lg shadow-primary/30 hover:shadow-primary/40 active:scale-95 transition-all text-lg flex items-center justify-center space-x-2"
                        >
                            {isSubscribing ? (
                                <Loader2 className="w-6 h-6 animate-spin" />
                            ) : (
                                <>
                                    <span>Активувати за {PLANS.find(p => p.id === selectedTier)?.price}</span>
                                    <Star className="w-5 h-5 fill-current" />
                                </>
                            )}
                        </button>
                        <button
                            onClick={() => setIsPaywallOpen(false)}
                            className="w-full py-2 text-text-secondary text-sm font-medium hover:text-text transition-colors"
                        >
                            Пізніше
                        </button>
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    );
};
