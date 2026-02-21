export interface Source {
    name: string;
    url?: string;
}

export interface Story {
    uid: string;
    id: number;
    type: 'story';
    title: string;
    summary: string;
    category: string;
    score: number;
    sources: Source[];
    url?: string;
    publications_count: number;
}

export interface BriefNews {
    uid: string;
    id: number;
    type: 'brief';
    title: string;
    summary: string;
    channel: string;
    category: string;
    sources: Source[];
    url?: string;
    time: string;
}

export interface CategoryData {
    items: DigestItem[];
    has_more: boolean;
    total_count: number;
}

export interface DigestItem {
    type: 'story' | 'brief';
    data: Story | BriefNews;
    time: string;
}

export interface DigestResponse {
    // Mode: category
    categories?: Record<string, CategoryData>;

    // Mode: channel
    channels?: Record<string, CategoryData>;

    // Mode: time
    items?: DigestItem[];

    has_more: boolean;

    stats: {
        total_stories?: number;
        total_briefs?: number;
        total_channels?: number;
        total?: number;
        mode: 'time' | 'category' | 'channel';
    };
}

export interface PublicationDetail {
    id: number;
    channel_title: string;
    content: string;
    url: string;
    published_at: string;
    views: number;
}

export interface StoryDetail {
    id: number;
    title: string;
    summary: string;
    category: string;
    timeline: PublicationDetail[];
}

export interface User {
    id: number;
    first_name: string;
    username?: string;
    language_code?: string;
}
