import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence, Reorder, useDragControls } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { useCatalogStore } from '../store/catalogStore';
import { API_ORIGIN } from '../api/client';
import { getUserId } from '../utils/telegram';
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
    AlertCircle,
    Star,
    Crown,
    Trash2,
    LayoutGrid,
    Bookmark,
    UserCog,
    Clock,
    GripVertical,
    Sparkles
} from 'lucide-react';

const PLANS = [
    {
        id: 'basic',
        name: 'Basic',
        price: 50,
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

const LockedSlot = ({ onClick, tier }: { onClick: () => void, tier?: string }) => {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            onClick={onClick}
            className="relative group bg-surface-secondary/50 dark:bg-surface/20 border-2 border-dashed border-border/60 dark:border-border/30 rounded-2xl p-4 cursor-pointer hover:border-primary/50 transition-all overflow-hidden shadow-sm dark:shadow-none"
        >
            {/* Shimmer Effect */}
            <div className="absolute inset-0 w-full h-full">
                <motion.div
                    animate={{
                        x: ['-100%', '200%'],
                    }}
                    transition={{
                        duration: 8,
                        repeat: Infinity,
                        ease: "linear",
                        repeatDelay: 5
                    }}
                    className="absolute inset-0 bg-gradient-to-r from-transparent via-[var(--shimmer)] to-transparent w-1/2 -skew-x-12"
                />
            </div>

            <div className="flex items-center space-x-4 relative z-10">
                <div className="w-12 h-12 rounded-xl bg-surface/80 dark:bg-surface-secondary/30 border border-border/50 flex items-center justify-center text-primary/40 group-hover:text-primary transition-colors shadow-sm dark:shadow-none">
                    {tier === 'premium' ? <Crown size={24} /> : <Lock size={20} />}
                </div>
                <div className="flex-1">
                    <h3 className="font-bold text-text-muted group-hover:text-text-primary transition-colors">Розблокувати слот</h3>
                    <p className="text-[10px] text-text-muted font-bold tracking-wider uppercase opacity-50">Наступний рівень</p>
                </div>
                <div className="p-2 text-primary opacity-0 group-hover:opacity-100 transition-all transform translate-x-2 group-hover:translate-x-0">
                    <Sparkles size={20} />
                </div>
            </div>
        </motion.div>
    );
};

interface ChannelItemProps {
    ch: any;
    index: number;
    userStatus: any;
    imgErrors: Record<number, boolean>;
    setImgErrors: React.Dispatch<React.SetStateAction<Record<number, boolean>>>;
    submittingIds: Record<number, boolean>;
    setSubmittingIds: React.Dispatch<React.SetStateAction<Record<number, boolean>>>;
    unsubscribeFromChannel: (userId: number, channelId: number) => Promise<any>;
    fetchMyChannels: (userId: number) => Promise<void>;
    userId: number;
}

const ChannelItem: React.FC<ChannelItemProps> = ({
    ch,
    index,
    userStatus,
    imgErrors,
    setImgErrors,
    submittingIds,
    setSubmittingIds,
    unsubscribeFromChannel,
    fetchMyChannels,
    userId
}) => {
    const controls = useDragControls();
    const isActiveSlot = userStatus ? index < userStatus.limit : true;
    const canUnsubscribeAt = ch.can_unsubscribe_at ? new Date(ch.can_unsubscribe_at) : null;
    const isLocked = canUnsubscribeAt ? canUnsubscribeAt > new Date() : false;

    return (
        <Reorder.Item
            key={ch.id}
            value={ch}
            dragListener={false}
            dragControls={controls}
            className={`relative group bg-surface border-2 rounded-2xl p-4 transition-all ${isActiveSlot
                ? 'border-success/30 shadow-success/5 active:scale-[0.99]'
                : 'border-error/30 opacity-70 scale-[0.98]'
                }`}
        >
            <div className="flex items-center space-x-3">
                <div
                    className="flex-shrink-0 cursor-grab active:cursor-grabbing p-1 -ml-1 text-text-muted opacity-40 group-hover:opacity-100 transition-opacity touch-none select-none"
                    onPointerDown={(e) => controls.start(e)}
                >
                    <GripVertical size={20} />
                </div>

                <div className="flex-1 min-w-0 flex items-center space-x-3">
                    <div className="relative flex-shrink-0">
                        <div className="w-12 h-12 rounded-xl bg-surface-secondary border border-border flex items-center justify-center overflow-hidden font-bold text-lg text-primary">
                            {!imgErrors[ch.id] && ch.avatar_url ? (
                                <motion.img
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    transition={{ duration: 0.3 }}
                                    src={`${API_ORIGIN}${ch.avatar_url}`}
                                    alt={ch.title}
                                    className="w-full h-full object-cover"
                                    loading="lazy"
                                    onError={() => {
                                        setImgErrors(prev => ({ ...prev, [ch.id]: true }));
                                    }}
                                />
                            ) : (
                                ch.title.charAt(0)
                            )}
                        </div>
                        {ch.partner_status === 'premium' && (
                            <div className="absolute -top-1 -right-1 bg-primary p-1 rounded-full border-2 border-surface">
                                <Zap className="w-3 h-3 text-white fill-current" />
                            </div>
                        )}
                    </div>
                    <div className="space-y-1 flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                            <h3 className="font-bold leading-tight truncate">{ch.title}</h3>
                            {ch.partner_status === 'pinned' && <Pin className="w-3 h-3 text-secondary" />}
                            {!isActiveSlot && (
                                <span className="flex-shrink-0 bg-error/10 text-error text-[9px] px-1.5 py-0.5 rounded-full font-bold border border-error/20">
                                    Inactive
                                </span>
                            )}
                            {isActiveSlot && (
                                <span className="flex-shrink-0 bg-success/10 text-success text-[9px] px-1.5 py-0.5 rounded-full font-bold border border-success/20">
                                    Active
                                </span>
                            )}
                        </div>
                        <div className="flex items-center space-x-3 text-xs text-text-muted">
                            <span className="flex items-center space-x-1">
                                <BarChart3 className="w-3 h-3" />
                                <span>{ch.posts_count_24h} постів/24г</span>
                            </span>
                        </div>
                    </div>
                </div>

                <div className="flex items-center space-x-2 flex-shrink-0 ml-2">
                    <a
                        href={ch.username ? `https://t.me/${ch.username}` : '#'}
                        target="_blank"
                        rel="noreferrer"
                        className="p-2 bg-surface/50 border border-border rounded-xl hover:bg-border transition-colors outline-none"
                    >
                        <ExternalLink className="w-5 h-5 text-text-muted" />
                    </a>

                    <button
                        onClick={async (e) => {
                            e.stopPropagation();
                            if (isLocked) {
                                const remainingMs = canUnsubscribeAt!.getTime() - new Date().getTime();
                                const hours = Math.floor(remainingMs / 3600000);
                                const minutes = Math.floor((remainingMs % 3600000) / 60000);
                                const timeStr = hours > 0 ? `${hours}г ${minutes}хв` : `${minutes}хв`;

                                const webApp = (window as any).Telegram?.WebApp;
                                const msg = `Цей слот заморожено на 24г для запобігання зловживанням. Ви зможете змінити його через ${timeStr}.`;

                                if (webApp?.showPopup) {
                                    webApp.showPopup({
                                        title: 'Слот заморожено',
                                        message: msg,
                                        buttons: [{ type: 'ok', text: 'Зрозуміло' }]
                                    });
                                } else {
                                    alert(msg);
                                }
                                return;
                            }

                            if (window.confirm(`Відписатися від ${ch.title}?`)) {
                                setSubmittingIds(prev => ({ ...prev, [ch.id]: true }));
                                await unsubscribeFromChannel(userId, ch.id);
                                setSubmittingIds(prev => ({ ...prev, [ch.id]: false }));
                                fetchMyChannels(userId);
                            }
                        }}
                        disabled={submittingIds[ch.id]}
                        className={`p-2 border rounded-xl transition-colors ${isLocked
                            ? 'bg-surface border-border text-text-muted opacity-50'
                            : 'bg-error/10 text-error border-error/20 hover:bg-error/20'
                            }`}
                    >
                        {submittingIds[ch.id] ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            isLocked ? (
                                <Clock className="w-5 h-5" />
                            ) : (
                                <Trash2 className="w-5 h-5" />
                            )
                        )}
                    </button>
                </div>
            </div>
        </Reorder.Item>
    );
};

export const MyChannelsPage: React.FC = () => {
    const navigate = useNavigate();
    const {
        channels,
        userStatus,
        isLoading,
        error,
        fetchMyChannels,
        fetchUserStatus,
        addCustomChannel,
        unsubscribeFromChannel,
        reorderChannels,
        createInvoice
    } = useCatalogStore();

    const [isAddModalOpen, setIsAddModalOpen] = useState(false);
    const [isPaywallOpen, setIsPaywallOpen] = useState(false);
    const [paywallReason, setPaywallReason] = useState<'limit' | 'upsell'>('upsell');
    const [channelUrl, setChannelUrl] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSubscribing, setIsSubscribing] = useState(false);
    const [selectedTier, setSelectedTier] = useState('standard');
    const [feedback, setFeedback] = useState<{ type: 'success' | 'error', message: string } | null>(null);
    const [imgErrors, setImgErrors] = useState<Record<number, boolean>>({});
    const [submittingIds, setSubmittingIds] = useState<Record<number, boolean>>({});
    const [localChannels, setLocalChannels] = useState<any[]>([]);
    const [hasOrderChanged, setHasOrderChanged] = useState(false);

    // Логіка відображення Locked Slot
    const shouldShowLockedSlot = () => {
        if (!userStatus) return false;

        // Для Demo завжди показуємо
        if (userStatus.tier === 'demo') return true;

        // Для інших (paid) якщо кількість каналів >= ліміт - 1
        return userStatus.sub_count >= userStatus.limit - 1;
    };

    const userId = getUserId();

    useEffect(() => {
        fetchMyChannels(userId);
        fetchUserStatus(userId);
    }, [userId, fetchMyChannels, fetchUserStatus]);

    useEffect(() => {
        setLocalChannels(channels);
        setHasOrderChanged(false);
    }, [channels]);

    const handleSubscribe = async () => {
        setIsSubscribing(true);
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
    };

    const handleAddClick = () => {
        if (userStatus && !userStatus.can_add) {
            setPaywallReason('limit');
            setIsPaywallOpen(true);
        } else if (userStatus && userStatus.tier === 'demo') {
            // Для демо просто переправляємо в каталог
            navigate('/catalog');
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
            <div className="pb-24 space-y-6">
                {/* Header Section */}
                <header className="mb-6 mt-2 px-1">
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <motion.h1
                                initial={{ x: -20, opacity: 0 }}
                                animate={{ x: 0, opacity: 1 }}
                                className="text-3xl font-black text-text-primary flex items-center gap-2"
                            >
                                <img src="/pulse-logo.svg" alt="Pulse" className="w-9 h-9" />
                                Мої канали
                            </motion.h1>
                            <div className="flex items-center space-x-2 pl-11">
                                <button
                                    onClick={() => navigate('/catalog')}
                                    className="p-1 hover:bg-surface rounded-full transition-colors text-text-muted"
                                >
                                    <ArrowLeft size={16} />
                                </button>
                                <p className="text-sm text-text-secondary font-medium">Керування вашими підписками</p>
                            </div>
                        </div>

                        <div className="flex items-center space-x-3">

                            <div className="flex p-1 bg-surface/40 backdrop-blur-md rounded-xl border border-border/50 shadow-sm">
                                <button
                                    onClick={() => navigate('/catalog')}
                                    className="p-2 rounded-lg transition-all text-text-secondary hover:text-text-primary"
                                    title="Каталог"
                                >
                                    <LayoutGrid size={18} />
                                </button>
                                <button
                                    onClick={() => navigate('/catalog/my')}
                                    className="p-2 rounded-lg transition-all bg-primary text-text-primary shadow-lg shadow-primary/20"
                                    title="Мої канали"
                                >
                                    <Bookmark size={18} />
                                </button>
                                <button
                                    onClick={() => navigate('/cabinet')}
                                    className="p-2 rounded-lg transition-all text-text-secondary hover:text-text-primary"
                                    title="Кабінет"
                                >
                                    <UserCog size={18} />
                                </button>
                            </div>
                        </div>
                    </div>
                </header>

                {/* Status Bar */}
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`border backdrop-blur-md rounded-2xl flex items-stretch transition-all overflow-hidden min-h-[72px] ${userStatus && userStatus.sub_count > userStatus.limit
                        ? 'bg-error/10 border-error/30 shadow-lg shadow-error/5'
                        : 'bg-surface/50 border-border shadow-sm'
                        }`}
                >
                    {!userStatus ? (
                        <div className="flex-1 flex items-center justify-center space-x-2 text-text-muted opacity-50">
                            <Loader2 size={16} className="animate-spin" />
                            <span className="text-xs">Завантаження статусу...</span>
                        </div>
                    ) : (
                        <>
                            {/* Left: Subscription Info/Upgrade */}
                            <div
                                onClick={() => setIsPaywallOpen(true)}
                                className="flex-1 p-4 flex items-center space-x-3 cursor-pointer hover:bg-surface/80 active:bg-surface transition-colors group"
                            >
                                <div className={`p-2 rounded-xl border transition-colors ${userStatus.sub_count > userStatus.limit
                                    ? 'bg-error/20 border-error text-error animate-pulse'
                                    : (userStatus.tier === 'premium' ? 'bg-primary/10 border-primary text-primary' : 'bg-surface border-border text-text-secondary')
                                    }`}>
                                    {userStatus.tier === 'premium' ? <Crown className="w-5 h-5" /> : <Zap className="w-5 h-5" />}
                                </div>
                                <div className="min-w-0">
                                    <p className={`text-[10px] uppercase font-bold tracking-wider ${userStatus.sub_count > userStatus.limit ? 'text-error animate-pulse' : 'text-text-muted'}`}>
                                        {userStatus.sub_count > userStatus.limit ? 'Ліміт перевищено' : 'Мій План'}
                                    </p>
                                    <div className="flex items-center gap-2 leading-none pt-0.5">
                                        <p className="font-bold capitalize truncate">{userStatus.tier || 'Free'}</p>
                                        <Sparkles className="w-3 h-3 text-primary opacity-0 group-hover:opacity-100 transition-opacity" />
                                    </div>
                                    {userStatus.expires_at && (
                                        <p className="text-[8px] text-text-muted mt-1">
                                            до {new Date(userStatus.expires_at).toLocaleDateString()}
                                        </p>
                                    )}
                                </div>
                            </div>

                            {/* Visual Divider */}
                            <div className="w-px bg-border/50 self-center h-8" />

                            {/* Right: Slots / Add Channel */}
                            <div
                                onClick={handleAddClick}
                                className="p-4 flex items-center space-x-4 cursor-pointer hover:bg-surface/80 active:bg-surface transition-colors group"
                            >
                                <div className="text-right flex flex-col justify-center">
                                    <p className="text-[10px] uppercase font-bold tracking-wider text-text-muted whitespace-nowrap">Слоти</p>
                                    <p className="font-bold text-lg leading-tight">
                                        <span className={userStatus.sub_count > userStatus.limit ? 'text-error' : 'text-primary'}>
                                            {userStatus.sub_count}
                                        </span>
                                        <span className="text-text-muted">/{userStatus.limit}</span>
                                    </p>
                                </div>
                                <div className={`p-2 rounded-xl transition-all ${userStatus.sub_count > userStatus.limit
                                    ? 'bg-error text-white'
                                    : 'bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white shadow-lg shadow-primary/10'
                                    }`}>
                                    <Plus className="w-5 h-5" />
                                </div>
                            </div>
                        </>
                    )}
                </motion.div>

                {/* Channels List */}
                <div className="px-1">
                    <Reorder.Group
                        axis="y"
                        values={localChannels}
                        onReorder={(newOrder) => {
                            setLocalChannels(newOrder);
                            setHasOrderChanged(true);
                        }}
                        className="space-y-3"
                    >
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

                        {localChannels.map((ch, index: number) => {
                            if (ch.is_placeholder) {
                                return (
                                    <Reorder.Item
                                        key={ch.id}
                                        value={ch}
                                        dragListener={false} // Порожні слоти не перетягуються
                                        className="relative group bg-surface/30 border-2 border-dashed border-border/50 rounded-2xl p-4 transition-all hover:border-primary/50"
                                    >
                                        <div className="flex items-center space-x-4">
                                            <div className="w-12 h-12 rounded-xl bg-surface-secondary/50 border border-dashed border-border flex items-center justify-center text-text-muted opacity-40">
                                                <Plus size={24} />
                                            </div>
                                            <div className="flex-1">
                                                <h3 className="font-bold text-text-secondary">Порожній слот</h3>
                                                <p className="text-xs text-text-muted">Натисніть, щоб додати канал</p>
                                            </div>
                                            <button
                                                onClick={handleAddClick}
                                                className="p-2.5 bg-surface-secondary text-text-secondary border border-border rounded-xl hover:bg-primary hover:text-white transition-all shadow-sm"
                                            >
                                                <Plus size={20} />
                                            </button>
                                        </div>
                                    </Reorder.Item>
                                );
                            }

                            return (
                                <ChannelItem
                                    key={ch.id}
                                    ch={ch}
                                    index={index}
                                    userStatus={userStatus}
                                    imgErrors={imgErrors}
                                    setImgErrors={setImgErrors}
                                    submittingIds={submittingIds}
                                    setSubmittingIds={setSubmittingIds}
                                    unsubscribeFromChannel={unsubscribeFromChannel}
                                    fetchMyChannels={fetchMyChannels}
                                    userId={userId}
                                />
                            );
                        })}
                    </Reorder.Group>

                    {/* Locked Upsell Slot */}
                    {shouldShowLockedSlot() && (
                        <div className="mt-3">
                            <LockedSlot
                                onClick={() => {
                                    setPaywallReason('upsell');
                                    setIsPaywallOpen(true);
                                }}
                                tier={userStatus?.tier}
                            />
                        </div>
                    )}
                </div>

                {error && (
                    <div className="p-4 bg-error/10 border border-error/20 rounded-xl text-error text-center text-sm">
                        {error}
                    </div>
                )}

                {/* Floating Save Button */}
                <AnimatePresence>
                    {hasOrderChanged && (
                        <motion.div
                            initial={{ y: 100, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            exit={{ y: 100, opacity: 0 }}
                            className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 w-full max-w-xs px-4"
                        >
                            <button
                                onClick={async () => {
                                    setIsSubmitting(true);
                                    const realChannelIds = localChannels
                                        .filter(ch => !ch.is_placeholder)
                                        .map(ch => ch.id);
                                    const result = await reorderChannels(userId, realChannelIds);
                                    if (result.success) {
                                        setHasOrderChanged(false);
                                        // fetchMyChannels вже викликається в reorderChannels якщо треба, 
                                        // або ми вже оновили стор
                                    } else {
                                        (window as any).Telegram?.WebApp?.showPopup?.({
                                            title: 'Обмеження',
                                            message: result.message,
                                            buttons: [{ type: 'ok', text: 'Зрозуміло' }]
                                        });
                                        setLocalChannels(channels); // Revert
                                        setHasOrderChanged(false);
                                    }
                                    setIsSubmitting(false);
                                }}
                                disabled={isSubmitting}
                                className="w-full py-4 bg-primary text-white rounded-2xl font-bold shadow-2xl flex items-center justify-center space-x-2"
                            >
                                {isSubmitting ? <Loader2 className="animate-spin" /> : <>
                                    <CheckCircle2 size={20} />
                                    <span>Зберегти порядок</span>
                                </>}
                            </button>
                        </motion.div>
                    )}
                </AnimatePresence>
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
                                            <span>Додати за посиланням</span>
                                        </>
                                    )}
                                </button>

                                <div className="relative">
                                    <div className="absolute inset-0 flex items-center">
                                        <div className="w-full border-t border-border"></div>
                                    </div>
                                    <div className="relative flex justify-center text-xs uppercase">
                                        <span className="bg-surface px-2 text-text-muted">або</span>
                                    </div>
                                </div>

                                <button
                                    onClick={() => {
                                        setIsAddModalOpen(false);
                                        navigate('/catalog');
                                    }}
                                    className="w-full py-4 bg-surface-secondary border border-border text-text-primary rounded-2xl font-bold flex items-center justify-center space-x-3 hover:bg-surface transition-colors"
                                >
                                    <LayoutGrid className="w-5 h-5" />
                                    <span>Вибрати з каталогу</span>
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
                                {paywallReason === 'upsell' ? (
                                    <Sparkles className="w-10 h-10 text-primary animate-pulse" />
                                ) : (
                                    <Lock className="w-10 h-10 text-primary" />
                                )}
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
                )}
            </AnimatePresence>
        </Layout>
    );
};
