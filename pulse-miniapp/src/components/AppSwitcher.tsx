import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Newspaper, LayoutGrid, User, Sun, Moon } from 'lucide-react';
import { useThemeStore } from '../store/themeStore';
import { clsx } from 'clsx';

export const AppSwitcher: React.FC = () => {
    const location = useLocation();
    const navigate = useNavigate();

    const tabs = [
        { id: 'digest', icon: Newspaper, label: 'Дайджест', path: '/' },
        { id: 'catalog', icon: LayoutGrid, label: 'Каталог', path: '/catalog' },
        { id: 'cabinet', icon: User, label: 'Кабінет', path: '/cabinet' },
    ];

    const { theme, toggleTheme } = useThemeStore();

    const activeTab = tabs.find(t => {
        if (t.path === '/') return location.pathname === '/';
        return location.pathname.startsWith(t.path);
    }) || tabs[0];

    return (
        <div className="fixed top-2 left-0 w-full z-50 px-4 pointer-events-none">
            <div className="max-w-md mx-auto pointer-events-auto">
                <nav className="bg-surface/60 backdrop-blur-xl border border-white/10 dark:border-white/5 rounded-2xl p-1.5 flex items-center shadow-lg shadow-black/5">
                    {tabs.map((tab) => {
                        const isActive = activeTab.id === tab.id;
                        const Icon = tab.icon;

                        return (
                            <button
                                key={tab.id}
                                onClick={() => navigate(tab.path)}
                                className={clsx(
                                    "relative flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl transition-all duration-300 active:scale-95",
                                    isActive ? "text-primary font-bold" : "text-text-secondary hover:text-text-primary"
                                )}
                            >
                                {isActive && (
                                    <motion.div
                                        layoutId="activeTab"
                                        className="absolute inset-0 bg-primary/10 rounded-xl"
                                        transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                                    />
                                )}
                                <Icon size={18} strokeWidth={isActive ? 2.5 : 2} className="relative z-10" />
                                <span className="text-[10px] uppercase tracking-wider relative z-10 font-black">
                                    {tab.label}
                                </span>
                            </button>
                        );
                    })}

                    <div className="w-px h-6 bg-white/10 dark:bg-white/5 mx-1" />

                    <button
                        onClick={toggleTheme}
                        className="p-2.5 text-text-secondary hover:text-accent transition-all active:scale-90"
                    >
                        {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
                    </button>
                </nav>
            </div>
        </div>
    );
};
