import { Action } from "redux";
import { TrajDataType, TrajType } from "../../components/DataLog";
import Roomba from "../../Roombas/Roomba";
import { IObjCoord,IQvalue } from "../../utils";

//Actions define the operations required by reducers and sagas
export const MOUSE_DOWN = "MOUSE_DOWN";
export const MOUSE_DOWN_MOVE = "MOUSE_DOWN_MOVE";
export const MOUSE_UP = "MOUSE_UP";
export const MOUSE_MOVE_SUCCESS = "MOUSE_MOVE_SUCCESS"
export const COLLISION = "COLLISION";
export const SELF_MOVE_START = "SELF_MOVE_START";
export const SELF_MOVE_STEP = "SELF_MOVE_STEP";
export const CONSIDER_SELF_MOVE_START = "CONSIDER_SELF_MOVE_START"
export const END_SELF_MOVE = "END_SELF_MOVE"
export const SAGA_END_SELF_MOVE = "SAGA_END_SELF_MOVE"
export const COLLISIONS = "COLLISIONS"
export const CREATE_PELLET = "CREATE_PELLET"
export const SAVE_TRAJ = 'SAVE_TRAJ';
export const ADD_QRESULT = 'ADD_QRESULT';
export const TRIGGER_AUTO_DRAG = 'TRIGGER_AUTO_DRAG';
export const CLEAR_AUTO_DRAG_REQUEST = 'CLEAR_AUTO_DRAG_REQUEST';

export const sendsimulations = (newRecord: IQvalue) => ({
    type: 'ADD_QRESULT',
    payload: newRecord
});

export const makeMouseMove = (mousePos: IObjCoord) => ({
    type: MOUSE_DOWN_MOVE,
    payload: mousePos
});

export const mouseMoveSuccess = (obj: any) => ({
    type: MOUSE_MOVE_SUCCESS,
    payload: {data: 'dummy'}
});

export const sagaMoveEndBlocking = (id: number) => ({
    type: SAGA_END_SELF_MOVE,
    payload: {
        id
    }
})

export const mouseMoveDownAction = (act: {type: string, payload: {id: number, mouseX: number, mouseY: number}}) => (act);

export const makeSmallSelfMove = (moveTo: IObjCoord, agentId: number) => ({
    type: SELF_MOVE_STEP,
    payload: {
        newPos: moveTo,
        id: agentId
    }
});

export const considerSelfMove = (agentId: number) => ({
    type: CONSIDER_SELF_MOVE_START,
    payload: {
        id: agentId,
    }
})

export const selfMoveAction = (move: MoveArgs) => ({
        type: CONSIDER_SELF_MOVE_START,
        payload: move
})

export interface MoveArgs extends Action {
    agentPos: IObjCoord,
    id: number,
    agentFn: Roomba
}

export interface SelfMoveArgs  {
    type: string,
    payload: MoveArgs
}

export interface SaveTrajArgs {
    type: string,
    payload: TrajDataType
}

export const createNewSelfMove = (selfMove: MoveArgs) => ({
    type: SELF_MOVE_START,
    payload: selfMove
})

export const createEndSelfMove = (id: number) => ({
    type: END_SELF_MOVE,
    payload: {
        id
    }
}) 

export const makeAfterMouseMoveCancelTask = (id: number) => ({
    type: "CANCEL_SELF_MOVE_AGENT_" + id,
    payload: {
        id
    }
})

export const makeAfterMouseMoveCancelTaskNameOnly = 
    (id: number) => makeAfterMouseMoveCancelTask(id).type;

export const createPelletAction = (pos: IObjCoord, feedback = 3) => ({
    type: CREATE_PELLET,
    payload: {
        pos,
        feedback
    }
});
    
export const makeSaveTrajAction = (traj: TrajDataType) => ({
    type: SAVE_TRAJ,
    payload: traj
}) 

export const triggerAutoDrag = (
    agentId: number,
    startPosition: { x: number; y: number }, 
    endPosition: { x: number; y: number }    
  ) => ({
    type: 'TRIGGER_AUTO_DRAG',
    payload: {
      id: agentId,
      startPosition, 
      endPosition    
    }
  });

export const clearAutoDragRequest = (id: number) => ({
    type: CLEAR_AUTO_DRAG_REQUEST,
    payload: { id },
});

export const PARAMETERS_READY = 'PARAMETERS_READY';