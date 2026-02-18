import { create } from 'zustand';
import type { DigestResponse, StoryDetail } from '../types';
import { apiClient } from '../api/client';

interface DigestState {
    digest: DigestResponse | null;
    isLoading: boolean;
    error: string | null;

    fetchDigest: (userId: number, groupBy?: string, pinned?: string) => Promise<void>;
}

export const useDigestStore = create<DigestState>((set) => ({
    digest: null,
    isLoading: false,
    error: null,

    fetchDigest: async (userId: number, groupBy: string = 'category', pinned?: string) => {
        set({ isLoading: true, error: null });
        try {
            const params = new URLSearchParams();
            params.append('group_by', groupBy);
            if (pinned) params.append('pinned', pinned);

            const response = await apiClient.get<DigestResponse>(`/digest/${userId}?${params.toString()}`);
            set({ digest: response.data, isLoading: false });
        } catch (error) {
            console.error('Failed to fetch digest:', error);
            set({ error: 'Failed to load digest', isLoading: false });
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
