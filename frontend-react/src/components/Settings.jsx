import React, { useState } from 'react';
import { X, Settings as SettingsIcon, Bell, Shield, Zap, Clock } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';

const Settings = ({ isOpen, onClose }) => {
    const [activeTab, setActiveTab] = useState('general');
    
    if (!isOpen) return null;
    
    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
                onClick={onClose}
            >
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.9, opacity: 0 }}
                    onClick={(e) => e.stopPropagation()}
                    className="glass-panel w-full max-w-4xl h-[80vh] rounded-xl border border-gray-700 overflow-hidden flex flex-col"
                >
                    {/* Header */}
                    <div className="flex items-center justify-between p-6 border-b border-gray-800">
                        <div className="flex items-center space-x-3">
                            <SettingsIcon className="text-electric" size={24} />
                            <h2 className="text-2xl font-bold text-white">Settings</h2>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                        >
                            <X size={20} className="text-gray-400" />
                        </button>
                    </div>
                    
                    {/* Content */}
                    <div className="flex flex-1 overflow-hidden">
                        {/* Sidebar */}
                        <div className="w-64 border-r border-gray-800 p-4 space-y-2">
                            <button
                                onClick={() => setActiveTab('general')}
                                className={clsx(
                                    "w-full text-left px-4 py-3 rounded-lg transition-all flex items-center space-x-3",
                                    activeTab === 'general' 
                                        ? "bg-electric/20 text-electric border border-electric/50" 
                                        : "text-gray-400 hover:bg-gray-800/50"
                                )}
                            >
                                <SettingsIcon size={18} />
                                <span>General</span>
                            </button>
                            <button
                                onClick={() => setActiveTab('notifications')}
                                className={clsx(
                                    "w-full text-left px-4 py-3 rounded-lg transition-all flex items-center space-x-3",
                                    activeTab === 'notifications' 
                                        ? "bg-electric/20 text-electric border border-electric/50" 
                                        : "text-gray-400 hover:bg-gray-800/50"
                                )}
                            >
                                <Bell size={18} />
                                <span>Notifications</span>
                            </button>
                            <button
                                onClick={() => setActiveTab('flow')}
                                className={clsx(
                                    "w-full text-left px-4 py-3 rounded-lg transition-all flex items-center space-x-3",
                                    activeTab === 'flow' 
                                        ? "bg-electric/20 text-electric border border-electric/50" 
                                        : "text-gray-400 hover:bg-gray-800/50"
                                )}
                            >
                                <Zap size={18} />
                                <span>Flow Settings</span>
                            </button>
                            <button
                                onClick={() => setActiveTab('privacy')}
                                className={clsx(
                                    "w-full text-left px-4 py-3 rounded-lg transition-all flex items-center space-x-3",
                                    activeTab === 'privacy' 
                                        ? "bg-electric/20 text-electric border border-electric/50" 
                                        : "text-gray-400 hover:bg-gray-800/50"
                                )}
                            >
                                <Shield size={18} />
                                <span>Privacy</span>
                            </button>
                        </div>
                        
                        {/* Main Content */}
                        <div className="flex-1 overflow-y-auto p-6">
                            {activeTab === 'general' && (
                                <div className="space-y-6">
                                    <div>
                                        <h3 className="text-lg font-bold mb-4">General Settings</h3>
                                        <div className="space-y-4">
                                            <div>
                                                <label className="block text-sm text-gray-400 mb-2">User Name</label>
                                                <input
                                                    type="text"
                                                    defaultValue="Victus"
                                                    className="w-full px-4 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-electric"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm text-gray-400 mb-2">Theme</label>
                                                <select className="w-full px-4 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-electric">
                                                    <option>Dark (Default)</option>
                                                    <option>Cyberpunk</option>
                                                    <option>Minimal</option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                            
                            {activeTab === 'notifications' && (
                                <div className="space-y-6">
                                    <div>
                                        <h3 className="text-lg font-bold mb-4">Notification Settings</h3>
                                        <div className="space-y-4">
                                            <label className="flex items-center justify-between p-4 bg-gray-900/30 rounded-lg cursor-pointer hover:bg-gray-900/50 transition-colors">
                                                <span className="text-sm">Flow State Alerts</span>
                                                <input type="checkbox" defaultChecked className="w-5 h-5 accent-electric" />
                                            </label>
                                            <label className="flex items-center justify-between p-4 bg-gray-900/30 rounded-lg cursor-pointer hover:bg-gray-900/50 transition-colors">
                                                <span className="text-sm">Distraction Warnings</span>
                                                <input type="checkbox" defaultChecked className="w-5 h-5 accent-electric" />
                                            </label>
                                            <label className="flex items-center justify-between p-4 bg-gray-900/30 rounded-lg cursor-pointer hover:bg-gray-900/50 transition-colors">
                                                <span className="text-sm">Session Complete Notifications</span>
                                                <input type="checkbox" defaultChecked className="w-5 h-5 accent-electric" />
                                            </label>
                                        </div>
                                    </div>
                                </div>
                            )}
                            
                            {activeTab === 'flow' && (
                                <div className="space-y-6">
                                    <div>
                                        <h3 className="text-lg font-bold mb-4">Flow Detection Settings</h3>
                                        <div className="space-y-4">
                                            <div>
                                                <label className="block text-sm text-gray-400 mb-2">Flow Threshold (minutes)</label>
                                                <input
                                                    type="number"
                                                    defaultValue={10}
                                                    min={3}
                                                    max={60}
                                                    className="w-full px-4 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-electric"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm text-gray-400 mb-2">Auto-start Flow</label>
                                                <select className="w-full px-4 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-electric">
                                                    <option>Enabled (Recommended)</option>
                                                    <option>Disabled</option>
                                                </select>
                                            </div>
                                            <div>
                                                <label className="block text-sm text-gray-400 mb-2">Fatigue Threshold</label>
                                                <input
                                                    type="number"
                                                    defaultValue={70}
                                                    min={50}
                                                    max={100}
                                                    className="w-full px-4 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-electric"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                            
                            {activeTab === 'privacy' && (
                                <div className="space-y-6">
                                    <div>
                                        <h3 className="text-lg font-bold mb-4">Privacy & Data</h3>
                                        <div className="space-y-4">
                                            <div className="p-4 bg-gray-900/30 rounded-lg">
                                                <p className="text-sm text-gray-400 mb-2">
                                                    All data is stored locally on your device. No data is sent to external servers except for AI analysis (optional).
                                                </p>
                                            </div>
                                            <label className="flex items-center justify-between p-4 bg-gray-900/30 rounded-lg cursor-pointer hover:bg-gray-900/50 transition-colors">
                                                <span className="text-sm">Enable AI Analysis</span>
                                                <input type="checkbox" defaultChecked className="w-5 h-5 accent-electric" />
                                            </label>
                                            <button className="w-full px-4 py-2 bg-red-900/20 hover:bg-red-900/30 border border-red-900/50 rounded-lg text-red-400 transition-colors">
                                                Clear All Data
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
};

export default Settings;

