import React, { useEffect } from 'react';
import ReactDOM from 'react-dom';
import axios from 'axios';
import Roomba from "../Roombas/Roomba"; 
import { QIndex } from "../Roombas/QLearningAgent";
import QLearnAgent from "../Roombas/QLearningAgent"; 
import QLearnAgent2 from "../Roombas/QLearningAgent2";
import { getSessionStorageParam } from './parameters';

//Parameters
export const NUM_AGENTS = getSessionStorageParam<number>('NUM_AGENTS', 1);
export const PELLET_PATCH_MEAN2 = getSessionStorageParam<number[][]>('PELLET_PATCH_MEAN2', [[3, 3], [3, 3]]);
export const PELLET_PATCH_VAR2 = getSessionStorageParam<number[][]>('PELLET_PATCH_VAR2', [[0.75, 0.75], [0.75, 0.75]]);
export const EXPECTED_PELLET_TIME = getSessionStorageParam<number>('EXPECTED_PELLET_TIME', 100);
export const AGENT_EPS = getSessionStorageParam<number>('AGENT_EPS', 0.3);
export const TEACH_EPS = getSessionStorageParam<number>('TEACH_EPS', 1);
export const MOVE_TIME = getSessionStorageParam<number>('MOVE_TIME', 2);
export const WAIT_TIME = getSessionStorageParam<number>('WAIT_TIME', 0);
export const Q_STEP_COST = getSessionStorageParam<number>('Q_STEP_COST', -1);
export const HUM_INT_FB = getSessionStorageParam<number>('HUM_INT_FB', -12);
export const PELLET_FEEDBACK = getSessionStorageParam<number>('PELLET_FEEDBACK', 6);
export const INTERPRET_TYPE = (() => {
    const username = Number(sessionStorage.getItem("userID")); // Convert username to an integer
    if (isNaN(username)) {
        console.error("Invalid username. Cannot determine INTERPRET_TYPE.");
        return 0; // Default to 0 if username is invalid
    }

    const candidates = [0, 1, 2, 3, 4, 5]; // Candidate values for INTERPRET_TYPE
    const index = (username - 1) % candidates.length; // Determine the index in the candidates array
    return candidates[index];
})();
export const PELLET_TILES = getSessionStorageParam<number[][]>(
  'PELLET_TILES', 
  [[0, 1], [7, 0], [3, 1], [1, 4], [7, 4], [2, 0], [7, 7], [7, 3], [4, 0], [2, 7], [4, 1], [4, 3], [4, 7]]
);

const agentTypeMapping: { [key: string]: typeof QLearnAgent | typeof QLearnAgent2 } = {
  'QLearnAgent': QLearnAgent,
  'QLearnAgent2': QLearnAgent2
};

const storedAgentTypes = getSessionStorageParam<string[]>('agentTypes', ['QLearnAgent2', 'QLearnAgent2','QLearnAgent2']);
export const agentTypes = storedAgentTypes.map(type => agentTypeMapping[type as keyof typeof agentTypeMapping]);

export const dragAllowed = [true, true, true];

export interface IObjCoord {
    x: number,
    y: number
}

export interface IQvalue {
    agentid:number,
    ExpectedQvalue:number
}

export const WIDTH = 600;
export const HEIGHT = 600;
export const GRID_W = 8;
export const GRID_H = 8;
export const BOX_W = (WIDTH/GRID_W);
export const BOX_H = (HEIGHT/GRID_H);

export const AGENT_W = 1;
export const AGENT_H = 1.;

export const REL_PELLET_SIZE = 1./4;

export const GREEDY_MAX_VIS = 6;

export interface IExtradata {
    qResults: IQvalue[];
    autoDragRequests: AutoDragRequest[];
  }

  export interface AutoDragRequest {
    id: number;
    startPosition: { 
      x: number;
      y: number;
    };
    endPosition: { 
      x: number;
      y: number;
    };
  }

// 0 => uniform over board
// 1 => one patch
export const PELLET_MODE = 2;

export const MAX_STEP_SIZE = 2.0;

export const RFH_TIME = 60;

export const Q_INIT = 1;

export const MIN_AXIS_DIFF_QLEARN = 0;

export const ROUND_EPS = 0.01;

export const MOVES_N = 8;

export const allMoves = [
    {x: -1, y: -1}, {x: -1, y: 0}, {x: -1, y: 1},
    {x: 1, y: -1}, {x: 1, y: 0}, {x: 1, y: 1},
    {x: 0, y: -1}, {x: 0, y: 1}
];

export const myWorld = [
    [0,1,1,1,1,1,1,0],
    [2,0,0,0,0,0,0,2],
    [2,0,0,0,0,0,0,2],
    [2,0,0,0,0,0,0,2],
    [2,0,0,0,0,0,0,2],
    [2,0,0,0,0,0,0,2],
    [2,0,0,0,0,0,0,2],
    [0,1,1,1,1,1,1,0],
]

export const agentStSqs = Array.from({ length: NUM_AGENTS }, () => ({
    x: Math.floor(Math.random() * GRID_W),
    y: Math.floor(Math.random() * GRID_H),
  }));

export const agentColors = [
    '#2266aa',
    '#aa2299',
    '#992200'
];

export const pelletColors = [
    '#29e691'
];

export interface NumDict {
    [key: number]: string
}

export const agentIdToImg: NumDict = {
    0:'https://alab.psych.wisc.edu/img/misc/robot0.png',
    1:'https://alab.psych.wisc.edu/img/misc/robot1.png',
    2:'https://alab.psych.wisc.edu/img/misc/robot2.png',
    3:'https://alab.psych.wisc.edu/img/misc/robot3.png',
    4:'https://alab.psych.wisc.edu/img/misc/robot4.png',
    5:'https://alab.psych.wisc.edu/img/misc/robot5.png'
}

 export const gridSqToImg : NumDict = {
    0: 'https://alab.psych.wisc.edu/experiments/intdogs/imgs/tile1.png',
    1: 'https://alab.psych.wisc.edu/experiments/intdogs/imgs/tile1V.png',
    2: 'https://alab.psych.wisc.edu/experiments/intdogs/imgs/tile1H.png'
}

export const pelletImg = 'https://alab.psych.wisc.edu/experiments/intdogs/imgs/garbage.png';

 // myId vs. id is a lil whacky. myId is its index in the redux store
 // id is a unique identifier (for React/DOM purposes)
export interface AgentParamType {
    myPos: IObjCoord,
    id?: string,
    myId: number,
    color: string,
    agentName: string,
    dispatch: any,
    myAgent: Roomba
}

export interface PelletParamType {
    myPos: IObjCoord,
    myType: string,
    id?: string,
    myId: number,
    color: string,
    feedback: (str: string) => number,
    dispatch: any
}


export interface IGlobalState {
    agent_pos: IObjCoord [] | [],
    pellet_pos: IObjCoord [] | [],
    agent_self_move: boolean [],
    agent_drag: number,
    agent_scores: number [],
    tot_num_pellets: number,
    extradata:IExtradata
}


export interface APIndex {
    agentInd: number,
    pelletInd: number
}

// Function to detect collisions between agents and pellets
export const agentPelletCollision = (
    agentPos: IObjCoord[], // Array of agent positions
    pelletPos: IObjCoord[] // Array of pellet positions
) => {
    let retVal: APIndex[] = []; // Array to store collision indices

    // Iterate through each agent's position
    agentPos.forEach((aPos: IObjCoord, aIndex) => {
        // Calculate the center of the agent
        const agentCtX = aPos.x + AGENT_W / 2.;
        const agentCtY = aPos.y + AGENT_H / 2.;

        // Iterate through each pellet's position
        pelletPos.forEach((pPos: IObjCoord, pIndex) => {
            // Calculate the center of the pellet
            const pCtX = pPos.x + REL_PELLET_SIZE * 0.5;
            const pCtY = pPos.y + REL_PELLET_SIZE * 0.5;

            // Calculate the distance between the agent and pellet centers
            const xDiff = Math.abs(agentCtX - pCtX);
            const yDiff = Math.abs(agentCtY - pCtY);

            // Define the maximum allowed distance for a collision
            const maxDiffX = AGENT_W / 2. + REL_PELLET_SIZE * 0.5;
            const maxDiffY = AGENT_H / 2. + REL_PELLET_SIZE * 0.5;

            // Check if a collision has occurred
            if ((xDiff <= maxDiffX) && (yDiff <= maxDiffY)) {
                retVal.push({ agentInd: aIndex, pelletInd: pIndex }); // Store the collision indices
            }
        });
    });

    return retVal; // Return the array of collision indices
};

// Function to round or floor a agent's position
export function retCorPos(pt: IObjCoord, round: boolean = true): IObjCoord {
    let retPt: IObjCoord;

    if (round) {
        retPt = { x: Math.round(pt.x), y: Math.round(pt.y) }; // Round the position
    } else {
        retPt = { x: Math.floor(pt.x), y: Math.floor(pt.y) }; // Floor the position
    }

    return retPt; // Return the adjusted position
}

// Generator function to simulate agent movement over time
export function* agentSelfActionOverT(boxSt: IObjCoord, boxEnd: IObjCoord) {
    const numPieces = Math.round(1000. * MOVE_TIME / RFH_TIME); // Calculate the number of steps
    const xOff = (boxEnd.x - boxSt.x) / numPieces; // Calculate the x-offset per step
    const yOff = (boxEnd.y - boxSt.y) / numPieces; // Calculate the y-offset per step

    // Yield intermediate positions over time
    for (let i = 0; i < (numPieces - 1); i++) {
        yield { x: (boxSt.x + (i * xOff)), y: (boxSt.y + (i * yOff)) };
    }

    yield { x: boxEnd.x, y: boxEnd.y }; // Yield the final position
}

// Function to calculate the distance between two points
export function calcDist(pt1: IObjCoord, pt2: IObjCoord) {
    return Math.sqrt(Math.pow(pt1.x - pt2.x, 2) + Math.pow(pt1.y - pt2.y, 2)); // Return the distance
}

// Custom Map class for storing key-value pairs with complex keys
export class MyMap<K, V> {
    private _ogMap: Map<string, V>; // Internal map for storing values
    private _keys: Array<K>; // Array for storing keys

    constructor() {
        this._ogMap = new Map<string, V>(); // Initialize the internal map
        this._keys = new Array<K>(); // Initialize the keys array
    }

    // Method to get a value by key
    get(key: K): V | undefined {
        return this._ogMap.get(JSON.stringify(key)); // Retrieve the value using the stringified key
    }

    // Method to get a value by a stringified key
    getByStringify(key: string): V | undefined {
        return this._ogMap.get(key); // Retrieve the value directly
    }

    // Method to set a value by key
    set(key: K, val: V) {
        const keyStr = JSON.stringify(key); // Stringify the key

        // Check if the key already exists in the keys array
        const existingKeyIndex = this._keys.findIndex((existingKey) => {
            const existingKeyObj = JSON.parse(JSON.stringify(existingKey));
            const keyObj = JSON.parse(keyStr);
            return existingKeyObj.myPos.x === keyObj.myPos.x && existingKeyObj.myPos.y === keyObj.myPos.y;
        });

        if (existingKeyIndex !== -1) {
            this._keys[existingKeyIndex] = key; // Update the existing key
        } else {
            this._keys.push(key); // Add the new key to the array
        }

        return this._ogMap.set(keyStr, val); // Set the value in the internal map
    }

    // Method to get all keys
    keys() {
        return this._keys; // Return the keys array
    }

    // Method to serialize the map to JSON
    toJSON() {
        return {
            _ogMap: Array.from(this._ogMap.entries()), // Serialize the internal map
            _keys: this._keys // Serialize the keys array
        };
    }

    // Static method to deserialize the map from JSON
    static fromJSON(data: { _ogMap: (string | number)[][]; _keys: { myPos: { x: number; y: number; }; action: number; }[] }): MyMap<any, any> {
        const myMap = new MyMap<any, any>(); // Create a new MyMap instance

        // Populate the internal map from the serialized data
        data._ogMap.forEach((item) => {
            if (item.length === 2 && typeof item[0] === 'string') {
                const [key, value] = item;
                const originalKey = JSON.parse(key); // Parse the original key
                myMap.set(originalKey, value); // Set the value in the map
            } else {
                console.error('Invalid _ogMap item:', item); // Log an error for invalid items
            }
        });

        myMap._keys = data._keys; // Populate the keys array

        return myMap; // Return the deserialized map
    }

    // Method to return a string representation of the map
    public toString() {
        let res = "\n";
        for (let i = 0; i < GRID_H; i++) {
            for (let j = 0; j < GRID_W; j++) {
                let myPos = { x: i, y: j };
                res += JSON.stringify(myPos) + ":\t\t";
                for (let action = 0; action < 9; action++) { // 9 is NUM_ACTIONS
                    let key: QIndex = {
                        myPos,
                        action
                    };
                    let keyK = key as K;
                    let qVal = this.get(keyK);
                    let qValNum = qVal as number;
                    res += qValNum.toFixed(2) + "\t"; // Format the Q-value
                }
                res += "\n";
            }
        }
        return res; // Return the formatted string
    }
}