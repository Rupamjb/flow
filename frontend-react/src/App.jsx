import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer,
    AreaChart, Area, XAxis, YAxis, Tooltip
} from 'recharts';
import {
    Battery, Zap, Shield, Activity, Play, Square,
    AlertTriangle, CheckCircle, Clock, Terminal, Settings
} from 'lucide-react';
import clsx from 'clsx';
import SettingsComponent from './components/Settings';
import DataVisualizer from './components/DataVisualizer';
import AIInsights from './components/AIInsights';
import Onboarding from './components/Onboarding';
import Login from './components/Login';

// ============================================================================
// COMPONENTS
// ============================================================================

const FlowBattery = ({ energy, isCharging }) => {
    // Calculate liquid fill height
    const fillHeight = `${energy}%`;

    return (
        <div className="relative w-64 h-64 mx-auto">
            {/* Outer Ring */}
            <div className="absolute inset-0 rounded-full border-4 border-gray-800 shadow-[0_0_20px_rgba(0,0,0,0.5)]"></div>

            {/* Inner Container */}
            <div className="absolute inset-2 rounded-full overflow-hidden bg-black/50 backdrop-blur-sm border border-gray-700">

                {/* Liquid Fill */}
                <motion.div
                    className={clsx(
                        "absolute bottom-0 left-0 right-0 transition-all duration-1000",
                        isCharging ? "bg-electric/80" : "bg-amber/80"
                    )}
                    style={{ height: fillHeight }}
                    animate={{
                        height: fillHeight,
                        filter: isCharging ? "hue-rotate(0deg)" : "hue-rotate(45deg)"
                    }}
                >
                    {/* Bubbles/Wave effect could go here */}
                    <div className="absolute top-0 left-0 right-0 h-2 bg-white/20"></div>
                </motion.div>

                {/* Center Text */}
                <div className="absolute inset-0 flex flex-col items-center justify-center z-10">
                    <span className="text-xs uppercase tracking-widest text-gray-400 mb-1">Cognitive Energy</span>
                    <span className={clsx(
                        "text-4xl font-bold font-mono",
                        isCharging ? "text-white text-neon-blue" : "text-amber text-neon-amber"
                    )}>
                        {Math.round(energy)}%
                    </span>
                    {isCharging && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="flex items-center mt-2 text-electric text-xs"
                        >
                            <Zap size={12} className="mr-1 fill-current" /> RECHARGING
                        </motion.div>
                    )}
                </div>
            </div>
        </div>
    );
};

const HexagonStats = ({ stats }) => {
    const data = [
        { subject: 'Stamina', A: stats.stamina, fullMark: 100 },
        { subject: 'Resilience', A: stats.resilience, fullMark: 100 },
        { subject: 'Consistency', A: stats.consistency, fullMark: 100 },
        { subject: 'Focus', A: stats.focus, fullMark: 100 },
        { subject: 'Flow', A: stats.flow, fullMark: 100 },
        { subject: 'Willpower', A: stats.willpower, fullMark: 100 },
    ];

    return (
        <div className="h-64 w-full relative">
            <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
                    <PolarGrid stroke="#333" />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#888', fontSize: 10 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                    <Radar
                        name="Stats"
                        dataKey="A"
                        stroke="#219ebc"
                        strokeWidth={2}
                        fill="#219ebc"
                        fillOpacity={0.3}
                    />
                </RadarChart>
            </ResponsiveContainer>

            {/* Decorative corners */}
            <div className="absolute top-0 left-0 w-4 h-4 border-t border-l border-electric/50"></div>
            <div className="absolute top-0 right-0 w-4 h-4 border-t border-r border-electric/50"></div>
            <div className="absolute bottom-0 left-0 w-4 h-4 border-b border-l border-electric/50"></div>
            <div className="absolute bottom-0 right-0 w-4 h-4 border-b border-r border-electric/50"></div>
        </div>
    );
};

const TimetableStatus = () => {
    const now = new Date();
    const hours = now.getHours();
    // Mock schedule check (9-17)
    const isWorkTime = hours >= 9 && hours < 17;

    return (
        <div className="glass-panel p-4 rounded-xl flex items-center justify-between">
            <div className="flex items-center">
                <Clock size={20} className={clsx("mr-3", isWorkTime ? "text-electric" : "text-gray-500")} />
                <div>
                    <div className="text-xs uppercase tracking-widest text-gray-500">Current Mode</div>
                    <div className={clsx("font-bold", isWorkTime ? "text-white" : "text-gray-400")}>
                        {isWorkTime ? "DEEP WORK PROTOCOL" : "REST & RECOVERY"}
                    </div>
                </div>
            </div>
            <div className="text-right">
                <div className="text-xs text-gray-500">SCHEDULE</div>
                <div className="font-mono text-electric">09:00 - 17:00</div>
            </div>
        </div>
    );
};

const QuestLog = ({ missionLog, sessions }) => {
    // Show AI-generated mission log goals if available, or use mock data
    const goals = missionLog?.goals && missionLog.goals.length > 0 ? missionLog.goals : [
        "Complete 3 deep work sessions this week",
        "Reduce average distractions to under 2 per session",
        "Maintain focus score above 75%"
    ];
    const focusAreas = missionLog?.focus_areas && missionLog.focus_areas.length > 0 ? missionLog.focus_areas : [
        "Deep Work",
        "Coding",
        "Learning"
    ];

    return (
        <div className="space-y-4">
            <h3 className="text-sm uppercase tracking-widest text-gray-500 flex items-center">
                <Terminal size={14} className="mr-2" /> Mission Log
            </h3>

            {/* AI-Generated Goals */}
            {goals.length > 0 && (
                <div className="space-y-2 mb-4">
                    <div className="text-xs text-gray-400 uppercase mb-2">AI Goals</div>
                    {goals.map((goal, idx) => (
                        <div
                            key={`goal-${idx}`}
                            className="p-3 rounded border border-l-4 bg-gray-900/50 border-gray-800 border-l-electric"
                        >
                            <div className="text-sm text-white">{goal}</div>
                        </div>
                    ))}
                </div>
            )}

            {/* Focus Areas */}
            {focusAreas.length > 0 && (
                <div className="space-y-2 mb-4">
                    <div className="text-xs text-gray-400 uppercase mb-2">Focus Areas</div>
                    <div className="flex flex-wrap gap-2">
                        {focusAreas.map((area, idx) => (
                            <span
                                key={`area-${idx}`}
                                className="px-2 py-1 text-xs bg-electric/20 text-electric rounded border border-electric/30"
                            >
                                {area}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* Session History */}
            {sessions.length > 0 && (
                <div className="space-y-2">
                    <div className="text-xs text-gray-400 uppercase mb-2">Recent Sessions</div>
                    {sessions.map((session, idx) => (
                        <div
                            key={idx}
                            className={clsx(
                                "p-3 rounded border border-l-4 transition-all hover:translate-x-1",
                                session.completed
                                    ? "bg-gray-900/50 border-gray-800 border-l-electric"
                                    : "bg-red-900/10 border-red-900/30 border-l-breach"
                            )}
                        >
                            <div className="flex justify-between items-start">
                                <div>
                                    <div className={clsx(
                                        "text-sm font-bold",
                                        session.completed ? "text-white" : "text-gray-400 line-through"
                                    )}>
                                        {session.title}
                                    </div>
                                    <div className="text-xs text-gray-500 mt-1 font-mono">
                                        {session.time} • {session.xp} XP
                                    </div>
                                </div>
                                {session.completed ? (
                                    <CheckCircle size={16} className="text-electric" />
                                ) : (
                                    <AlertTriangle size={16} className="text-breach" />
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}


        </div>
    );
};

// ============================================================================
// MAIN APP
// ============================================================================

function App() {
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [sessions, setSessions] = useState([]);
    const [settingsOpen, setSettingsOpen] = useState(false);
    const [showOnboarding, setShowOnboarding] = useState(false);
    const [userStatus, setUserStatus] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [userProfile, setUserProfile] = useState(null);
    const [missionLog, setMissionLog] = useState(null);
    const [checkingAuth, setCheckingAuth] = useState(true);

    const fetchUserStatus = async (forceShow = false) => {
        try {
            const res = await axios.get('http://127.0.0.1:8000/api/user/status');
            setUserStatus(res.data);
            // Only update showOnboarding if forceShow is true (initial load)
            // Otherwise, respect the current state (don't override if user just completed onboarding)
            if (forceShow) {
                if (res.data.is_new || !res.data.onboarding_complete) {
                    setShowOnboarding(true);
                } else {
                    setShowOnboarding(false);
                }
            }
            // If not forceShow, we trust the current state and just update userStatus
        } catch (err) {
            console.error("Failed to fetch user status:", err);
            // Only default to showing onboarding on initial load
            if (forceShow) {
                setShowOnboarding(true);
            }
        }
    };

    const restoreSession = async () => {
        const userId = localStorage.getItem('flow_user_id');
        if (!userId) {
            setCheckingAuth(false);
            return;
        }

        try {
            const res = await axios.post(`http://127.0.0.1:8000/api/auth/restore?user_id=${userId}`);
            if (res.data.success) {
                setIsAuthenticated(true);
                // Fetch user profile and status
                await Promise.all([
                    fetchUserProfile(),
                    fetchUserStatus(true),
                    fetchMissionLog()
                ]);
            }
        } catch (err) {
            console.error("Failed to restore session:", err);
            localStorage.removeItem('flow_user_id');
            localStorage.removeItem('flow_username');
        } finally {
            setCheckingAuth(false);
        }
    };

    const fetchUserProfile = async () => {
        try {
            const res = await axios.get('http://127.0.0.1:8000/api/user/profile');
            setUserProfile(res.data);
        } catch (err) {
            console.error("Failed to fetch user profile:", err);
        }
    };

    const fetchMissionLog = async () => {
        try {
            const res = await axios.get('http://127.0.0.1:8000/api/user/mission-log');
            setMissionLog(res.data);
        } catch (err) {
            console.error("Failed to fetch mission log:", err);
            setMissionLog({ goals: [], focus_areas: [] });
        }
    };

    const fetchStatus = async () => {
        try {
            const res = await axios.get('http://127.0.0.1:8000/api/status');
            setStatus(res.data);
            setError(null);
        } catch (err) {
            console.error("Backend offline");
            setError("Backend disconnected");
            // Don't set mock data, just show error
        } finally {
            setLoading(false);
        }
    };

    const fetchSessions = async () => {
        try {
            const res = await axios.get('http://127.0.0.1:8000/api/sessions/recent?limit=5');
            setSessions(res.data || []);
        } catch (e) {
            // ignore silently when backend is offline
        }
    };

    useEffect(() => {
        // Check authentication first
        restoreSession();
    }, []);

    useEffect(() => {
        if (isAuthenticated) {
            fetchStatus();
            const interval = setInterval(fetchStatus, 1000);
            return () => clearInterval(interval);
        }
    }, [isAuthenticated]);

    useEffect(() => {
        fetchSessions();
        const interval = setInterval(fetchSessions, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleStartSession = async () => {
        try {
            await axios.post('http://127.0.0.1:8000/api/start');
            fetchStatus();
        } catch (err) {
            console.error("Failed to start session");
        }
    };

    const handleStopSession = async () => {
        try {
            await axios.post('http://127.0.0.1:8000/api/stop');
            fetchStatus();
        } catch (err) {
            console.error("Failed to stop session");
        }
    };

    const handleLoginSuccess = async (user) => {
        setIsAuthenticated(true);
        await Promise.all([
            fetchUserProfile(),
            fetchUserStatus(true),
            fetchMissionLog()
        ]);
    };

    if (checkingAuth) {
        return <div className="flex h-screen items-center justify-center bg-void text-electric">INITIALIZING...</div>;
    }

    // Show login if not authenticated
    if (!isAuthenticated) {
        return <Login onLoginSuccess={handleLoginSuccess} />;
    }

    if (loading) return <div className="flex h-screen items-center justify-center bg-void text-electric">LOADING...</div>;

    // Show onboarding if needed
    if (showOnboarding) {
        return (
            <Onboarding
                onComplete={async () => {
                    // Hide onboarding immediately
                    setShowOnboarding(false);
                    // Refresh mission log and user status
                    await Promise.all([
                        fetchMissionLog(),
                        fetchUserStatus(false),
                        fetchUserProfile()
                    ]);
                }}
            />
        );
    }

    const isRunning = status?.is_running || false;

    return (
        <div className="min-h-screen bg-void text-white p-8 font-sans selection:bg-electric selection:text-black overflow-x-hidden">

            {/* Header */}
            <header className="flex justify-between items-center mb-12 border-b border-gray-800 pb-6">
                <div>
                    <h1 className="text-3xl font-bold tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-500">
                        FLOW ENGINE <span className="text-electric text-xs align-top">v1.0</span>
                    </h1>
                    <p className="text-gray-500 text-sm font-mono mt-1">NEURO-PRODUCTIVITY SYSTEM</p>
                </div>

                <div className="flex items-center space-x-6">
                    <div className="text-right">
                        <div className="text-xs text-gray-500 uppercase">Level {userProfile?.level || 1}</div>
                        <div className="text-xl font-mono font-bold text-amber">{userProfile?.total_xp || 0} XP</div>
                    </div>
                    <button
                        onClick={() => setSettingsOpen(true)}
                        className="h-10 w-10 rounded bg-gray-800 border border-gray-700 flex items-center justify-center hover:bg-gray-700 hover:border-electric transition-colors"
                        title="Settings"
                    >
                        <Settings size={18} className="text-gray-400 hover:text-electric transition-colors" />
                    </button>
                    <div className="h-10 w-10 rounded bg-gray-800 border border-gray-700 flex items-center justify-center">
                        <span className="font-bold text-electric">V</span>
                    </div>
                </div>
            </header>

            {/* Main Grid */}
            <div className="grid grid-cols-12 gap-6">

                {/* Left Column: Quest Log */}
                <div className="col-span-3 space-y-6 overflow-y-auto max-h-[calc(100vh-200px)] pr-2">
                    <TimetableStatus />

                    <div className="glass-panel p-6 rounded-xl">
                        <QuestLog sessions={sessions.length > 0 ? sessions.map(s => ({
                            title: `Session ${s.id || 'N/A'}`,
                            time: s.start_time ? new Date(s.start_time).toLocaleTimeString() : 'N/A',
                            xp: s.xp_total || 0,
                            completed: s.end_time != null
                        })) : [
                            { title: "No sessions yet", time: "Start your first flow session", xp: 0, completed: false },
                        ]} />
                    </div>

                    <div className="glass-panel p-6 rounded-xl">
                        <h3 className="text-sm uppercase tracking-widest text-gray-500 mb-4">System Status</h3>
                        <div className="space-y-2 text-xs font-mono text-gray-400">
                            <div className="flex justify-between items-center">
                                <span>BACKEND</span>
                                <div className="flex items-center space-x-2">
                                    <span className={clsx(
                                        "h-2 w-2 rounded-full",
                                        error ? "bg-breach" : "bg-electric animate-pulse"
                                    )}></span>
                                    <span className={error ? "text-breach" : "text-electric"}>{error ? "OFFLINE" : "CONNECTED"}</span>
                                </div>
                            </div>
                            <div className="flex justify-between items-center">
                                <span>EXTENSION</span>
                                <div className="flex items-center space-x-2">
                                    <span className="h-2 w-2 rounded-full bg-electric animate-pulse"></span>
                                    <span className="text-electric">ACTIVE</span>
                                </div>
                            </div>
                            <div className="flex justify-between items-center">
                                <span>OVERLAY</span>
                                <div className="flex items-center space-x-2">
                                    <span className="h-2 w-2 rounded-full bg-electric animate-pulse"></span>
                                    <span className="text-electric">READY</span>
                                </div>
                            </div>
                            <div className="flex justify-between">
                                <span>APM</span>
                                <span className={clsx(
                                    "font-mono",
                                    (status?.apm || 0) > 20 ? "text-electric" : "text-gray-300"
                                )}>{Number(status?.apm || 0).toFixed(1)}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>ACTIVITY</span>
                                <span className={clsx(
                                    "uppercase font-bold",
                                    status?.activity_pattern === 'active' ? "text-electric" :
                                        status?.activity_pattern === 'passive' ? "text-amber" : "text-gray-400"
                                )}>{status?.activity_pattern || 'idle'}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>FATIGUE</span>
                                <span className={clsx(
                                    (status?.fatigue_score || 0) > 70 ? "text-breach" :
                                        (status?.fatigue_score || 0) > 50 ? "text-amber" : "text-gray-300"
                                )}>{Number(status?.fatigue_score || 0).toFixed(0)}%</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Center Column: Flow Battery & Controls */}
                <div className="col-span-6 flex flex-col items-center justify-center space-y-8 min-h-[500px]">

                    {/* Battery */}
                    <FlowBattery energy={status?.energy || 0} isCharging={!isRunning} />

                    {/* Current Task Display */}
                    <motion.div
                        className="text-center space-y-2"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                    >
                        <div className="text-xs uppercase tracking-widest text-gray-500">Current Focus</div>
                        <div className="text-2xl font-bold text-white truncate max-w-md">
                            {status?.current_task || "Ready to Initialize"}
                        </div>
                        {isRunning && (
                            <motion.div
                                className="text-electric font-mono text-lg"
                                key={status?.session_duration}
                                initial={{ scale: 1.1 }}
                                animate={{ scale: 1 }}
                                transition={{ duration: 0.2 }}
                            >
                                {Math.floor((status?.session_duration || 0) / 60)}m {(status?.session_duration || 0) % 60}s
                            </motion.div>
                        )}
                    </motion.div>

                    {/* Controls */}
                    <div className="flex space-x-4">
                        {!isRunning ? (
                            <motion.button
                                onClick={handleStartSession}
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                className="group relative px-8 py-4 bg-electric/10 hover:bg-electric/20 border border-electric/50 rounded-lg overflow-hidden transition-all shadow-lg shadow-electric/20"
                            >
                                <div className="absolute inset-0 bg-electric/20 blur-xl group-hover:bg-electric/30 transition-all"></div>
                                <span className="relative flex items-center text-electric font-bold tracking-widest">
                                    <Play size={20} className="mr-2" /> INITIATE FLOW
                                </span>
                            </motion.button>
                        ) : (
                            <motion.button
                                onClick={handleStopSession}
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                className="group px-8 py-4 bg-red-900/10 hover:bg-red-900/20 border border-red-900/50 rounded-lg transition-all shadow-lg shadow-red-900/20"
                            >
                                <span className="flex items-center text-red-500 font-bold tracking-widest">
                                    <Square size={20} className="mr-2 fill-current" /> TERMINATE
                                </span>
                            </motion.button>
                        )}
                    </div>
                </div>

                {/* Right Column: Stats */}
                <div className="col-span-3 space-y-6 overflow-y-auto max-h-[calc(100vh-200px)] pr-2">
                    <div className="glass-panel p-6 rounded-xl">
                        <h3 className="text-sm uppercase tracking-widest text-gray-500 mb-4 text-center">Cognitive Profile</h3>
                        <div className="h-64">
                            <HexagonStats stats={{
                                stamina: status?.stamina || 60,
                                resilience: status?.resilience ? Math.min(100, status.resilience) : 60,
                                consistency: 80,
                                focus: status?.focus_score || 85,
                                flow: 70,
                                willpower: 65
                            }} />
                        </div>
                    </div>

                    {/* AI Insights Component */}
                    <AIInsights />

                    <div className="glass-panel p-6 rounded-xl">
                        <h3 className="text-sm uppercase tracking-widest text-gray-500 mb-4">Last Session XP Breakdown</h3>
                        {(() => {
                            const hasRealSession = sessions.length > 0;
                            const s = hasRealSession ? sessions[0] : null;
                            const hasRealXP = s && (s.xp_total > 0 || s.duration_seconds > 0);

                            if (hasRealXP) {
                                const xb = s.xp_breakdown || {};
                                return (
                                    <div className="text-sm text-gray-300 space-y-2">
                                        <div className="flex justify-between font-mono">
                                            <span>Total XP</span>
                                            <span className="text-amber font-bold">{s.xp_total ?? 0}</span>
                                        </div>
                                        <div className="grid grid-cols-2 gap-2 text-xs">
                                            <div className="flex justify-between bg-gray-900/40 p-2 rounded"><span>Base</span><span>+{xb.base ?? 0}</span></div>
                                            <div className="flex justify-between bg-gray-900/40 p-2 rounded"><span>Resilience</span><span>+{xb.resilience ?? 0}</span></div>
                                            <div className="flex justify-between bg-gray-900/40 p-2 rounded"><span>Stamina</span><span>+{xb.stamina ?? 0}</span></div>
                                            <div className="flex justify-between bg-gray-900/40 p-2 rounded"><span>Focus</span><span>+{xb.focus ?? 0}</span></div>
                                            <div className="flex justify-between bg-gray-900/40 p-2 rounded col-span-2"><span>Penalty</span><span>-{xb.penalty ?? 0}</span></div>
                                        </div>
                                        <div className="text-xs text-gray-500 mt-2">
                                            Duration: {Math.floor((s.duration_seconds || 0) / 60)}m • Distractions: {s.distraction_count || 0}
                                        </div>
                                    </div>
                                );
                            } else {
                                // Show mock data for better UX
                                return (
                                    <div className="text-sm text-gray-300 space-y-2">
                                        <div className="flex justify-between font-mono">
                                            <span>Total XP</span>
                                            <span className="text-amber font-bold">125</span>
                                        </div>
                                        <div className="grid grid-cols-2 gap-2 text-xs">
                                            <div className="flex justify-between bg-gray-900/40 p-2 rounded"><span>Base</span><span>+100</span></div>
                                            <div className="flex justify-between bg-gray-900/40 p-2 rounded"><span>Resilience</span><span>+15</span></div>
                                            <div className="flex justify-between bg-gray-900/40 p-2 rounded"><span>Stamina</span><span>+10</span></div>
                                            <div className="flex justify-between bg-gray-900/40 p-2 rounded"><span>Focus</span><span>+8</span></div>
                                            <div className="flex justify-between bg-gray-900/40 p-2 rounded col-span-2"><span>Penalty</span><span>-8</span></div>
                                        </div>
                                        <div className="text-xs text-gray-500 mt-2">
                                            Example session: 25m • 1 distraction
                                        </div>
                                        <div className="text-xs text-electric/70 mt-2 italic">
                                            ✨ Complete a full session to see real XP data
                                        </div>
                                    </div>
                                );
                            }
                        })()}
                    </div>
                </div>

            </div>

            {/* Data Visualizer Section */}
            <div className="mt-12 mb-8">
                <h2 className="text-xl font-bold mb-6 text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-500">
                    Analytics & Insights
                </h2>
                <DataVisualizer />
            </div>

            {/* Settings Modal */}
            <SettingsComponent isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
        </div>
    );
}

export default App;
