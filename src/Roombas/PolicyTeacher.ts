import { AgentAction } from "./QLearningAgent";
import ExpectedProbabilityCalculator from "../components/ExpectedQvalue";

export class PolicyTeacher {
    private _bestActionsMap: Map<string, AgentAction[]>; 
    private _expectedProbCalculator: ExpectedProbabilityCalculator;

    constructor() {
        this._expectedProbCalculator = new ExpectedProbabilityCalculator();
        this._bestActionsMap = this._calculateBestActions();
    }

    // Calculate the list of optimal actions for each position
    private _calculateBestActions(): Map<string, AgentAction[]> {
        const bestActions = new Map<string, AgentAction[]>();
        const { expectedProbabilities } = this._expectedProbCalculator;

        //  Iterate through all grid positions
        for (let x = 0; x < 8; x++) {
            for (let y = 0; y < 8; y++) {
                const positionKey = `${x},${y}`;
                let maxProbability = -Infinity;
                let bestActionsForPos: AgentAction[] = [];

                // Check all possible actions
                for (const action in AgentAction) {
                    if (isNaN(Number(action))) continue;
                    const actionNum = Number(action);
                    const prob = this._expectedProbCalculator.findActionProbability(x, y, actionNum);
                    
                    if (prob > maxProbability) {
                        maxProbability = prob;
                        bestActionsForPos = [actionNum];
                    } else if (prob === maxProbability) {
                        bestActionsForPos.push(actionNum);
                    }
                }

                bestActions.set(positionKey, bestActionsForPos);
            }
        }
        return bestActions;
    }

    // Retrieve the list of optimal actions for a specified position
    public getBestActions(x: number, y: number): AgentAction[] {
        return this._bestActionsMap.get(`${x},${y}`) || [AgentAction.NOMOVE];
    }

    // Determine if a given action is one of the optimal actions
    public isOptimalAction(x: number, y: number, action: AgentAction): boolean {
        const bestActions = this.getBestActions(x, y);
        return bestActions.includes(action);
    }
}

export const policyTeacher = new PolicyTeacher();