import { create } from 'zustand';
import type { DigestResponse, StoryDetail } from '../types';
import { apiClient } from '../api/client';

interface DigestState {
    digest: DigestResponse | null;
    isLoading: boolean;
    isRefreshing: boolean; // For "load more" state
    error: string | null;

    fetchDigest: (userId: number, groupBy?: string, pinned?: string, offset?: number) => Promise<void>;
}

export const useDigestStore = create<DigestState>((set) => ({
    digest: null,
    isLoading: false,
    isRefreshing: false,
    error: null,

    fetchDigest: async (userId: number, groupBy: string = 'category', pinned?: string, offset: number = 0) => {
        const isLoadMore = offset > 0;
        if (isLoadMore) {
            set({ isRefreshing: true });
        } else {
            set({ isLoading: true, error: null });
        }

        try {
            const params = new URLSearchParams();
            params.append('group_by', groupBy);
            params.append('offset', offset.toString());
            params.append('limit', '20'); // Пакет по 20 елементів
            if (pinned) params.append('pinned', pinned);

            const response = await apiClient.get<DigestResponse>(`/digest/${userId}?${params.toString()}`);

            set((state) => {
                if (!isLoadMore || !state.digest) {
                    return { digest: response.data, isLoading: false, isRefreshing: false };
                }

                // Логіка об'єднання даних при "дозавантаженні"
                const prevDigest = state.digest;
                const nextDigest = response.data;

                const merged: DigestResponse = { ...nextDigest };

                if (groupBy === 'category' && prevDigest.categories && nextDigest.categories) {
                    // Об'єднуємо категорії
                    merged.categories = { ...prevDigest.categories };
                    Object.entries(nextDigest.categories).forEach(([name, data]) => {
                        if (merged.categories![name]) {
                            // Якщо категорія вже є — об'єднуємо її елементи (на всяк випадок)
                            merged.categories![name].items = [
                                ...merged.categories![name].items,
                                ...data.items.filter(newItem =>
                                    !merged.categories![name].items.some(oldItem => oldItem.data.uid === newItem.data.uid)
                                )
                            ];
                        } else {
                            merged.categories![name] = data;
                        }
                    });
                } else if (groupBy === 'channel' && prevDigest.channels && nextDigest.channels) {
                    merged.channels = { ...prevDigest.channels };
                    Object.entries(nextDigest.channels).forEach(([name, data]) => {
                        if (merged.channels![name]) {
                            merged.channels![name].items = [...merged.channels![name].items, ...data.items];
                        } else {
                            merged.channels![name] = data;
                        }
                    });
                } else if (groupBy === 'time' && prevDigest.items && nextDigest.items) {
                    // Об'єднуємо загальний список
                    merged.items = [
                        ...prevDigest.items,
                        ...nextDigest.items.filter(newItem =>
                            !prevDigest.items!.some(oldItem => oldItem.data.uid === newItem.data.uid)
                        )
                    ];
                }

                return { digest: merged, isLoading: false, isRefreshing: false };
            });
        } catch (error: any) {
            console.error('Failed to fetch digest:', error);
            const msg = error.response?.data?.detail || error.message || 'Unknown error';
            set({ error: 'Failed to load digest: ' + msg, isLoading: false, isRefreshing: false });
        }
    },
}));

interface StoryState {
    currentStory: StoryDetail | null;
    isLoading: boolean;
    error: string | null;

    fetchStory: (storyId: number) => Promise<void>;
}

export const useStoryStore = create<StoryState>((set) => ({
    currentStory: null,
    isLoading: false,
    error: null,

    fetchStory: async (storyId: number) => {
        set({ isLoading: true, error: null, currentStory: null });
        try {
            const response = await apiClient.get<StoryDetail>(`/story/${storyId}`);
            set({ currentStory: response.data, isLoading: false });
        } catch (error) {
            console.error('Failed to fetch story:', error);
            set({ error: 'Failed to load story', isLoading: false });
        }
    },
}));
