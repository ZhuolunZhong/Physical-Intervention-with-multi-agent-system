import React, { FC, useState, useEffect } from 'react';
import { useNumTrajData } from "./DataLog";
import { useSelector } from "react-redux";
import { IGlobalState } from "../utils";

// NumMovesBox is a component that displays the number of moves taken by a specific agent
 interface BoxType  {
    myId: string
}

const NumMovesBox: FC<BoxType> = ({myId}) : JSX.Element => {
    const agentId = Number(myId); // Convert myId to a number
    const numMoves = useNumTrajData(agentId); // Fetch number of moves
    
    // Construct the string to display
    const strToWrite = ( 'agent ' + agentId + ' has taken ' + numMoves + ' so far');

    return (<div
        style = {{
            position: 'relative',
            fontSize: '20px' }}>
    <b>{
            strToWrite
        }
    </b></div>)
}

export default NumMovesBox