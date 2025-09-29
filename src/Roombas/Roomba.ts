import { TrajDataType } from "../components/DataLog";
import { IGlobalState, IObjCoord } from "../utils";

// TS basic class for agents
abstract class Roomba {
    protected _myId: number;
    protected _canGetPellet: boolean;
    constructor(id: number) {
        this._myId = id;
        this._canGetPellet = true;
    }
    abstract getMove(curXBoxN:number, curYBoxN:number, pelletPos:IObjCoord[],
                     curGState:IGlobalState) : IObjCoord;

    abstract vizOverlay() : boolean;

    abstract addTrajData(this:Roomba, trajData: TrajDataType) : void;

    abstract toString(this:Roomba) :string;

    public canGetPellet(this:Roomba) : boolean {
        return this._canGetPellet;
    }
    public setGetPellet(this:Roomba, newGetPelletVal: boolean) : void {
        this._canGetPellet = newGetPelletVal;
    }
}

export default Roomba;