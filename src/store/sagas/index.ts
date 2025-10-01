import { CallEffect, put, delay,PutEffect, take, select,
     cancelled, CancelledEffect, takeEvery, spawn,
     race, call, StrictEffect, SelectEffect, ForkEffect, takeLatest } from "@redux-saga/core/effects";
import { Action } from "redux";
import { addAgentTraj, getAgentData, autoDrag, TrajDataType, calculateAction } from "../../components/DataLog";
import { agentSelfActionOverT, BOX_H, BOX_W,
        EXPECTED_PELLET_TIME, IGlobalState,
        GRID_H, GRID_W,
        IObjCoord, MAX_STEP_SIZE, RFH_TIME,WAIT_TIME, REL_PELLET_SIZE, PELLET_MODE, PELLET_PATCH_MEAN2, PELLET_PATCH_VAR2,
         retCorPos, calcDist, ROUND_EPS, IQvalue, PELLET_TILES,PELLET_TILE_PROPS } from "../../utils";

import { makeSmallSelfMove, MoveArgs, createEndSelfMove, SelfMoveArgs,
     SAGA_END_SELF_MOVE, sagaMoveEndBlocking, makeAfterMouseMoveCancelTaskNameOnly,
     createPelletAction, SAVE_TRAJ, SaveTrajArgs, makeSaveTrajAction, triggerAutoDrag, sendsimulations, PARAMETERS_READY} from "../actions";
import Roomba from "../../Roombas/Roomba";
import QLearnAgent from "../../Roombas/QLearningAgent";
import QLearnAgent2 from "../../Roombas/QLearningAgent2";
import { agentInsts } from "../../components/Grid";
import ExpectedProbabilityCalculator from "../../components/ExpectedQvalue";


// Helper function to get a subset of the global state using a selector
function getSubState<T>(selector: (s:IGlobalState) => T): SelectEffect {
    return select(selector);
  }

// Helper function to get the full global state
function getFullState() : SelectEffect {
    return select((s:IGlobalState) => s);
}

// Saga to handle self-movement of agents
function * selfMoveSaga(payload : any [] ) :
Generator< PutEffect<{type: string, payload: {newPos: IObjCoord, id: number}}>
    | PutEffect<{type: string, payload: {id: number}}>
    | PutEffect<{type: string, payload: TrajDataType}>
    | CallEffect
    | CancelledEffect
    | SelectEffect
    | ForkEffect<any>
>{
    if (payload === undefined || payload[0] === undefined) {
        console.log('selfMoveSaga got an undefined payload...')
        return undefined;
    }
    const myMove : MoveArgs = payload[0].payload as MoveArgs; // Extract the move arguments
    const myAgentId = myMove.id; // Get the agent ID
    const myRoomba : Roomba = myMove.agentFn; // Get the agent's Roomba instance
    const myStPos : IObjCoord = myMove.agentPos; // Get the agent's starting position

    // If the agent is a Q-learning agent, spawn a learning saga
    if ((myRoomba instanceof QLearnAgent) || (myRoomba instanceof QLearnAgent2)) {
        yield spawn(callLearnSaga, myRoomba);
    }

    yield delay(WAIT_TIME*1000); 

    const stTime = new Date(); // Record the start time
    const prevFullState = yield getFullState(); // Get the full state before the move
    const prevTFullState = prevFullState as IGlobalState; // Cast to the global state type

    const curPelletPos = yield getSubState<IObjCoord []>((state: IGlobalState) => (state.pellet_pos)); // Get the current pellet positions

    let gotNewMoveP = false; // Flag to check if a valid move has been found
    let newPos:IObjCoord = {x: 0, y:0}; // Initialize the new position
    while (gotNewMoveP === false) {
        const newAct : IObjCoord = myRoomba.getMove(myStPos.x, myStPos.y,
                                            curPelletPos as IObjCoord[],
                                            prevTFullState); // Get the next move from the agent
        newPos = retCorPos({
            x: newAct.x+myStPos.x,
            y: newAct.y+myStPos.y
        }); // Calculate the new position
        gotNewMoveP = calcDist(myStPos, newPos) > ROUND_EPS; // Check if the move is valid
    }

    if (calcDist(newPos, retCorPos(newPos, true)) <= ROUND_EPS) {
        newPos = retCorPos(newPos, true); // Round the position if necessary
    }

    // The actual move
    let myMoveGen = agentSelfActionOverT(myStPos, newPos); // Create a generator for the move
    let doneP = false; // Flag to check if the move is complete
    let optimal = !autoDrag(myAgentId,myStPos,newPos)

    // get q value and expected q value
    const action = calculateAction(myStPos, newPos);
    let qValue: number | undefined;
    let expected_qValue: number | undefined;
    if (myRoomba instanceof QLearnAgent || myRoomba instanceof QLearnAgent2) {
    qValue = myRoomba._myQTable.get({
        myPos: { x: myStPos.x, y: myStPos.y },
        action: action
    });
    }
    const expectedProbCalculator = new ExpectedProbabilityCalculator();
    expected_qValue = expectedProbCalculator.findActionProbability(
        myStPos.x, 
        myStPos.y, 
        action
    );

    // Save the unfinished trajectory (because it could be cancelled during the update)
    yield put(makeSaveTrajAction({
        agent_st_pos: myStPos,
        agent_id: myAgentId,
        qValue: qValue,
        expected_qValue: expected_qValue,
        was_dragP: false,
        st_time: stTime,
        start_state: prevTFullState,
        is_optimal: optimal
    }))
    try {
        const scoreSt = prevTFullState.agent_scores[myAgentId]; // Get the agent's starting score
        while (!doneP) {
            let smallStep = myMoveGen.next(); // Get the next step in the move
            if (!smallStep.done) {
                const smallStepVal :IObjCoord = smallStep.value as IObjCoord; // Extract the step value

                if (smallStepVal === undefined) {
                    console.log('bad step, bad') // Log an error if the step is invalid
                }

                const stDist = Math.sqrt(Math.pow(smallStepVal.x-myStPos.x,2)+
                                         Math.pow(smallStepVal.y-myStPos.y,2)); // Calculate the distance from the start
                const endDist = Math.sqrt(Math.pow(smallStepVal.x-newPos.x,2)+
                                          Math.pow(smallStepVal.y-newPos.y,2)); // Calculate the distance to the end

                if ((stDist > MAX_STEP_SIZE) ||
                    (endDist > MAX_STEP_SIZE)) {
                    console.log( 'Agent: ' + myAgentId + ', ttooo big step size sagas') // Log an error if the step is too large
                    console.log(' BIG MOVE IS BEING TAKEN')
                 }
                    yield put(makeSmallSelfMove({x: smallStepVal.x * BOX_W, y: smallStepVal.y*BOX_H},
                                                myAgentId)); // Dispatch the small move action
            }

            // if (smallStep.done) {
            //     const agentId = myMove.id;
            //     const st_pos_x = myStPos.x;
            //     const st_pos_y = myStPos.y;
                
            //     if (autoDrag(agentId,myStPos,newPos)) {yield put(triggerAutoDrag(agentId,{ x: st_pos_x, y: st_pos_y },{ x: st_pos_x, y: st_pos_y }))}

            // }

            if (!doneP) doneP = smallStep.done as boolean; // Check if the move is complete
            yield delay(RFH_TIME); // Wait for a specified time (60ms)
        }
        const endTime = new Date(); // Record the end time
        put(sagaMoveEndBlocking(myAgentId)); // Dispatch the end move action
        const endState = yield getFullState(); // Get the full state after the move
        const typedEndState = endState as IGlobalState; // Cast to the global state type
        const scoreEnd = typedEndState.agent_scores[myAgentId]; // Get the agent's ending score

        const endTrajData :TrajDataType = {
            agent_st_pos: myStPos,
            agent_end_pos: newPos,
            agent_id: myAgentId,
            was_dragP: false,
            st_time: stTime,
            cancelP: false,
            end_time: endTime,
            duration: endTime.valueOf() - stTime.valueOf(),
            start_state: prevTFullState,
            cur_state: typedEndState,
            feedback: scoreEnd-scoreSt
        }; // Create the trajectory data
        yield call(saveDataSagas, makeSaveTrajAction(endTrajData)); // Save the trajectory data
        myRoomba.addTrajData(endTrajData); // Add the trajectory data to the agent

        return;

    } finally {
        if (yield cancelled()){
            console.log('self move cancelled!!') // Log if the move was cancelled
            const cancTime = new Date(); // Record the cancellation time
            const cancState = yield getFullState();
            // Get feedback before canceled
            const typedCancState = cancState as IGlobalState;
            const cancScore = typedCancState.agent_scores[myAgentId];
            const feedback = cancScore - prevTFullState.agent_scores[myAgentId];

            put(sagaMoveEndBlocking(myAgentId)); // Dispatch the end move action
            const endState = yield getFullState(); // Get the full state after cancellation
            const cancTrajData : TrajDataType = {
                agent_st_pos: myStPos,
                agent_id: myAgentId,
                was_dragP: false,
                st_time: stTime,
                cancelP: true,
                is_optimal: optimal,
                qValue: qValue,
                expected_qValue: expected_qValue,
                end_time: cancTime,
                duration: cancTime.valueOf() - stTime.valueOf(),
                start_state: prevTFullState,
                cur_state: endState as IGlobalState,
                agent_try_pos: newPos,
                feedback: feedback
            } // Create the cancellation trajectory data
            yield put(makeSaveTrajAction(cancTrajData)); // Save the cancellation trajectory data
            myRoomba.addTrajData(cancTrajData); // Add the cancellation trajectory data to the agent
            return undefined;
        }
    }
}

// Saga to handle the end of a self-move
function * endSelfMoveSaga(args: any []) {
    const myMove = args[0].payload as MoveArgs; // Extract the move arguments
    yield put(createEndSelfMove(myMove.id)); // Dispatch the end move action
}

// Saga to self-move vs drag
function * handleSelfMoveSaga(fnArgs : Action):any{
    const args : SelfMoveArgs= fnArgs as SelfMoveArgs; // Cast the arguments to the correct type
    const myAgentId = args.payload.id; // Get the agent ID

    const cancelActionNameToWatch = makeAfterMouseMoveCancelTaskNameOnly(myAgentId); // Get the cancel action name
    const raceResult = yield race({
        selfMove: call(selfMoveSaga, [args]), // Start the self-move saga
        cancelMove: take(cancelActionNameToWatch) // Watch for a cancel action
    });

    // This section is commented out but can be enabled to simulate actions and send Q-results
    // if ('selfMove' in raceResult) {
    //     const newQResult:IQvalue = (agentInsts[myAgentId] as QLearnAgent).simulateActions();
    //     yield put (sendsimulations(newQResult));
    // } else if ('cancelMove' in raceResult) {
    //     const newQResult:IQvalue = (agentInsts[myAgentId] as QLearnAgent).simulateActions();
    //     yield put (sendsimulations(newQResult));
    // }

    yield call(endSelfMoveSaga, [args]); // Call the end self-move saga
}

// Saga to call the learning process for a Q-learning agent
function * callLearnSaga(myArg: QLearnAgent | QLearnAgent2) : Generator<CallEffect> {
    if (myArg instanceof QLearnAgent) {
        yield call(helpCallMyLearn, myArg) // Call the learning process for QLearnAgent
    }
    else if (myArg instanceof QLearnAgent2) {
        yield call(helpCallMyLearn2, myArg) // Call the learning process for QLearnAgent2
    }
}

// Helper function to call the learning process for QLearnAgent
function helpCallMyLearn(myArg:QLearnAgent) {
    myArg?.runLearn(); // Run the learning process
}

// Helper function to call the learning process for QLearnAgent2
function helpCallMyLearn2(myArg:QLearnAgent2) {
    myArg?.runLearn(); // Run the learning process
}

// Saga to create pellets at random positions
function * pelletCreatorSaga() :
Generator<PutEffect|CallEffect>
 {
    console.log('starting to make pellets') // Log the start of pellet creation
    try {
    while (true) {
        let pelletPos : IObjCoord; // Initialize the pellet position
        let xPos: number = 5;
        let yPos: number = 5;

        const randNum = Math.random(); // Generate a random number
        const nextWaitTime = -Math.log(randNum)*EXPECTED_PELLET_TIME; // Calculate the next wait time
        yield delay(nextWaitTime); // Wait for the calculated time
        let isInsideGrid = false; // Flag to check if the pellet is inside the grid
        while (!isInsideGrid) {
            switch (PELLET_MODE as number){
            case 0:
                xPos = Math.random() * (GRID_W-REL_PELLET_SIZE); // Random position for mode 0
                yPos = Math.random() * (GRID_H-REL_PELLET_SIZE);
                break;
            case 1:
                let pickMode = Math.floor(2*Math.random()); // Random mode for mode 1
                const u1 = Math.random();
                const u2 = Math.random();

                const z0 = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2); // Generate a normal distribution value
                const z1 = Math.sqrt(-2.0 * Math.log(u1)) * Math.sin(2.0 * Math.PI * u2);
                xPos = z0*PELLET_PATCH_VAR2[pickMode][0]+PELLET_PATCH_MEAN2[pickMode][0]; // Calculate the x position
                yPos = z1*PELLET_PATCH_VAR2[pickMode][1]+PELLET_PATCH_MEAN2[pickMode][1]; // Calculate the y position
                break;
            case 2:
                const pelletTiles = PELLET_TILES;
                const pelletTileProps = PELLET_TILE_PROPS;
                const randVal = Math.random();
                let cumProb = 0;
                let selectedTile: number[] = pelletTiles[0];
                for (let i=0; i<pelletTileProps.length; i++) {
                    cumProb += pelletTileProps[i];
                    if (randVal <= cumProb) {
                        selectedTile = pelletTiles[i];
                        break;
                    }
                }
//                const selectedTile = pelletTiles[Math.floor(Math.random() * pelletTiles.length)];
                xPos = selectedTile[0] + Math.random()* (1 - REL_PELLET_SIZE); 
                yPos = selectedTile[1] + Math.random()* (1 - REL_PELLET_SIZE);
                break;
            }
            xPos = Math.min(Math.max(0, xPos), GRID_W - REL_PELLET_SIZE); // Ensure the x position is within the grid
            yPos = Math.min(Math.max(0, yPos), GRID_H - REL_PELLET_SIZE); // Ensure the y position is within the grid

            isInsideGrid = xPos >= 0 && xPos < GRID_W && yPos >= 0 && yPos < GRID_H; // Check if the position is inside the grid
        }
        pelletPos = {x: xPos, y: yPos}; // Set the pellet position

        yield(put(createPelletAction(pelletPos))); // Dispatch the create pellet action
    }
    }
    catch (e) {
        console.log('got error ' + e + ' in pelletCreatorSaga'); // Log any errors
    }
 }

 // Saga to save trajectory data
 function * saveDataSagas(curAction: Action) : Generator<StrictEffect>
 {
    const args : SaveTrajArgs = curAction as SaveTrajArgs; // Cast the arguments to the correct type
    const myTraj : TrajDataType = args.payload; // Extract the trajectory data
    if (myTraj.cur_state !== undefined) {
        yield call(addAgentTraj, myTraj); // Save the trajectory data
    }
    else {
        const curState = yield getFullState(); // Get the full state
        const myTrajData: TrajDataType = {...myTraj, cur_state: curState as IGlobalState}; // Add the current state to the trajectory data
        yield call(addAgentTraj, myTrajData); // Save the trajectory data
        const myRoomba = args.payload.agent_type; // Get the agent's Roomba instance
        myRoomba?.addTrajData(myTrajData); // Add the trajectory data to the agent
    }
 }

// Watcher saga to handle various actions
function * watcherSagas( ) : Generator<StrictEffect>  {
    yield takeLatest(PARAMETERS_READY, pelletCreatorSaga); // Start the pellet creator saga when parameters are ready

    yield takeEvery(SAVE_TRAJ, saveDataSagas); // Handle save trajectory actions

    while (true) {
        try {
            yield takeEvery('SELF_MOVE_START', handleSelfMoveSaga); // Handle self-move start actions
            yield take(SAGA_END_SELF_MOVE); // Handle end self-move actions
        }
        catch (e) {
            console.log('got an error ', e); // Log any errors
        }
    }
}

export default watcherSagas;