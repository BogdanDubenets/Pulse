import { Zap, Star, Crown } from 'lucide-react';

export const PLANS = [
    {
        id: 'basic',
        name: 'Basic',
        price: 60,
        limit: 6,
        icon: <Zap className="w-5 h-5" />,
        color: 'from-blue-500 to-cyan-500',
        features: 'До 6 каналів'
    },
    {
        id: 'standard',
        name: 'Standard',
        price: 90,
        limit: 10,
        icon: <Star className="w-5 h-5" />,
        color: 'from-purple-500 to-pink-500',
        popular: true,
        features: 'До 10 каналів'
    },
    {
        id: 'premium',
        name: 'Premium',
        price: 120,
        limit: 15,
        icon: <Crown className="w-5 h-5" />,
        color: 'from-amber-400 to-orange-500',
        features: 'До 15 каналів'
    }
];
