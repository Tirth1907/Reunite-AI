/**
 * Reunite AI API Service
 * Centralized API client for communicating with the FastAPI backend
 */

const API_BASE = 'http://localhost:8000/api/v1';

// Helper function for making API requests
async function apiRequest<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const token = localStorage.getItem('reunite_token');

    const headers: Record<string, string> = {
        ...(options.headers as Record<string, string>),
    };

    // Add auth token if available
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // Add content-type for JSON requests (not for FormData)
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || `HTTP error ${response.status}`);
    }

    return response.json();
}

// ============ Auth API ============

export interface LoginResponse {
    access_token: string;
    token_type: string;
    user: {
        id: string;
        name: string;
        email: string;
        phone: string;
        role: string;
        area?: string;
        city?: string;
    };
}

export async function login(username: string, password: string): Promise<LoginResponse> {
    return apiRequest<LoginResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
    });
}

export async function signup(userData: {
    name: string;
    email: string;
    phone: string;
    password: string;
    role?: string;
}): Promise<LoginResponse> {
    return apiRequest<LoginResponse>('/auth/signup', {
        method: 'POST',
        body: JSON.stringify(userData),
    });
}

// ============ Statistics API ============

export interface Statistics {
    totalRegistered: number;
    foundCases: number;
    activeCases: number;
    aiMatches: number;
}

export async function getStatistics(): Promise<Statistics> {
    return apiRequest<Statistics>('/statistics');
}

// ============ Cases API ============

export interface Case {
    id: string;
    name: string;
    age: string;
    status: string;
    last_seen: string;
    birth_marks?: string;
    matched_with?: string;
    complainant_mobile?: string;
    submitted_on?: string;
    photo_url?: string;
    father_name?: string;
    address?: string;
    complainant_name?: string;
    submitted_by?: string;
}

export async function getCases(options?: {
    status?: string;
    submitted_by?: string;
    limit?: number;
}): Promise<Case[]> {
    const params = new URLSearchParams();
    if (options?.status) params.append('status', options.status);
    if (options?.submitted_by) params.append('submitted_by', options.submitted_by);
    if (options?.limit) params.append('limit', options.limit.toString());

    const query = params.toString() ? `?${params.toString()}` : '';
    console.log('[API] Fetching cases from:', `/cases${query}`);
    const result = await apiRequest<Case[]>(`/cases${query}`);
    console.log('[API] Cases received:', result.length, 'cases');
    return result;
}

export async function getCase(caseId: string): Promise<Case> {
    return apiRequest<Case>(`/cases/${caseId}`);
}

export async function registerCase(formData: FormData): Promise<Case> {
    const token = localStorage.getItem('reunite_token');

    const headers: Record<string, string> = {};
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}/cases`, {
        method: 'POST',
        headers,
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to register case' }));
        throw new Error(error.detail || `HTTP error ${response.status}`);
    }

    return response.json();
}

export async function deleteCase(caseId: string): Promise<{ status: string; id: string }> {
    return apiRequest(`/cases/${caseId}`, { method: 'DELETE' });
}

// ============ Public Submissions API ============

export interface PublicSubmission {
    id: string;
    status: string;
    location?: string;
    mobile?: string;
    birth_marks?: string;
    submitted_on?: string;
    submitted_by?: string;
    photo_url?: string;
}

export async function getPublicSubmissions(status?: string): Promise<PublicSubmission[]> {
    const query = status ? `?status=${status}` : '';
    return apiRequest<PublicSubmission[]>(`/public${query}`);
}

export async function getPublicSubmission(id: string): Promise<PublicSubmission> {
    return apiRequest<PublicSubmission>(`/public/${id}`);
}

export async function deletePublicSubmission(id: string): Promise<{ status: string; id: string }> {
    return apiRequest(`/public/${id}`, { method: 'DELETE' });
}

export async function submitSighting(formData: FormData): Promise<PublicSubmission> {
    const response = await fetch(`${API_BASE}/public`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to submit sighting' }));
        throw new Error(error.detail || `HTTP error ${response.status}`);
    }

    return response.json();
}

// ============ Matching API ============

export interface MatchResult {
    status: boolean;
    message?: string;
    result?: Record<string, Array<{
        public_id: string;
        distance: number;
        confidence: number;
    }>>;
}

export async function runMatching(tolerance: number = 0.6): Promise<MatchResult> {
    return apiRequest<MatchResult>(`/matching/run?tolerance=${tolerance}`, {
        method: 'POST',
    });
}

export async function confirmMatch(
    registeredCaseId: string,
    publicCaseId: string
): Promise<{ status: string }> {
    return apiRequest('/matching/confirm', {
        method: 'POST',
        body: JSON.stringify({
            registered_case_id: registeredCaseId,
            public_case_id: publicCaseId,
        }),
    });
}

export async function getRecentMatches(): Promise<Case[]> {
    return apiRequest<Case[]>('/matches');
}

// ============ Default Export ============

const api = {
    // Auth
    login,
    signup,

    // Statistics
    getStatistics,

    // Cases
    getCases,
    getCase,
    registerCase,
    deleteCase,

    // Public
    getPublicSubmissions,
    submitSighting,
    deletePublicSubmission,

    // Matching
    runMatching,
    confirmMatch,
    getRecentMatches,
};

export default api;
