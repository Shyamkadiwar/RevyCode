'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';

interface User {
    id: string;
    github_username: string;
    email: string;
    name?: string;
    avatar_url?: string;
}

export default function DashboardPage() {
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    useEffect(() => {
        const loadUser = async () => {
            // Get token from localStorage
            const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;

            if (!token) {
                router.push('/signin');
                return;
            }

            try {
                const response = await axios.get(`${API_URL}/api/auth/me`, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                    },
                });
                setUser(response.data);
            } catch (err) {
                setError('Failed to load user data');
                console.error('Error fetching user:', err);
            } finally {
                setLoading(false);
            }
        };

        loadUser();
    }, [router, API_URL]);

    const handleLogout = () => {
        // Remove token from localStorage
        if (typeof window !== 'undefined') {
            localStorage.removeItem('auth_token');
        }
        router.push('/signin');
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading...</p>
                </div>
            </div>
        );
    }

    if (error || !user) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="text-center">
                    <p className="text-red-600">{error || 'User not found'}</p>
                    <button
                        onClick={() => router.push('/signin')}
                        className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                    >
                        Back to Sign In
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <nav className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        <h1 className="text-xl font-semibold text-gray-900">RevyCode Dashboard</h1>
                        <button
                            onClick={handleLogout}
                            className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 border border-gray-300 rounded-md hover:bg-gray-50"
                        >
                            Logout
                        </button>
                    </div>
                </div>
            </nav>

            <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                <div className="px-4 py-6 sm:px-0">
                    <div className="bg-white shadow rounded-lg p-6">
                        <div className="flex items-center space-x-4 mb-6">
                            {user.avatar_url && (
                                <img
                                    src={user.avatar_url}
                                    alt={user.github_username}
                                    className="h-16 w-16 rounded-full"
                                />
                            )}
                            <div>
                                <h2 className="text-2xl font-bold text-gray-900">
                                    {user.name || user.github_username}
                                </h2>
                                <p className="text-sm text-gray-500">@{user.github_username}</p>
                            </div>
                        </div>

                        <div className="border-t border-gray-200 pt-6">
                            <h3 className="text-lg font-medium text-gray-900 mb-4">User Information</h3>
                            <dl className="grid grid-cols-1 gap-4">
                                <div>
                                    <dt className="text-sm font-medium text-gray-500">Username</dt>
                                    <dd className="mt-1 text-sm text-gray-900">{user.github_username}</dd>
                                </div>
                                <div>
                                    <dt className="text-sm font-medium text-gray-500">Email</dt>
                                    <dd className="mt-1 text-sm text-gray-900">{user.email || 'Not available'}</dd>
                                </div>
                                {user.name && (
                                    <div>
                                        <dt className="text-sm font-medium text-gray-500">Full Name</dt>
                                        <dd className="mt-1 text-sm text-gray-900">{user.name}</dd>
                                    </div>
                                )}
                            </dl>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
