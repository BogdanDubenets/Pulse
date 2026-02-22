import React from 'react';
import { Layout } from '../components/Layout';
import { motion } from 'framer-motion';
import { Construction, Sparkles, Rocket } from 'lucide-react';

export const CabinetPlaceholder: React.FC = () => {
    return (
        <Layout className="flex items-center justify-center">
            <div className="text-center space-y-8 px-6">
                <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ type: "spring", bounce: 0.5 }}
                    className="relative inline-block"
                >
                    <div className="absolute -inset-4 bg-primary/20 blur-2xl rounded-full animate-pulse" />
                    <Construction size={80} className="relative z-10 text-primary mx-auto" />
                </motion.div>

                <div className="space-y-4">
                    <motion.h1
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.2 }}
                        className="text-4xl font-black text-text-primary"
                    >
                        Кабінет у розробці
                    </motion.h1>
                    <motion.p
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.3 }}
                        className="text-text-secondary text-lg"
                    >
                        Ми готуємо для вас преміальну партнерку та персоналізацію стрічки.
                    </motion.p>
                </div>

                <motion.div
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.4 }}
                    className="flex flex-col gap-4 mt-8"
                >
                    <div className="flex items-center gap-3 p-4 bg-surface/40 backdrop-blur-xl border border-white/10 rounded-2xl text-left">
                        <Sparkles className="text-accent" size={24} />
                        <div>
                            <p className="font-bold text-sm">Партнерська програма</p>
                            <p className="text-xs text-text-secondary">Заробляйте разом з Pulse</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3 p-4 bg-surface/40 backdrop-blur-xl border border-white/10 rounded-2xl text-left">
                        <Rocket className="text-primary" size={24} />
                        <div>
                            <p className="font-bold text-sm">Персональні фільтри</p>
                            <p className="text-xs text-text-secondary">Тонке налаштування вашого дайджесту</p>
                        </div>
                    </div>
                </motion.div>

                <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.6 }}
                    className="text-[10px] text-text-muted font-bold uppercase tracking-widest pt-8"
                >
                    Дякуємо, що ви з нами!
                </motion.p>
            </div>
        </Layout>
    );
};
