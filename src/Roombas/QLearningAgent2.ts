import { TrajDataType } from '../components/DataLog';
import {IObjCoord, IQvalue, GRID_W, GRID_H, AGENT_EPS,
        Q_INIT, HUM_INT_FB, MIN_AXIS_DIFF_QLEARN, IGlobalState,
        Q_STEP_COST, MyMap, AGENT_W, AGENT_H, INTERPRET_TYPE} from '../utils/index'
import extractQLearnFeatures from './QLearningFeatureExtractor';
import RandAgent from './RandAgent';
import Roomba from './Roomba';
import ExpectedProbabilityCalculator from '../components/ExpectedQvalue';

//check QLearningAgent.ts for information, QLearningAgent2.ts for no policy loaded version
export enum AgentAction  {
    UP = 0.,
    DOWN,
    LEFT,
    RIGHT,
    UPLEFT,
    UPRIGHT,
    DOWNLEFT,
    DOWNRIGHT,
    NOMOVE
}

export enum HumIntInterp {
    SUGGESTION = 0,
    RESET,
    INTERRUPT,
    TRANSITION,
    DISRUPT,
    IMPEDE
}

const agActToStr = [
    'UP', 'DOWN', 'LEFT','RIGHT', 'UPLEFT',
    'UPRIGHT','DOWNLEFT','DOWNRIGHT','NOMOVE'
];

export interface QAgentState   {
    pelDist : number;
    agDist: number;
}

export interface QAgentStateGrid {
    myPos: IObjCoord;
}

export interface QAgentExtState extends QAgentState {
    myPos : IObjCoord;
    nearPelPos : IObjCoord;
    nearAgPos : IObjCoord;
}

export interface QIndex extends QAgentStateGrid {
    action: AgentAction
}


class QLearnAgent2 extends Roomba {
    readonly _myEps: number;
    private _myTrajs  : TrajDataType [];
    private _myTrajsToRun: TrajDataType [];
    private _mouseUpTrajsToRun: TrajDataType[] = [];
    public _myQTable : MyMap <QIndex, number>;
    private _myAlpha : number; // learning rate
    private _myGamma : number; // discount rate
    readonly _possActions: Array<AgentAction>
    readonly QStateSpace :  MyMap<QAgentStateGrid, AgentAction []>;
    private _myPolicy: MyMap<QAgentStateGrid, AgentAction>;
    private _myFeatExt: (s: IGlobalState, id: number) => QAgentExtState;

    private testFlag = 0;
    public isLearning = false;
    
    readonly _int_type : HumIntInterp;

    constructor(id :number,
                int_type = INTERPRET_TYPE,
                eps_to_set=AGENT_EPS,
                alph=0.1,
                gam=0.9,
                max_pel_dist=Math.ceil(Math.sqrt(Math.pow(GRID_W,2)+Math.pow(GRID_H,2)))+1,
                max_ag_dist=Math.ceil(Math.sqrt(Math.pow(GRID_W,2)+Math.pow(GRID_H,2)))+1,
                feat_ext=extractQLearnFeatures) {
        super(id);
        this._myEps = eps_to_set;
        this._myTrajs = []
        this._myTrajsToRun = [];
        this._myAlpha=alph;
        this._myGamma=gam;
        this._myFeatExt = feat_ext;
        this._myQTable = new MyMap<QIndex,number> ();
        this.QStateSpace = new MyMap<QAgentStateGrid,AgentAction []>();
        this._myPolicy = new MyMap<QAgentStateGrid, AgentAction>();
        this._myId = id;
        this._int_type = int_type;
        this._possActions = Object.keys(AgentAction).filter(
                                             (x: string)=> !isNaN(Number(x))).map((x: string) => Number(x));

        // Initialize the state space
        for (let i = 0; i < GRID_W; i++) {
            for (let j = 0; j < GRID_H; j++) {
                for (let a of this._possActions) {
                    this._myQTable.set({myPos: {x: i, y: j}, action: a},
                         Q_INIT)
                }
                this.QStateSpace.set({myPos: {x: i, y: j}},
                    this._possActions)
            }
        }

        // Initialize the policy
        this._myPolicy = this.getPolicy()
    }

    getPolicy(this: QLearnAgent2, force_no_learn=true,force_learn=false) : MyMap<QAgentStateGrid,AgentAction> {
        if (force_learn && !force_no_learn) {
            this.runLearn();
        }
        const myPolicy = new MyMap<QAgentStateGrid, AgentAction>();

        const isValidAction = (state: QAgentStateGrid, action: AgentAction): boolean => {
            const {x, y} = state.myPos; 
            switch (action) {
                case AgentAction.UP: return y > 0;
                case AgentAction.DOWN: return y < 7;
                case AgentAction.LEFT: return x > 0;
                case AgentAction.RIGHT: return x < 7;
                case AgentAction.UPLEFT: return y > 0 && x > 0;
                case AgentAction.UPRIGHT: return y > 0 && x < 7;
                case AgentAction.DOWNLEFT: return y < 7 && x > 0;
                case AgentAction.DOWNRIGHT: return y < 7 && x < 7;
                default: return true; 
            }
        };
    
        for (let state of this.QStateSpace.keys()) {
            const acts = this.QStateSpace.get(state);
            if (acts) {
                let curBestSc = -Infinity;
                let curBestA: AgentAction = AgentAction.UP; 
                let curBestActList: AgentAction[] = [];
                for (let a of acts) {
                    if (!isValidAction(state, a)) continue; 
                    const curScore = this._myQTable.get({...state, action: a});
                    if (curScore === curBestSc) {
                        curBestActList.push(a);
                    }
                    if (curScore && (curScore > curBestSc)) {
                        curBestSc = curScore;
                        curBestA = a;
                        curBestActList = [a];
                    }
                }
                if (curBestActList.length > 1) {
                    myPolicy.set(state, curBestActList[Math.floor(Math.random()*curBestActList.length)]);
                } else {
                    myPolicy.set(state, curBestA);
                }
            } else {
                console.log('Trying to find best action for a state not in state space.');
            }
        }
        this._myPolicy = myPolicy;
        return myPolicy;
    }

    runLearn(this: QLearnAgent2) {
        if (this._myTrajsToRun.length > 0) {
            this.isLearning = true;
            
            let myTraj = this._myTrajsToRun.pop();
            let dragTraj = this._mouseUpTrajsToRun.pop();
            console.log("IS learning", myTraj);
            if (myTraj &&
            (myTraj.cancelP === false) &&
            (myTraj.agent_st_pos !== undefined) && (myTraj.agent_end_pos !== undefined) &&
            (myTraj.cur_state !== undefined)) {

                const prevPos : IObjCoord = myTraj.agent_st_pos;
                let curPos: IObjCoord;
                if (myTraj.agent_end_pos !== undefined) {
                  curPos = myTraj.agent_end_pos;
                } else {
                    throw new Error("agent_end_pos is undefined.");
                }
                const prevFeats = this._myFeatExt(myTraj.start_state, myTraj.agent_id);
                const curFeats = this._myFeatExt(myTraj.cur_state, myTraj.agent_id);

                const prevState : QAgentStateGrid = {
                    myPos: prevFeats.myPos
                }
                let curState: QAgentStateGrid = {
                    myPos: curFeats.myPos
                }
                let fb :number = 0.;
                let myAct : AgentAction;
                fb = (myTraj.feedback === undefined)? 0. : myTraj.feedback;

                myAct = this.inferAct(prevPos, curPos);
                let qValToUpdate = this._myQTable.get({...prevState, action: myAct});
                const possActs : AgentAction [] = []
                if (curPos.y > AGENT_H) {
                    possActs.push(AgentAction.UP);
                    if (curPos.x > AGENT_W) possActs.push(AgentAction.UPLEFT);
                    if (curPos.x < (GRID_W - AGENT_W)) possActs.push(AgentAction.UPRIGHT);
                }
                else if (curPos.y < GRID_H - AGENT_H) {
                    possActs.push(AgentAction.DOWN);
                    if (curPos.x > AGENT_W) possActs.push(AgentAction.DOWNLEFT);
                    if (curPos.x < (GRID_W - AGENT_W)) possActs.push(AgentAction.DOWNRIGHT);

                }
                if (curPos.x > AGENT_W) possActs.push(AgentAction.LEFT);
                if (curPos.x < (GRID_W-AGENT_W)) possActs.push(AgentAction.RIGHT);

                let curBestVal = -Infinity;
                // let curBestVal = -9999999999;
                let step_cost_multiplier = 1;
                let curBestAct = AgentAction.NOMOVE;
                for (let act of possActs) {
                    const myVal : number | undefined = this._myQTable.get({...curState, action: act});
                    if ((myVal) && (myVal > curBestVal)) {
                        curBestVal = myVal;
                        curBestAct = act;

                        if ([AgentAction.UP, AgentAction.DOWN, AgentAction.LEFT, AgentAction.RIGHT].includes(act)) {
                            step_cost_multiplier = 1;
                            // console.log("ONE step cost multiplier");
                        } else if ([AgentAction.UPLEFT, AgentAction.UPRIGHT, AgentAction.DOWNLEFT, AgentAction.DOWNRIGHT].includes(act)) {
                            step_cost_multiplier = 1.414;
                            // console.log("sqrt(2) step cost multiplier");
                        } else if (act === AgentAction.NOMOVE) {
                            step_cost_multiplier = 0;
                        }

                    }
                }

                if (!qValToUpdate) {
                    console.log("uh oh. (s,s',a) not in qTable, ", );
                    console.log('setting qval to q_init')
                    qValToUpdate = Q_INIT;
                    step_cost_multiplier = 1;
                }

                if (!curBestVal || (!isFinite(curBestVal))) {
                    console.log('no actions seem ok from here. weird.');
                    qValToUpdate = -2;
                    curBestVal = 0;
                    step_cost_multiplier = 1;
                }

                const myTD  = fb + Q_STEP_COST * step_cost_multiplier +  this._myGamma * curBestVal - qValToUpdate;

                const newQVal = qValToUpdate + this._myAlpha * myTD;
                this._myQTable.set({...prevState, action: myAct}, newQVal);

                if ((isNaN(newQVal)) || (!isFinite(newQVal))) {
                    console.log('nanana');
                }

                console.log(this.toString(), ' - my q table update: ',
                    { ...prevState, action: agActToStr[myAct] }, '; Qvalue: ', newQVal);

                const maxPrintNum = 1;
                if (this.testFlag < maxPrintNum) {
                    console.log("TEST print Qtable", this._myQTable.toString());
                    this.testFlag++;
                }
                
            }
            else if (myTraj && dragTraj &&
            (dragTraj.feedback !== undefined) && (myTraj.cancelP) &&
            (myTraj.agent_st_pos !== undefined) && (dragTraj.agent_end_pos !== undefined) &&
            (myTraj.cur_state !== undefined)) {    
                const prevPos : IObjCoord = myTraj.agent_st_pos;
                let curPos: IObjCoord;
                if (dragTraj.agent_end_pos !== undefined) {
                  curPos = dragTraj.agent_end_pos;
                } else {
                    throw new Error("agent_end_pos is undefined.");
                }
                const prevFeats = this._myFeatExt(myTraj.start_state, myTraj.agent_id);
                const curFeats = this._myFeatExt(myTraj.cur_state, myTraj.agent_id);

                const prevState : QAgentStateGrid = {
                    myPos: prevFeats.myPos
                }
                let curState: QAgentStateGrid = {
                    myPos: curFeats.myPos
                }
                let fb :number = 0.;
                let myAct : AgentAction;
                let interrupt = false
                if (this._int_type === HumIntInterp.SUGGESTION) {
                    if (prevPos.x === curPos.x && prevPos.y === curPos.y) {
                        interrupt = true;
                    }
                    else {
                        fb = dragTraj.feedback;
                    }
                }
                else if (this._int_type === HumIntInterp.RESET) {
                    const tryNPos: IObjCoord = myTraj.agent_try_pos as IObjCoord;
                    const tryFeats : QAgentStateGrid = {
                        myPos: tryNPos
                    };
                    curPos = tryNPos;
                    curState = tryFeats;
                    fb = (myTraj.feedback === undefined)? 0. : myTraj.feedback;
                }
                else if (this._int_type === HumIntInterp.INTERRUPT) {
                    interrupt = true;
                }
                else if (this._int_type === HumIntInterp.TRANSITION) {
                    if (prevPos.x === curPos.x && prevPos.y === curPos.y) {
                        const tryNPos: IObjCoord = myTraj.agent_try_pos as IObjCoord;
                        const tryFeats : QAgentStateGrid = {
                            myPos: tryNPos
                        };
                        curPos = tryNPos;
                        curState = tryFeats;
                        fb = HUM_INT_FB;
                    }
                    else {
                        fb = -HUM_INT_FB;
                    }
                }
                else if (this._int_type === HumIntInterp.DISRUPT) {
                    if (prevPos.x === curPos.x && prevPos.y === curPos.y) {
                        interrupt = true;
                    }
                    else {
                        fb = HUM_INT_FB;
                    }
                }
                else if (this._int_type === HumIntInterp.IMPEDE) {
                    const tryNPos: IObjCoord = myTraj.agent_try_pos as IObjCoord;
                    const tryFeats : QAgentStateGrid = {
                        myPos: tryNPos
                    };
                    curPos = tryNPos;
                    curState = tryFeats;
                    fb = HUM_INT_FB;
                }

                if (interrupt === false) {
                    myAct = this.inferAct(prevPos, curPos);
                    let qValToUpdate = this._myQTable.get({...prevState, action: myAct});
                    const possActs : AgentAction [] = []
                    if (curPos.y > AGENT_H) {
                        possActs.push(AgentAction.UP);
                        if (curPos.x > AGENT_W) possActs.push(AgentAction.UPLEFT);
                        if (curPos.x < (GRID_W - AGENT_W)) possActs.push(AgentAction.UPRIGHT);
                    }
                    else if (curPos.y < GRID_H - AGENT_H) {
                        possActs.push(AgentAction.DOWN);
                        if (curPos.x > AGENT_W) possActs.push(AgentAction.DOWNLEFT);
                        if (curPos.x < (GRID_W - AGENT_W)) possActs.push(AgentAction.DOWNRIGHT);

                    }
                    if (curPos.x > AGENT_W) possActs.push(AgentAction.LEFT);
                    if (curPos.x < (GRID_W-AGENT_W)) possActs.push(AgentAction.RIGHT);

                    let curBestVal = -Infinity;
                    // let curBestVal = -9999999999;
                    let step_cost_multiplier = 1;
                    let curBestAct = AgentAction.NOMOVE;
                    for (let act of possActs) {
                        const myVal : number | undefined = this._myQTable.get({...curState, action: act});
                        if ((myVal) && (myVal > curBestVal)) {
                            curBestVal = myVal;
                            curBestAct = act;

                            if ([AgentAction.UP, AgentAction.DOWN, AgentAction.LEFT, AgentAction.RIGHT].includes(act)) {
                                step_cost_multiplier = 1;
                                // console.log("ONE step cost multiplier");
                            } else if ([AgentAction.UPLEFT, AgentAction.UPRIGHT, AgentAction.DOWNLEFT, AgentAction.DOWNRIGHT].includes(act)) {
                                step_cost_multiplier = 1.414;
                                // console.log("sqrt(2) step cost multiplier");
                            } else if (act === AgentAction.NOMOVE) {
                                step_cost_multiplier = 0;
                            }

                        }
                    }

                    if (!qValToUpdate) {
                        console.log("uh oh. (s,s',a) not in qTable, ", );
                        console.log('setting qval to q_init')
                        qValToUpdate = Q_INIT;
                        step_cost_multiplier = 1;
                    }

                    if (!curBestVal || (!isFinite(curBestVal))) {
                        console.log('no actions seem ok from here. weird.');
                        qValToUpdate = -2;
                        curBestVal = 0;
                        step_cost_multiplier = 1;
                    }

                    const myTD  = fb + Q_STEP_COST * step_cost_multiplier +  this._myGamma * curBestVal - qValToUpdate;

                    const newQVal = qValToUpdate + this._myAlpha * myTD;
                    this._myQTable.set({...prevState, action: myAct}, newQVal);

                    if ((isNaN(newQVal)) || (!isFinite(newQVal))) {
                        console.log('nanana');
                    }

                    console.log(this.toString(), ' - my q table update: ',
                        { ...prevState, action: agActToStr[myAct] }, '; Qvalue: ', newQVal);

                    const maxPrintNum = 1;
                    if (this.testFlag < maxPrintNum) {
                        console.log("TEST print Qtable", this._myQTable.toString());
                        this.testFlag++;
                    }
                }
            }
            // call runLearn again to do another traj in the ones to run
            this.runLearn();
        } else {
            setTimeout(() => {
                this.isLearning = false;
                console.log("NOT learning");
            }, 250);
        }
    }

    inferAct(stPos: IObjCoord, endPos: IObjCoord) : AgentAction {
        const xDiff = endPos.x - stPos.x;
        const yDiff = endPos.y - stPos.y;

        if (xDiff > MIN_AXIS_DIFF_QLEARN) {
            if (yDiff > MIN_AXIS_DIFF_QLEARN) {
                return AgentAction.DOWNRIGHT;
            }
            else if (yDiff < MIN_AXIS_DIFF_QLEARN) {
                return AgentAction.UPRIGHT;
            }
            else {
                return AgentAction.RIGHT;
            }
        }
        else if (xDiff < MIN_AXIS_DIFF_QLEARN) {
            if (yDiff > MIN_AXIS_DIFF_QLEARN) {
                return AgentAction.DOWNLEFT;
            }
            else if (yDiff < MIN_AXIS_DIFF_QLEARN) {
                return AgentAction.UPLEFT;
            }
            else {
                return AgentAction.LEFT;
            }
        }
        else if (yDiff > MIN_AXIS_DIFF_QLEARN) {
            return AgentAction.DOWN;
        }
        else if (yDiff < MIN_AXIS_DIFF_QLEARN) {
            return AgentAction.UP;
        }
        else {
            return AgentAction.NOMOVE;
        }

    }

    addTrajData(newTraj: TrajDataType, force_learn:boolean=false,force_no_use_for_learn: boolean = false) {
        this._myTrajs.push(newTraj);
        if (newTraj.was_dragP === true) {
            this._mouseUpTrajsToRun.push(newTraj);
        }
        else if (!force_no_use_for_learn) {
            this._myTrajsToRun.push(newTraj);
        }
        
        if (force_learn) {
            this.runLearn();
        }
    }

    //TODO: Make actions for direction unit vector closest to pellet in that quandrant? (seems too coarse grained when watching)
    convertAgentActToGrid(a: AgentAction) : IObjCoord {
        switch (a) {
            case AgentAction.UP:
                return ({x: 0, y: -1});
            case AgentAction.UPLEFT:
                return ({x: -1, y: -1});
            case AgentAction.UPRIGHT:
                return ({x: 1, y: -1});
            case AgentAction.LEFT:
                return({x: -1, y: 0});
            case AgentAction.RIGHT:
                return({x:1, y:0});
            case AgentAction.DOWNLEFT:
                return({x: -1, y:1});
            case AgentAction.DOWN:
                return({x:0, y:1});
            case AgentAction.DOWNRIGHT:
                return ({x:1, y:1});
            default:
                return ({x: Math.random() * 0.1, y: Math.random()*0.1})
        }
    }

    getValidActions(x: number, y: number): AgentAction[] {
        const validActions: AgentAction[] = [];
        if (y > 0) validActions.push(AgentAction.UP);
        if (y < 7) validActions.push(AgentAction.DOWN);
        if (x > 0) validActions.push(AgentAction.LEFT);
        if (x < 7) validActions.push(AgentAction.RIGHT);
        if (x > 0 && y > 0) validActions.push(AgentAction.UPLEFT);
        if (x < 7 && y > 0) validActions.push(AgentAction.UPRIGHT);
        if (x > 0 && y < 7) validActions.push(AgentAction.DOWNLEFT);
        if (x < 7 && y < 7) validActions.push(AgentAction.DOWNRIGHT);
        return validActions;
    }
    
    simulateActions(): IQvalue {
        let TotalQ = 0;
        const loops = 100;
        const ExpectedQtable = new ExpectedProbabilityCalculator;        
        const myPol = this.getPolicy();
        for (let i = 0; i < loops; i++) {
            let currentx = Math.floor(Math.random() * 8);
            let currenty = Math.floor(Math.random() * 8);
            const steps = 30;
            for (let step = 0; step < steps; step++) {    
                let action = myPol.get({myPos: {x: currentx, y: currenty}});
                if (action === AgentAction.NOMOVE) {
                    const validActions = this.getValidActions(currentx, currenty);
                    action = validActions[Math.floor(Math.random() * validActions.length)];
                }
                const currentQ = ExpectedQtable.findActionProbability(currentx, currenty, action);
                TotalQ += currentQ;
                const newPosition = ExpectedQtable.calculateNewPosition(currentx, currenty, action);
                currentx = newPosition.x;
                currenty = newPosition.y;
            }
        }
        const newRecord: IQvalue = {agentid: this._myId, ExpectedQvalue: TotalQ};
        return newRecord;
    }

    getMove(curXBoxN: number, curYBoxN: number,
            pelletPos: IObjCoord[], curGState: IGlobalState): IObjCoord {
        const myPol = this.getPolicy();
        const curAlmostState = this._myFeatExt(curGState,this._myId);
        const curState = {
            myPos: curAlmostState.myPos
        }
        const myAct = myPol.get(curState);

        //eps greedy policy
        if ((Math.random() < this._myEps) || ((!myAct) && (myAct!==0))) {
            return RandAgent.getMove(curXBoxN,curYBoxN, pelletPos, curGState);
        }
        else{
            let retVal = this.convertAgentActToGrid(myAct);
            return retVal;        }
    }

    toString() :string {
        return 'QLearnAgent' + this._myId;
    }

    vizOverlay(): boolean {
        return false;
    }

}
export default QLearnAgent2