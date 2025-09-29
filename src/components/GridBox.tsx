import { GRID_H, GRID_W, gridSqToImg, NumDict } from "../utils";
import {FC} from 'react';

// GridBox is a component that renders an image representing a grid square
interface GridBoxParamType {
    i: number,
    mySqType: number
} 
const GridBox : FC<GridBoxParamType> = ({i, mySqType} ) : JSX.Element => {
    return (
        <img
            style={{
                width: String(100./GRID_W) + '%',
                height: String(100./GRID_H) + '%',
                zIndex: 2,
                position: 'relative',
                margin: '0 0 0 0',
                userSelect: 'none',
                pointerEvents: 'none',
            }}
            src={gridSqToImg[mySqType as keyof NumDict]} // Image source
            alt={"grid square " + i}
            tabIndex={0}
        />
    );
}

export default GridBox;