import Grid from "../components/Grid";
import GridBox from "../components/GridBox";
import AgentScoreBox from "../components/AgentScoreBox";
import React, { Fragment, useRef, useEffect, useState } from "react";
import { Provider, useSelector, useDispatch } from "react-redux";
import { GRID_H, GRID_W, myWorld, HEIGHT, WIDTH, IGlobalState, NUM_AGENTS} from "../utils";
import store from "../store";
import dataService from "../services/data.service";
import NumMovesBox from "../components/NumMovesBox";
import {testDataFunc} from "../components/DataLog";
import ExportButton from "../components/Qdatabutton";
import ParameterForm from "../components/ParameterForm";
import PickQtable from "../components/PickQtable";
import Timer from "../components/Timer";
import { PARAMETERS_READY } from "../store/actions";
import { initializeParameters } from "../utils/parameters";

function renderGridSq(i: number) {

    const x = i % GRID_W;
    const y = Math.floor(i / GRID_H);
    try {
        const mySqType = myWorld[x][y];
    }
    catch {
        console.log('err. x: ' + x + ', y: ' + y + '. myWorld[x][y]=' + myWorld[x][y]);
    }

    return (<GridBox key={i} i={i} mySqType={myWorld[x][y]} />);
}

export default function MainExpt() {
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const initialize = async () => {
            await initializeParameters(); 
            setIsLoading(false); 
        };

        initialize();
    }, []);

    if (isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <Provider store={store}>
            <MainExperimentWithRedux />
        </Provider>
    );
}

function MainExperimentWithRedux() {
    const dispatch = useDispatch(); 

    useEffect(() => {
        dispatch({ type: PARAMETERS_READY }); 
    }, [dispatch]);

    const squares = [];
    for (let i = 0; i < GRID_H * GRID_W; i++) {
        squares.push(renderGridSq(i));
    }

    return (
        <Fragment>
            <div className="main" style={{
                width: HEIGHT,
                height: WIDTH,
                display: 'flex',
                flexWrap: 'wrap',
                placeItems: 'center',
                placeContent: 'center',
                position: 'relative',
                zIndex: 2
            }}
            >
                {squares}
            </div>
            <Grid />
            <PickQtable />
            {/* <ParameterForm /> */}
            {/* <Timer /> */}
            {Array.from({ length: NUM_AGENTS }, (_, i) => (
                <Fragment key={i}>
                    <AgentScoreBox myId={i.toString()} />
                    <NumMovesBox myId={i.toString()} />
                </Fragment>
            ))}
        </Fragment>
    );
}