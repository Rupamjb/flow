import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
    LineChart, Line, AreaChart, Area,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { TrendingUp, Clock, Loader } from 'lucide-react';
import clsx from 'clsx';

const DataVisualizer = () => {
    const [xpData, setXpData] = useState([]);
    const [flowData, setFlowData] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [xpRes, flowRes] = await Promise.all([
                    axios.get('http://127.0.0.1:8000/api/analytics/daily-xp?days=30'),
                    axios.get('http://127.0.0.1:8000/api/analytics/flow-time?days=30')
                ]);

                setXpData(xpRes.data || []);
                setFlowData(flowRes.data || []);
            } catch (err) {
                console.error("Failed to fetch analytics data:", err);
                // Use mock data as fallback
                const generateMockDates = (days) => {
                    const dates = [];
                    const today = new Date();
                    for (let i = days - 1; i >= 0; i--) {
                        const date = new Date(today);
                        date.setDate(date.getDate() - i);
                        dates.push(date.toISOString().split('T')[0]);
                    }
                    return dates;
                };

                const mockDates = generateMockDates(14); // Last 14 days

                setXpData(mockDates.map((date, idx) => ({
                    date,
                    xp: Math.floor(Math.random() * 200) + 50 // Random XP between 50-250
                })));

                setFlowData(mockDates.map((date, idx) => ({
                    date,
                    flow_minutes: Math.floor(Math.random() * 120) + 30, // Random minutes between 30-150
                    sessions: Math.floor(Math.random() * 3) + 1 // 1-3 sessions
                })));
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);



    // Format date for display
    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        return `${date.getMonth() + 1}/${date.getDate()}`;
    };

    if (loading) {
        return (
            <div className="glass-panel p-6 rounded-xl">
                <div className="flex items-center justify-center h-64">
                    <Loader className="animate-spin text-electric" size={32} />
                </div>
            </div>
        );
    }

    // Show empty state if no data
    if (xpData.length === 0 && flowData.length === 0) {
        return (
            <div className="glass-panel p-6 rounded-xl text-center">
                <div className="py-12">
                    <TrendingUp className="text-gray-600 mx-auto mb-3" size={48} />
                    <p className="text-sm text-gray-500 mb-2">No data yet</p>
                    <p className="text-xs text-gray-600">Complete sessions to see your analytics</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* XP Gained Per Day */}
            <div className="glass-panel p-6 rounded-xl">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                        <TrendingUp className="text-electric" size={20} />
                        <h3 className="text-sm uppercase tracking-widest text-gray-500">XP Gained Per Day</h3>
                    </div>
                    <span className="text-xs text-gray-500">Last 30 days</span>
                </div>

                <ResponsiveContainer width="100%" height={250}>
                    <AreaChart data={xpData}>
                        <defs>
                            <linearGradient id="xpGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#ffb703" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#ffb703" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                        <XAxis
                            dataKey="date"
                            tickFormatter={formatDate}
                            stroke="#666"
                            style={{ fontSize: '10px' }}
                        />
                        <YAxis
                            stroke="#666"
                            style={{ fontSize: '10px' }}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#1a1a1a',
                                border: '1px solid #333',
                                borderRadius: '8px',
                                color: '#fff'
                            }}
                            labelFormatter={(value) => `Date: ${formatDate(value)}`}
                            formatter={(value) => [`${value} XP`, 'XP']}
                        />
                        <Area
                            type="monotone"
                            dataKey="xp"
                            stroke="#ffb703"
                            strokeWidth={2}
                            fill="url(#xpGradient)"
                        />
                    </AreaChart>
                </ResponsiveContainer>

                <div className="mt-4 flex items-center justify-between text-xs text-gray-500">
                    <span>Total XP: {xpData.reduce((sum, d) => sum + (d.xp || 0), 0)}</span>
                    <span>Avg Daily: {Math.round(xpData.reduce((sum, d) => sum + (d.xp || 0), 0) / Math.max(xpData.length, 1))}</span>
                </div>
            </div>

            {/* Flow State Time */}
            <div className="glass-panel p-6 rounded-xl">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                        <Clock className="text-electric" size={20} />
                        <h3 className="text-sm uppercase tracking-widest text-gray-500">Flow State Time</h3>
                    </div>
                    <span className="text-xs text-gray-500">Last 30 days</span>
                </div>

                <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={flowData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                        <XAxis
                            dataKey="date"
                            tickFormatter={formatDate}
                            stroke="#666"
                            style={{ fontSize: '10px' }}
                        />
                        <YAxis
                            stroke="#666"
                            style={{ fontSize: '10px' }}
                            label={{ value: 'Minutes', angle: -90, position: 'insideLeft', style: { fill: '#666' } }}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#1a1a1a',
                                border: '1px solid #333',
                                borderRadius: '8px',
                                color: '#fff'
                            }}
                            labelFormatter={(value) => `Date: ${formatDate(value)}`}
                            formatter={(value, name) => {
                                if (name === 'flow_minutes') return [`${value} min`, 'Flow Time'];
                                if (name === 'sessions') return [`${value}`, 'Sessions'];
                                return value;
                            }}
                        />
                        <Legend
                            wrapperStyle={{ fontSize: '12px', color: '#999' }}
                        />
                        <Line
                            type="monotone"
                            dataKey="flow_minutes"
                            stroke="#219ebc"
                            strokeWidth={2}
                            dot={{ fill: '#219ebc', r: 3 }}
                            activeDot={{ r: 5 }}
                            name="Flow Time (min)"
                        />
                    </LineChart>
                </ResponsiveContainer>

                <div className="mt-4 flex items-center justify-between text-xs text-gray-500">
                    <span>Total Flow Time: {Math.round(flowData.reduce((sum, d) => sum + (d.flow_minutes || 0), 0))} min</span>
                    <span>Avg Daily: {Math.round(flowData.reduce((sum, d) => sum + (d.flow_minutes || 0), 0) / Math.max(flowData.length, 1))} min</span>
                </div>
            </div>
        </div>
    );
};

export default DataVisualizer;

