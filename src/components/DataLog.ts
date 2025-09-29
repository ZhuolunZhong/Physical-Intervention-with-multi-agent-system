import { IGlobalState, IObjCoord, NUM_AGENTS, TEACH_EPS, dragAllowed } from "../utils"; 
import { Mutex } from "async-mutex"; 
import Roomba from "../Roombas/Roomba"; 
import { useMemo, useSyncExternalStore } from "react"; 
import { AgentAction } from "../Roombas/QLearningAgent"; 
import { policyTeacher } from "../Roombas/PolicyTeacher";
import axios from 'axios'; 

//Datalog defines the trajectory data of the agent and the functions for getting data.

// Initialize an array to store trajectory data for each agent
const myData: Array<Array<TrajDataType>> = new Array(NUM_AGENTS);
// Initialize a set to store listeners for state changes
let listeners: Set<() => void> = new Set<() => void>();

// Create a mutex to handle concurrent writes to myData
const writeMutex = new Mutex();

// Initialize the myData array with empty arrays for each agent
for (let i = 0; i < NUM_AGENTS; i++) {
    myData[i] = [];
}

// Define the TrajType interface for trajectory data
export interface TrajType {
    agent_st_pos?: IObjCoord, // Start position of the agent
    agent_end_pos?: IObjCoord, // End position of the agent
    qValue?: number, // action q value
    expected_qValue?: number, // action expected q value
    agent_id: number, // ID of the agent
    was_dragP: boolean, // Whether the trajectory was a drag operation
    st_time: Date, // Start time of the trajectory
    cancelP?: boolean, // Whether the trajectory was canceled
    is_optimal?: boolean, // Whether the action is optimal
    end_time?: Date, // End time of the trajectory
    got_pelletP?: boolean, // Whether the agent got a pellet
    pellet_loc?: IObjCoord, // Location of the pellet
    duration?: number, // Duration of the trajectory
    pellet_feedback?: number, // Feedback from the pellet
    agent_mouse_traj?: IObjCoord[] | [], // Trajectory of the mouse (if applicable)
    agent_self_traj?: IObjCoord[] | [], // Trajectory of the agent (if applicable)
    agent_type?: Roomba, // Type of the agent
    feedback?: number, // points
    agent_try_pos?: IObjCoord // Position the agent tried to move to
}

// Define the TrajDataType interface, extending TrajType with state information
export type TrajDataType = TrajType & {
    start_state: IGlobalState, // Global state at the start of the trajectory
    cur_state?: IGlobalState // Current global state (if applicable)
}

// Function to get trajectory data for a specific agent
export function getAgentData(agentNum: number): Array<TrajDataType> {
    return (myData[agentNum]);
}

// Function to add trajectory data for an agent
export async function addAgentTraj(traj: TrajDataType) {
    await new Promise<void>((resolve, reject) => {
        // Acquire the mutex to ensure thread-safe writes
        writeMutex.acquire().then(function (release) {
            try {
                myData[traj.agent_id].push(traj); // Add the trajectory to the agent's data
                resolve(); // Resolve the promise
            } catch (error) {
                reject(error); 
            } finally {
                release(); 
            }
        });
    });
    // Notify all listeners of the state change
    listeners.forEach(notify => notify());
}

// Function to count the number of full trajectories for an agent
export function numFullTraj(id = 0): number {
    const fullTrajsForId: Array<TrajDataType> = myData[id].filter((el) => {
        return (el.agent_end_pos !== undefined ); // Filter for full, non-drag trajectories
    });
    return fullTrajsForId.length; // Return the count
}

// Function to determine if an auto-drag should occur
export function autoDrag(id = 0, st_pos: IObjCoord, end_pos: IObjCoord): boolean {
    if (!dragAllowed[id]) return false;
    if (Math.random() >= TEACH_EPS) return false;

    const action = calculateAction(st_pos, end_pos);
    const isOptimal = policyTeacher.isOptimalAction(st_pos.x, st_pos.y, action);

    return !isOptimal && action !== AgentAction.NOMOVE;
}

// Custom hook to get the number of full trajectories for an agent
export const useNumTrajData = (id = 0) => {
    const getData = () => numFullTraj(id); // Function to get the number of full trajectories
    const subscribe = useMemo(() => {
        return (notify: () => void) => {
            numTrajDataSub(notify); // Subscribe to notifications
            return () => {
                numTrajDataUnsub(notify) // Unsubscribe from notifications
            }
        }
    }, [])
    return useSyncExternalStore(subscribe, getData); // Use React's useSyncExternalStore to manage state
}

// Function to subscribe a listener
function numTrajDataSub(notify: () => void) {
    listeners.add(notify); // Add the listener to the set
}

// Function to unsubscribe a listener
function numTrajDataUnsub(notify: () => void) {
    listeners.delete(notify); // Remove the listener from the set
}

// Function to calculate the action based on start and end positions
export const calculateAction = (st_pos: any, end_pos: any) => {
    const dx = end_pos.x - st_pos.x; // Calculate the change in X
    const dy = end_pos.y - st_pos.y; // Calculate the change in Y

    if (dx === 0 && dy === 0) { // No movement
        return AgentAction.NOMOVE;
    }

    if (dx === 0) { // Vertical movement
        if (dy > 0) {
            return AgentAction.DOWN;
        } else {
            return AgentAction.UP;
        }
    }

    if (dy === 0) { // Horizontal movement
        if (dx > 0) {
            return AgentAction.RIGHT;
        } else {
            return AgentAction.LEFT;
        }
    }

    if (dx > 0) { // Diagonal movement (right)
        if (dy > 0) {
            return AgentAction.DOWNRIGHT;
        } else {
            return AgentAction.UPRIGHT;
        }
    } else { // Diagonal movement (left)
        if (dy > 0) {
            return AgentAction.DOWNLEFT;
        } else {
            return AgentAction.UPLEFT;
        }
    }
};

export default myData;

// Function to send trajectory data to the server
export const testDataFunc = () => {
    const user_id = sessionStorage.getItem('userID') || 'unknown'; // Get the user ID from session storage
    const round = sessionStorage.getItem('round'); // Get the round from session storage
    const _id = `${user_id}_${round}`; // Create a unique ID for the data

    const dataToSend = {
        _id: _id, // Include the unique ID
        data: myData // Include the trajectory data
    };

    // Send the data to the server using axios
    axios.post('/api/upload/mongo', dataToSend)
        .then(response => {
            console.log("POST response:", response.data); // Log the server response
        })
        .catch(error => {
            console.error("Error uploading data:", error); // Log any errors
        });

    console.log("Data sent from React, waiting for server response..."); // Log that the data was sent
};

// Function to get dragged trajectories for an agent
export function getDraggedTraj(id = 0): Array<TrajDataType> {
    const draggedTrajsForId: Array<TrajDataType> = myData[id].filter((el) => {
        return el.was_dragP === true; // Filter for dragged trajectories
    });
    return draggedTrajsForId; // Return the filtered trajectories
}

// Function to get canceled trajectories for an agent
export function getCanceledTraj(id = 0): Array<TrajDataType> {
    const canceledTrajsForId: Array<TrajDataType> = myData[id].filter((el) => {
        return el.cancelP === true; // Filter for canceled trajectories
    });
    return canceledTrajsForId; // Return the filtered trajectories
}

// Function to get try position trajectories for an agent
export function getTryTraj(id = 0): Array<TrajDataType> {
    const canceledTrajsForId: Array<TrajDataType> = myData[id].filter((el) => {
        return el.agent_end_pos === undefined; // Filter for canceled trajectories
    });
    return canceledTrajsForId; // Return the filtered trajectories
}

// Function to get end position trajectories for an agent
export function getEndTraj(id = 0): Array<TrajDataType> {
    const canceledTrajsForId: Array<TrajDataType> = myData[id].filter((el) => {
        return el.agent_end_pos !== undefined; // Filter for canceled trajectories
    });
    return canceledTrajsForId; // Return the filtered trajectories
}

// Function to get the start time of the first trajectory for an agent
export function getStartTime(id = 0): Date {
    const fullTrajsFortime: Array<TrajDataType> = myData[id].filter((el) => {
        return (el.st_time !== undefined); // Filter for trajectories with a start time
    });
    const st_time = fullTrajsFortime[0].st_time; // Get the start time of the first trajectory
    return st_time; // Return the start time
}