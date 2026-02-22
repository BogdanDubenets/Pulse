import { create } from 'zustand';
import type { CatalogCategory, ChannelCatalogItem } from '../types';
import { apiClient } from '../api/client';

export interface UserStatus {
    tier: string;
    sub_count: number;
    limit: number;
    can_add: boolean;
}

interface CatalogState {
    categories: CatalogCategory[];
    channels: ChannelCatalogItem[];
    userStatus: UserStatus | null;
    isLoading: boolean;
    error: string | null;

    fetchCategories: () => Promise<void>;
    fetchChannels: (category?: string) => Promise<void>;
    fetchMyChannels: (userId: number) => Promise<void>;
    fetchUserStatus: (userId: number) => Promise<void>;
    addCustomChannel: (userId: number, url: string) => Promise<{ success: boolean; message: string }>;
    placeBid: (userId: number, channelId: number, category: string, amount: number) => Promise<boolean>;
}

export const useCatalogStore = create<CatalogState>((set, get) => ({
    categories: [],
    channels: [],
    userStatus: null,
    isLoading: false,
    error: null,

    fetchUserStatus: async (userId: number) => {
        try {
            const response = await apiClient.get<UserStatus>(`/catalog/user/status/${userId}`);
            set({ userStatus: response.data });
        } catch (error) {
            console.error('Failed to fetch user status:', error);
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
        set({ isLoading: true, error: null });
        try {
            const url = category ? `/catalog/channels?category=${encodeURIComponent(category)}` : '/catalog/channels';
            const response = await apiClient.get<ChannelCatalogItem[]>(url);
            set({ channels: response.data, isLoading: false });
        } catch (error: any) {
            console.error('Failed to fetch channels:', error);
            set({ error: 'Помилка завантаження каналів', isLoading: false });
        }
    },

    fetchMyChannels: async (userId: number) => {
        set({ isLoading: true, error: null });
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
            await apiClient.post('/catalog/auction/bid', {
                user_id: userId,
                channel_id: channelId,
                category,
                amount
            });
            return true;
        } catch (error: any) {
            console.error('Failed to place bid:', error);
            return false;
        }
    }
}));
