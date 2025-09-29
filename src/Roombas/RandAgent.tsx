import { TrajDataType } from '../components/DataLog';
import {MOVES_N, allMoves, GRID_H, GRID_W, IObjCoord, IGlobalState, AGENT_W, AGENT_H} from '../utils/index'
import Roomba from './Roomba';

// Define the RandAgent class, which response for random action
class RandAgent extends Roomba {
    // Constructor to initialize the RandAgent with a unique ID
    constructor(id:number) {
        super(id); // Call the constructor of the parent class (Roomba)
    }

    // Static method to determine a random valid move for the agent
    static getMove(curXBoxN:number, curYBoxN:number, pelletPos?: IObjCoord [], agentMoves?: IGlobalState) : IObjCoord {
        const possMoves = []; // Array to store all possible valid moves
        let numPossMoves = 0; // Counter to track the number of valid moves

        // Iterate through all possible moves (defined in allMoves)
        for (let i = 0; i < MOVES_N; i++) {
            const curPossMove = allMoves[i]; // Get the current move from the list of all moves
            const possX = curPossMove.x; // Extract the x-coordinate of the move
            const possY = curPossMove.y; // Extract the y-coordinate of the move

            // Check if the move is valid (i.e., within the grid boundaries)
            if ((possX + curXBoxN >= 0) && (possX+curXBoxN < GRID_W) &&
                (possY + curYBoxN >= 0) && (possY+curYBoxN < GRID_H)) {
                    // Adjust the move if it would take the agent outside the grid on the right or bottom
                    let xToPush = (possX+curXBoxN +AGENT_W > GRID_W) ? Math.min(1, GRID_W -AGENT_W) : possX;
                    let yToPush = (possY+curYBoxN +AGENT_H > GRID_H) ? Math.min(1, GRID_H -AGENT_H) : possY;

                    // Adjust the move if it would take the agent outside the grid on the left or top
                    xToPush = (possX+curXBoxN < 0) ? curXBoxN : xToPush;
                    yToPush = (possY + curYBoxN < 0) ? curYBoxN : yToPush;

                    // Create a move object with the adjusted coordinates
                    const moveToPush = {
                        x: xToPush,
                        y: yToPush,
                    }
                    possMoves.push(moveToPush); // Add the valid move to the list of possible moves
                    numPossMoves += 1; // Increment the counter for valid moves
            }
        }

        // If no valid moves are found, generate a move to bring the agent back into the grid
        if (possMoves.length === 0) {
            console.log('we in bad spot. -- make move to fix'); // Log a warning message
            const moveToPush = {
                x: -(curXBoxN - GRID_W+AGENT_W), // Calculate a move to bring the agent back into the grid on the x-axis
                y: -(curYBoxN - GRID_H+AGENT_H) // Calculate a move to bring the agent back into the grid on the y-axis
            }
            return moveToPush; // Return the corrective move
        }

        // Randomly select a move from the list of valid moves
        const myMoveI = Math.floor(Math.random()*numPossMoves); // Generate a random index
        return possMoves[myMoveI]; // Return the move at the randomly selected index
    }

    // Instance method to get the next move for the agent
    getMove(curXBoxN:number, curYBoxN:number, pelletPos?: IObjCoord [], curGState?: IGlobalState) : IObjCoord {
        return RandAgent.getMove(curXBoxN, curYBoxN, pelletPos, curGState); // Call the static getMove method
    }

    addTrajData(trajData: TrajDataType) {
    }

    toString() :string {
        return 'RandAgent' + this._myId; 
    }

    vizOverlay(): boolean {
        return false; 
    }
}

export default RandAgent;