import { create } from 'zustand';
import type { CatalogCategory, ChannelCatalogItem } from '../types';
import { apiClient } from '../api/client';
import { getUserId } from '../utils/telegram';

export interface UserStatus {
    tier: string;
    sub_count: number;
    limit: number;
    can_add: boolean;
    expires_at?: string;
}

export interface AffiliateStats {
    user_id: number;
    referral_link: string;
    earned_stars: number;
    referrals_count: number;
    commission_percent: number;
}

interface CatalogState {
    categories: CatalogCategory[];
    channels: ChannelCatalogItem[];
    userStatus: UserStatus | null;
    affiliateStats: AffiliateStats | null;
    isLoading: boolean;
    error: string | null;

    fetchCategories: () => Promise<void>;
    fetchChannels: (category?: string) => Promise<void>;
    fetchMyChannels: (userId: number) => Promise<void>;
    fetchUserStatus: (userId: number) => Promise<void>;
    fetchAffiliateStats: (userId: number) => Promise<void>;
    addCustomChannel: (userId: number, url: string) => Promise<{ success: boolean; message: string }>;
    fetchAuctions: () => Promise<any[]>;
    buyPremium: (userId: number, channelId: number, category: string, days: number) => Promise<{ success: boolean; message: string }>;
    verifyPin: (userId: number, channelId: number) => Promise<{ success: boolean; message: string }>;
    createInvoice: (userId: number, tier: string, extra?: any) => Promise<string | null>;
    placeBid: (userId: number, channelId: number, category: string, amount: number) => Promise<boolean>;
    subscribeToChannel: (userId: number, channelId: number) => Promise<{ success: boolean; errorCode?: number }>;
    unsubscribeFromChannel: (userId: number, channelId: number) => Promise<boolean>;
    reorderChannels: (userId: number, channelIds: number[]) => Promise<{ success: boolean; message?: string }>;
}

export const useCatalogStore = create<CatalogState>((set, get) => ({
    categories: [],
    channels: [],
    userStatus: null,
    affiliateStats: null,
    isLoading: false,
    error: null,

    fetchUserStatus: async (userId: number) => {
        try {
            const response = await apiClient.get<UserStatus>(`/catalog/user/status/${userId}`);
            set({ userStatus: response.data });
        } catch (error) {
            console.error('Failed to fetch user status:', error);
            // Скидаємо в базовий стан при помилці, щоб уникнути нескінченного завантаження
            set({
                userStatus: {
                    tier: 'demo',
                    sub_count: 0,
                    limit: 3,
                    can_add: true
                }
            });
        }
    },

    addCustomChannel: async (userId: number, url: string) => {
        set({ isLoading: true, error: null });
        try {
            const response = await apiClient.post('/catalog/add-custom-channel', { user_id: userId, url });
            await get().fetchUserStatus(userId);
            await get().fetchMyChannels(userId);
            set({ isLoading: false });
            return { success: true, message: response.data.message };
        } catch (error: any) {
            const message = error.response?.data?.detail || 'Помилка додавання каналу';
            set({ isLoading: false });
            return { success: false, message };
        }
    },

    createInvoice: async (userId: number, tier: string, extra: any = {}) => {
        set({ isLoading: true, error: null });
        try {
            const response = await apiClient.post<{ invoice_link: string }>('/billing/create-invoice', {
                user_id: userId,
                tier,
                ...extra
            });
            set({ isLoading: false });
            return response.data.invoice_link;
        } catch (error: any) {
            const message = error.response?.data?.detail || 'Помилка створення інвойсу';
            set({ error: message, isLoading: false });
            return null;
        }
    },

    fetchCategories: async () => {
        set({ isLoading: true, error: null });
        try {
            const response = await apiClient.get<CatalogCategory[]>('/catalog/categories');
            set({ categories: response.data, isLoading: false });
        } catch (error: any) {
            console.error('Failed to fetch categories:', error);
            set({ error: 'Помилка завантаження категорій', isLoading: false });
        }
    },

    fetchChannels: async (category?: string) => {
        set({ channels: [], isLoading: true, error: null });
        try {
            const userId = getUserId();
            const params = new URLSearchParams();
            if (category) params.append('category', category);
            if (userId) params.append('user_id', userId.toString());

            const response = await apiClient.get<ChannelCatalogItem[]>(`/catalog/channels?${params.toString()}`);
            set({ channels: response.data, isLoading: false });
        } catch (error: any) {
            console.error('Failed to fetch channels:', error);
            set({ error: 'Помилка завантаження каналів', isLoading: false });
        }
    },

    fetchMyChannels: async (userId: number) => {
        set({ channels: [], isLoading: true, error: null });
        try {
            const response = await apiClient.get<ChannelCatalogItem[]>(`/catalog/my-channels/${userId}`);
            set({ channels: response.data, isLoading: false });
        } catch (error: any) {
            console.error('Failed to fetch my channels:', error);
            set({ error: 'Помилка завантаження ваших підписок', isLoading: false });
        }
    },

    placeBid: async (userId: number, channelId: number, category: string, amount: number) => {
        try {
            const invoiceLink = await get().createInvoice(userId, 'auction_bid', {
                category,
                channel_id: channelId,
                amount
            });

            if (invoiceLink) {
                return new Promise((resolve) => {
                    (window.Telegram?.WebApp as any).openInvoice(invoiceLink, (status: string) => {
                        resolve(status === 'paid');
                    });
                });
            }
            return false;
        } catch (error: any) {
            console.error('Failed to place bid:', error);
            return false;
        }
    },

    subscribeToChannel: async (userId: number, channelId: number) => {
        try {
            await apiClient.post('/catalog/subscribe', { user_id: userId, channel_id: channelId });
            // Оновлюємо статус локально для швидкості
            set(state => ({
                channels: state.channels.map(ch =>
                    ch.id === channelId ? { ...ch, is_subscribed: true } : ch
                )
            }));
            await get().fetchUserStatus(userId);
            return { success: true };
        } catch (error: any) {
            const errorCode = error.response?.status;
            return { success: false, errorCode };
        }
    },

    unsubscribeFromChannel: async (userId: number, channelId: number) => {
        try {
            await apiClient.post('/catalog/unsubscribe', { user_id: userId, channel_id: channelId });
            // Оновлюємо статус локально
            set(state => ({
                channels: state.channels.map(ch =>
                    ch.id === channelId ? { ...ch, is_subscribed: false } : ch
                )
            }));
            await get().fetchUserStatus(userId);
            return true;
        } catch (error) {
            console.error('Failed to unsubscribe:', error);
            return false;
        }
    },

    reorderChannels: async (userId: number, channelIds: number[]) => {
        // Локально оновлюємо порядок для миттєвого відгуку
        const currentChannels = get().channels;
        const newOrder = channelIds.map(id => currentChannels.find(ch => ch.id === id)).filter(Boolean) as ChannelCatalogItem[];
        set({ channels: newOrder });

        try {
            await apiClient.post('/catalog/reorder', { user_id: userId, channel_ids: channelIds });
            return { success: true };
        } catch (error: any) {
            console.error('Failed to reorder channels:', error);
            const message = error.response?.data?.detail || 'Помилка зміни порядку';
            // Відкочуємо назад при помилці
            await get().fetchMyChannels(userId);
            return { success: false, message };
        }
    },

    fetchAuctions: async () => {
        try {
            const response = await apiClient.get<any[]>('/catalog/auctions');
            return response.data;
        } catch (error) {
            console.error('Failed to fetch auctions:', error);
            return [];
        }
    },

    buyPremium: async (userId: number, channelId: number, category: string, days: number) => {
        try {
            const invoiceLink = await get().createInvoice(userId, 'ad_premium', {
                channel_id: channelId,
                category,
                days
            });

            if (invoiceLink) {
                return new Promise((resolve) => {
                    (window.Telegram?.WebApp as any).openInvoice(invoiceLink, (status: string) => {
                        if (status === 'paid') {
                            resolve({ success: true, message: 'Оплата успішна! Преміум активовано.' });
                        } else {
                            resolve({ success: false, message: 'Оплату скасовано' });
                        }
                    });
                });
            }
            return { success: false, message: 'Не вдалося створити інвойс' };
        } catch (error: any) {
            const message = error.response?.data?.detail || 'Помилка купівлі преміум-слоту';
            return { success: false, message };
        }
    },

    verifyPin: async (userId: number, channelId: number) => {
        try {
            const response = await apiClient.post('/catalog/partner/verify', {
                user_id: userId,
                channel_id: channelId
            });
            await get().fetchMyChannels(userId);
            return { success: true, message: response.data.message };
        } catch (error: any) {
            const message = error.response?.data?.detail || 'Помилка верифікації закрепу';
            return { success: false, message };
        }
    },

    fetchAffiliateStats: async (userId: number) => {
        try {
            const response = await apiClient.get<AffiliateStats>(`/affiliate/stats/${userId}`);
            set({ affiliateStats: response.data });
        } catch (error) {
            console.error('Failed to fetch affiliate stats:', error);
        }
    }
}));
