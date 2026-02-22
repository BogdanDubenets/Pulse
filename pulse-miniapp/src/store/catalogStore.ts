import { create } from 'zustand';
import type { CatalogCategory, ChannelCatalogItem } from '../types';
import { apiClient } from '../api/client';

interface CatalogState {
    categories: CatalogCategory[];
    channels: ChannelCatalogItem[];
    isLoading: boolean;
    error: string | null;

    fetchCategories: () => Promise<void>;
    fetchChannels: (category?: string) => Promise<void>;
    placeBid: (userId: number, channelId: number, category: string, amount: number) => Promise<boolean>;
}

export const useCatalogStore = create<CatalogState>((set) => ({
    categories: [],
    channels: [],
    isLoading: false,
    error: null,

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
