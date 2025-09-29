import { BOX_H, BOX_W, HEIGHT, WIDTH, PelletParamType, REL_PELLET_SIZE,
pelletImg } from "../utils";
import React, {FC} from 'react'
import '../index.css';

// Component renders a pellet
const Pellet: FC<PelletParamType> = ({myId,myType,myPos,color, dispatch, feedback}) :JSX.Element => {

    const myStyle = {
        width: REL_PELLET_SIZE*BOX_W,
        height: REL_PELLET_SIZE*BOX_H,
        border: '2px black',
        zIndex: 3,
        position: 'absolute',
        left: Math.max(0,Math.min(myPos.x *BOX_W, WIDTH)),
        top: Math.max(0,Math.min(myPos.y * BOX_H, HEIGHT)),
        background: "url('" + pelletImg + "') center center",
        backgroundSize: 'contain'
    } as React.CSSProperties;

    return (
        <div style={myStyle} className='pellet' >
                   </div>
    );
}

export default Pellet;
