import {
    MOUSE_DOWN, MOUSE_DOWN_MOVE, MOUSE_UP,
    makeAfterMouseMoveCancelTask,
    SAVE_TRAJ, clearAutoDragRequest, COLLISION
} from "../store/actions";
import React, { FC, useCallback, useEffect, useState, useRef } from 'react'
import { useSelector } from 'react-redux';
import { BOX_W, BOX_H, AgentParamType, IObjCoord, agentIdToImg, GREEDY_MAX_VIS, AGENT_W, AGENT_H, retCorPos, GRID_W, GRID_H, HEIGHT, WIDTH, IGlobalState, AutoDragRequest, agentPelletCollision, PELLET_FEEDBACK, pelletColors } from "../utils";
import '../index.css'
import { TrajDataType } from "./DataLog";
import QLearnAgent, { AgentAction, QIndex } from "../Roombas/QLearningAgent";

const POSITION: IObjCoord = { x: 0, y: 0 };

// The agent component defines the external activities of the agent: its appearance and its drag-and-drop related functionalities.
const Agent: FC<AgentParamType> = ({ myPos, id, myId, color, dispatch, myAgent }): JSX.Element => {
    // State to track if the agent is being dragged
    const [dragP, setDragP] = useState(false);
    // State to control the visibility of the overlay
    const [showOverlay, setShowOverlay] = useState(false);
    // Fetch auto-drag requests from the Redux state
    const autoDragRequest = useSelector((state: IGlobalState) => state.extradata.autoDragRequests);
    // State to track mouse origin and translation during drag
    const [mouseHelps, setMouseHelps] = useState({
        origin: POSITION,
        translation: POSITION
    });
    // Get the current round from session storage
    const roundString = sessionStorage.getItem('round');
    // Parse the round as a number, default to 0 if not found
    const round: number = roundString !== null ? parseInt(roundString, 10) : 0;
    // Calculate the image ID based on the round and agent ID
    const imgid: number = (round + myId * 2) % 6;
    // Ref to store the start time of a drag operation
    let stTime = useRef(new Date());
    // Ref to store the start location of a drag operation
    let stLoc = useRef({ x: 0, y: 0 });
    // Fetch
    const currentState = useSelector((state: IGlobalState) => state);
    const latestStateRef = useRef(currentState);

    // Style for the agent when being dragged
    const myStyle = {
        width: BOX_W * AGENT_W, // Width of the agent
        height: BOX_H * AGENT_H, // Height of the agent
        borderRadius: 0, // No border radius
        background: "url('" + agentIdToImg[imgid] + "')", // Background image based on imgid
        backgroundPosition: '50% 50%', // Center the background image
        overflow: 'hidden', // Hide overflow
        backgroundSize: '100% 100%', // Scale the background image to fit
        backgroundRepeat: 'no-repeat', // Prevent background image from repeating
        position: "absolute", // Absolute positioning
        zIndex: 4, // Stacking order
        transform: `translate(${mouseHelps.translation.x}px, ${mouseHelps.translation.y}px`, // Apply translation during drag
        transition: 'transform 50ms', // Smooth transition for transform
        left: `${mouseHelps.origin.x}`, // Left position
        top: `${mouseHelps.origin.y}`, // Top position
        cursor: 'grabbing', // Cursor style during drag
        display: 'block' // Display as block
    } as React.CSSProperties;

    // lightBulb is displayed when studying
    const lightBulbStyle = {
        width: BOX_W * AGENT_W * 0.5, // Half the width of the agent
        height: BOX_H * AGENT_H * 0.5, // Half the height of the agent
        borderRadius: 0, // No border radius
        background: `url(${"light_bulb.png"})`, // Background image for the light bulb
        backgroundPosition: '50% 50%', // Center the background image
        overflow: 'hidden', // Hide overflow
        backgroundSize: '100% 100%', // Scale the background image to fit
        backgroundRepeat: 'no-repeat', // Prevent background image from repeating
        position: "absolute", // Absolute positioning
        zIndex: 4, // Stacking order
        transform: `translate(${mouseHelps.translation.x}px, ${mouseHelps.translation.y}px`, // Apply translation during drag
        transition: 'transform 50ms', // Smooth transition for transform
        left: `${mouseHelps.origin.x}`, // Left position
        top: `${mouseHelps.origin.y}`, // Top position
        cursor: 'grabbing', // Cursor style during drag
        display: 'block' // Display as block
    } as React.CSSProperties;

    // Style for the agent when not being dragged
    const parentStyle = {
        width: BOX_W * AGENT_W, // Width of the agent
        height: BOX_H * AGENT_H, // Height of the agent
        borderRadius: 0, // No border radius
        background: "url('" + agentIdToImg[imgid] + "')", // Background image based on imgid
        backgroundPosition: '50% 50%', // Center the background image
        overflow: 'hidden', // Hide overflow
        backgroundSize: '100% 100%', // Scale the background image to fit
        position: "absolute", // Absolute positioning
        backgroundRepeat: 'no-repeat', // Prevent background image from repeating
        cursor: 'grab', // Cursor style when not dragging
        zIndex: 4, // Stacking order
        left: myPos.x * BOX_W, // Left position based on agent's grid position
        top: myPos.y * BOX_H, // Top position based on agent's grid position
        display: 'block' // Display as block
    } as React.CSSProperties;

    // Determine which style to use based on whether the agent is being dragged
    const styleToUse = dragP ? myStyle : parentStyle;

    // Handle mouse down event (start of drag)
    const handleMouseDown = useCallback((evt: React.MouseEvent) => {
        evt.preventDefault(); // Prevent default behavior
        const element = evt.currentTarget as HTMLElement; // Get the target element
        const clientX = evt.clientX; // Get the mouse X position
        const clientY = evt.clientY; // Get the mouse Y position

        stTime.current = new Date(); // Record the start time
        stLoc.current = { x: evt.clientX / BOX_W, y: evt.clientY / BOX_H }; // Record the start location

        setDragP(dragP => true); // Set drag state to true
        setMouseHelps(mouseHelps => ({
            ...mouseHelps,
            origin: { x: clientX, y: clientY } // Update the origin of the drag
        }));
        setShowOverlay(showOverlay => false); // Hide the overlay

        dispatch({
            type: MOUSE_DOWN,
            payload: {
                id: myId,
                mouseX: clientX / BOX_W,
                mouseY: clientY / BOX_H
            }
        }); // Dispatch MOUSE_DOWN action
        dispatch(makeAfterMouseMoveCancelTask(myId)); // Dispatch a task to cancel after mouse move

        // Update position to make mouse move clear
        const offsetX = (BOX_W * AGENT_W) / 2; // Calculate X offset
        const offsetY = (BOX_H * AGENT_H) / 2; // Calculate Y offset
        element.style.left = `${clientX - offsetX}px`; // Update element's left position
        element.style.top = `${clientY - offsetY}px`; // Update element's top position

    }, [myId, dispatch]);

    // Handle mouse move event (during drag)
    const handleMouseMove = useCallback((evt: MouseEvent) => {
        evt.preventDefault(); // Prevent default behavior
        const clientX = evt.clientX; // Get the mouse X position
        const clientY = evt.clientY; // Get the mouse Y position
        const translation = {
            x: clientX - mouseHelps.origin.x, // Calculate X translation
            y: clientY - mouseHelps.origin.y // Calculate Y translation
        };
        setMouseHelps(mouseHelps => ({
            ...mouseHelps,
            translation // Update the translation
        }))
        dispatch({
            type: MOUSE_DOWN_MOVE,
            payload: {
                id: myId,
                mouseX: clientX / BOX_W,
                mouseY: clientY / BOX_H
            }
        }) // Dispatch MOUSE_DOWN_MOVE action
    }, [mouseHelps.origin, myId, dispatch]);

    // Handle mouse up event (end of drag)
    const handleMouseUp = useCallback((evt: MouseEvent) => {
        evt.preventDefault(); // Prevent default behavior
        const endTime = new Date(); // Record the end time
        let newClientX = evt.clientX; // Get the mouse X position
        let newClientY = evt.clientY; // Get the mouse Y position

        // Limit the coordinates to the grid boundaries
        if (newClientX < 0) newClientX = 0;
        if (newClientY < 0) newClientY = 0;
        if (newClientX > GRID_W * BOX_W) newClientX = (GRID_W - 1) * BOX_W;
        if (newClientY > GRID_H * BOX_H) newClientY = (GRID_H - 1) * BOX_H;

        const myRoundPt = retCorPos({ x: newClientX / BOX_W, y: newClientY / BOX_H }, false); // Round the coordinates to the grid

        //calculate collisions for mouse up position
        const collisions = agentPelletCollision(
            [{ x: myRoundPt.x, y: myRoundPt.y }],
            latestStateRef.current.pellet_pos
        );
        const releaseScore = collisions.length * PELLET_FEEDBACK;
        if (collisions.length > 0) {
            dispatch({
                type: COLLISION,
                payload: { cols: collisions }
            });
        }
        
        dispatch(makeAfterMouseMoveCancelTask(myId)); // Dispatch a task to cancel after mouse move
        setDragP(false); // Set drag state to false
        dispatch({
            type: MOUSE_UP,
            payload: {
                id: myId,
                mouseX: myRoundPt.x,
                mouseY: myRoundPt.y
            }
        }); // Dispatch MOUSE_UP action

        dispatch({
            type: SAVE_TRAJ,
            payload: {
                agent_st_pos: stLoc.current, // Start position
                agent_end_pos: myRoundPt, // End position
                agent_id: myId, // Agent ID
                was_dragP: true, // Whether it was a drag operation
                st_time: stTime.current, // Start time
                end_time: endTime, // End time
                got_pellet: false, // Whether the agent got a pellet
                duration: endTime.valueOf() - stTime.current.valueOf(), // Duration of the drag
                agent_type: myAgent // Agent type
            }
        }); // Dispatch SAVE_TRAJ action for global data
        const trajData: TrajDataType = {
            agent_st_pos: stLoc.current, // Start position
            agent_end_pos: myRoundPt, // End position
            agent_id: myId, // Agent ID
            was_dragP: true, // Whether it was a drag operation
            st_time: stTime.current, // Start time
            end_time: endTime, // End time
            got_pelletP: false, // Whether the agent got a pellet
            duration: endTime.valueOf() - stTime.current.valueOf(), // Duration of the drag
            agent_type: myAgent, // Agent type
            start_state: latestStateRef.current,
            feedback: releaseScore
        };
        myAgent.addTrajData(trajData);
    }, [myId, myAgent, dispatch]);

    // Simulate a drag operation to a specific grid position
    function simulateDragTo(
        startPosition: { x: number; y: number }, // Start position (grid coordinates)
        endPosition: { x: number; y: number },   // End position (grid coordinates)
        id: number                               // Agent ID
      ) {
        const element = document.getElementById(`agent-${id}`); // Get the agent element
        if (!element) {
          console.error(`Element with ID agent-${id} not found`); // Log error if element not found
          return;
        }
      
        // Convert start position from grid coordinates to pixel coordinates
        const startPixelX = startPosition.x * BOX_W;
        const startPixelY = startPosition.y * BOX_H;
      
        // Convert end position from grid coordinates to pixel coordinates
        const endPixelX = endPosition.x * BOX_W;
        const endPixelY = endPosition.y * BOX_H;
      
        // Simulate mouse down event at the start position
        const simulatedMouseDownEvent = {
          preventDefault: () => { },
          currentTarget: element,
          clientX: startPixelX,
          clientY: startPixelY,
        };
        handleMouseDown(simulatedMouseDownEvent as any); // Trigger mouse down handler
      
        // Simulate mouse move event to the end position
        const simulatedMouseMoveEvent = {
          preventDefault: () => { },
          clientX: endPixelX,
          clientY: endPixelY,
        };
        handleMouseMove(simulatedMouseMoveEvent as any);
      
        // Simulate mouse up event at the end position
        setTimeout(() => {
          const simulatedMouseUpEvent = {
            preventDefault: () => { },
            clientX: endPixelX,
            clientY: endPixelY,
          };
          handleMouseUp(simulatedMouseUpEvent as any); // Trigger mouse up handler
          dispatch(clearAutoDragRequest(id));         // Clear the auto-drag request
        }, 0); // Execute after a short delay
      }

    // Handle auto-drag requests
    useEffect(() => {
        autoDragRequest.forEach((request: AutoDragRequest) => {
          if (request.id === myId) {
            const { startPosition, endPosition } = request; // Get start and end positions
            simulateDragTo(startPosition, endPosition, request.id); // Simulate drag from start to end
          }
        });
      }, [autoDragRequest, myId]);

    // Add or remove mouse move and mouse up event listeners based on drag state
    useEffect(() => {
        if (dragP) {
            window.addEventListener('mousemove', handleMouseMove); // Add mouse move listener
            window.addEventListener('mouseup', handleMouseUp); // Add mouse up listener
        } else {
            window.removeEventListener('mousemove', handleMouseMove); // Remove mouse move listener
            window.removeEventListener('mouseup', handleMouseUp); // Remove mouse up listener
        }
        setMouseHelps(mouseHelps => ({
            ...mouseHelps,
            translation: POSITION // Reset translation when drag ends
        }));

    }, [dragP, handleMouseMove, handleMouseUp]);

    //tract state
    useEffect(() => {
        latestStateRef.current = currentState;
      }, [currentState]);

    // Render the agent and overlay
    return (
        <>
            <div
                id={`agent-${myId}`} // Unique ID for the agent
                className="agent" // CSS class
                draggable="true" // Make the agent draggable
                style={styleToUse} // Apply the appropriate style
                onMouseDown={handleMouseDown} // Handle mouse down event
                onMouseEnter={() => setShowOverlay(true)} // Show overlay on mouse enter
                onMouseLeave={() => setShowOverlay(false)} // Hide overlay on mouse leave
            >
                {/* Render a light bulb overlay if the agent is learning */}
                {/* {(myAgent as QLearnAgent).isLearning && <div
                    className="lightbulb"
                    style={lightBulbStyle}
                />} */}
            </div>

            {/* Render the overlay if not dragging and overlay is visible */}
            {!dragP && showOverlay && myAgent.vizOverlay() && <div
                className='agentoverlay'
                style={{
                    ...parentStyle,
                    background: 'rgba(0,50,200,0.5)', // Semi-transparent blue background
                    borderRadius: '50%', // Circular shape
                    left: myPos.x * BOX_W - GREEDY_MAX_VIS * AGENT_W * BOX_W + AGENT_W * 0.5 * BOX_W, // Calculate left position
                    top: myPos.y * BOX_H - GREEDY_MAX_VIS * AGENT_H * BOX_H + AGENT_H * 0.5 * BOX_H, // Calculate top position
                    width: GREEDY_MAX_VIS * BOX_W, // Width of the overlay
                    height: GREEDY_MAX_VIS * BOX_H, // Height of the overlay
                    zIndex: 3 // Stacking order
                }}
            />}
        </>
    )
}

export default Agent; 