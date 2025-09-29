import { calcDist, GRID_H, GRID_W, IGlobalState, IObjCoord } from "../utils"; 
import { QAgentExtState } from './QLearningAgent'; 

// Function to extract features for a Q-learning agent 
function extractQLearnFeatures(state: IGlobalState, id: number): QAgentExtState {
    const myAgentPos = state.agent_pos[id]; // Get the position of the current agent
    let nearAgentDist = Math.sqrt(Math.pow(GRID_W, 2) + Math.pow(GRID_H, 2)); // Initialize the nearest agent distance to the maximum possible distance
    let nearAgentPos: IObjCoord = { x: -1, y: -1 }; // Initialize the nearest agent position

    // Loop through all agents to find the nearest one
    for (let i = 0; i < state.agent_pos.length; i++) {
        if (i !== id) { // Skip the current agent
            const curDist = calcDist(myAgentPos, state.agent_pos[i]); // Calculate the distance to the other agent
            if (curDist < nearAgentDist) { // Update if this agent is closer
                nearAgentDist = curDist;
                nearAgentPos = state.agent_pos[i];
            }
        }
    }

    let nearPelDist = Math.sqrt(Math.pow(GRID_W, 2) + Math.pow(GRID_H, 2)); // Initialize the nearest pellet distance to the maximum possible distance
    let nearPelPos: IObjCoord = { x: -1, y: -1 }; // Initialize the nearest pellet position

    // Loop through all pellets to find the nearest one
    for (let j = 0; j < state.pellet_pos.length; j++) {
        const curDist = calcDist(myAgentPos, state.pellet_pos[j]); // Calculate the distance to the pellet
        if (curDist < nearPelDist) { // Update if this pellet is closer
            nearPelDist = curDist;
            nearPelPos = state.pellet_pos[j];
        }
    }

    // Return the extracted features as a QAgentExtState object
    return {
        myPos: myAgentPos, // Position of the current agent
        nearAgPos: nearAgentPos, // Position of the nearest agent
        agDist: nearAgentDist, // Distance to the nearest agent
        nearPelPos: nearPelPos, // Position of the nearest pellet
        pelDist: nearPelDist // Distance to the nearest pellet
    };
}

export default extractQLearnFeatures; // Export the function