import { IObjCoord, IGlobalState, BOX_W, BOX_H, MAX_STEP_SIZE,
         agentStSqs, APIndex, PELLET_FEEDBACK, AutoDragRequest, NUM_AGENTS  } from "../../utils";
import { COLLISION, CONSIDER_SELF_MOVE_START, CREATE_PELLET, END_SELF_MOVE,
    MOUSE_DOWN, MOUSE_DOWN_MOVE, MOUSE_MOVE_SUCCESS, MOUSE_UP,
    SELF_MOVE_STEP, ADD_QRESULT, TRIGGER_AUTO_DRAG, CLEAR_AUTO_DRAG_REQUEST} from "../actions";

// Define the initial global state    
const initGlobalState: IGlobalState = {
    agent_pos: agentStSqs,
    pellet_pos: [],
    agent_self_move: Array.from({ length: NUM_AGENTS }, () => false),
    agent_drag: -1,
    agent_scores: Array.from({ length: NUM_AGENTS }, () => 0),
    tot_num_pellets: 1,
    extradata: {
      qResults: [],
      autoDragRequests: [],
    },
  };
  
// The reducer handles real-time changes to the global state 
const gameReducer = (state=initGlobalState, action: any) => {
    switch (action.type) {
        // Handle the CREATE_PELLET action to add a new pellet to the grid
        case CREATE_PELLET:
            const newPelletLoc : IObjCoord = action.payload.pos; // Extract the new pellet's position
            const myPellets : IObjCoord [] = [...state.pellet_pos, newPelletLoc]; // Add the new pellet to the list
            return {
                ...state,
                pellet_pos: myPellets, // Update the pellet positions
                tot_num_pellets: state.tot_num_pellets+1 // Increment the total number of pellets
            };

        // Handle the COLLISION action to resolve collisions between agents and pellets
        case COLLISION:
            const myCols : APIndex [] = action.payload.cols; // Extract the collision data
            let newPellets : IObjCoord [] = Array.from(state.pellet_pos); // Copy the current pellet positions
            const newScores: number[] = Array.from(state.agent_scores); // Copy the current agent scores

            // Iterate through all collisions
            for (let i = 0; i < myCols.length; i++){
                const curAgentInd = myCols[i].agentInd; // Get the agent index involved in the collision
                newScores[curAgentInd] += PELLET_FEEDBACK; // Increment the agent's score

                const curPelletInd = myCols[i].pelletInd-i; // Get the pellet index involved in the collision
                newPellets = [...newPellets.slice(0, curPelletInd),
                              ...newPellets.slice(curPelletInd+1)]; // Remove the pellet from the list
            }

            return {
                ...state,
                agent_scores: Array.from(newScores), // Update the agent scores
                pellet_pos: newPellets // Update the pellet positions
            }

        // Handle the MOUSE_DOWN action to start dragging an agent
        case MOUSE_DOWN:
            const newSelfMove : boolean[] = [...state.agent_self_move.slice(0,action.payload.id),
                                             true, 
                                            ...state.agent_self_move.slice(action.payload.id+1)];

            return {
                ...state,
                agent_self_move: newSelfMove, // Update the self-move status
                agent_drag: action.payload.id // Set the dragged agent's ID
            }

        // Handle the MOUSE_DOWN_MOVE action to update the position of the dragged agent
        case MOUSE_DOWN_MOVE:
            const newAgentPos : IObjCoord= {
                x: action.payload.mouseX, // Extract the new x-coordinate
                y: action.payload.mouseY}; // Extract the new y-coordinate

            const newAPosArr : IObjCoord[] = [...state.agent_pos.slice(0,state.agent_drag),
                                               newAgentPos, // Update the dragged agent's position
                                              ...state.agent_pos.slice(state.agent_drag+1)];

            // Log an error if the new position is invalid
            if (newAgentPos.x < 0 ||newAgentPos.y < 0) {
                console.log('mouse down move went rogue x: ' + newAgentPos.x+ ', y: '+ newAgentPos.y );
            }

            return {
                ...state,
                agent_pos: newAPosArr // Update the agent positions
            };

        // Handle the MOUSE_UP action to stop dragging an agent
        case MOUSE_UP:
            const thePos : IObjCoord= {
                x: action.payload.mouseX, // Extract the final x-coordinate
                y: action.payload.mouseY}; // Extract the final y-coordinate

            const agentId : number = action.payload.id; // Get the agent's ID

            const newThePos : IObjCoord[] = [...state.agent_pos.slice(0,agentId),
                                                thePos, // Update the agent's position
                                                ...state.agent_pos.slice(agentId+1)];

            const mySelfMoves : boolean [] = [...state.agent_self_move.slice(0,agentId),
                                                false, 
                                                ...state.agent_self_move.slice(agentId+1)];

            // Log an error if the final position is invalid
            if (thePos.x < 0 ||thePos.y < 0) {
                console.log('end of drag move (mouse up) went rogue x: ' + thePos.x+ ', y: '+ thePos.y );
            }

            return {
                ...state,
                agent_pos: newThePos, // Update the agent positions
                agent_self_move: mySelfMoves, // Update the self-move status
                agent_drag: -1 // Reset the dragged agent's ID
            };

        // Handle the MOUSE_MOVE_SUCCESS action (currently a no-op)
        case MOUSE_MOVE_SUCCESS:
            console.log('move success!');
            return state;

        // Handle the CONSIDER_SELF_MOVE_START action to start a self-move for an agent
        case CONSIDER_SELF_MOVE_START:
            const myId = action.payload.id; // Get the agent's ID
            if (state.agent_self_move[myId]) {
                console.log('starting a self-move despite moving already');
                console.log('gameReducer: CONSIDER_SELF_MOVE_START action');
            }

            if (myId !== state.agent_drag) {
                const addSelfMove: boolean[] = [...state.agent_self_move.slice(0, myId),
                    true, 
                    ...state.agent_self_move.slice(myId+1)
                ];
                return {
                    ...state,
                    agent_self_move: addSelfMove // Update the self-move status
                }
            }
            else {
                return state;
            }

        // Handle the SELF_MOVE_STEP action to update the position of a self-moving agent
        case SELF_MOVE_STEP:
            const selfMoveAgentPos : IObjCoord = {
                x: action.payload.newPos.x/BOX_W, // Normalize the x-coordinate
                y: action.payload.newPos.y/BOX_H, // Normalize the y-coordinate
            };
            const mySelfMoveAgentId = action.payload.id; // Get the agent's ID

            // Prevent self-move if the agent is being dragged
            if (state.agent_drag === mySelfMoveAgentId) {
                console.log('try to self move dragging agent')
                return state; 
            }

            const newSelfAPosArr: IObjCoord[] = [...state.agent_pos.slice(0, mySelfMoveAgentId),
                                                 selfMoveAgentPos, // Update the agent's position
                                                ...state.agent_pos.slice(mySelfMoveAgentId+1)];

            // Log an error if the new position is invalid
            if ((selfMoveAgentPos.x < 0) ||(selfMoveAgentPos.y < 0))  {
                console.log('self move went rogue x: ' + selfMoveAgentPos.x+ ', y: '+ selfMoveAgentPos.y );
            }

            // Calculate the distance of the move
            const newPosDist = Math.sqrt(Math.pow(selfMoveAgentPos.x-state.agent_pos[mySelfMoveAgentId].x,2) +
                                         Math.pow(selfMoveAgentPos.y-state.agent_pos[mySelfMoveAgentId].y,2))

            // Prevent the move if it exceeds the maximum step size
            if (newPosDist > MAX_STEP_SIZE) {
                console.log('step too big.')
                return state
            }
            else {
                return {
                    ...state,
                    agent_pos: newSelfAPosArr // Update the agent positions
                };
            }

        // Handle the END_SELF_MOVE action to stop a self-move for an agent
        case END_SELF_MOVE:
            const agentToEnd = action.payload.id as number; // Get the agent's ID

            const newSlfMoveArr : boolean[] = [
                ...state.agent_self_move.slice(0,agentToEnd),
                false, 
                ...state.agent_self_move.slice(agentToEnd+1)]

            return {...state,
                agent_self_move: newSlfMoveArr // Update the self-move status
            };
        
        // Handle the ADD_QRESULT action to add a Expected Q value result to the state
        case ADD_QRESULT:
            return {
                ...state,
                extradata: {
                  ...state.extradata,
                  qResults: [...state.extradata.qResults, action.payload], 
                }
              };

        // Handle the TRIGGER_AUTO_DRAG action to add an auto-drag request to the state
        case TRIGGER_AUTO_DRAG:
            console.log('triggered')
            return {
                ...state,
                extradata: {
                  ...state.extradata,
                  autoDragRequests: [...state.extradata.autoDragRequests, action.payload], // Add the new auto-drag request
                }
              };

        // Handle the CLEAR_AUTO_DRAG_REQUEST action to remove an auto-drag request from the state
        case CLEAR_AUTO_DRAG_REQUEST:
            return {
                ...state,
                extradata: {
                  ...state.extradata,
                  autoDragRequests: state.extradata.autoDragRequests.filter((request: AutoDragRequest) => request.id !== action.payload.id), // Remove the auto-drag request
                }
              };

        // Default case to return the current state for unrecognized actions
        default:
            return state;
    }
}

export default gameReducer;