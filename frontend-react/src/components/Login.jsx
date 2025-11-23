import React, { useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { LogIn, UserPlus, Loader, AlertCircle } from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000';

const Login = ({ onLoginSuccess }) => {
    const [isLogin, setIsLogin] = useState(true);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [name, setName] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        try {
            if (isLogin) {
                // Login
                const response = await axios.post(`${API_BASE}/api/auth/login`, {
                    username,
                    password
                });

                if (response.data.success) {
                    // Store user ID in localStorage
                    localStorage.setItem('flow_user_id', response.data.user_id.toString());
                    localStorage.setItem('flow_username', username);
                    onLoginSuccess(response.data.user);
                } else {
                    setError(response.data.message || 'Login failed');
                }
            } else {
                // Register
                if (!name.trim()) {
                    setError('Name is required');
                    setLoading(false);
                    return;
                }

                const response = await axios.post(`${API_BASE}/api/auth/register`, {
                    username,
                    password,
                    name
                });

                if (response.data.success) {
                    // Store user ID in localStorage
                    localStorage.setItem('flow_user_id', response.data.user_id.toString());
                    localStorage.setItem('flow_username', username);
                    onLoginSuccess(response.data.user);
                } else {
                    setError(response.data.message || 'Registration failed');
                }
            }
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-void-black text-white flex items-center justify-center p-4">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-panel p-8 rounded-xl w-full max-w-md border border-gray-800"
            >
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-500 mb-2">
                        FLOW ENGINE
                    </h1>
                    <p className="text-gray-500 text-sm font-mono">NEURO-PRODUCTIVITY SYSTEM</p>
                </div>

                <div className="flex space-x-4 mb-6">
                    <button
                        onClick={() => {
                            setIsLogin(true);
                            setError(null);
                        }}
                        className={`flex-1 py-2 px-4 rounded-lg transition-all ${
                            isLogin
                                ? 'bg-electric text-black font-bold'
                                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                        }`}
                    >
                        <LogIn size={16} className="inline mr-2" />
                        Login
                    </button>
                    <button
                        onClick={() => {
                            setIsLogin(false);
                            setError(null);
                        }}
                        className={`flex-1 py-2 px-4 rounded-lg transition-all ${
                            !isLogin
                                ? 'bg-electric text-black font-bold'
                                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                        }`}
                    >
                        <UserPlus size={16} className="inline mr-2" />
                        Register
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {!isLogin && (
                        <div>
                            <label className="block text-sm text-gray-400 mb-2">Name</label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg focus:outline-none focus:border-electric text-white"
                                placeholder="Your name"
                                required={!isLogin}
                            />
                        </div>
                    )}

                    <div>
                        <label className="block text-sm text-gray-400 mb-2">Username</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg focus:outline-none focus:border-electric text-white"
                            placeholder="Username"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm text-gray-400 mb-2">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg focus:outline-none focus:border-electric text-white"
                            placeholder="Password"
                            required
                        />
                    </div>

                    {error && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="flex items-center space-x-2 text-red-400 text-sm bg-red-900/20 border border-red-900/50 p-3 rounded-lg"
                        >
                            <AlertCircle size={16} />
                            <span>{error}</span>
                        </motion.div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-3 bg-electric text-black font-bold rounded-lg hover:bg-electric/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                    >
                        {loading ? (
                            <>
                                <Loader className="animate-spin mr-2" size={16} />
                                {isLogin ? 'Logging in...' : 'Registering...'}
                            </>
                        ) : (
                            isLogin ? 'Login' : 'Register'
                        )}
                    </button>
                </form>
            </motion.div>
        </div>
    );
};

export default Login;

