import { Link } from "react-router-dom"
import { agentIdToImg } from "../utils"
import React from 'react';

const Consent2 = () => {
  return (
    <div style={{ fontSize: '18px', lineHeight: '1.6', margin: '20px' }}>
      <h1 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '20px' }}>
        WHAT WILL MY PARTICIPATION INVOLVE?
      </h1>
      <p>
        Your task is to teach control of learning agents who take sequential actions in a simple virtual environment. The environments are typically "gridworlds" in which agents can move in eight directions (primary and diagonal directions). The agents have one objective: to take movements that will result in them getting as many points as possible.
      </p>
      <p>
        The agent learns successful movements by acquiring points, but it cannot see where the points are. <strong>Your task is to help the agent learn</strong>.
      </p>
      <p>
        You can assist by clicking and dragging the agent with your mouse, moving it to the desired location. When you release the mouse, the agent will drop and continue its actions.
      </p>
      <p>
        Sometimes you will be teaching one agent. At other times, you will be teaching two agents simultaneously.
      </p>
      <p>
        Note: Points collected by the agent immediately when you drop the agent do not count towards the agent's score and its learning. To get a point, the agent must move there by its own volition.
      </p>
      <p>
        The agents look like the following:
      </p>
      
      <div style={{ display: 'flex', justifyContent: 'flex-start', gap: '20px', margin: '20px 0' }}>
        <img src={agentIdToImg[0]} alt="Agent 0" style={{ width: '100px', height: '100px' }} />
        <img src={agentIdToImg[1]} alt="Agent 1" style={{ width: '100px', height: '100px' }} />
        <img src={agentIdToImg[2]} alt="Agent 2" style={{ width: '100px', height: '100px' }} />
        <img src={agentIdToImg[3]} alt="Agent 3" style={{ width: '100px', height: '100px' }} />
        <img src={agentIdToImg[4]} alt="Agent 4" style={{ width: '100px', height: '100px' }} />
        <img src={agentIdToImg[5]} alt="Agent 5" style={{ width: '100px', height: '100px' }} />
      </div>

      <p>
        Each game round lasts for 100 seconds, with a total of 9 rounds. After each round, you can take a break before pressing confirm to proceed.
        The first round is a trial, giving you a chance to observe and get a feel for the game. The remaining 8 rounds consist of 4 different settings, each repeated 2 times. 
        Before entering a new setting, there will be a reminder on the screen.
      </p>

      <p>
        After completing a set of four rounds, you will be asked to briefly describe your teaching strategy and the reasons behind your approach. Your participation will require 1 session lasting between 30 and 40 minutes total.
      </p>
      <div style={{ marginTop: '20px', textAlign: 'center' }}>
        <Link to='/main_expt'>Proceed to the experiment</Link>
      </div>
    </div>
  );
};

export default Consent2;
