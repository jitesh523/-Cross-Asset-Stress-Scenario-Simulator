import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Activity,
  Brain,
  BarChart3,
  Settings,
  PlusCircle,
  Play,
  RefreshCcw,
  ChevronRight,
  ShieldAlert,
  Zap
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area
} from 'recharts';

const API_BASE = 'http://localhost:8000/api';

function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [systemStats, setSystemStats] = useState<any>(null);
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [aiPrompt, setAiPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedScenario, setGeneratedScenario] = useState<any>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [statsRes, scenariosRes] = await Promise.all([
        axios.get(`${API_BASE}/analysis/summary`),
        axios.get(`${API_BASE}/scenarios/`)
      ]);
      setSystemStats(statsRes.data);
      setScenarios(scenariosRes.data);
    } catch (err) {
      setError('Failed to connect to simulation engine');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateAI = async () => {
    if (!aiPrompt) return;
    setIsGenerating(true);
    try {
      const res = await axios.post(`${API_BASE}/scenarios/generate-ai`, { prompt: aiPrompt });
      setGeneratedScenario(res.data);
    } catch (err) {
      setError('AI Generation failed. Check API keys and backend status.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex font-sans text-slate-900">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-white flex flex-col">
        <div className="p-6 flex items-center gap-3">
          <div className="bg-indigo-500 p-2 rounded-lg">
            <Zap size={24} />
          </div>
          <h1 className="font-bold text-xl tracking-tight">StressSim AI</h1>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-2">
          <button
            onClick={() => setActiveTab('overview')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === 'overview' ? 'bg-indigo-600' : 'hover:bg-slate-800'}`}
          >
            <Activity size={20} />
            <span>Overview</span>
          </button>
          <button
            onClick={() => setActiveTab('scenarios')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === 'scenarios' ? 'bg-indigo-600' : 'hover:bg-slate-800'}`}
          >
            <ShieldAlert size={20} />
            <span>Scenarios</span>
          </button>
          <button
            onClick={() => setActiveTab('ai-gen')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === 'ai-gen' ? 'bg-indigo-600' : 'hover:bg-slate-800'}`}
          >
            <Brain size={20} />
            <span>AI Generator</span>
          </button>
          <button
            onClick={() => setActiveTab('optimizer')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === 'optimizer' ? 'bg-indigo-600' : 'hover:bg-slate-800'}`}
          >
            <BarChart3 size={20} />
            <span>Optimizer</span>
          </button>
        </nav>

        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center gap-3 px-4 py-3">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse shadow-[0_0_10px_rgba(34,197,94,0.5)]"></div>
            <span className="text-sm font-medium text-slate-400">System Ready</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-20 bg-white border-b border-slate-200 flex items-center justify-between px-8">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-semibold capitalize">{activeTab.replace('-', ' ')}</h2>
            <div className="bg-slate-100 px-3 py-1 rounded-full text-xs font-medium text-slate-500 uppercase tracking-widest">
              Risk Phase: Moderate
            </div>
          </div>
          <button className="flex items-center gap-2 bg-indigo-600 text-white px-5 py-2.5 rounded-lg font-medium hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-200">
            <PlusCircle size={18} />
            <span>New Simulation</span>
          </button>
        </header>

        <div className="flex-1 overflow-y-auto p-8">
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl flex items-center gap-3">
              <ShieldAlert size={20} />
              <p>{error}</p>
            </div>
          )}

          {activeTab === 'overview' && (
            <div className="space-y-8">
              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {[
                  { label: 'Scenarios', value: systemStats?.total_scenarios || 0, icon: ShieldAlert, color: 'text-blue-600', bg: 'bg-blue-50' },
                  { label: 'Simulations', value: systemStats?.total_simulations_run || 0, icon: Play, color: 'text-emerald-600', bg: 'bg-emerald-50' },
                  { label: 'Predefined', value: systemStats?.predefined_scenarios || 0, icon: Settings, color: 'text-amber-600', bg: 'bg-amber-50' },
                  { label: 'Assets', value: 24, icon: BarChart3, color: 'text-indigo-600', bg: 'bg-indigo-50' },
                ].map((stat, i) => (
                  <div key={i} className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-4">
                      <div className={`${stat.bg} ${stat.color} p-3 rounded-xl`}>
                        <stat.icon size={24} />
                      </div>
                    </div>
                    <div>
                      <p className="text-slate-500 text-sm font-medium">{stat.label}</p>
                      <h3 className="text-3xl font-bold mt-1">{stat.value}</h3>
                    </div>
                  </div>
                ))}
              </div>

              {/* Chart Section placeholder */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 bg-white p-8 rounded-2xl shadow-sm border border-slate-100">
                  <div className="flex items-center justify-between mb-8">
                    <h3 className="text-lg font-bold">System Activity</h3>
                    <select className="bg-slate-50 border-none text-sm rounded-lg focus:ring-0">
                      <option>Last 7 Days</option>
                      <option>Last 30 Days</option>
                    </select>
                  </div>
                  <div className="h-80 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={[
                        { name: 'Mon', value: 40 }, { name: 'Tue', value: 30 }, { name: 'Wed', value: 65 },
                        { name: 'Thu', value: 45 }, { name: 'Fri', value: 90 }, { name: 'Sat', value: 20 }, { name: 'Sun', value: 50 },
                      ]}>
                        <defs>
                          <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1} />
                            <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                        <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12 }} dy={10} />
                        <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12 }} />
                        <Tooltip />
                        <Area type="monotone" dataKey="value" stroke="#6366f1" strokeWidth={3} fillOpacity={1} fill="url(#colorValue)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100">
                  <h3 className="text-lg font-bold mb-6">Recent Scenarios</h3>
                  <div className="space-y-4">
                    {scenarios.slice(0, 5).map((s, i) => (
                      <div key={i} className="flex items-center justify-between p-4 rounded-xl border border-slate-50 hover:bg-slate-50 transition-colors group cursor-pointer">
                        <div>
                          <p className="font-bold text-sm">{s.name}</p>
                          <p className="text-xs text-slate-500 uppercase font-medium">{s.category}</p>
                        </div>
                        <ChevronRight size={16} className="text-slate-300 group-hover:text-indigo-500 transform group-hover:translate-x-1 transition-all" />
                      </div>
                    ))}
                  </div>
                  <button className="w-full mt-6 text-sm font-semibold text-indigo-600 hover:text-indigo-700 py-2 border-t border-slate-50">
                    View All Scenarios
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'ai-gen' && (
            <div className="max-w-4xl mx-auto space-y-8">
              <div className="bg-white p-8 rounded-3xl shadow-xl border border-slate-100 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-50 rounded-full -mr-32 -mt-32 opacity-50"></div>

                <div className="relative">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="bg-indigo-600 text-white p-2 rounded-lg">
                      <Brain size={24} />
                    </div>
                    <h2 className="text-2xl font-bold">AI Scenario Generator</h2>
                  </div>

                  <p className="text-slate-600 mb-8 leading-relaxed">
                    Describe a market scenario in plain English. Our AI engine will transform your description
                    into a structured stress model with correlated shocks and volatility adjustments.
                  </p>

                  <div className="space-y-4">
                    <textarea
                      value={aiPrompt}
                      onChange={(e) => setAiPrompt(e.target.value)}
                      placeholder="e.g., A global pandemic causing travel restrictions and a 30% drop in energy demand while tech companies see increased usage..."
                      className="w-full h-40 bg-slate-50 border-2 border-transparent focus:border-indigo-500 focus:bg-white rounded-2xl p-6 text-lg transition-all outline-none resize-none"
                    />

                    <div className="flex gap-4">
                      <button
                        onClick={handleGenerateAI}
                        disabled={isGenerating || !aiPrompt}
                        className="flex-1 bg-indigo-600 text-white py-4 rounded-xl text-lg font-bold hover:bg-indigo-700 transition-all flex items-center justify-center gap-3 disabled:opacity-50"
                      >
                        {isGenerating ? <RefreshCcw className="animate-spin" size={24} /> : <Zap size={24} />}
                        <span>{isGenerating ? 'Analyzing Market Trends...' : 'Generate Neural Scenario'}</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {generatedScenario && (
                <div className="bg-white p-8 rounded-3xl shadow-xl border border-emerald-100 animate-in fade-in slide-in-from-bottom-5 duration-700">
                  <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-3">
                      <div className="bg-emerald-500 text-white p-2 rounded-lg">
                        <Activity size={24} />
                      </div>
                      <h3 className="text-2xl font-bold">{generatedScenario.name}</h3>
                    </div>
                    <span className="bg-emerald-100 text-emerald-700 px-4 py-1.5 rounded-full text-sm font-bold uppercase">
                      {generatedScenario.category}
                    </span>
                  </div>

                  <p className="text-slate-700 text-lg mb-8 italic">"{generatedScenario.description}"</p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-4">
                      <h4 className="font-bold text-slate-500 uppercase tracking-widest text-sm">Return Shocks</h4>
                      <div className="space-y-2">
                        {Object.entries(generatedScenario.parameters.return_shocks).map(([ticker, shock]: any) => (
                          <div key={ticker} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                            <span className="font-bold">{ticker}</span>
                            <span className={`font-bold ${shock < 0 ? 'text-red-500' : 'text-emerald-500'}`}>
                              {shock > 0 ? '+' : ''}{(shock * 100).toFixed(1)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-4">
                      <h4 className="font-bold text-slate-500 uppercase tracking-widest text-sm">Systemic Adjustments</h4>
                      <div className="bg-slate-900 text-white p-6 rounded-2xl">
                        <div className="flex justify-between items-center mb-4">
                          <span>Correlation Shift</span>
                          <span className="text-indigo-400 font-bold">x{generatedScenario.parameters.correlation_multiplier.toFixed(2)}</span>
                        </div>
                        <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                          <div
                            className="bg-indigo-500 h-full transition-all duration-1000"
                            style={{ width: `${(generatedScenario.parameters.correlation_multiplier / 2) * 100}%` }}
                          ></div>
                        </div>
                        <p className="mt-4 text-xs text-slate-400 leading-relaxed uppercase tracking-tighter">
                          All assets recalculated with systemic stress multipliers.
                        </p>
                      </div>
                    </div>
                  </div>

                  <button className="w-full mt-12 bg-slate-900 text-white py-5 rounded-2xl text-xl font-bold hover:bg-black transition-all shadow-xl">
                    Run AI Simulation
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
