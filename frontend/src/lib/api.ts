/**
 * LegalLens API Client
 * Handles all communication with the FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export interface ChatRequest {
    message: string;
    act_filter?: string;
    top_k?: number;
}

export interface Citation {
    index: number;
    act_name: string;
    section_number: string;
    title: string | null;
    content_snippet: string;
}

export interface ChatResponse {
    answer: string;
    citations: Citation[];
    query_intent: string;
    is_relevant: boolean;
}

export interface HealthResponse {
    status: string;
    database: string;
    embedding_model: string;
}

class ApiClient {
    private baseUrl: string;

    constructor(baseUrl: string = API_BASE_URL) {
        this.baseUrl = baseUrl;
    }

    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;

        const response = await fetch(url, {
            headers: {
                "Content-Type": "application/json",
                ...options.headers,
            },
            ...options,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `API Error: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Health check endpoint
     */
    async getHealth(): Promise<HealthResponse> {
        return this.request<HealthResponse>("/health");
    }

    /**
     * Send chat message and get RAG response
     */
    async chat(request: ChatRequest): Promise<ChatResponse> {
        return this.request<ChatResponse>("/api/chat/", {
            method: "POST",
            body: JSON.stringify(request),
        });
    }

    /**
     * Check if API is available
     */
    async isAvailable(): Promise<boolean> {
        try {
            await this.getHealth();
            return true;
        } catch {
            return false;
        }
    }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export class for custom instances
export default ApiClient;
