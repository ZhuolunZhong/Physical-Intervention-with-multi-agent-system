import { FC } from "react";
import { useSelector } from "react-redux";
import { IGlobalState } from "../utils";

 interface ScoreBoxType  {
    myId: string
}

// The AgentScoreBox component display the current score of the agent based on the input agent ID.
const AgentScoreBox: FC<ScoreBoxType> = ({ myId }): JSX.Element => {
    // Convert the myId string to a number for use in array indexing
    const agentId = Number(myId);

    // Fetch the agent scores from the Redux state
    const scores = useSelector((state: IGlobalState) => state.agent_scores);
    // Fetch the agent positions from the Redux state
    const pos = useSelector((state: IGlobalState) => state.agent_pos);

    // Construct a string to display the agent's score and position
    const strToWrite = 'Agent ' + agentId + ' has ' + scores[agentId] + ' points. It is in position x: ' + pos[agentId].x + ' and y: ' + pos[agentId].y;

    // Render the component
    return (
        <div style={{
            position: 'relative', // Position the div relatively
            fontSize: '16px' // Set the font size to 16px
        }}>
            {strToWrite} {/* Display the constructed string */}
        </div>
    );
};

export default AgentScoreBox;