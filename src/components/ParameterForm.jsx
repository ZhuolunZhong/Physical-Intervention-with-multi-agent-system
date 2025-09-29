import React, { useState, useEffect } from 'react';
import { loadPolicy } from '../utils';

//ParameterForm component is a comprehensive React form that allows users to configure various parameters for a simulation or experiment
const ParameterForm = () => {
  // State variables for form
  const [isOpen, setIsOpen] = useState(true);
  const [pelletsTime, setPelletsTime] = useState(2000);
  const [moveTime, setMoveTime] = useState(2.0);
  const [waitTime, setWaitTime] = useState(0);
  const [agentEps, setAgentEps] = useState(0.2);
  const [teachEps, setTeachEps] = useState(0.0);
  const [patchVariance, setPatchVariance] = useState([0.75, 0.75, 0.75, 0.75]);
  const [patchPosition, setPatchPosition] = useState([3.0, 3.0, 3.0, 3.0]);
  const [stepCost, setStepCost] = useState(-1);
  const [interventionFeedback, setInterventionFeedback] = useState(-12);
  const [pelletFeedback, setPelletFeedback] = useState(6);
  const [interpretType, setInterpretType] = useState(0);
  const [numberOfAgents, setNumberOfAgents] = useState(1);
  const [agentTypes, setAgentTypes] = useState(['QLearnAgentPreload']);
  const [message, setMessage] = useState('');

  // Clear message after 1.5 seconds
  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => {
        setMessage('');
      }, 1500); 
      return () => clearTimeout(timer); 
    }
  }, [message]);

  // Toggle form visibility
  const handleToggle = () => {
    setIsOpen(!isOpen);
  };

  const handlePatchVarianceChange = (index, value) => {
    const newPatchVariance = [...patchVariance];
    newPatchVariance[index] = parseFloat(value);
    setPatchVariance(newPatchVariance);
  };

  const handlePatchPositionChange = (index, value) => {
    const newPatchPosition = [...patchPosition];
    newPatchPosition[index] = parseFloat(value);
    setPatchPosition(newPatchPosition);
  };

  const handleNumberOfAgentsChange = (e) => {
    const num = parseInt(e.target.value);
    setNumberOfAgents(num);
    setAgentTypes(Array(num).fill('QLearnAgentPreload'));
  };

  const handleAgentTypeChange = (index, value) => {
    const newAgentTypes = [...agentTypes];
    newAgentTypes[index] = value;
    setAgentTypes(newAgentTypes);
  };

   // Handle form submission
  const handleSubmit = async (event) => {
    event.preventDefault();

    // Map agent types to a consistent format
    const mappedAgentTypes = agentTypes.map(agentType => 
        agentType === 'QLearnAgentPreload' ? 'QLearnAgent' : 'QLearnAgent2'
    );

    // Construct params object
    const params = {
        NUM_AGENTS: numberOfAgents,
        PELLET_PATCH_MEAN2: [
            [patchPosition[0], patchPosition[1]],
            [patchPosition[2], patchPosition[3]]
        ],
        PELLET_PATCH_VAR2: [
            [patchVariance[0], patchVariance[1]],
            [patchVariance[2], patchVariance[3]]
        ],
        EXPECTED_PELLET_TIME: pelletsTime,
        AGENT_EPS: agentEps,
        TEACH_EPS: teachEps,
        MOVE_TIME: moveTime,
        WAIT_TIME: waitTime,
        Q_STEP_COST: stepCost,
        HUM_INT_FB: interventionFeedback,
        PELLET_FEEDBACK: pelletFeedback,
        INTERPRET_TYPE: interpretType,
        agentTypes: mappedAgentTypes,
    };

    // Save params to sessionStorage
    Object.keys(params).forEach(key => {
        sessionStorage.setItem(key, JSON.stringify(params[key]));
    });

    try {
      await loadPolicy(params.PELLET_PATCH_MEAN2, params.PELLET_PATCH_VAR2);
      setMessage('Parameters updated successfully!');
      setTimeout(() => {
          window.location.reload();
      }, 1500); 
  } catch (error) {
      if (error.message === 'File not found') {
          if (agentTypes.includes('QLearnAgentPreload')) {
              alert('Policy file not found for the provided parameters.');
          } else {
              setMessage('Parameters updated successfully!');
              setTimeout(() => {
                  window.location.reload();
              }, 1500); 
          }
      } else {
          console.error('Error loading policy:', error);
      }
  }
  
};

  return (
    <div className="parameter-form-container">
      <button onClick={handleToggle}>
        {isOpen ? 'Collapse' : 'Expand'}
      </button>
      {isOpen && (
        <form onSubmit={handleSubmit} style={{ marginTop: '10px' }}>
          <div>
            <label>
              Pellets Time:
              <input 
                type="number" 
                value={pelletsTime} 
                onChange={(e) => setPelletsTime(parseInt(e.target.value))} 
              />
            </label>
          </div>
          <div>
            <label>
              Move Time:
              <input 
                type="number" 
                step="0.1" 
                value={moveTime} 
                onChange={(e) => setMoveTime(parseFloat(e.target.value))} 
              />
            </label>
          </div>
          <div>
            <label>
              Wait Time:
              <input 
                type="number" 
                value={waitTime} 
                onChange={(e) => setWaitTime(parseFloat(e.target.value))} 
              />
            </label>
          </div>
          <div>
            <label>
              Agent Eps:
              <input 
                type="number" 
                step="0.01" 
                value={agentEps} 
                onChange={(e) => setAgentEps(parseFloat(e.target.value))} 
              />
            </label>
          </div>
          <div>
            <label>
              Teach Eps:
              <input 
                type="number" 
                step="0.1" 
                value={teachEps} 
                onChange={(e) => setTeachEps(parseFloat(e.target.value))} 
              />
            </label>
          </div>
          <div>
            <label>
              Patch Variance:
              {patchVariance.map((value, index) => (
                <input 
                  key={index}
                  type="number"
                  step="0.25"
                  value={value}
                  onChange={(e) => handlePatchVarianceChange(index, e.target.value)}
                  style={{ marginLeft: '5px', width: '60px' }}
                />
              ))}
            </label>
          </div>
          <div>
            <label>
              Patch Position:
              {patchPosition.map((value, index) => (
                <input 
                  key={index}
                  type="number"
                  step="1"
                  value={value}
                  onChange={(e) => handlePatchPositionChange(index, e.target.value)}
                  style={{ marginLeft: '5px', width: '60px' }}
                />
              ))}
            </label>
          </div>
          <div>
            <label>
              Step Cost:
              <input 
                type="number" 
                value={stepCost} 
                onChange={(e) => setStepCost(parseFloat(e.target.value))} 
              />
            </label>
          </div>
          <div>
            <label>
              Intervention Feedback:
              <input 
                type="number" 
                value={interventionFeedback} 
                onChange={(e) => setInterventionFeedback(parseFloat(e.target.value))} 
              />
            </label>
          </div>
          <div>
            <label>
              Pellet Feedback:
              <input 
                type="number" 
                value={pelletFeedback} 
                onChange={(e) => setPelletFeedback(parseFloat(e.target.value))} 
              />
            </label>
          </div>
          <div>
            <label>
              Interpret Type:
              <select 
                value={interpretType} 
                onChange={(e) => setInterpretType(parseInt(e.target.value))}
              >
                <option value={0}>0</option>
                <option value={1}>1</option>
                <option value={3}>3</option>
                <option value={4}>4</option>
              </select>
            </label>
          </div>
          <div>
            <label>
              Number of Agents:
              <select 
                value={numberOfAgents} 
                onChange={handleNumberOfAgentsChange}
              >
                <option value={1}>1</option>
                <option value={2}>2</option>
                <option value={3}>3</option>
              </select>
            </label>
          </div>
          {Array.from({ length: numberOfAgents }).map((_, index) => (
            <div key={index}>
              <label>
                Agent {index} Type:
                <select 
                  value={agentTypes[index]} 
                  onChange={(e) => handleAgentTypeChange(index, e.target.value)}
                >
                  <option value="QLearnAgentPreload">QLearnAgentPreload</option>
                  <option value="QLearnAgent">QLearnAgent</option>
                </select>
              </label>
            </div>
          ))}
          <button type="submit" style={{ marginTop: '10px' }}>Submit</button>
        </form>
      )}
      {message && <p>{message}</p>}
    </div>
  );
};

export default ParameterForm;
