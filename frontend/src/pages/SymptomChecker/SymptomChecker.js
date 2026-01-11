import React, { useState } from 'react';
import { mlAPI } from '../../api';
import { toast } from 'react-toastify';
import {
  FiActivity, FiAlertCircle, FiCheckCircle,
  FiSend, FiRefreshCw, FiInfo, FiAlertTriangle, FiHeart,
  FiThermometer, FiClock
} from 'react-icons/fi';
import './SymptomChecker.css';

const SymptomChecker = () => {
  const [symptoms, setSymptoms] = useState('');
  const [loading, setLoading] = useState(false);
  const [guidance, setGuidance] = useState(null);
  const [history, setHistory] = useState([]);

  // Common symptoms for quick selection
  const commonSymptoms = [
    'Headache', 'Fever', 'Cough', 'Cold', 'Body Pain',
    'Fatigue', 'Nausea', 'Dizziness', 'Sore Throat', 'Chest Pain',
    'Stomach Ache', 'Back Pain', 'Joint Pain', 'Difficulty Breathing', 'Skin Rash'
  ];

  const handleSymptomClick = (symptom) => {
    if (symptoms.includes(symptom)) {
      setSymptoms(symptoms.replace(symptom, '').replace(/,\s*,/g, ',').replace(/^,\s*|,\s*$/g, '').trim());
    } else {
      setSymptoms(symptoms ? `${symptoms}, ${symptom}` : symptom);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!symptoms.trim()) {
      toast.error('Please describe your symptoms');
      return;
    }

    setLoading(true);
    setGuidance(null);

    try {
      const response = await mlAPI.getGuidance({ symptoms: symptoms });
      const result = response.data;
      
      setGuidance(result);
      setHistory([{ symptoms, result, timestamp: new Date() }, ...history.slice(0, 4)]);
      toast.success('Analysis complete!');
    } catch (error) {
      console.error('Error getting guidance:', error);
      toast.error('Unable to analyze symptoms. Please try again.');
      
      // Mock response for demo if API fails
      setGuidance({
        guidance: "Based on your symptoms, here are some recommendations:\n\n1. **Rest and Hydration**: Get plenty of rest and drink lots of fluids.\n\n2. **Monitor Your Symptoms**: Keep track of any changes in your condition.\n\n3. **Over-the-Counter Remedies**: Consider appropriate OTC medications for symptom relief.\n\n4. **Seek Medical Attention If**:\n   - Symptoms persist for more than 3-5 days\n   - You develop high fever (above 103°F)\n   - You experience difficulty breathing\n   - Symptoms suddenly worsen\n\n⚠️ **Disclaimer**: This is AI-generated guidance and should not replace professional medical advice. Please consult a healthcare provider for accurate diagnosis.",
        severity: "moderate",
        recommended_specialist: "General Physician"
      });
    }

    setLoading(false);
  };

  const handleClear = () => {
    setSymptoms('');
    setGuidance(null);
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'mild': return '#10B981';
      case 'moderate': return '#F59E0B';
      case 'severe': return '#EF4444';
      default: return '#6B7280';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'mild': return <FiCheckCircle />;
      case 'moderate': return <FiAlertCircle />;
      case 'severe': return <FiAlertTriangle />;
      default: return <FiInfo />;
    }
  };

  return (
    <div className="symptom-checker-page">
      {/* Header */}
      <div className="sc-header">
        <div className="sc-header-content">
          <FiActivity className="sc-header-icon" />
          <h1>AI Symptom Checker</h1>
          <p>Describe your symptoms and get personalized health guidance</p>
        </div>
      </div>

      <div className="sc-container">
        {/* Main Form Section */}
        <div className="sc-main">
          <form onSubmit={handleSubmit} className="symptoms-form">
            <div className="symptoms-input-wrapper">
              <label>What symptoms are you experiencing?</label>
              <textarea
                value={symptoms}
                onChange={(e) => setSymptoms(e.target.value)}
                placeholder="Describe your symptoms in detail... (e.g., I have a headache for 2 days, along with mild fever and body ache)"
                rows={4}
              />
              <div className="input-actions">
                <button 
                  type="button" 
                  className="clear-btn"
                  onClick={handleClear}
                  disabled={!symptoms}
                >
                  <FiRefreshCw /> Clear
                </button>
                <button 
                  type="submit" 
                  className="analyze-btn"
                  disabled={loading || !symptoms.trim()}
                >
                  {loading ? (
                    <>
                      <span className="loading-spinner"></span>
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <FiSend /> Analyze Symptoms
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Common Symptoms */}
            <div className="common-symptoms">
              <h3>Common Symptoms (Click to add)</h3>
              <div className="symptom-tags">
                {commonSymptoms.map((symptom, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className={`symptom-tag ${symptoms.includes(symptom) ? 'selected' : ''}`}
                    onClick={() => handleSymptomClick(symptom)}
                  >
                    {symptom}
                  </button>
                ))}
              </div>
            </div>
          </form>

          {/* Results Section */}
          {guidance && (
            <div className="guidance-results">
              <div className="results-header">
                <h2><FiHeart /> AI Health Guidance</h2>
                {guidance.severity && (
                  <span 
                    className="severity-badge"
                    style={{ background: getSeverityColor(guidance.severity) }}
                  >
                    {getSeverityIcon(guidance.severity)}
                    {guidance.severity} Severity
                  </span>
                )}
              </div>

              {guidance.recommended_specialist && (
                <div className="specialist-recommendation">
                  <FiThermometer />
                  <span>Recommended Specialist: <strong>{guidance.recommended_specialist}</strong></span>
                </div>
              )}

              <div className="guidance-content">
                {guidance.guidance.split('\n').map((line, idx) => (
                  <p key={idx}>{line}</p>
                ))}
              </div>

              <div className="guidance-disclaimer">
                <FiAlertCircle />
                <p>
                  <strong>Important:</strong> This is AI-generated guidance based on the symptoms you described. 
                  It is not a medical diagnosis. Always consult with a qualified healthcare professional 
                  for proper diagnosis and treatment.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="sc-sidebar">
          {/* Tips Card */}
          <div className="tips-card">
            <h3><FiInfo /> Tips for Better Results</h3>
            <ul>
              <li>Be specific about your symptoms</li>
              <li>Mention how long you've had them</li>
              <li>Include any other relevant details (age, pre-existing conditions)</li>
              <li>Describe the intensity (mild, moderate, severe)</li>
            </ul>
          </div>

          {/* Recent Searches */}
          {history.length > 0 && (
            <div className="history-card">
              <h3><FiClock /> Recent Checks</h3>
              <div className="history-list">
                {history.map((item, idx) => (
                  <div 
                    key={idx} 
                    className="history-item"
                    onClick={() => setSymptoms(item.symptoms)}
                  >
                    <span className="history-symptoms">{item.symptoms.substring(0, 40)}...</span>
                    <span className="history-time">
                      {new Date(item.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Emergency Warning */}
          <div className="emergency-warning">
            <FiAlertTriangle className="warning-icon" />
            <h4>Experiencing Emergency Symptoms?</h4>
            <p>If you have severe symptoms like chest pain, difficulty breathing, or severe injury, please call emergency services immediately.</p>
            <a href="/emergency" className="emergency-link">
              Go to Emergency Services →
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SymptomChecker;
