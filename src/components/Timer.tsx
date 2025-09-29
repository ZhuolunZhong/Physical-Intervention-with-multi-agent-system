import React, { useState, useEffect, useRef } from 'react'; 
import { useSelector } from "react-redux"; 
import { useNavigate } from 'react-router-dom'; 
import { IGlobalState, NUM_AGENTS, PELLET_TILES } from "../utils"; 
import axios from 'axios'; 
import { getDraggedTraj, getStartTime, getCanceledTraj, getTryTraj, getEndTraj } from './DataLog'; 
import { onRoundComplete, fetchParameters } from '../utils/parameters'; 
import { agentInsts } from './Grid'; 
import { IQvalue } from '../utils'; 
import QLearnAgent from '../Roombas/QLearningAgent'; 
import ConfirmDialog from './confirm_dialog'; 

// The timer is used in human experiments, responsible for displaying the countdown, and upon completion, it sends multiple sets of data to the backend, prepare the next round
const Timer: React.FC = () => {
  const [time, setTime] = useState<number>(0); // State to track elapsed time
  const [data, setData] = useState<{ score: number, agent_id: number, time: number, user_id: string, round: number }[]>([]); // State to store score data
  const [qValuesData, setQValuesData] = useState<{ agent_id: number, time: number, user_id: string, round: number, ExpectedQvalue: number }[]>([]); // State to store Q-values data
  const [downloaded, setDownloaded] = useState<boolean>(false); // State to track if data has been downloaded
  const [roundCompleted, setRoundCompleted] = useState<boolean>(false); // State to track if the round is completed
  const [isDialogOpen, setIsDialogOpen] = useState<boolean>(false); // State to control the visibility of the ConfirmDialog
  const [dialogMessage, setDialogMessage] = useState<string>(''); // State to store the dialog message
  const [nextRound, setNextRound] = useState<number | null>(null); // State to store the next round number
  const [navigatePath, setNavigatePath] = useState<string | null>(null); // State to store the navigation path
  const [surveyMessage, setSurveyMessage] = useState<string | null>(null); // State to store the survey message
  const scoresRef = useRef<number[]>([]); // Ref to store scores for use in the worker
  const scores = useSelector((state: IGlobalState) => state.agent_scores); // Access scores from the Redux store
  const workerRef = useRef<Worker | null>(null); // Ref to store the Web Worker
  const lastCollectedTimeRef = useRef<number>(0); // Ref to store the last time data was collected
  const navigate = useNavigate(); // Hook for programmatic navigation
  
  // Update the scoresRef whenever scores change
  useEffect(() => {
    scoresRef.current = scores;
  }, [scores]);

  // Set up the Web Worker to track time and collect data
  useEffect(() => {
    if (!workerRef.current) {
      workerRef.current = new Worker(new URL('./timerWorker.js', import.meta.url)); // Create a new Web Worker
      workerRef.current.onmessage = (event) => {
        const currentTime = event.data; // Get the current time from the worker
        setTime(currentTime); // Update the time state

        // Collect data every 0.5 seconds
        if (currentTime - lastCollectedTimeRef.current >= 0.5) {
          const currentScores = scoresRef.current; // Get the latest scores
          const user_id = sessionStorage.getItem('userID') || 'unknown'; // Get the user ID
          const round = parseInt(sessionStorage.getItem('round') || '1', 10); // Get the current round

          // Create new score data
          const newData = currentScores.map((score, index) => ({
            score, 
            agent_id: index, 
            time: currentTime, 
            user_id, 
            round 
          }));

          setData(prevData => [...prevData, ...newData]); // Update the score data state

          // Create new Q-values data
          const newQValuesData = agentInsts
          .filter((agent, index) => index < NUM_AGENTS && agent) 
          .map((agent) => {
            const qResult: IQvalue = (agent as QLearnAgent).simulateActions(); // Simulate actions and get Q-values
            return {
                agent_id: qResult.agentid,
                time: currentTime,
                user_id,
                round,
                ExpectedQvalue: qResult.ExpectedQvalue
          };});

          setQValuesData(prevQValuesData => [...prevQValuesData, ...newQValuesData]); // Update the Q-values data state

          lastCollectedTimeRef.current = currentTime; // Update the last collected time
        }

        // Trigger data download when time reaches 100 seconds
        if (currentTime >= 100 && !downloaded) {
          setDownloaded(true); // Mark data as downloaded
        }
      };
      workerRef.current.postMessage('start'); // Start the worker
    }

    // Clean up the worker when the component unmounts
    return () => {
      if (workerRef.current) {
        workerRef.current.postMessage('stop'); // Stop the worker
        workerRef.current.terminate(); // Terminate the worker
        workerRef.current = null; // Clear the worker ref
      }
    };
  }, [downloaded]);

  // Handle round completion and data upload
  useEffect(() => {
    const completeRound = async () => {
      if (downloaded) {
        uploadQValuesToServer(); // Upload Q-values data
        uploadCSVToServer(); // Upload score data
        uploadDraggedTrajToServer(); // Upload dragged trajectory data
        uploadTryTrajToServer(); // Upload try trajectory data
        uploadEndCountsToServer(); // Upload end count data

        if (!roundCompleted) {
          setRoundCompleted(true); // Mark the round as completed
          await onRoundComplete(); // Perform round completion tasks

          const nextRoundValue = parseInt(sessionStorage.getItem('round') || '1', 10); // Get the next round
          setNextRound(nextRoundValue); // Update the next round state
          
          let dialogMsg = 'Continue'; // Default dialog message
          let surveyMsg = null; // Default survey message
          let path = null; // Default navigation path

          // Set messages and path based on the next round
          switch (nextRoundValue) {
            case 2:
              dialogMsg = `Well done! You have completed 1 out of 9 rounds. \n\nPlease note that even if the robot in the next round looks like one from a previous round, it is a completely new robot and has no connection to the previous ones.`;
              surveyMsg = 'You will train one agent in the next two rounds. ';
              path = '/survey';
              break;
            case 4:
              dialogMsg = `Well done! You have completed 3 out of 9 rounds. \n\nPlease note that even if the robot in the next round looks like one from a previous round, it is a completely new robot and has no connection to the previous ones.`;
              surveyMsg = 'You will train one agent in the next two rounds.';
              path = '/survey';
              break;
            case 6:
              dialogMsg = `Well done! You have completed 5 out of 9 rounds. \n\nPlease note that even if the robot in the next round looks like one from a previous round, it is a completely new robot and has no connection to the previous ones.`;
              surveyMsg = 'You will train two agents in the next two rounds.';
              path = '/survey';
              break;
            case 8:
              dialogMsg = `Well done! You have completed 7 out of 9 rounds. \n\nPlease note that even if the robot in the next round looks like one from a previous round, it is a completely new robot and has no connection to the previous ones.`;
              surveyMsg = 'You will train two agents in the next two rounds.';
              path = '/survey';
              break;
            case 10:
              dialogMsg = 'Thank you for your participation. You have completed all rounds.';
              surveyMsg = 'Please complete the final survey carefully and make sure to note the special code you receive after submission.';
              path = '/survey';
              break;  
            default:
              dialogMsg = `Well done! You have completed ${nextRoundValue-1} out of 9 rounds. \n\nPlease note that even if the robot in the next round looks like one from a previous round, it is a completely new robot and has no connection to the previous ones.`;
          }

          setDialogMessage(dialogMsg); // Update the dialog message
          setSurveyMessage(surveyMsg); // Update the survey message
          setNavigatePath(path); // Update the navigation path
          setIsDialogOpen(true); // Open the ConfirmDialog
        }
      }
    };
  
    completeRound(); // Call the completeRound function
  }, [downloaded]);

  // Handle confirmation of the dialog
  const handleConfirm = () => {
    setIsDialogOpen(false); // Close the dialog

    if (navigatePath) {
      navigate(navigatePath, { state: { message: surveyMessage } }); // Navigate to the specified path
    } else {
      window.location.reload(); // Reload the page
    }
  };

  // Upload score data to the server
  const uploadCSVToServer = () => {
    const csvData = data.map(row => ({
      score: row.score,
      agent_id: row.agent_id,
      time: row.time,
      user_id: row.user_id,
      round: row.round  
    }));

    axios.post('/api/upload/mysql', {
      data: csvData
    }).then(response => {
      console.log("CSV data uploaded:", response.data);
    }).catch(error => {
      console.error("Error uploading CSV data:", error);
    });
  };

  // Upload Q-values data to the server
  const uploadQValuesToServer = () => {
    const qValuesPayload = qValuesData.map(row => ({
        agent_id: row.agent_id,
        time: row.time,
        user_id: row.user_id,
        round: row.round,
        ExpectedQvalue: row.ExpectedQvalue
    }));

    axios.post('/api/upload/mysql3', {
        data: qValuesPayload
    }).then(response => {
        console.log("QValues data uploaded:", response.data);
    }).catch(error => {
        console.error("Error uploading QValues data:", error);
    });
  };

  // Define the structure of dragged trajectory data
  interface DraggedTrajData {
    agent_st_pos_x: number | null;
    agent_st_pos_y: number | null;
    agent_end_pos_x: number | null;
    agent_end_pos_y: number | null;
    agent_ini_pos_x: number | null;
    agent_ini_pos_y: number | null;
    is_optimal: boolean | null;
    q_value: number | null;
    expected_q_value?: number | null;
    agent_id: number;
    duration: number | null;
    user_id: string;
    round: number;
    st_time_relative: number | null;  
    end_time_relative: number | null; 
  }

  // Upload dragged trajectory data to the server
  const uploadDraggedTrajToServer = () => {
    const user_id = sessionStorage.getItem('userID') || 'unknown';
    const round   = parseInt(sessionStorage.getItem('round') || '1', 10);
    const zero_time = getStartTime();

    const draggedTrajData: DraggedTrajData[] = [];

    for (let agentId = 0; agentId < NUM_AGENTS; agentId++) {
      const draggedTrajs  = getDraggedTraj(agentId);
      const canceledTrajs = getCanceledTraj(agentId);

      draggedTrajs.forEach((d, i) => {
        const c = canceledTrajs[i];

        const st_time_relative = d.st_time
          ? parseFloat(((d.st_time.valueOf() - zero_time.valueOf()) / 1000).toFixed(1))
          : null;
        const end_time_relative = d.end_time
          ? parseFloat(((d.end_time.valueOf() - zero_time.valueOf()) / 1000).toFixed(1))
          : null;

        draggedTrajData.push({
          agent_st_pos_x: d.agent_st_pos!.x,
          agent_st_pos_y: d.agent_st_pos!.y,
          agent_end_pos_x: d.agent_end_pos!.x,
          agent_end_pos_y: d.agent_end_pos!.y,

          agent_ini_pos_x: c.agent_st_pos!.x,
          agent_ini_pos_y: c.agent_st_pos!.y,
          is_optimal:      c.is_optimal!,
          q_value:         c.qValue!,
          expected_q_value: c.expected_qValue!,

          agent_id: d.agent_id,
          duration: d.duration!,
          user_id,
          round,
          st_time_relative,
          end_time_relative
        });
      });
    }

    axios.post('/api/upload/mysql2', { data: draggedTrajData })
      .then(r => console.log('Dragged traj data uploaded:', r.data))
      .catch(e => console.error('Error uploading dragged traj data:', e));
  };

  // Define the structure of try trajectory data
  interface TryTrajData {
    user_id: string;
    round: number;
    agent_id: number;
    agent_st_pos_x: number;
    agent_st_pos_y: number;
    q_value: number;
    expected_q_value: number;
    is_optimal: boolean;
  }

  const uploadTryTrajToServer = () => {
    const user_id = sessionStorage.getItem('userID') || 'unknown';
    const round   = parseInt(sessionStorage.getItem('round') || '1', 10);

    const payload: TryTrajData[] = [];
    for (let agentId = 0; agentId < NUM_AGENTS; agentId++) {
      getTryTraj(agentId).forEach(t => {
        payload.push({
          user_id,
          round,
          agent_id: t.agent_id,
          agent_st_pos_x: t.agent_st_pos!.x,
          agent_st_pos_y: t.agent_st_pos!.y,
          q_value: t.qValue!,
          expected_q_value: t.expected_qValue!,
          is_optimal: t.is_optimal!
        });
      });
    }

    axios.post('/api/upload/mysql6', { data: payload })
      .then(r => console.log('Try traj data uploaded:', r.data))
      .catch(e => console.error('Error uploading try traj:', e));
  };

  const uploadEndCountsToServer = () => {
    const user_id = sessionStorage.getItem('userID') || 'unknown';
    const round   = parseInt(sessionStorage.getItem('round') || '1', 10);

    const counter: Record<number, Record<string, number>> = {};

    for (let agentId = 0; agentId < NUM_AGENTS; agentId++) {
      counter[agentId] = {};
      getEndTraj(agentId).forEach(t => {
        const k = `${t.agent_end_pos!.x},${t.agent_end_pos!.y}`;
        counter[agentId][k] = (counter[agentId][k] || 0) + 1;
      });
    }

    const payload: Array<{
      user_id: string;
      round: number;
      agent_id: number;
      tile_x: number;
      tile_y: number;
      cnt: number;
    }> = [];

    for (let agentId = 0; agentId < NUM_AGENTS; agentId++) {
      PELLET_TILES.forEach(([x, y]) => {
        const key = `${x},${y}`;
        payload.push({
          user_id,
          round,
          agent_id: agentId,
          tile_x: x,
          tile_y: y,
          cnt: counter[agentId][key] || 0  
        });
      });
    }

    axios.post('/api/upload/mysql7', { data: payload })
      .then(r => console.log('End counts uploaded:', r.data))
      .catch(e => console.error('Error uploading end counts:', e));
  };

  return (
    <div>
      <h1>Timer: {Math.max(0, 100 - Math.floor(time))} seconds left</h1>

      {isDialogOpen && (
        <ConfirmDialog 
          message={dialogMessage} 
          onConfirm={handleConfirm}
        />
      )}
    </div>
  );
};

export default React.memo(Timer); 