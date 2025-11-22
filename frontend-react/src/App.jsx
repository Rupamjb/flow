import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer,
    AreaChart, Area, XAxis, YAxis, Tooltip
} from 'recharts';
import {
    Battery, Zap, Shield, Activity, Play, Square,
    AlertTriangle, CheckCircle, Clock, Terminal
} from 'lucide-react';
import clsx from 'clsx';

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

const QuestLog = ({ sessions }) => {
    return (
        <div className="space-y-4">
            <h3 className="text-sm uppercase tracking-widest text-gray-500 flex items-center">
                <Terminal size={14} className="mr-2" /> Mission Log
            </h3>

            <div className="space-y-2">
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

                {sessions.length === 0 && (
                    <div className="text-center py-8 text-gray-600 text-xs italic">
                        No missions recorded today.
                    </div>
                )}
            </div>
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

    // Mock Data for UI Dev (Fallback)
    const mockStatus = {
        is_running: false,
        energy: 85.5,
        focus_score: 92,
        current_task: "Idle",
        session_duration: 0,
        resilience: 450,
        xp: 1250
    };

    const fetchStatus = async () => {
        try {
            const res = await axios.get('http://127.0.0.1:8000/api/status');
            setStatus(res.data);
            setError(null);
        } catch (err) {
            console.error("Backend offline, using mock data");
            setStatus(mockStatus); // Fallback for demo
            setError("Backend disconnected");
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
        fetchStatus();
        const interval = setInterval(fetchStatus, 1000);
        return () => clearInterval(interval);
    }, []);

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

    if (loading) return <div className="flex h-screen items-center justify-center bg-void text-electric">INITIALIZING...</div>;

    const isRunning = status?.is_running || false;

    return (
        <div className="min-h-screen bg-void text-white p-8 font-sans selection:bg-electric selection:text-black">

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
                        <div className="text-xs text-gray-500 uppercase">Level 5 Architect</div>
                        <div className="text-xl font-mono font-bold text-amber">{status?.xp || 0} XP</div>
                    </div>
                    <div className="h-10 w-10 rounded bg-gray-800 border border-gray-700 flex items-center justify-center">
                        <span className="font-bold text-electric">V</span>
                    </div>
                </div>
            </header>

            {/* Main Grid */}
            <div className="grid grid-cols-12 gap-8">

                {/* Left Column: Quest Log */}
                <div className="col-span-3 space-y-6">
                    <TimetableStatus />

                    <div className="glass-panel p-6 rounded-xl">
                        <QuestLog sessions={[
                            { title: "Deep Dive Alpha", time: "09:00 - 09:45", xp: 250, completed: true },
                            { title: "System Architecture", time: "10:00 - 11:30", xp: 400, completed: true },
                            { title: "Lunch Break", time: "12:00 - 13:00", xp: 0, completed: false },
                        ]} />
                    </div>

                    <div className="glass-panel p-6 rounded-xl">
                        <h3 className="text-sm uppercase tracking-widest text-gray-500 mb-4">System Status</h3>
                        <div className="space-y-2 text-xs font-mono text-gray-400">
                            <div className="flex justify-between">
                                <span>BACKEND</span>
                                <span className={error ? "text-breach" : "text-electric"}>{error ? "OFFLINE" : "CONNECTED"}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>EXTENSION</span>
                                <span className="text-electric">ACTIVE</span>
                            </div>
                            <div className="flex justify-between">
                                <span>OVERLAY</span>
                                <span className="text-electric">READY</span>
                            </div>
                            <div className="flex justify-between">
                                <span>APM</span>
                                <span className="text-gray-300">{Number(status?.apm || 0).toFixed(1)}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>ACTIVITY</span>
                                <span className="text-gray-300">{status?.activity_pattern || 'idle'}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>FATIGUE</span>
                                <span className="text-gray-300">{Number(status?.fatigue_score || 0).toFixed(0)}%</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Center Column: Flow Battery & Controls */}
                <div className="col-span-6 flex flex-col items-center justify-center space-y-12">

                    {/* Battery */}
                    <FlowBattery energy={status?.energy || 0} isCharging={!isRunning} />

                    {/* Current Task Display */}
                    <div className="text-center space-y-2">
                        <div className="text-xs uppercase tracking-widest text-gray-500">Current Focus</div>
                        <div className="text-2xl font-bold text-white truncate max-w-md">
                            {status?.current_task || "Ready to Initialize"}
                        </div>
                        {isRunning && (
                            <div className="text-electric font-mono text-lg">
                                {Math.floor((status?.session_duration || 0) / 60)}m {(status?.session_duration || 0) % 60}s
                            </div>
                        )}
                    </div>

                    {/* Controls */}
                    <div className="flex space-x-4">
                        {!isRunning ? (
                            <button
                                onClick={handleStartSession}
                                className="group relative px-8 py-4 bg-electric/10 hover:bg-electric/20 border border-electric/50 rounded-lg overflow-hidden transition-all"
                            >
                                <div className="absolute inset-0 bg-electric/20 blur-xl group-hover:bg-electric/30 transition-all"></div>
                                <span className="relative flex items-center text-electric font-bold tracking-widest">
                                    <Play size={20} className="mr-2" /> INITIATE FLOW
                                </span>
                            </button>
                        ) : (
                            <button
                                onClick={handleStopSession}
                                className="group px-8 py-4 bg-red-900/10 hover:bg-red-900/20 border border-red-900/50 rounded-lg transition-all"
                            >
                                <span className="flex items-center text-red-500 font-bold tracking-widest">
                                    <Square size={20} className="mr-2 fill-current" /> TERMINATE
                                </span>
                            </button>
                        )}
                    </div>
                </div>

                {/* Right Column: Stats */}
                <div className="col-span-3 space-y-6">
                    <div className="glass-panel p-6 rounded-xl h-80">
                        <h3 className="text-sm uppercase tracking-widest text-gray-500 mb-4 text-center">Cognitive Profile</h3>
                        <HexagonStats stats={{
                            stamina: status?.stamina || 60,
                            resilience: status?.resilience ? Math.min(100, status.resilience) : 60,
                            consistency: 80,
                            focus: status?.focus_score || 85,
                            flow: 70,
                            willpower: 65
                        }} />
                    </div>

                    <div className="glass-panel p-6 rounded-xl">
                        <h3 className="text-sm uppercase tracking-widest text-gray-500 mb-4">Actionable Insights</h3>
                        <ul className="space-y-2 text-sm text-gray-300">
                            {(() => {
                                const tips = [];
                                const energy = status?.energy ?? 100;
                                const apm = status?.apm ?? 0;
                                const fatigue = status?.fatigue_score ?? 0;
                                const resilience = status?.resilience ?? 0;
                                const activity = (status?.activity_pattern || '').toString();
                                if (fatigue > 60) tips.push('High fatigue detected: take a 2-3 min reset to recover.');
                                if (energy < 40) tips.push('Low energy: hydrate and consider a short walk.');
                                if (activity === 'passive' && apm < 5 && energy > 60) tips.push('Transition from passive browsing to a defined task.');
                                if (resilience < 20 && apm > 10) tips.push('Great pace—avoid opening distracting tabs to build resilience.');
                                const last = sessions?.[0];
                                if (last && last.distraction_count >= 3) tips.push('Reduce context switches—mute notifications or close extra tabs.');
                                if (last && last.duration_seconds >= 45*60 && (last.focus_score ?? 0) >= 80) tips.push('Excellent long session—schedule a proper break to consolidate.');
                                if (tips.length === 0) tips.push('You are on track. Maintain your current focus routine.');
                                return tips.map((t, i) => (
                                    <li key={i} className="flex items-start">
                                        <span className="h-1.5 w-1.5 rounded-full bg-electric mt-2 mr-2"></span>
                                        <span>{t}</span>
                                    </li>
                                ));
                            })()}
                        </ul>
                    </div>

                    <div className="glass-panel p-6 rounded-xl">
                        <h3 className="text-sm uppercase tracking-widest text-gray-500 mb-4">Last Session XP Breakdown</h3>
                        {sessions.length > 0 ? (
                            (() => {
                                const s = sessions[0];
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
                                            Duration: {Math.floor((s.duration_seconds||0)/60)}m • Distractions: {s.distraction_count||0}
                                        </div>
                                    </div>
                                );
                            })()
                        ) : (
                            <div className="text-xs text-gray-500">No sessions yet. Start one to see your XP breakdown.</div>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
}

export default App;
