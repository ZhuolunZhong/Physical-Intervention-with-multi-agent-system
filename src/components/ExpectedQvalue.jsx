import { PELLET_PATCH_MEAN2, PELLET_PATCH_VAR2, GRID_H, GRID_W, PELLET_MODE, PELLET_TILES } from "../utils"; 
import jStat from 'jstat'; 
import { AgentAction } from "../Roombas/QLearningAgent";

// The ExpectedProbabilityCalculator class design for simulations of the policy
class ExpectedProbabilityCalculator {
    constructor() {
        // Initialize means and variances for pellet patches
        this.xMeans = PELLET_PATCH_MEAN2.map(item => item.slice(0, 1)); // Extract x means
        this.yMeans = PELLET_PATCH_MEAN2.map(item => item.slice(1, 2)); // Extract y means
        this.xVars = PELLET_PATCH_VAR2.map(item => item.slice(0, 1)); // Extract x variances
        this.yVars = PELLET_PATCH_VAR2.map(item => item.slice(1, 2)); // Extract y variances

        // Calculate grid probabilities and expected probabilities
        this.gridProbabilities = this.calculateGridProbabilities(); // Calculate probabilities for each grid cell
        this.expectedProbabilities = this.calculateExpectedProbabilities(); // Calculate expected probabilities for each action
    }

    // Function to calculate the probability of a pellet being in a grid cell
    gridProbability(xMeans, yMeans, xVariances, yVariances, xGridStart, yGridStart) {
        if (PELLET_MODE === 2) {
            const pelletTiles = PELLET_TILES;
            const isInTargetTile = pelletTiles.some(([x, y]) => 
            xGridStart === Math.floor(x) && yGridStart === Math.floor(y)
            );
            return isInTargetTile ? 1 / pelletTiles.length : 0;
        }
        else {
            let totalProbability = 0;
            for (let i = 0; i < 2; i++) {
            const pX = jStat.normal.cdf(xGridStart + 1, xMeans[i], Math.sqrt(xVariances[i])) -
                        jStat.normal.cdf(xGridStart, xMeans[i], Math.sqrt(xVariances[i]));
            const pY = jStat.normal.cdf(yGridStart + 1, yMeans[i], Math.sqrt(yVariances[i])) -
                        jStat.normal.cdf(yGridStart, yMeans[i], Math.sqrt(yVariances[i]));
            totalProbability += 0.5 * (pX * pY);
            }
            return totalProbability;
        }
        }

    // Function to calculate probabilities for all grid cells
    calculateGridProbabilities() {
        const gridProbabilities = []; // Initialize array to store grid probabilities

        // Iterate over all grid cells
        for (let x = 0; x < GRID_W; x++) {
            for (let y = 0; y < GRID_H; y++) {
                // Calculate probability for the current grid cell
                const probability = this.gridProbability(this.xMeans, this.yMeans, this.xVars, this.yVars, x, y);
                // Store the probability along with the grid coordinates
                gridProbabilities.push({
                    x,
                    y,
                    probability
                });
            }
        }

        return gridProbabilities; // Return the array of grid probabilities
    }

    // Function to find the probability of a specific grid cell
    findProbability(x, y) {
        // Find the grid cell in the gridProbabilities array
        const result = this.gridProbabilities.find(element => element.x === x && element.y === y);
        if (result) {
            return result.probability; // Return the probability if found
        } else {
            return 'No matching grid found.'; // Return a message if not found
        }
    }

    // Function to calculate the new position based on an action
    calculateNewPosition(x, y, action) {
        switch (action) {
            case AgentAction.UP: return { x, y: y - 1 }; // Move up
            case AgentAction.DOWN: return { x, y: y + 1 }; // Move down
            case AgentAction.LEFT: return { x: x - 1, y }; // Move left
            case AgentAction.RIGHT: return { x: x + 1, y }; // Move right
            case AgentAction.UPLEFT: return { x: x - 1, y: y - 1 }; // Move up-left
            case AgentAction.UPRIGHT: return { x: x + 1, y: y - 1 }; // Move up-right
            case AgentAction.DOWNLEFT: return { x: x - 1, y: y + 1 }; // Move down-left
            case AgentAction.DOWNRIGHT: return { x: x + 1, y: y + 1 }; // Move down-right
            case AgentAction.NOMOVE: return { x, y, noMove: true }; // No movement
            default: return { x, y }; // Default to no movement
        }
    }

    // Function to get side grids for diagonal actions
    getSideGrids(x, y, action) {
        switch (action) {
            case AgentAction.UPLEFT:
                return [{ x: x - 1, y }, { x, y: y - 1 }]; // Side grids for up-left
            case AgentAction.UPRIGHT:
                return [{ x: x + 1, y }, { x, y: y - 1 }]; // Side grids for up-right
            case AgentAction.DOWNLEFT:
                return [{ x: x - 1, y }, { x, y: y + 1 }]; // Side grids for down-left
            case AgentAction.DOWNRIGHT:
                return [{ x: x + 1, y }, { x, y: y + 1 }]; // Side grids for down-right
            default:
                return []; // No side grids for non-diagonal actions
        }
    }

    // Function to calculate the expected probability for a specific action
    calculateExpectedProbability(x, y, action) {
        if (action === AgentAction.NOMOVE) {
            return 0; // Return 0 for no movement
        }

        // Calculate the new position based on the action
        const newPosition = this.calculateNewPosition(x, y, action);
        // Check if the new position is out of bounds
        if (newPosition.x < 0 || newPosition.x >= GRID_W || newPosition.y < 0 || newPosition.y >= GRID_H) {
            return 0; // Return 0 if out of bounds
        }

        // Get the probability of the new position
        let expectedProbability = this.findProbability(newPosition.x, newPosition.y);

        // For diagonal actions, add probabilities of side grids
        if ([AgentAction.UPLEFT, AgentAction.UPRIGHT, AgentAction.DOWNLEFT, AgentAction.DOWNRIGHT].includes(action)) {
            const sideGrids = this.getSideGrids(x, y, action);
            const sideProbabilities = sideGrids.map(({ x, y }) => this.findProbability(x, y) / 2);
            expectedProbability += sideProbabilities.reduce((acc, prob) => acc + prob, 0);
        }

        return expectedProbability; // Return the expected probability
    }

    // Function to calculate expected probabilities for all actions and grid cells
    calculateExpectedProbabilities() {
        const actionValues = Object.values(AgentAction).filter(value => typeof value === 'number'); // Get all action values
        const expectedProbabilities = []; // Initialize array to store expected probabilities

        // Iterate over all grid cells and actions
        for (let x = 0; x < GRID_W; x++) {
            for (let y = 0; y < GRID_H; y++) {
                actionValues.forEach(actionValue => {
                    // Calculate the expected probability for the current action and grid cell
                    const probability = this.calculateExpectedProbability(x, y, actionValue);
                    // Store the result
                    expectedProbabilities.push({
                        x, y, action: actionValue, expectedProbability: probability,
                    });
                });
            }
        }

        return expectedProbabilities; // Return the array of expected probabilities
    }

    // Function to find the expected probability for a specific action and grid cell
    findActionProbability(x, y, action) {
        // Find the result in the expectedProbabilities array
        const result = this.expectedProbabilities.find(item => item.x === x && item.y === y && item.action === action);
        if (result) {
            return result.expectedProbability; // Return the probability if found
        } else {
            return 'No matching action found.'; // Return a message if not found
        }
    }
}

// Export the ExpectedProbabilityCalculator class as the default export
export default ExpectedProbabilityCalculator;