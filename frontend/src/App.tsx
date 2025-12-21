import { useState, useEffect } from 'react';
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
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area
} from 'recharts';

const API_BASE = 'http://localhost:8000/api';

interface ScenarioParameters {
  return_shocks: Record<string, number>;
  volatility_multipliers: Record<string, number>;
  correlation_multiplier: number;
}

interface Scenario {
  id: number;
  name: string;
  description: string;
  category: string;
  parameters: ScenarioParameters;
  is_predefined: boolean;
  tags: string[];
}

interface SystemStats {
  total_scenarios: number;
  total_simulations_run: number;
  predefined_scenarios: number;
}

interface OptimizationResult {
  expected_return: number;
  volatility: number;
  sharpe_ratio: number;
  weights: Record<string, number>;
}

interface OptimizationResponse {
  max_sharpe: OptimizationResult;
  min_volatility: OptimizationResult;
}

const ALL_TICKERS = [
  "SPY", "QQQ", "DIA", "IWM", "AAPL", "MSFT", "GOOGL", "AMZN",
  "TLT", "IEF", "SHY", "LQD", "HYG",
  "GLD", "SLV", "USO", "DBA",
  "EUR/USD", "GBP/USD", "JPY/USD", "AUD/USD"
];

function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [aiPrompt, setAiPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedScenario, setGeneratedScenario] = useState<Partial<Scenario> | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);

  // Optimizer state
  const [selectedAssets, setSelectedAssets] = useState<string[]>(["SPY", "TLT", "GLD"]);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optResults, setOptResults] = useState<OptimizationResponse | null>(null);

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

  const handleRunAISimulation = async () => {
    if (!generatedScenario || !generatedScenario.parameters) return;
    setIsSimulating(true);
    try {
      // First save the scenario to get an ID
      const saveRes = await axios.post(`${API_BASE}/scenarios/`, {
        name: generatedScenario.name,
        description: generatedScenario.description,
        category: generatedScenario.category,
        parameters: generatedScenario.parameters,
        tags: ["ai-generated"]
      });

      const scenarioId = saveRes.data.id;
      await executeSimulation(scenarioId, generatedScenario.name || 'AI Scenario');
    } catch (err) {
      setError('Failed to run simulation for generated scenario.');
    } finally {
      setIsSimulating(false);
    }
  };

  const executeSimulation = async (scenarioId: number, name: string) => {
    await axios.post(`${API_BASE}/scenarios/${scenarioId}/run`, {
      tickers: selectedAssets.length > 0 ? selectedAssets : ["SPY", "QQQ", "TLT", "GLD"],
      start_date: "2020-01-01",
      end_date: "2024-12-01",
      num_simulations: 1000,
      num_days: 252
    });

    alert(`Simulation completed for ${name}! View results in Overview.`);
    fetchData(); // Refresh stats
  };

  const handleRunScenario = async (scenario: Scenario) => {
    setIsSimulating(true);
    try {
      await executeSimulation(scenario.id, scenario.name);
    } catch (err) {
      setError(`Failed to run simulation for ${scenario.name}`);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleOptimize = async () => {
    if (selectedAssets.length < 2) {
      alert("Please select at least 2 assets for optimization");
      return;
    }
    setIsOptimizing(true);
    try {
      const res = await axios.post(`${API_BASE}/simulations/optimize`, {
        tickers: selectedAssets,
        start_date: "2023-01-01",
        end_date: "2024-12-01"
      });
      setOptResults(res.data);
    } catch (err) {
      setError('Optimization failed. Ensure selected assets have historical data.');
    } finally {
      setIsOptimizing(false);
    }
  };

  const toggleAsset = (ticker: string) => {
    setSelectedAssets((prev: string[]) =>
      prev.includes(ticker) ? prev.filter((t: string) => t !== ticker) : [...prev, ticker]
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 flex font-sans text-slate-900">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-white flex flex-col">
        <div className="p-6 flex items-center gap-3">
          <div className="bg-indigo-500 p-2 rounded-lg text-white">
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
            <div className={`w-3 h-3 rounded-full shadow-[0_0_10px_rgba(34,197,94,0.5)] ${loading ? 'bg-amber-500 animate-pulse' : 'bg-green-500 animate-pulse'}`}></div>
            <span className="text-sm font-medium text-slate-400">{loading ? 'Connecting...' : 'System Ready'}</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-20 bg-white border-b border-slate-200 flex items-center justify-between px-8">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-semibold capitalize">{activeTab.replace('-', ' ')}</h2>
            <div className="bg-slate-100 px-3 py-1 rounded-full text-xs font-medium text-slate-500 uppercase tracking-widest hidden sm:block">
              Risk Phase: Moderate
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={fetchData}
              className="p-2.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors text-slate-500"
              title="Refresh Data"
            >
              <RefreshCcw size={18} className={loading ? 'animate-spin' : ''} />
            </button>
            <button className="flex items-center gap-2 bg-indigo-600 text-white px-5 py-2.5 rounded-lg font-medium hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-200">
              <PlusCircle size={18} />
              <span>New Simulation</span>
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-8">
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl flex items-center gap-3">
              <ShieldAlert size={20} />
              <p>{error}</p>
              <button onClick={() => setError(null)} className="ml-auto text-xs font-bold uppercase">Dismiss</button>
            </div>
          )}

          {activeTab === 'overview' && (
            <div className="space-y-8 animate-in fade-in duration-500">
              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {[
                  { label: 'Scenarios', value: systemStats?.total_scenarios || 0, icon: ShieldAlert, color: 'text-blue-600', bg: 'bg-blue-50' },
                  { label: 'Simulations', value: systemStats?.total_simulations_run || 0, icon: Play, color: 'text-emerald-600', bg: 'bg-emerald-50' },
                  { label: 'Predefined', value: systemStats?.predefined_scenarios || 0, icon: Settings, color: 'text-amber-600', bg: 'bg-amber-50' },
                  { label: 'Assets', value: ALL_TICKERS.length, icon: BarChart3, color: 'text-indigo-600', bg: 'bg-indigo-50' },
                ].map((stat, i) => (
                  <div key={i} className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-4">
                      <div className={`${stat.bg} ${stat.color} p-3 rounded-xl`}>
                        <stat.icon size={24} />
                      </div>
                    </div>
                    <div>
                      <p className="text-slate-500 text-sm font-medium">{stat.label}</p>
                      <h3 className="text-3xl font-bold mt-1">{loading ? '...' : stat.value}</h3>
                    </div>
                  </div>
                ))}
              </div>

              {/* Chart Section */}
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
                    {loading ? (
                      <div className="h-full w-full bg-slate-50 animate-pulse rounded-xl"></div>
                    ) : (
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
                    )}
                  </div>
                </div>

                <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-bold">Recent Scenarios</h3>
                    <ShieldAlert size={18} className="text-slate-400" />
                  </div>
                  <div className="space-y-3">
                    {loading ? [1, 2, 3, 4, 5].map(i => (
                      <div key={i} className="h-16 bg-slate-50 animate-pulse rounded-xl"></div>
                    )) : scenarios.slice(0, 6).map((s, i) => (
                      <div
                        key={i}
                        onClick={() => setActiveTab('scenarios')}
                        className="flex items-center justify-between p-4 rounded-xl border border-slate-50 hover:bg-slate-50 transition-colors group cursor-pointer"
                      >
                        <div>
                          <p className="font-bold text-sm line-clamp-1">{s.name}</p>
                          <p className="text-xs text-slate-500 uppercase font-medium mt-0.5">{s.category.replace('_', ' ')}</p>
                        </div>
                        <ChevronRight size={16} className="text-slate-300 group-hover:text-indigo-500 transform group-hover:translate-x-1 transition-all" />
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={() => setActiveTab('scenarios')}
                    className="w-full mt-6 text-sm font-semibold text-indigo-600 hover:text-indigo-700 py-2 border-t border-slate-50"
                  >
                    Explore All
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'scenarios' && (
            <div className="animate-in fade-in slide-in-from-bottom-2 duration-500">
              <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
                <div>
                  <h2 className="text-2xl font-bold">Scenario Repository</h2>
                  <p className="text-slate-500">Browse and run stress tests across different categories.</p>
                </div>
                <div className="flex gap-2 bg-white p-1 rounded-xl shadow-sm border border-slate-100">
                  {['all', 'market_crash', 'rate_shock', 'commodity_shock'].map(cat => (
                    <button key={cat} className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-all ${cat === 'all' ? 'bg-indigo-600 text-white shadow-md shadow-indigo-100' : 'text-slate-600 hover:bg-slate-50'}`}>
                      {cat.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {loading ? [1, 2, 3, 4, 5, 6].map(i => (
                  <div key={i} className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm h-64 animate-pulse flex flex-col">
                    <div className="flex justify-between mb-4">
                      <div className="h-6 w-20 bg-slate-100 rounded-full"></div>
                      <div className="h-4 w-4 bg-slate-100 rounded"></div>
                    </div>
                    <div className="h-6 w-3/4 bg-slate-100 rounded mb-4"></div>
                    <div className="h-4 w-full bg-slate-100 rounded mb-2"></div>
                    <div className="h-4 w-5/6 bg-slate-100 rounded mb-6"></div>
                    <div className="mt-auto h-12 w-full bg-slate-100 rounded-xl"></div>
                  </div>
                )) : scenarios.map((scenario) => (
                  <div key={scenario.id} className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-all flex flex-col group">
                    <div className="flex items-center justify-between mb-4">
                      <span className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${scenario.category === 'market_crash' ? 'bg-red-50 text-red-600' :
                        scenario.category === 'rate_shock' ? 'bg-indigo-50 text-indigo-600' :
                          'bg-amber-50 text-amber-600'
                        }`}>
                        {scenario.category.replace('_', ' ')}
                      </span>
                      {scenario.is_predefined && <Settings size={14} className="text-slate-400" />}
                    </div>
                    <h3 className="text-lg font-bold mb-2 group-hover:text-indigo-600 transition-colors">{scenario.name}</h3>
                    <p className="text-slate-600 text-sm mb-6 flex-1 line-clamp-3 leading-relaxed">
                      {scenario.description}
                    </p>
                    <div className="flex flex-wrap gap-2 mb-6">
                      {scenario.tags?.slice(0, 3).map((tag: string) => (
                        <span key={tag} className="text-[10px] bg-slate-50 text-slate-500 px-2 py-0.5 rounded-md border border-slate-100 uppercase font-medium">#{tag}</span>
                      ))}
                    </div>
                    <button
                      onClick={() => handleRunScenario(scenario)}
                      disabled={isSimulating}
                      className="w-full bg-slate-900 text-white py-3 rounded-xl font-bold hover:bg-indigo-600 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      {isSimulating ? <RefreshCcw className="animate-spin" size={16} /> : <Play size={16} fill="currentColor" />}
                      <span>{isSimulating ? 'Running...' : 'Execute Scenario'}</span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'ai-gen' && (
            <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in zoom-in-95 duration-500">
              <div className="bg-white p-8 rounded-3xl shadow-xl border border-slate-100 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-50 rounded-full -mr-32 -mt-32 opacity-50"></div>

                <div className="relative">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="bg-indigo-600 text-white p-2.5 rounded-xl shadow-lg shadow-indigo-200">
                      <Brain size={28} />
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold">AI Scenario Generator</h2>
                      <p className="text-slate-500 text-sm">Powered by GPT-4 and Sonnet 3.5</p>
                    </div>
                  </div>

                  <p className="text-slate-600 mb-8 leading-relaxed text-lg">
                    Describe a market event in plain English. Our engine will synthesize asset shocks,
                    implied volatility shifts, and correlation migrations.
                  </p>

                  <div className="space-y-4">
                    <textarea
                      value={aiPrompt}
                      onChange={(e) => setAiPrompt(e.target.value)}
                      placeholder="e.g., A massive tech decoupling where mega-cap tech stocks crash by 30% but safe-haven bonds and gold rally significantly..."
                      className="w-full h-44 bg-slate-50 border-2 border-slate-100 focus:border-indigo-500 focus:bg-white rounded-2xl p-6 text-lg transition-all outline-none resize-none shadow-inner"
                    />

                    <div className="flex gap-4">
                      <button
                        onClick={handleGenerateAI}
                        disabled={isGenerating || !aiPrompt}
                        className="flex-1 bg-indigo-600 text-white py-4 rounded-xl text-lg font-bold hover:bg-indigo-700 transition-all shadow-xl shadow-indigo-100 flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed group"
                      >
                        {isGenerating ? <RefreshCcw className="animate-spin" size={24} /> : <Zap size={24} className="group-hover:scale-110 transition-transform" />}
                        <span>{isGenerating ? 'Synthesizing Neural Model...' : 'Generate New Scenario'}</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {generatedScenario && (
                <div className="bg-white p-8 rounded-3xl shadow-2xl border border-emerald-100 animate-in slide-in-from-bottom-8 duration-700 relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-2 h-full bg-emerald-500"></div>
                  <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-4">
                      <div className="bg-emerald-100 text-emerald-600 p-2 rounded-lg">
                        <Activity size={24} />
                      </div>
                      <div>
                        <h3 className="text-2xl font-bold text-slate-900">{generatedScenario.name}</h3>
                        <p className="text-emerald-600 text-xs font-bold uppercase tracking-widest mt-1">Generated Stress Model</p>
                      </div>
                    </div>
                    <span className="bg-emerald-50 text-emerald-700 px-5 py-2 rounded-full text-xs font-black uppercase border border-emerald-100">
                      {generatedScenario.category?.replace('_', ' ') || ''}
                    </span>
                  </div>

                  <div className="bg-slate-50 p-6 rounded-2xl mb-8 border border-slate-100">
                    <p className="text-slate-700 text-lg leading-relaxed italic">"{generatedScenario.description}"</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-4">
                      <h4 className="font-black text-slate-400 uppercase tracking-widest text-[10px]">Projected Asset Impacts</h4>
                      <div className="space-y-2 max-h-64 overflow-y-auto pr-2 custom-scrollbar">
                        {generatedScenario.parameters && (Object.entries(generatedScenario.parameters.return_shocks) as [string, number][]).map(([ticker, shock]) => (
                          <div key={ticker} className="flex items-center justify-between p-4 bg-white rounded-xl border border-slate-100 shadow-sm">
                            <div className="flex items-center gap-3">
                              <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs ${shock < 0 ? 'bg-red-50 text-red-500' : 'bg-emerald-50 text-emerald-500'}`}>
                                {ticker[0]}
                              </div>
                              <span className="font-bold text-slate-700 uppercase">{ticker}</span>
                            </div>
                            <span className={`font-black text-lg ${shock < 0 ? 'text-red-500' : 'text-emerald-500'}`}>
                              {shock > 0 ? '+' : ''}{(shock * 100).toFixed(1)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-4">
                      <h4 className="font-black text-slate-400 uppercase tracking-widest text-[10px]">Systemic Configuration</h4>
                      <div className="bg-slate-900 text-white p-8 rounded-2xl shadow-xl">
                        <div className="flex justify-between items-center mb-6">
                          <div className="flex flex-col">
                            <span className="text-indigo-400 font-black text-2xl">x{generatedScenario.parameters?.correlation_multiplier?.toFixed(2) || '1.00'}</span>
                            <span className="text-slate-400 text-xs uppercase tracking-tighter">Correlation Shift</span>
                          </div>
                          <RefreshCcw size={24} className="text-slate-700" />
                        </div>
                        <div className="w-full bg-slate-800 h-3 rounded-full overflow-hidden mb-8">
                          <div
                            className="bg-indigo-500 h-full transition-all duration-1000 shadow-[0_0_15px_rgba(99,102,241,0.5)]"
                            style={{ width: `${((generatedScenario.parameters?.correlation_multiplier || 1) / 2) * 100}%` }}
                          ></div>
                        </div>

                        <div className="space-y-4">
                          <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-xl border border-slate-700/50">
                            <ShieldAlert size={18} className="text-indigo-400" />
                            <span className="text-xs text-slate-300 font-medium">Auto-calibrated volatility surfaces</span>
                          </div>
                          <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-xl border border-slate-700/50">
                            <Play size={18} className="text-emerald-400" />
                            <span className="text-xs text-slate-300 font-medium">Monte Carlo ready ensemble</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={handleRunAISimulation}
                    disabled={isSimulating}
                    className="w-full mt-10 bg-indigo-600 text-white py-5 rounded-2xl text-xl font-black hover:bg-slate-900 transition-all shadow-2xl flex items-center justify-center gap-4"
                  >
                    {isSimulating ? <RefreshCcw className="animate-spin" size={24} /> : <Play size={24} fill="white" />}
                    <span>{isSimulating ? 'SIMULATING ACROSS PATHS...' : 'RUN NEURAL SIMULATION'}</span>
                  </button>
                </div>
              )}
            </div>
          )}

          {activeTab === 'optimizer' && (
            <div className="animate-in fade-in duration-500 max-w-6xl mx-auto">
              <div className="mb-10">
                <h2 className="text-3xl font-extrabold tracking-tight">Portfolio Optimizer</h2>
                <p className="text-slate-500 text-lg">Use Markowitz Mean-Variance Optimization to find defensive asset allocations.</p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                {/* Asset Selector */}
                <div className="lg:col-span-1 border border-slate-200 rounded-3xl p-6 bg-white shadow-sm overflow-hidden flex flex-col h-[600px]">
                  <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
                    <PlusCircle size={18} className="text-indigo-500" />
                    Select Assets
                  </h3>
                  <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-1">
                    {ALL_TICKERS.map(ticker => (
                      <button
                        key={ticker}
                        onClick={() => toggleAsset(ticker)}
                        className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-bold transition-all border-2 ${selectedAssets.includes(ticker)
                          ? 'bg-indigo-50 border-indigo-200 text-indigo-700'
                          : 'bg-white border-transparent text-slate-500 hover:bg-slate-50'
                          }`}
                      >
                        <span>{ticker}</span>
                        {selectedAssets.includes(ticker) && <div className="w-2 h-2 bg-indigo-500 rounded-full"></div>}
                      </button>
                    ))}
                  </div>
                  <button
                    onClick={handleOptimize}
                    disabled={isOptimizing || selectedAssets.length < 2}
                    className="mt-6 w-full bg-slate-900 text-white py-4 rounded-xl font-black flex items-center justify-center gap-2 hover:bg-indigo-600 transition-all disabled:opacity-30"
                  >
                    {isOptimizing ? <RefreshCcw size={18} className="animate-spin" /> : <BarChart3 size={18} />}
                    <span>{isOptimizing ? 'Optimizing...' : 'Run Optimization'}</span>
                  </button>
                </div>

                {/* Results Display */}
                <div className="lg:col-span-3 space-y-8">
                  {!optResults ? (
                    <div className="h-full flex flex-col items-center justify-center text-center p-12 border-2 border-dashed border-slate-200 rounded-3xl bg-slate-50/50">
                      <div className="bg-white p-4 rounded-full shadow-md mb-6">
                        <BarChart3 size={48} className="text-slate-300" />
                      </div>
                      <h4 className="text-xl font-bold text-slate-400">No Optimization Run</h4>
                      <p className="text-slate-400 max-w-xs mt-2">Select assets on the left and click 'Run Optimization' to see results here.</p>
                    </div>
                  ) : (
                    <>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* Maximum Sharpe */}
                        <div className="bg-white p-8 rounded-3xl border border-indigo-100 shadow-xl relative overflow-hidden">
                          <div className="absolute top-0 right-0 bg-indigo-600 text-white px-4 py-1.5 rounded-bl-2xl text-[10px] font-black uppercase tracking-widest">
                            Max Sharpe Ratio
                          </div>
                          <h4 className="text-xl font-black mb-8">Optimal Portfolio</h4>

                          <div className="flex items-center gap-8 mb-8">
                            <div className="flex flex-col">
                              <span className="text-4xl font-black text-indigo-600">{(optResults.max_sharpe.expected_return * 100).toFixed(1)}%</span>
                              <span className="text-xs text-slate-400 font-bold uppercase">Exp. Return</span>
                            </div>
                            <div className="flex flex-col">
                              <span className="text-4xl font-black text-slate-900">{optResults.max_sharpe.sharpe_ratio.toFixed(2)}</span>
                              <span className="text-xs text-slate-400 font-bold uppercase">Sharpe Ratio</span>
                            </div>
                          </div>

                          <div className="space-y-3">
                            {(Object.entries(optResults.max_sharpe.weights) as [string, number][])
                              .sort(([, a], [, b]) => b - a)
                              .filter(([, w]) => w > 0.01)
                              .map(([ticker, weight]) => (
                                <div key={ticker} className="flex flex-col gap-1">
                                  <div className="flex justify-between text-xs font-bold uppercase">
                                    <span>{ticker}</span>
                                    <span className="text-indigo-600">{(weight * 100).toFixed(1)}%</span>
                                  </div>
                                  <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                                    <div className="bg-indigo-500 h-full" style={{ width: `${weight * 100}%` }}></div>
                                  </div>
                                </div>
                              ))}
                          </div>
                        </div>

                        {/* Minimum Volatility */}
                        <div className="bg-slate-900 p-8 rounded-3xl shadow-xl relative overflow-hidden">
                          <div className="absolute top-0 right-0 bg-emerald-500 text-white px-4 py-1.5 rounded-bl-2xl text-[10px] font-black uppercase tracking-widest">
                            Min Volatility
                          </div>
                          <h4 className="text-xl font-black text-white mb-8">Defensive Portfolio</h4>

                          <div className="flex items-center gap-8 mb-8">
                            <div className="flex flex-col">
                              <span className="text-4xl font-black text-emerald-400">{(optResults.min_volatility.volatility * 100).toFixed(1)}%</span>
                              <span className="text-slate-500 text-xs font-bold uppercase">Volatility</span>
                            </div>
                            <div className="flex flex-col">
                              <span className="text-4xl font-black text-white">{(optResults.min_volatility.expected_return * 100).toFixed(1)}%</span>
                              <span className="text-slate-500 text-xs font-bold uppercase">Exp. Return</span>
                            </div>
                          </div>

                          <div className="space-y-3">
                            {(Object.entries(optResults.min_volatility.weights) as [string, number][])
                              .sort(([, a], [, b]) => b - a)
                              .filter(([, w]) => w > 0.01)
                              .map(([ticker, weight]) => (
                                <div key={ticker} className="flex flex-col gap-1">
                                  <div className="flex justify-between text-xs font-bold text-slate-400 uppercase">
                                    <span>{ticker}</span>
                                    <span className="text-emerald-400">{(weight * 100).toFixed(1)}%</span>
                                  </div>
                                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                                    <div className="bg-emerald-500 h-full" style={{ width: `${weight * 100}%` }}></div>
                                  </div>
                                </div>
                              ))}
                          </div>
                        </div>
                      </div>

                      <div className="bg-indigo-50 p-6 rounded-2xl border border-indigo-100 flex items-start gap-4">
                        <ShieldAlert className="text-indigo-600 shrink-0" size={24} />
                        <div>
                          <h5 className="font-bold text-indigo-900 uppercase text-xs tracking-widest mb-1">Defense Recommendation</h5>
                          <p className="text-indigo-700 text-sm leading-relaxed">
                            Based on current market correlations, a shift towards <strong>{
                              Object.entries(optResults.min_volatility.weights)
                                .sort(([, a]: any, [, b]: any) => b - a)[0][0]
                            }</strong> provides the strongest hedge against systemic volatility spikes.
                          </p>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
