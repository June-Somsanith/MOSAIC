import React, { useState, useMemo } from 'react';
import Plot from 'react-plotly.js';
import { Activity, AlertTriangle, Dna, Database, X, Plus, Play } from 'lucide-react';

export default function App() {
  // --- STATE MANAGEMENT ---
  const [studies, setStudies] = useState(['OSD-379', 'OSD-137']);
  const [inputValue, setInputValue] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [heatmapPayload, setHeatmapPayload] = useState(null);
  const [error, setError] = useState(null);
  
  // --- ADD TITLE ---
  const [showWarningModal, setShowWarningModal] = useState(false);

  // --- INPUT HANDLING ---
  const handleAddStudy = (e) => {
    e.preventDefault();
    const cleanId = inputValue.trim().toUpperCase();
    if (cleanId && !studies.includes(cleanId)) {
      setStudies([...studies, cleanId]);
      setInputValue('');
    }
  };

  const handleRemoveStudy = (idToRemove) => {
    setStudies(studies.filter(id => id !== idToRemove));
  };

  // --- WARNING MODAL ---
  const initiateAnalysis = () => {
    if (studies.length === 0) {
      setError("Please add at least one NASA OSDR study ID to begin.");
      return;
    }
    setError(null);

    // Check:
    if (studies.length > 5) {
      setShowWarningModal(true);
    } else {
      executeMetaAnalysis();
    }
  };

  // --- API RECRUITMENT ---
  const executeMetaAnalysis = async () => {
    setShowWarningModal(false);
    setIsProcessing(true);
    setError(null);

    try {
      // Recruiting the Backend Engine
      const response = await fetch('http://127.0.0.1:8000/analyze/meta', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ study_ids: studies })
      });

      if (!response.ok) {
        throw new Error('Failed to execute meta-analysis');
      }

      const data = await response.json();
      
      if (data.heatmap_data && data.heatmap_data.length > 0) {
        setHeatmapPayload(data.heatmap_data);
      } else {
        setError("Meta-analysis completed but no heatmap data was returned. Check payload");
      }
    } catch (err) {
      setError(err.message || "Failed to execute meta-analysis. Please try again.");
    } finally {
      setIsProcessing(false);
    }
  };

  // --- PLOTLY DATA TRANSFORMATION ---
  const plotlyConfig = useMemo(() => {
    if (!heatmapPayload) return null;

    const studyColumns = Object.keys(heatmapPayload[0]).filter(key => key.endsWith('_log2fc'));
    const xLabels = studyColumns.map(col => col.replace('_log2fc', ''));
    const yLabels = heatmapPayload.map(row => row.human_ortholog_id || 'Unknown');
    const zValues = heatmapPayload.map(row => {
      return studyColumns.map(col => {
        const val = row[col]; 
        return val !== null && val !== undefined ? parseFloat(val) : 0; // Handle NaNs
      });
    });

    return {
      data: [{
        z: zValues,
        x: xLabels,
        y: yLabels,
        type: 'heatmap',
        colorscale: 'RdBu',
        reversescale: true, // Red = Upregulated, Blue = Downregulated
        colorbar: { title: 'Log2 FC' },
        hovertemplate: 'Gene: %{y}<br>Study: %{x}<br>Log2FC: %{z:.2f}<extra></extra>'
      }],
      layout: {
        title: { text: 'Consensus Dysregulation Matrix (Top 100 Orthologs)', font: { color: '#e2e8f0' } },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: '#94a3b8' },
        xaxis: { title: 'Study Accession', tickangle: -45 },
        yaxis: { title: 'Human Ensembl ID', autorange: 'reversed' },
        margin: { l: 150, r: 50, t: 80, b: 100 },
        autosize: true
      }
    };
  }, [heatmapPayload]);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-200 font-sans p-6">
      
      {/* HEADER */}
      <header className="mb-8 border-b border-slate-700 pb-4">
        <h1 className="text-3xl font-bold flex items-center gap-3 text-white">
          <Dna className="text-emerald-400" size={32} />
          MOSAIC Comparison Dashboard
        </h1>
        <p className="text-slate-400 mt-2">
          Multi-Organism Spaceflight Analysis and Integrated Consensus
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* SIDEBAR CONFIGURATION */}
        <div className="lg:col-span-1 bg-slate-800 rounded-xl p-5 border border-slate-700 shadow-xl h-fit">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Database size={20} className="text-blue-400" />
            Study Recruitment
          </h2>

          <form onSubmit={handleAddStudy} className="flex gap-2 mb-6">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="e.g. OSD-899"
              className="flex-1 bg-slate-900 border border-slate-600 rounded px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
            />
            <button type="submit" className="bg-slate-700 hover:bg-slate-600 p-2 rounded transition-colors">
              <Plus size={20} />
            </button>
          </form>

          <div className="space-y-2 mb-8">
            {studies.map((study) => (
              <div key={study} className="flex items-center justify-between bg-slate-900 p-3 rounded border border-slate-700">
                <span className="font-mono text-sm">{study}</span>
                <button onClick={() => handleRemoveStudy(study)} className="text-red-400 hover:text-red-300">
                  <X size={16} />
                </button>
              </div>
            ))}
            {studies.length === 0 && (
              <div className="text-sm text-slate-500 text-center py-4 italic">No studies recruited.</div>
            )}
          </div>

          <button
            onClick={initiateAnalysis}
            disabled={isProcessing}
            className={`w-full py-3 rounded-lg font-bold flex items-center justify-center gap-2 transition-all
              ${isProcessing ? 'bg-slate-700 text-slate-400 cursor-not-allowed' : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg hover:shadow-emerald-500/20'}`}
          >
            {isProcessing ? (
              <><Activity className="animate-spin" size={20} /> Processing Matrix...</>
            ) : (
              <><Play size={20} /> Generate Consensus</>
            )}
          </button>

          {error && (
            <div className="mt-4 p-3 bg-red-900/50 border border-red-500/50 rounded text-red-200 text-sm">
              <AlertTriangle className="inline mr-2" size={16} />
              {error}
            </div>
          )}
        </div>

        {/* MAIN VISUALIZATION */}
        <div className="lg:col-span-3 bg-slate-800 rounded-xl p-5 border border-slate-700 shadow-xl min-h-[600px] flex flex-col">
          {heatmapPayload && plotlyConfig ? (
            <div className="flex-1 w-full h-full relative">
               <Plot
                  data={plotlyConfig.data}
                  layout={plotlyConfig.layout}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '100%', minHeight: '600px' }}
                  config={{ responsive: true, displayModeBar: true }}
                />
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-500">
              <Activity size={48} className="mb-4 opacity-20" />
              <p className="text-lg">Awaiting Matrix Recruitment.</p>
              <p className="text-sm mt-2">Add study accessions and generate consensus to begin.</p>
            </div>
          )}
        </div>
      </div>

      {showWarningModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 border border-amber-500/50 rounded-xl p-6 max-w-md shadow-2xl">
            <div className="flex items-center gap-3 text-amber-500 mb-4">
              <AlertTriangle size={32} />
              <h2 className="text-xl font-bold">Interpretability Warning</h2>
            </div>
            <p className="text-slate-300 mb-6 leading-relaxed">
              You are attempting to aggregate <strong>{studies.length} datasets</strong>. This exceeds the recommended maximum of 5. 
              Data may become convoluted, diluting specific biological signals across species. 
              <br /><br />
              Are you sure you want to proceed with this high-volume set?
            </p>
            <div className="flex gap-4 justify-end">
              <button 
                onClick={() => setShowWarningModal(false)}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-white font-medium transition-colors"
              >
                Deload (Cancel)
              </button>
              <button 
                onClick={executeMetaAnalysis}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-500 rounded text-white font-bold transition-colors"
              >
                Proceed (Ego-Lift)
              </button>
            </div>
          </div>
        </div>
      )}
      
    </div>
  );
}