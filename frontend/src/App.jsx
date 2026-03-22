

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
  
}