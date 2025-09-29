import React, { useRef, useState } from 'react';
import { HEIGHT, WIDTH, NUM_AGENTS, GRID_H, GRID_W } from "../utils";
import { agentInsts } from './Grid';
import QLearnAgent, { AgentAction, QIndex } from "../Roombas/QLearningAgent";
import paper from 'paper';

// The PickQtable component transform a given ​policy​ into a ​visual representation
const PickQtable: React.FC = () => {
  // State to keep track of the selected agent
  const [selectedAgent, setSelectedAgent] = useState<string>('Agent 0');
  // State to store the image source of the Q-table visualization
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  // State to toggle the visibility of the Q-table visualization image
  const [isImageVisible, setIsImageVisible] = useState<boolean>(false);
  // Ref to access the canvas element
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Handler for changing the selected agent in the dropdown
  const handleSelectChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedAgent(event.target.value);
  };

  // Handler for the button click to draw the Q-table
  const handleButtonClick = () => {
    if (canvasRef.current) {
      drawQTable(selectedAgent);
    }
  };

  // Handler for the button click to toggle the visibility of the Q-table visualization image
  const handleToggleButtonClick = () => {
    setIsImageVisible(!isImageVisible);
  };

  // Function to draw the Q-table on the canvas
  const drawQTable = (agentId: string) => {
    if (canvasRef.current) {
      // Parse the agent index from the agent ID string
      const agentIndex = parseInt(agentId.split(' ')[1], 10);
      // Get the Q-learning agent instance
      const qAgent = agentInsts[agentIndex] as QLearnAgent; 
      // Get the Q-table from the agent
      const qTable = qAgent._myQTable; 

      // Set the canvas dimensions
      canvasRef.current.width = 550;
      canvasRef.current.height = 550;
      // Setup Paper.js with the canvas
      paper.setup(canvasRef.current);
      // Set the view size to match the canvas dimensions
      paper.view.viewSize = new paper.Size(canvasRef.current.width, canvasRef.current.height);

      // Clear the Paper.js project to start fresh
      paper.project.clear();
      // Loop through each cell in the grid
      for (let i = 0; i < GRID_H * GRID_W; i++) {
        // Calculate the x and y coordinates of the current cell
        const x = i % GRID_W;
        const y = Math.floor(i / GRID_H);
        // Create a position object for the current cell
        let myPos = { x, y };
        // Arrays to store actions and their corresponding Q-values
        let actArr: string[] = [];
        let valArr: number[] = [];

        // Arrays to define the direction vectors for actions
        let dx = [0, 0, -1, 1, -0.707, 0.707, -0.707, 0.707, 0];
        let dy = [-1, 1, 0, 0, -0.707, -0.707, 0.707, 0.707, 0];

        // Loop through each action in the AgentAction enum
        for (var enumMember in AgentAction) {
          var isValueProperty = Number(enumMember) >= 0;
          if (isValueProperty) {
            // Get the action index and its corresponding string
            var action_idx = Number(enumMember);
            var action_str = AgentAction[action_idx];
            // Create a key object for the Q-table lookup
            let key: QIndex = {
              myPos,
              action: action_idx
            };
            // Get the Q-value for the current state-action pair
            let qVal = qTable.get(key);
            let qValNum = qVal as number;
            // Store the action and its Q-value in the arrays
            actArr.push(action_str);
            valArr.push(qValNum);
          }
        }

        // Calculate the position on the canvas for the current cell
        let x1 = 50 + x * 80;
        let y1 = 50 + y * 80;
        const baseLen = 20;

        // Loop through each action to draw the corresponding path
        for (let idx = 0; idx < 9; idx++) { 
          let path = new paper.Path();

          // Set the stroke color and width based on the Q-value
          if (isNaN(valArr[idx]) || !isFinite(valArr[idx])) {
            path.strokeColor = new paper.Color('red');
            path.strokeWidth = 5;
          } else {
            path.strokeColor = new paper.Color(valArr[idx] >= 0 ? 'green' : 'purple');
            path.strokeWidth = Math.abs(valArr[idx]) < 2 ? 1 : Math.abs(valArr[idx]) / 2;
          }
          // Calculate the length of the path based on the Q-value
          let len = baseLen * Math.min(Math.abs(valArr[idx]), 2);
          path.moveTo([x1, y1]);
          let x2 = x1 + dx[idx] * len;
          let y2 = y1 + dy[idx] * len;
          path.lineTo([x2, y2]);
        }

        // Draw a circle at the center of the cell
        let path = new paper.Path.Circle([x1, y1], baseLen);
        path.strokeColor = new paper.Color(0.5, 0.5, 0.5, 0.5); 
      }
      // Update the Paper.js view to render the paths
      paper.view.update();

      // Convert the canvas content to a data URL and set it as the image source
      const dataURL = canvasRef.current.toDataURL('image/png');
      setImageSrc(dataURL);
    }
  };

  // Render the component UI
  return (
    <div style={{
      position: 'absolute',
      left: WIDTH * 1.1,
      top: HEIGHT * 0.1,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      zIndex: 2,
      backgroundColor: 'rgba(255, 255, 255, 0.8)',
      padding: '10px',
      borderRadius: '10px'
    }}>
      {/* Label and dropdown for selecting an agent */}
      <label htmlFor="agent-select">Select Agent: </label>
      <select id="agent-select" value={selectedAgent} onChange={handleSelectChange}>
        {Array.from({ length: NUM_AGENTS }, (_, index) => (
          <option key={index} value={`Agent ${index}`}>{`Agent ${index}`}</option>
        ))}
      </select>
      {/* Button to trigger drawing the Q-table */}
      <button onClick={handleButtonClick}>Get the current policy</button>
      {/* Button to toggle the visibility of the Q-table visualization image */}
      <button onClick={handleToggleButtonClick}>{isImageVisible ? 'Hide' : 'Show'} QTable Visualization</button>
      {/* Canvas element for drawing the Q-table, initially hidden */}
      <canvas ref={canvasRef} style={{ display: 'none' }}></canvas>
      {/* Display the Q-table visualization image if visible */}
      {isImageVisible && imageSrc && <img src={imageSrc} alt="QTable Visualization" style={{ width: 800, height: 800, border: '1px solid black', marginTop: '10px' }} />}
    </div>
  );
};

export default PickQtable;
