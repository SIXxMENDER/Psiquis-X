"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Send, Terminal, Database, Activity, Shield,
  CpuIcon, Layers, Clock, Zap, FileText, ChevronRight,
  Folder, Lock, Cpu, BarChart4, PieChart, FlaskConical, Search,
  ChevronLeft, X, ExternalLink, Download, Trash2, Save, Check,
  Target, Settings, Info, Gauge, Edit3
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

// --- COMPONENTS ---

const GlassPanel = ({ children, className, glow = false, ...props }: any) => (
  <motion.div
    {...props}
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    className={cn(
      "glass-panel rounded-2xl p-6 relative overflow-hidden flex flex-col",
      glow && "neon-border",
      className
    )}
  >
    {children}
  </motion.div>
);

const GlowButton = ({ children, className, onClick, variant = "default", active = false, disabled = false }: any) => {
  const base = "px-6 py-3 rounded-xl font-bold transition-all flex items-center justify-center gap-3 relative overflow-hidden group";
  const styles = {
    default: "bg-brand-emerald/10 text-brand-emerald border border-brand-emerald/30 hover:bg-brand-emerald/20",
    primary: "bg-brand-emerald text-dark-deep hover:bg-white shadow-xl shadow-brand-emerald/20",
    glow: "bg-brand-cyan/10 text-brand-cyan border border-brand-cyan/30 hover:bg-brand-cyan/20",
    ghost: "text-slate-400 hover:text-white hover:bg-white/5",
    danger: "bg-red-500/10 text-red-500 border border-red-500/30 hover:bg-red-500/20"
  };

  return (
    <button
      disabled={disabled}
      onClick={onClick}
      className={cn(base, styles[variant as keyof typeof styles], active && "bg-white/10 text-white border-white/50", disabled && "opacity-50 cursor-not-allowed", className)}
    >
      {children}
    </button>
  );
};

// --- REAL-TIME GRAPH VISUALIZER ---

const NeuralGraph = ({ activeNode, size = "large", topology, onNodeMove, onAddEdge }: { activeNode: string, size?: "large" | "small", topology?: any, onNodeMove?: (topo: any) => void, onAddEdge?: (from: string, to: string) => void }) => {
  const [localNodes, setLocalNodes] = useState<any[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  useEffect(() => {
    if (topology?.nodes) {
      setLocalNodes(topology.nodes);
    }
  }, [topology]);

  const defaultEdges = [
    { from: 'SUPERVISOR', to: 'FINANCE' },
    { from: 'SUPERVISOR', to: 'MARKETING' },
    { from: 'FINANCE', to: 'TRIBUNAL' },
    { from: 'MARKETING', to: 'TRIBUNAL' }
  ];

  const edges = topology?.edges || defaultEdges;
  const svgRef = useRef<SVGSVGElement>(null);

  const handleDrag = (id: string, info: any) => {
    const svgRect = svgRef.current?.getBoundingClientRect();
    if (!svgRect) return;

    // Map screen coordinates to 0-300 SVG coordinate system
    const newX = ((info.point.x - svgRect.left) / svgRect.width) * 300;
    const newY = ((info.point.y - svgRect.top) / svgRect.height) * 300;

    setLocalNodes(prev => prev.map(n =>
      n.id === id ? { ...n, x: Math.max(15, Math.min(285, newX)), y: Math.max(15, Math.min(285, newY)) } : n
    ));
  };

  const handleDragEnd = () => {
    if (onNodeMove) onNodeMove({ ...topology, nodes: localNodes });
  };

  const handleNodeClick = (id: string) => {
    if (!selectedNode) {
      setSelectedNode(id);
    } else if (selectedNode === id) {
      setSelectedNode(null);
    } else {
      if (onAddEdge) onAddEdge(selectedNode, id);
      setSelectedNode(null);
    }
  };

  return (
    <div className="relative w-full h-full flex items-center justify-center bg-black/20 rounded-xl overflow-hidden min-h-[200px]">
      <svg ref={svgRef} className={cn("w-full h-full", size === "large" ? "max-w-[400px]" : "max-w-[250px]")} viewBox="0 0 300 300">
        <defs>
          <filter id="glow_node">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {edges.map((conn: any, i: number) => {
          const from = localNodes.find((n: any) => n.id === conn.from);
          const to = localNodes.find((n: any) => n.id === conn.to);
          if (!from || !to) return null;
          const isActive = activeNode.toLowerCase().includes(conn.from.toLowerCase()) || activeNode.toLowerCase().includes(conn.to.toLowerCase());
          return (
            <motion.line
              key={`${conn.from}-${conn.to}`}
              x1={from.x} y1={from.y} x2={to.x} y2={to.y}
              stroke={isActive ? "#10b981" : "#1e293b"}
              strokeWidth={isActive ? 2 : 1}
              animate={{ x1: from.x, y1: from.y, x2: to.x, y2: to.y }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
            />
          );
        })}

        {localNodes.map((node: any) => {
          const isActive = activeNode.toLowerCase().includes(node.id.toLowerCase());
          const isSelected = selectedNode === node.id;
          const Icon = ({
            'SUPERVISOR': CpuIcon,
            'FINANCE': BarChart4,
            'MARKETING': PieChart,
            'TRIBUNAL': Shield,
            'ESTRATEGA': Target
          } as any)[node.id] || Cpu;

          return (
            <motion.g
              key={node.id}
              drag={isSelected}
              dragMomentum={false}
              onDrag={(_, info) => handleDrag(node.id, info)}
              onDragEnd={handleDragEnd}
              onDoubleClick={(e) => {
                e.stopPropagation();
                handleNodeClick(node.id);
              }}
              initial={false}
              animate={{ x: node.x, y: node.y, scale: isSelected ? 1.2 : 1 }}
              transition={{ type: "spring", stiffness: 400, damping: 40 }}
              style={{ cursor: isSelected ? 'grabbing' : 'pointer' }}
            >
              <circle
                r={size === "large" ? 20 : 14}
                fill={isSelected ? "#3b82f6" : (isActive ? "#10b981" : "#0f172a")}
                stroke={isSelected ? "#60a5fa" : (isActive ? "#34d399" : "#1e293b")}
                strokeWidth="2"
                filter={(isActive || isSelected) ? "url(#glow_node)" : ""}
              />
              <Icon
                x={size === "large" ? -10 : -7}
                y={size === "large" ? -10 : -7}
                width={size === "large" ? 20 : 14}
                height={size === "large" ? 20 : 14}
                className={isSelected ? "text-white" : (isActive ? "text-dark-deep" : "text-brand-cyan/60")}
              />
              <text
                y={size === "large" ? 40 : 30}
                textAnchor="middle"
                className="fill-slate-400 font-mono text-[9px] font-bold uppercase tracking-widest pointer-events-none"
              >
                {node.label || node.id}
              </text>
            </motion.g>
          );
        })}
      </svg>
      {selectedNode && (
        <div className="absolute top-4 left-4 text-[10px] font-mono text-blue-400 animate-pulse bg-blue-500/10 px-2 py-1 rounded">
          MODO ENLACE: Selecciona nodo destino
        </div>
      )}
    </div>
  );
};

// --- VIEWS ---

const VaultView = ({ onOpenFile, API_URL, refreshTrigger }: any) => {
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [folders, setFolders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchVault = () => {
    setLoading(true);
    fetch(`${API_URL}/api/vault/list`)
      .then(res => res.json())
      .then(data => {
        setFolders(data.folders || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    fetchVault();
  }, [API_URL, refreshTrigger]);

  const handleDelete = async (e: React.MouseEvent, path: string) => {
    e.stopPropagation();
    if (!confirm(`¿Confirmas la eliminación definitiva de ${path}?`)) return;
    try {
      await fetch(`${API_URL}/api/vault/delete?path=${path}`, { method: 'DELETE' });
      fetchVault();
    } catch (e) { }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0] || !selectedFolder) return;
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append('file', file);

    try {
      const resp = await fetch(`${API_URL}/api/vault/upload?folder=${selectedFolder}`, {
        method: 'POST',
        body: formData
      });
      const data = await resp.json();
      if (data.status === 'SUCCESS') fetchVault();
      else alert("Error en subida: " + data.message);
    } catch (e) { alert("Error de conexión"); }
  };

  const handleRename = async (e: React.MouseEvent, folderPath: string, fileName: string) => {
    e.stopPropagation();
    const newName = prompt("Nuevo nombre para " + fileName + ":", fileName);
    if (!newName || newName === fileName) return;

    try {
      const resp = await fetch(`${API_URL}/api/vault/rename`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ old_path: `${folderPath}/${fileName}`, new_path: `${folderPath}/${newName}` })
      });
      const data = await resp.json();
      if (data.status === 'SUCCESS') fetchVault();
      else alert("Error al renombrar: " + data.message);
    } catch (e) { alert("Error de conexión"); }
  };

  if (loading) return <div className="flex-1 flex items-center justify-center text-brand-emerald animate-pulse">SINCRONIZANDO NÚCLEO...</div>;

  if (selectedFolder) {
    const folder = folders.find(f => f.path === selectedFolder);
    return (
      <div className="space-y-6 flex-1 flex flex-col h-full overflow-hidden">
        <div className="flex justify-between items-center shrink-0">
          <button onClick={() => setSelectedFolder(null)} className="flex items-center gap-2 text-brand-emerald text-sm hover:underline">
            <ChevronLeft className="w-4 h-4" /> VOLVER A DATA/
          </button>
          <div className="flex gap-4">
            <input type="file" ref={fileInputRef} onChange={handleUpload} className="hidden" />
            <GlowButton variant="glow" className="h-8 px-4 text-[10px]" onClick={() => fileInputRef.current?.click()}>
              <Download className="w-3 h-3 rotate-180" /> SUBIR ARCHIVO
            </GlowButton>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 overflow-y-auto scrollbar-hide p-1">
          {folder?.files.map((file: string) => {
            const isImage = /\.(png|jpg|jpeg|gif|webp)$/i.test(file);
            const fullPath = `${folder.path}${folder.path ? '/' : ''}${file}`;

            return (
              <GlassPanel
                key={file}
                className="aspect-square p-4 flex flex-col items-center justify-center hover:neon-border cursor-pointer transition-all group relative"
                onClick={() => onOpenFile(fullPath)}
              >
                {isImage ? (
                  <div className="w-full h-24 overflow-hidden rounded-lg mb-4 flex items-center justify-center bg-black/40">
                    <img
                      src={`${API_URL}/data/${fullPath}`}
                      alt={file}
                      className="w-full h-full object-cover group-hover:scale-110 transition-all font-sans"
                      onError={(e: any) => { e.target.src = ""; e.target.className = "hidden"; }}
                    />
                  </div>
                ) : (
                  <FileText className="w-12 h-12 text-brand-cyan mb-4" />
                )}
                <div className="text-[10px] font-mono text-center truncate w-full px-2 uppercase">{file}</div>

                <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-all">
                  <button onClick={(e) => handleRename(e, folder.path, file)} className="p-2 bg-brand-cyan/10 text-brand-cyan rounded-lg hover:bg-brand-cyan hover:text-white">
                    <Edit3 className="w-3 h-3" />
                  </button>
                  <button onClick={(e) => handleDelete(e, `${folder.path}/${file}`)} className="p-2 bg-red-500/10 text-red-500 rounded-lg hover:bg-red-500 hover:text-white">
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </GlassPanel>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 flex-1 overflow-y-auto scrollbar-hide">
      {folders.map(f => (
        <GlassPanel key={f.path} className="h-48 hover:neon-border cursor-pointer group" onClick={() => setSelectedFolder(f.path)}>
          <Folder className="w-10 h-10 text-brand-emerald mb-4 group-hover:scale-110 transition-all pointer-events-none" />
          <h3 className="font-bold pointer-events-none">{f.name}</h3>
          <p className="text-[9px] text-slate-500 font-mono mt-2 uppercase pointer-events-none">{f.files.length} ELEMENTOS</p>
        </GlassPanel>
      ))}
    </div>
  );
};

// --- MAIN LAYOUT ---

export default function PsiquisApp() {
  const [entered, setEntered] = useState(false);
  const [activeTab, setActiveTab] = useState("chat");
  const [messages, setMessages] = useState<{ role: 'user' | 'ai', content: string }[]>([]);
  const [input, setInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [liveLog, setLiveLog] = useState<string[]>(["Initializing Sovereign Engine...", "Neural Uplink Stable.", "Awaiting Instruction..."]);
  const [graphState, setGraphState] = useState("supervisor");
  const [sseStatus, setSseStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const [viewingFile, setViewingFile] = useState<any>(null);
  const [editContent, setEditContent] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [vaultRefresh, setVaultRefresh] = useState(0);

  // SESSION STATS
  const [stats, setStats] = useState({ tokens: 1240, cost: 0.031 });
  const [identity, setIdentity] = useState<any>(null);
  const [topology, setTopology] = useState<any>(null);

  const API_URL = 'http://localhost:8001';

  const fetchStats = () => {
    fetch(`${API_URL}/api/system/stats`)
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(() => { });
  };

  const fetchIdentity = () => {
    fetch(`${API_URL}/api/system/identity`)
      .then(res => res.json())
      .then(data => setIdentity(data))
      .catch(() => { });
  };

  const fetchTopology = () => {
    fetch(`${API_URL}/api/system/topology`)
      .then(res => res.json())
      .then(data => setTopology(data))
      .catch(() => { });
  };

  useEffect(() => {
    if (!entered) return;
    fetchStats();
    fetchIdentity();
    fetchTopology();
    const interval = setInterval(fetchStats, 2000);

    const evtSource = new EventSource(`${API_URL}/stream/mission`);
    evtSource.onopen = () => setSseStatus('connected');
    evtSource.onmessage = (event) => {
      if (!event.data || event.data === ": keep-alive") return;
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'thought') setLiveLog(prev => [...prev, data.data].slice(-50));
        if (data.type === 'graph_update') setGraphState(data.node);
        fetchStats();
      } catch (e) { }
    };
    evtSource.onerror = () => setSseStatus('error');
    return () => {
      evtSource.close();
      clearInterval(interval);
    };
  }, [entered]);

  const handleSend = async () => {
    if (!input.trim() || isProcessing) return;
    const userMsg = input;
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput("");
    setIsProcessing(true);
    setLiveLog(prev => [...prev, `> Neural Request: ${userMsg}`]);

    try {
      const resp = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg })
      });
      const data = await resp.json();
      setMessages(prev => [...prev, { role: 'ai', content: data.response }]);
      fetchStats();
    } catch (e) {
      setMessages(prev => [...prev, { role: 'ai', content: "CRITICAL_ERROR: Connection Reset by Peer." }]);
    } finally { setIsProcessing(false); }
  };

  const openFileContent = async (path: string) => {
    try {
      const res = await fetch(`${API_URL}/api/vault/read?path=${path}`);
      const data = await res.json();
      setViewingFile({ path, name: path.split('/').pop(), content: data.content });
      setEditContent(data.content);
    } catch (e) {
      alert("Error al abrir el archivo.");
    }
  };

  const handleSaveFile = async () => {
    if (!viewingFile || isSaving) return;
    setIsSaving(true);
    try {
      const resp = await fetch(`${API_URL}/api/vault/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: viewingFile.path, content: editContent })
      });
      const data = await resp.json();
      if (data.status === 'SUCCESS') {
        setViewingFile({ ...viewingFile, content: editContent });
        alert("Sincronización Exitosa.");
      } else {
        alert("Error de Escritura.");
      }
    } catch (e) {
      alert("Error de Conexión.");
    } finally { setIsSaving(false); }
  };

  const updateIdentity = async () => {
    if (!identity) return;
    setIsSaving(true);
    try {
      await fetch(`${API_URL}/api/system/identity`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(identity)
      });
      alert("Personalidad Neural Actualizada.");
    } catch (e) {
      alert("Error de Sincronización.");
    } finally { setIsSaving(false); }
  };

  const updateTopology = async (newTopo: any) => {
    setTopology(newTopo);
    try {
      await fetch(`${API_URL}/api/system/topology`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTopo)
      });
    } catch (e) { }
  };

  const addEdge = (from: string, to: string) => {
    if (from === to) return;
    const exists = topology?.edges?.some((e: any) =>
      (e.from === from && e.to === to) || (e.from === to && e.to === from)
    );
    if (exists) return;

    updateTopology({
      ...topology,
      edges: [...(topology?.edges || []), { from, to }]
    });
  };

  const [isExecuting, setIsExecuting] = useState(false);

  const executeSovereign = async () => {
    if (isExecuting) return;
    setIsExecuting(true);

    // FIND THE REAL OBJECTIVE (Last User Message)
    // We reverse the array to find the most recent user message
    const lastUserMsg = [...messages].reverse().find(m => m.role === 'user');
    const objective = lastUserMsg?.content || "System Integrity Audit";

    try {
      setLiveLog(prev => [...prev, `🚀 INITIATING SOVEREIGN PROTOCOL: ${objective.substring(0, 50)}...`]);
      await fetch(`${API_URL}/api/sovereign/launch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ objetivo: objective, mode: "efficient" })
      });
      // Note: We do NOT set isExecuting to false here because the user wants it blocked "al primer log".
      // It will remain blocked until page refresh, effectively enforcing "one mission at a time".
    } catch (e) {
      setIsExecuting(false); // Only re-enable on network error
    }
  };

  if (!entered) return (
    <div className="h-screen w-full bg-dark-deep grid-bg flex flex-col items-center justify-center relative overflow-hidden">
      <div className="scanline" />
      <motion.div animate={{ opacity: [0, 1, 0.8, 1], scale: [0.95, 1] }} className="text-center">
        <h1 className="text-9xl font-black tracking-[0.3em] text-white drop-shadow-[0_0_30px_rgba(255,255,255,0.4)] mb-12">
          PSIQUIS-X
        </h1>
        <GlowButton onClick={() => setEntered(true)} variant="primary" className="h-24 w-96 text-2xl tracking-widest">
          <Shield className="w-8 h-8" /> ENLACE NEURAL
        </GlowButton>
      </motion.div>
    </div>
  );

  return (
    <div className="h-screen bg-dark-deep text-slate-200 flex overflow-hidden font-sans grid-bg">
      {/* SIDEBAR CENTRAL */}
      <aside className="w-72 border-r border-white/5 bg-slate-950/80 backdrop-blur-3xl flex flex-col p-6 z-30 shadow-2xl relative">
        <div className="flex items-center gap-3 mb-16 px-1">
          <CpuIcon className="text-brand-emerald w-8 h-8 emerald-glow" />
          <span className="font-black text-2xl tracking-tighter">PSIQUIS-X</span>
        </div>
        <nav className="flex-1 space-y-4">
          {[
            { id: 'chat', icon: Activity, label: 'Dynamic Command' },
            { id: 'terminal', icon: Terminal, label: 'System Trace' },
            { id: 'vault', icon: Database, label: 'Knowledge Vault' },
            { id: 'history', icon: Clock, label: 'Mission History' },
            { id: 'neural', icon: Target, label: 'Neural Tuning' }
          ].map(tab => (
            <NavButton
              key={tab.id} icon={tab.icon} label={tab.label}
              active={activeTab === tab.id} onClick={() => setActiveTab(tab.id)}
            />
          ))}
        </nav>
        <div className="pt-8 border-t border-white/5 flex flex-col gap-4">
          <div className="flex items-center gap-3 text-[10px] font-mono text-slate-500">
            <div className={cn("w-2 h-2 rounded-full", sseStatus === 'connected' ? "bg-brand-emerald animate-pulse" : "bg-red-500")} />
            CORE_UPLINK: {sseStatus.toUpperCase()}
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 flex flex-col relative">
        <header className="h-24 border-b border-white/5 flex items-center justify-between px-10 bg-dark-deep/40 backdrop-blur-xl z-20">
          <div>
            <h2 className="text-[10px] font-mono text-brand-emerald opacity-50 tracking-[0.5em] uppercase">Sovereign Control</h2>
            <div className="font-black text-2xl tracking-tighter uppercase">{activeTab.replace('_', ' ')} OVERVIEW</div>
          </div>

          {/* FUEL MONITOR HUD */}
          <div className="flex items-center gap-10 bg-black/40 px-8 py-3 rounded-2xl border border-white/5 shadow-inner">
            <div className="flex flex-col items-center">
              <span className="text-[9px] font-mono text-slate-500 uppercase flex items-center gap-2"><Gauge className="w-3 h-3" /> CONSUMO_TOKENS</span>
              <span className="text-sm font-black text-brand-cyan tracking-widest">{stats.tokens.toLocaleString()}</span>
            </div>
            <div className="w-px h-8 bg-white/10" />
            <div className="flex flex-col items-center">
              <span className="text-[9px] font-mono text-slate-500 uppercase flex items-center gap-2"><Zap className="w-3 h-3" /> COSTO_SESIÓN</span>
              <span className="text-sm font-black text-brand-emerald tracking-widest">${stats.cost.toFixed(5)}</span>
            </div>
          </div>

          <div className="flex gap-4">
            {activeTab === 'chat' && (
              <GlowButton
                variant={isExecuting ? "ghost" : "glow"}
                onClick={executeSovereign}
                className="text-sm px-8"
                disabled={isExecuting}
              >
                {isExecuting ? <Activity className="w-5 h-5 animate-spin" /> : <Zap className="w-5 h-5 fill-current" />}
                {isExecuting ? "PROTOCOL ACTIVE" : "EXECUTE SOVEREIGN"}
              </GlowButton>
            )}
          </div>
        </header>

        <div className="flex-1 overflow-hidden p-10 flex gap-10 h-full">
          {/* CONTENT SWITCHER */}
          <div className="flex-1 flex flex-col h-full overflow-hidden">
            <AnimatePresence mode="wait">
              {activeTab === 'chat' && (
                <GlassPanel key="chat" className="flex-1 p-0 border-white/5 h-full" glow>
                  <div className="flex-1 overflow-y-auto p-10 space-y-8 scrollbar-hide min-h-0">
                    {messages.map((m, i) => (
                      <motion.div initial={{ opacity: 0, x: m.role === 'user' ? 20 : -20 }} animate={{ opacity: 1, x: 0 }} key={i} className={cn("flex", m.role === 'user' ? "justify-end" : "justify-start")}>
                        <div className={cn("p-6 rounded-2xl text-sm max-w-[75%] shadow-2xl leading-relaxed", m.role === 'user' ? "bg-brand-emerald/10 text-brand-emerald border border-brand-emerald/30" : "bg-white/5 border border-white/10 text-slate-200")}>
                          {m.content}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                  <div className="p-6 bg-black/40 border-t border-white/10 flex gap-6 shrink-0">
                    <textarea
                      value={input} onChange={e => setInput(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
                      placeholder="Escribe una instrucción para el comando dinámico..."
                      className="flex-1 bg-black/60 border border-white/5 rounded-2xl p-6 text-sm focus:border-brand-emerald/50 focus:ring-0 resize-none h-20 transition-all font-mono shadow-inner"
                    />
                    <GlowButton onClick={handleSend} variant="primary" className="w-20 h-20 p-0 text-dark-deep">
                      <Send className="w-8 h-8" />
                    </GlowButton>
                  </div>
                </GlassPanel>
              )}

              {activeTab === 'terminal' && (
                <div key="system" className="flex-1 flex flex-col gap-8 h-full">
                  <div className="flex gap-8 h-full min-h-0">
                    <GlassPanel className="flex-1 bg-black/60 font-mono text-[11px] text-brand-emerald/90 p-8 border-brand-emerald/10 h-full shadow-inner overflow-hidden flex flex-col">
                      <div className="mb-4 text-brand-cyan border-b border-brand-cyan/20 pb-2 flex justify-between shrink-0">
                        <span>[ PSIQUIS_X KERNEL TRACE ]</span>
                        <span className="animate-pulse">ONLINE</span>
                      </div>
                      <div className="flex-1 overflow-y-auto scrollbar-hide space-y-1">
                        {liveLog.map((log, i) => <div key={i} className="flex gap-3"><span className="opacity-30">{new Date().toLocaleTimeString()}</span> <span className="text-white/20">{">"}</span> {log}</div>)}
                        <div className="w-2 h-4 bg-brand-emerald animate-pulse inline-block" />
                      </div>
                    </GlassPanel>
                    <GlassPanel className="w-[450px] p-0 h-full overflow-hidden flex flex-col" glow>
                      <div className="p-4 border-b border-white/5 text-center font-mono text-[10px] text-slate-500 tracking-[0.4em]">TOPOLOGY_CORE</div>
                      <div className="flex-1 p-6 flex flex-col">
                        {/* <NeuralGraph activeNode={graphState} size="large" topology={topology} onNodeMove={updateTopology} onAddEdge={addEdge} /> */}
                      </div>
                    </GlassPanel>
                  </div>
                </div>
              )}

              {activeTab === 'vault' && (
                <div key="vault" className="h-full flex flex-col">
                  <VaultView API_URL={API_URL} onOpenFile={(f: string) => openFileContent(f)} refreshTrigger={vaultRefresh} />
                </div>
              )}

              {activeTab === 'history' && (
                <div key="history" className="space-y-6 overflow-y-auto scrollbar-hide h-full">
                  {['finance/consolidated_1768532188.md', 'marketing/catalog_20260113_184738.md', 'portfolio/mvp_platinum_architecture.md'].map((path, i) => (
                    <GlassPanel key={i} className="flex-row items-center gap-10 p-8 hover:neon-border transition-all group">
                      <div className="w-16 h-16 bg-brand-emerald/10 rounded-2xl flex items-center justify-center text-brand-emerald shrink-0">
                        <FileText className="w-8 h-8" />
                      </div>
                      <div className="flex-1">
                        <h3 className="text-lg font-bold">{path.split('/').pop()}</h3>
                        <p className="text-[10px] font-mono text-slate-500 uppercase">PATH: {path}</p>
                      </div>
                      <GlowButton variant="glow" onClick={() => openFileContent(path)}>EDIT REPORTE</GlowButton>
                    </GlassPanel>
                  ))}
                </div>
              )}

              {activeTab === 'neural' && (
                <div key="neural" className="flex-1 flex flex-col gap-8 h-full overflow-y-auto scrollbar-hide pb-10">
                  <div className="grid grid-cols-2 gap-8 shrink-0">
                    {/* MAESTRO GOAL */}
                    <GlassPanel glow className="gap-6 bg-slate-900/40">
                      <div className="flex items-center gap-4 text-brand-emerald">
                        <Target className="w-8 h-8" />
                        <h3 className="font-black text-xl tracking-tighter uppercase">Propósito Maestro</h3>
                      </div>
                      <textarea
                        value={identity?.master_goal || ""}
                        onChange={e => setIdentity((prev: any) => ({ ...(prev || {}), master_goal: e.target.value }))}
                        className="flex-1 bg-black/60 border border-white/5 rounded-xl p-6 text-sm font-serif italic leading-relaxed focus:border-brand-emerald/50 min-h-[150px] resize-none"
                      />
                    </GlassPanel>

                    {/* PERSONALITY TRAITS */}
                    <GlassPanel className="gap-6 bg-slate-900/40">
                      <div className="flex items-center gap-4 text-brand-cyan">
                        <Settings className="w-8 h-8" />
                        <h3 className="font-black text-xl tracking-tighter uppercase">Rasgos de Personalidad</h3>
                      </div>
                      <div className="flex flex-wrap gap-3 overflow-y-auto max-h-[120px] scrollbar-hide">
                        {identity?.personality?.traits.map((trait: string, i: number) => (
                          <div key={i} className="px-4 py-2 bg-brand-cyan/10 border border-brand-cyan/30 text-brand-cyan rounded-full text-[10px] font-mono flex items-center gap-3 uppercase">
                            {trait}
                            <button onClick={() => {
                              const newTraits = [...identity.personality.traits];
                              newTraits.splice(i, 1);
                              setIdentity({ ...identity, personality: { ...identity.personality, traits: newTraits } });
                            }} className="hover:text-white"><X className="w-3 h-3" /></button>
                          </div>
                        ))}
                      </div>
                      <button
                        onClick={() => {
                          const trait = prompt("Nuevo Rasgo:");
                          if (trait) setIdentity({ ...identity, personality: { ...identity.personality, traits: [...identity.personality.traits, trait.toUpperCase()] } });
                        }}
                        className="mt-4 px-4 py-2 bg-white/5 border border-white/10 text-slate-500 rounded-full text-[10px] font-mono hover:text-white transition-all uppercase w-fit"
                      >
                        + AÑADIR RASGO
                      </button>
                    </GlassPanel>
                  </div>

                  {/* VISUAL ORCHESTRATOR BRIDGE */}
                  <GlassPanel className="p-0 overflow-hidden bg-black/40 min-h-[300px]" glow>
                    <div className="p-4 border-b border-white/5 text-center font-mono text-[10px] text-slate-500 tracking-[0.4em]">ORQUESTADOR_NEURAL_VIVO</div>
                    <div className="flex-1 p-10 flex items-center justify-center">
                      {/* <NeuralGraph activeNode={graphState} size="large" topology={topology} onNodeMove={updateTopology} onAddEdge={addEdge} /> */}
                    </div>
                  </GlassPanel>

                  {/* TOPOLOGY EDITOR */}
                  <div className="grid grid-cols-2 gap-8 shrink-0">
                    <GlassPanel className="gap-6 bg-slate-900/40 shrink-0">
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-4 text-brand-cyan">
                          <Layers className="w-8 h-8" />
                          <h3 className="font-black text-xl tracking-tighter uppercase">Nodos del Sistema</h3>
                        </div>
                        <GlowButton variant="glow" className="h-8 px-4 text-[9px]" onClick={() => {
                          const name = prompt("Nombre del Nuevo Nodo:");
                          if (name) {
                            const newId = name.toUpperCase().replace(/\s+/g, '_');
                            updateTopology({
                              ...topology,
                              nodes: [...(topology?.nodes || []), { id: newId, label: name.toUpperCase(), type: 'worker', x: 150, y: 150 }]
                            });
                          }
                        }}>+ CREAR NODO</GlowButton>
                      </div>
                      <div className="space-y-3 overflow-y-auto max-h-[300px] pr-2 scrollbar-hide">
                        {topology?.nodes?.map((node: any, i: number) => (
                          <div key={node.id} className="flex items-center gap-4 bg-black/40 p-4 rounded-xl border border-white/5 hover:border-brand-emerald/20 transition-all">
                            <div className="w-8 h-8 bg-brand-emerald/10 text-brand-emerald flex items-center justify-center rounded-lg font-mono text-[10px]">{i + 1}</div>
                            <input
                              value={node.label}
                              onChange={(e) => {
                                const newNodes = [...topology.nodes];
                                newNodes[i] = { ...newNodes[i], label: e.target.value.toUpperCase() };
                                updateTopology({ ...topology, nodes: newNodes });
                              }}
                              className="flex-1 bg-transparent border-none text-xs font-bold tracking-widest uppercase focus:ring-0 text-white outline-none"
                            />
                            <button onClick={() => {
                              if (confirm(`¿Eliminar nodo ${node.id}?`)) {
                                updateTopology({
                                  ...topology,
                                  nodes: topology.nodes.filter((n: any) => n.id !== node.id),
                                  edges: topology.edges.filter((e: any) => e.from !== node.id && e.to !== node.id)
                                });
                              }
                            }} className="text-red-500/50 hover:text-red-500 p-2"><Trash2 className="w-4 h-4" /></button>
                          </div>
                        ))}
                      </div>
                    </GlassPanel>

                    <GlassPanel className="gap-6 bg-slate-900/40 shrink-0">
                      <div className="flex items-center gap-4 text-brand-cyan">
                        <Zap className="w-8 h-8" />
                        <h3 className="font-black text-xl tracking-tighter uppercase">Conexiones Neurales</h3>
                      </div>
                      <div className="space-y-3 overflow-y-auto max-h-[300px] pr-2 scrollbar-hide">
                        {topology?.edges?.map((edge: any, i: number) => (
                          <div key={i} className="flex items-center gap-3 bg-black/20 p-3 rounded-lg border border-white/5 font-mono text-[10px]">
                            <span className="text-brand-emerald">{edge.from}</span>
                            <ChevronRight className="w-3 h-3 text-slate-600" />
                            <span className="text-brand-cyan">{edge.to}</span>
                            <button onClick={() => {
                              const newEdges = [...topology.edges];
                              newEdges.splice(i, 1);
                              updateTopology({ ...topology, edges: newEdges });
                            }} className="ml-auto text-slate-600 hover:text-red-500"><X className="w-3 h-3" /></button>
                          </div>
                        ))}
                        <GlowButton variant="ghost" className="w-full h-10 text-[9px] border-dashed border-white/10" onClick={() => {
                          const from = prompt("ID del Nodo Origen (ej: SUPERVISOR):");
                          const to = prompt("ID del Nodo Destino (ej: FINANCE):");
                          if (from && to) {
                            updateTopology({ ...topology, edges: [...(topology?.edges || []), { from: from.toUpperCase(), to: to.toUpperCase() }] });
                          }
                        }}>+ AÑADIR CONEXIÓN</GlowButton>
                      </div>
                    </GlassPanel>
                  </div>

                  {/* SYNC BUTTON */}
                  <GlassPanel className="p-0 overflow-hidden bg-black/20 shrink-0">
                    <div className="p-8 flex items-center justify-between border-b border-white/5">
                      <div>
                        <h4 className="font-black text-lg tracking-tighter uppercase">Sincronización Neural</h4>
                        <p className="text-[10px] font-mono text-slate-500 uppercase">Aplica cambios de comportamiento al núcleo del motor</p>
                      </div>
                      <GlowButton variant="primary" onClick={updateIdentity} disabled={isSaving}>
                        {isSaving ? <Activity className="w-5 h-5 animate-spin" /> : <Save className="w-5 h-5" />} {isSaving ? "SINCRONIZANDO..." : "SINCRO_NÚCLEO EN VIVO"}
                      </GlowButton>
                    </div>
                  </GlassPanel>
                </div>
              )}
            </AnimatePresence>
          </div>

          {/* SIDEBAR DERECHO CONDICIONAL (SOLO EN CHAT) */}
          <AnimatePresence>
            {activeTab === 'chat' && (
              <motion.aside
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: 320, opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                className="flex flex-col gap-8 overflow-hidden h-full shrink-0"
              >
                <GlassPanel className="h-2/5 p-0 shadow-2xl" glow>
                  <div className="p-4 border-b border-white/5 font-mono text-[9px] text-slate-500 uppercase tracking-widest flex justify-between">
                    <span>Real-time Trace</span>
                    <div className="w-1.5 h-1.5 rounded-full bg-brand-emerald animate-pulse" />
                  </div>
                  <div className="flex-1 overflow-y-auto p-5 font-mono text-[9px] text-brand-cyan/70 space-y-2 scrollbar-hide">
                    {liveLog.slice(-12).map((log, i) => <div key={i} className="flex gap-2 leading-relaxed tracking-tighter"><span className="opacity-30">#</span> {log}</div>)}
                  </div>
                </GlassPanel>
                <GlassPanel className="flex-1 p-0 flex flex-col bg-black/40 h-full shadow-2xl">
                  <div className="p-4 border-b border-white/5 font-mono text-[9px] text-slate-500 uppercase tracking-widest text-center">Neural Nodes</div>
                  <div className="flex-1 p-4 flex items-center justify-center scale-90">
                    <NeuralGraph activeNode={graphState} size="small" topology={topology} onNodeMove={updateTopology} onAddEdge={addEdge} />
                  </div>
                </GlassPanel>
              </motion.aside>
            )}
          </AnimatePresence>
        </div >
      </main >

      {/* COMMAND CENTER EDITOR MODAL */}
      <AnimatePresence>
        {
          viewingFile && (
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 bg-black/95 backdrop-blur-3xl flex items-center justify-center p-10"
            >
              <motion.div
                initial={{ scale: 0.9, y: 50 }} animate={{ scale: 1, y: 0 }}
                className="w-full max-w-6xl h-full max-h-[90vh] bg-slate-950 border border-white/10 rounded-3xl overflow-hidden flex flex-col shadow-[0_0_150px_rgba(0,0,0,1)]"
              >
                <div className="h-20 border-b border-white/5 px-10 flex items-center justify-between bg-slate-900/50">
                  <div className="flex items-center gap-4 text-brand-emerald">
                    <FileText className="w-6 h-6" />
                    <span className="font-mono text-sm tracking-widest uppercase">{viewingFile.name} (MODO COMANDO)</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <GlowButton variant="default" onClick={handleSaveFile} disabled={isSaving} className="h-10 px-6">
                      {isSaving ? <Activity className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} {isSaving ? "GUARDANDO..." : "GUARDAR CAMBIOS"}
                    </GlowButton>
                    <button onClick={() => setViewingFile(null)} className="p-2 hover:bg-white/10 rounded-full transition-all text-slate-500 hover:text-white">
                      <X className="w-8 h-8" />
                    </button>
                  </div>
                </div>

                <div className="flex-1 flex overflow-hidden">
                  {/* EDITOR PANEL / IMAGE VIEWER */}
                  <div className="flex-1 relative bg-black/20 p-8 border-r border-white/5 flex items-center justify-center overflow-auto">
                    {/\.(png|jpg|jpeg|gif|webp)$/i.test(viewingFile.path) ? (
                      <div className="max-w-full max-h-full flex flex-col items-center gap-4">
                        <img
                          src={`${API_URL}/data/${viewingFile.path}`}
                          alt={viewingFile.name}
                          className="max-w-full max-h-[70vh] rounded-xl shadow-2xl border border-white/10"
                        />
                        <div className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">{viewingFile.path}</div>
                      </div>
                    ) : (
                      <>
                        <div className="absolute top-4 right-8 text-[10px] font-mono text-slate-600 uppercase">Markdown Core</div>
                        <textarea
                          value={editContent} onChange={e => setEditContent(e.target.value)}
                          className="w-full h-full bg-transparent border-none focus:ring-0 text-slate-300 font-mono text-sm leading-loose resize-none scrollbar-hide"
                          placeholder="Inicia la edición del conocimiento soberano..."
                        />
                      </>
                    )}
                  </div>
                  {/* PREVIEW/HELP PANEL */}
                  <div className="w-80 bg-slate-900/20 p-8 flex flex-col gap-6">
                    <h4 className="text-[10px] font-mono text-brand-emerald uppercase tracking-widest">Atajos de Mando</h4>
                    <div className="space-y-4">
                      {[
                        { icon: Check, label: 'Guardado Instantáneo', desc: 'Sync con disco' },
                        { icon: Download, label: 'Exportación Binaria', desc: 'Próximamente' },
                        { icon: Shield, label: 'Integridad de Datos', desc: 'Soberanía Total' }
                      ].map((item, i) => (
                        <div key={i} className="flex gap-3 items-start">
                          <item.icon className="w-4 h-4 text-brand-cyan mt-1" />
                          <div>
                            <div className="text-xs font-bold">{item.label}</div>
                            <div className="text-[9px] text-slate-500 uppercase">{item.desc}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="mt-auto p-4 bg-brand-emerald/5 border border-brand-emerald/20 rounded-xl text-[10px] text-brand-emerald/70 font-mono leading-relaxed">
                      Cualquier cambio realizado aquí se verá reflejado en las misiones futuras del motor.
                    </div>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )
        }
      </AnimatePresence >
    </div >
  );
}

const NavButton = ({ icon: Icon, label, active, onClick }: any) => (
  <button
    onClick={onClick}
    className={cn(
      "w-full flex items-center gap-4 px-6 py-5 rounded-2xl text-[13px] tracking-tight transition-all relative group shadow-sm",
      active ? "bg-brand-emerald text-dark-deep font-black shadow-brand-emerald/20 opacity-100" : "text-slate-500 hover:text-white hover:bg-white/5 opacity-80"
    )}
  >
    <Icon className={cn("w-6 h-6", active ? "text-dark-deep" : "text-brand-emerald/40 group-hover:text-brand-emerald")} />
    <span className="truncate">{label}</span>
    {active && <motion.div layoutId="nav-pill" className="absolute left-0 w-1.5 h-8 bg-white rounded-r-full shadow-[0_0_10px_white]" />}
  </button>
);
