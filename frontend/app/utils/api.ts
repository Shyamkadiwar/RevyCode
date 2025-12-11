// API utility functions

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchUser(token: string) {
    const response = await fetch(`${API_URL}/api/auth/me`, {
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });

    if (!response.ok) {
        throw new Error('Failed to fetch user');
    }

    return response.json();
}

export function getGithubLoginUrl() {
    return `${API_URL}/api/auth/login`;
}
