import React, { useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Loader2, CheckCircle, Calendar, Briefcase, Target, AlertCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const Onboarding = ({ onComplete }) => {
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [analysis, setAnalysis] = useState(null);
    const [error, setError] = useState(null);
    
    const [formData, setFormData] = useState({
        timetable: {
            start_time: '09:00',
            end_time: '17:00',
            work_days: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        },
        work_type: '',
        challenges: '',
        goals: ''
    });

    const workTypes = [
        'Coding/Software Development',
        'Writing/Content Creation',
        'Design/Creative Work',
        'Research/Analysis',
        'Learning/Education',
        'Other'
    ];

    const workDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

    const handleSubmit = async () => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await axios.post(`${API_BASE}/api/onboarding/submit`, formData);
            setAnalysis(response.data.analysis);
            setStep(3);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to submit onboarding. Please try again.');
            console.error('Onboarding error:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleComplete = async () => {
        // Wait a moment for backend to process, then call onComplete
        await new Promise(resolve => setTimeout(resolve, 500));
        if (onComplete) {
            onComplete();
        }
    };

    return (
        <div className="min-h-screen bg-void-black text-white flex items-center justify-center p-4">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-2xl w-full"
            >
                <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-lg p-8 shadow-2xl">
                    {/* Progress Indicator */}
                    <div className="mb-8">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-gray-400">Step {step} of 3</span>
                            <span className="text-sm text-gray-400">{Math.round((step / 3) * 100)}%</span>
                        </div>
                        <div className="w-full bg-gray-800 rounded-full h-2">
                            <motion.div
                                className="bg-electric h-2 rounded-full"
                                initial={{ width: 0 }}
                                animate={{ width: `${(step / 3) * 100}%` }}
                                transition={{ duration: 0.3 }}
                            />
                        </div>
                    </div>

                    {/* Step 1: Timetable */}
                    {step === 1 && (
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                        >
                            <div className="flex items-center mb-6">
                                <Calendar className="mr-3 text-electric" size={24} />
                                <h2 className="text-2xl font-bold">Daily Timetable</h2>
                            </div>
                            
                            <div className="space-y-6">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Work Start Time
                                    </label>
                                    <input
                                        type="time"
                                        value={formData.timetable.start_time}
                                        onChange={(e) => setFormData({
                                            ...formData,
                                            timetable: { ...formData.timetable, start_time: e.target.value }
                                        })}
                                        className="w-full bg-gray-800 border border-gray-700 rounded px-4 py-2 text-white focus:outline-none focus:border-electric"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Work End Time
                                    </label>
                                    <input
                                        type="time"
                                        value={formData.timetable.end_time}
                                        onChange={(e) => setFormData({
                                            ...formData,
                                            timetable: { ...formData.timetable, end_time: e.target.value }
                                        })}
                                        className="w-full bg-gray-800 border border-gray-700 rounded px-4 py-2 text-white focus:outline-none focus:border-electric"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Work Days
                                    </label>
                                    <div className="grid grid-cols-4 gap-2">
                                        {workDays.map((day) => (
                                            <button
                                                key={day}
                                                type="button"
                                                onClick={() => {
                                                    const days = formData.timetable.work_days;
                                                    const newDays = days.includes(day)
                                                        ? days.filter(d => d !== day)
                                                        : [...days, day];
                                                    setFormData({
                                                        ...formData,
                                                        timetable: { ...formData.timetable, work_days: newDays }
                                                    });
                                                }}
                                                className={`px-3 py-2 rounded text-sm transition-colors ${
                                                    formData.timetable.work_days.includes(day)
                                                        ? 'bg-electric text-white'
                                                        : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                                                }`}
                                            >
                                                {day.slice(0, 3)}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <button
                                onClick={() => setStep(2)}
                                className="mt-8 w-full bg-electric hover:bg-electric/80 text-white font-semibold py-3 rounded transition-colors"
                            >
                                Next: Work Type
                            </button>
                        </motion.div>
                    )}

                    {/* Step 2: Work Type & Challenges */}
                    {step === 2 && (
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                        >
                            <div className="flex items-center mb-6">
                                <Briefcase className="mr-3 text-electric" size={24} />
                                <h2 className="text-2xl font-bold">Work & Challenges</h2>
                            </div>
                            
                            <div className="space-y-6">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        What type of work do you primarily do?
                                    </label>
                                    <select
                                        value={formData.work_type}
                                        onChange={(e) => setFormData({ ...formData, work_type: e.target.value })}
                                        className="w-full bg-gray-800 border border-gray-700 rounded px-4 py-2 text-white focus:outline-none focus:border-electric"
                                    >
                                        <option value="">Select work type...</option>
                                        {workTypes.map((type) => (
                                            <option key={type} value={type}>{type}</option>
                                        ))}
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        What are your main productivity challenges?
                                    </label>
                                    <textarea
                                        value={formData.challenges}
                                        onChange={(e) => setFormData({ ...formData, challenges: e.target.value })}
                                        placeholder="e.g., Getting distracted by social media, difficulty maintaining focus for long periods..."
                                        rows={4}
                                        className="w-full bg-gray-800 border border-gray-700 rounded px-4 py-2 text-white focus:outline-none focus:border-electric resize-none"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        What are your goals?
                                    </label>
                                    <textarea
                                        value={formData.goals}
                                        onChange={(e) => setFormData({ ...formData, goals: e.target.value })}
                                        placeholder="e.g., Complete project X, improve focus time, reduce distractions..."
                                        rows={4}
                                        className="w-full bg-gray-800 border border-gray-700 rounded px-4 py-2 text-white focus:outline-none focus:border-electric resize-none"
                                    />
                                </div>
                            </div>

                            <div className="flex gap-4 mt-8">
                                <button
                                    onClick={() => setStep(1)}
                                    className="flex-1 bg-gray-800 hover:bg-gray-700 text-white font-semibold py-3 rounded transition-colors"
                                >
                                    Back
                                </button>
                                <button
                                    onClick={handleSubmit}
                                    disabled={loading || !formData.work_type}
                                    className="flex-1 bg-electric hover:bg-electric/80 text-white font-semibold py-3 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 className="mr-2 animate-spin" size={20} />
                                            Analyzing...
                                        </>
                                    ) : (
                                        'Analyze & Complete'
                                    )}
                                </button>
                            </div>
                        </motion.div>
                    )}

                    {/* Step 3: AI Analysis Results */}
                    {step === 3 && analysis && (
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                        >
                            <div className="flex items-center mb-6">
                                <CheckCircle className="mr-3 text-green-500" size={24} />
                                <h2 className="text-2xl font-bold">Your Personalized Schedule</h2>
                            </div>

                            {error && (
                                <div className="mb-6 p-4 bg-red-900/20 border border-red-800 rounded flex items-center">
                                    <AlertCircle className="mr-2 text-red-500" size={20} />
                                    <span className="text-red-400">{error}</span>
                                </div>
                            )}

                            <div className="space-y-6">
                                {analysis.schedule && (
                                    <div className="bg-gray-800/50 rounded p-4">
                                        <h3 className="text-lg font-semibold mb-3 flex items-center">
                                            <Calendar className="mr-2 text-electric" size={20} />
                                            Predicted Flow Windows
                                        </h3>
                                        <div className="space-y-2">
                                            {analysis.schedule.predicted_flow_windows?.map((window, idx) => (
                                                <div key={idx} className="text-gray-300">
                                                    • {window}
                                                </div>
                                            ))}
                                        </div>
                                        <div className="mt-3 text-sm text-gray-400">
                                            Baseline Focus Duration: {analysis.schedule.baseline_focus_duration} minutes
                                        </div>
                                    </div>
                                )}

                                {analysis.mission_log && (
                                    <div className="bg-gray-800/50 rounded p-4">
                                        <h3 className="text-lg font-semibold mb-3 flex items-center">
                                            <Target className="mr-2 text-electric" size={20} />
                                            Mission Log
                                        </h3>
                                        <div className="space-y-2">
                                            {analysis.mission_log.goals?.map((goal, idx) => (
                                                <div key={idx} className="text-gray-300 flex items-start">
                                                    <span className="text-electric mr-2">•</span>
                                                    <span>{goal}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {analysis.app_suggestions && (
                                    <div className="bg-gray-800/50 rounded p-4">
                                        <h3 className="text-lg font-semibold mb-3">App Suggestions</h3>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <div className="text-sm text-green-400 mb-2">Productive Apps</div>
                                                <div className="space-y-1">
                                                    {analysis.app_suggestions.productive?.map((app, idx) => (
                                                        <div key={idx} className="text-gray-300 text-sm">• {app}</div>
                                                    ))}
                                                </div>
                                            </div>
                                            <div>
                                                <div className="text-sm text-red-400 mb-2">Distracting Apps</div>
                                                <div className="space-y-1">
                                                    {analysis.app_suggestions.distracting?.map((app, idx) => (
                                                        <div key={idx} className="text-gray-300 text-sm">• {app}</div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>

                            <button
                                onClick={handleComplete}
                                className="mt-8 w-full bg-electric hover:bg-electric/80 text-white font-semibold py-3 rounded transition-colors"
                            >
                                Start Using Flow Engine
                            </button>
                        </motion.div>
                    )}
                </div>
            </motion.div>
        </div>
    );
};

export default Onboarding;

