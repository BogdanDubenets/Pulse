import React from 'react';
import { clsx } from 'clsx';

interface LayoutProps {
    children: React.ReactNode;
    className?: string;
}

export const Layout: React.FC<LayoutProps> = ({ children, className }) => {
    return (
        <div className="min-h-screen bg-background text-text-primary font-sans selection:bg-primary/30">
            <div className={clsx("max-w-md mx-auto min-h-screen px-4 py-6 relative", className)}>
                {/* Ambient Background Glow */}
                <div className="fixed top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
                    <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-primary/20 blur-[100px] rounded-full dark:mix-blend-screen mix-blend-multiply opacity-50 dark:opacity-100 animate-pulse-slow" />
                    <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-accent/10 blur-[100px] rounded-full dark:mix-blend-screen mix-blend-multiply opacity-50 dark:opacity-100 animate-pulse-slow delay-1000" />
                </div>

                {children}
            </div>
        </div>
    );
};
