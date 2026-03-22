

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
    }
  };

  const handRemoveStudy = (idToRemove) => {
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
    setShowWarningModal (false);
    setIsProcessing (true);
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
    }