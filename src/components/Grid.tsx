import { Fragment, FC, useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import QLearnAgent from "../Roombas/QLearningAgent";
import QLearnAgent2 from "../Roombas/QLearningAgent2";
import Roomba from "../Roombas/Roomba";
import { COLLISION, considerSelfMove, createNewSelfMove, MoveArgs } from "../store/actions";
import {AgentParamType, IObjCoord, IGlobalState,
        agentColors, NUM_AGENTS, PelletParamType, pelletColors, agentPelletCollision, APIndex, agentTypes} from '../utils'
import Agent from "./Agent";
import Pellet from "./Pellet";
import { stat } from "fs";

//The grid component is responsible for the instantiation and activities of the agents (rather than grid rendering).

// Initialize agent instances based on the agentTypes
export const agentInsts: Roomba[] = agentTypes.map((AgentType, index) => new AgentType(index));

// Function to render an Agent component
function renderAgent(agentParams: AgentParamType) {
    return (
        <Agent
            key={'agent' + agentParams.myId} // Unique key for React
            id={['agent' + agentParams.myId].reduce((i, s) => s.charCodeAt(0) + i, 0).toString()} // Generate a unique ID
            myId={agentParams.myId} // Agent ID
            dispatch={agentParams.dispatch} // Redux dispatch function
            myPos={agentParams.myPos} // Agent position
            color={agentParams.color} // Agent color
            myAgent={agentParams.myAgent} // Agent instance
            agentName={agentParams.agentName} // Agent name
        ></Agent>
    );
}

// Function to render a Pellet component
function renderPellet(pelletParams: PelletParamType) {
    return (
        <Pellet
            key={'pellet' + pelletParams.myId} // Unique key for React
            id={['pellet' + pelletParams.myId].reduce((i, s) => s.charCodeAt(0) + i, 0).toString()} // Generate a unique ID
            myId={pelletParams.myId} // Pellet ID
            dispatch={pelletParams.dispatch} // Redux dispatch function
            feedback={pelletParams.feedback} // Feedback function
            myPos={pelletParams.myPos} // Pellet position
            myType={pelletParams.myType} // Pellet type
            color={pelletParams.color} // Pellet color
        />
    );
}

// Define the Grid functional component
const Grid: FC = (obj: any) => {
    const dispatch = useDispatch(); // Redux dispatch function
    const agentPos = useSelector((state: IGlobalState) => state.agent_pos); // Get agent positions from Redux store
    const agentSelfMoveP = useSelector((state: IGlobalState) => state.agent_self_move); // Get agent self-move state from Redux store
    const agentDrag = useSelector((state: IGlobalState) => state.agent_drag); // Get agent drag state from Redux store
    const pelletPos = useSelector((state: IGlobalState) => state.pellet_pos); // Get pellet positions from Redux store
    const curAgentPos: IObjCoord[] = agentPos; // Current agent positions
    const curPelletPos: IObjCoord[] = pelletPos; // Current pellet positions
    const agentParams: AgentParamType[] = []; // Array to store agent parameters

    // Populate agentParams array with agent data
    for (let i = 0; i < NUM_AGENTS; i++) {
        agentParams.push({
            myId: i, // Agent ID
            color: agentColors[i], // Agent color
            agentName: `AutoBetterAgent${i + 1}`, // Agent name
            myPos: curAgentPos[i], // Agent position
            myAgent: agentInsts[i], // Agent instance
            dispatch // Redux dispatch function
        });
    }

    const agents = []; // Array to store rendered Agent components

    // Push render information for each agents
    for (let i = 0; i < NUM_AGENTS; i++) {
        agents.push(renderAgent(agentParams[i]));
    }

    const pellets = []; // Array to store rendered Pellet components

    // Push render information for each pellets
    for (let i = 0; i < pelletPos.length; i++) {
        pellets.push(renderPellet({
            myId: i, // Pellet ID
            color: pelletColors[0], // Pellet color
            myType: 'value 3 only', // Pellet type
            feedback: (x: any) => 3, // Feedback function
            myPos: curPelletPos[i], // Pellet position
            dispatch // Redux dispatch function
        }));
    }

    // useEffect to detect collisions between agents and pellets
    useEffect(() => {
        let canGetPelletAgents: IObjCoord[] = Array.from(agentPos); // Agents that can get pellets

        // Filter out agents that are being dragged or cannot get pellets
        canGetPelletAgents = canGetPelletAgents.filter((val, index) => {
            return (index !== agentDrag && agentInsts[index].canGetPellet());
        });

        // Detect collisions between agents and pellets
        const collisions: APIndex[] = agentPelletCollision(canGetPelletAgents, pelletPos);

        // Dispatch a COLLISION action if collisions are detected
        if (collisions.length > 0) {
            dispatch({
                type: COLLISION,
                payload: {
                    cols: collisions
                }
            });
        }
    });

    // useEffect to handle agent self-moves
    useEffect(() => {
        if (agentDrag === -1) { // Only proceed if no agent is being dragged
            for (let i = 0; i < agentSelfMoveP.length; i++) {
                if (!agentSelfMoveP[i]) { // If the agent is not already self-moving
                    dispatch(considerSelfMove(i)); // Dispatch considerSelfMove action
                    dispatch(createNewSelfMove({
                        agentPos: agentPos[i], // Agent position
                        id: i, // Agent ID
                        agentFn: agentInsts[i] // Agent instance
                    } as MoveArgs)); // Dispatch createNewSelfMove action
                }
            }
        }
    }, [agentSelfMoveP, agentPos, dispatch, agentDrag]);

    // Render agents and pellets
    return (
        <Fragment>
            {agents} {/* Render agents */}
            {pellets} {/* Render pellets */}
        </Fragment>
    );
};

export default Grid;