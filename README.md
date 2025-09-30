# Getting started
You need to have node.js installed on your system to run the code. Follow these [instructions](https://nodejs.org/en/download).

You may also need to run  `npm install react-scripts --save-dev`

run `npm install` in the main directory to install needed packages

`npm start`  <- use this in terminal to start after install

# Open src/utils/index.tsx to set parameters. 
## Max number of agents is 3.
## Change PELLET_MODE to 1 to use PELLET_PATCH_MEAN2 and PELLET_PATCH_VAR2
## EXPECTED_PELLET_TIME control the pellet generation rate
## AGENT_EPS -> Exploration rate
## TEACH_EPS -> Stimulated teacher's intervention rate, currently, it is used to determining whether an agent's action is optimal, generally requires no modification
## MOVE_TIME -> Agents move time for 1 step, the unit is seconds
## WAIT_TIME -> Agents wait time before next action
## HUM_INT_FB -> Control intrepretation feedback
## PELLET_FEEDBACK -> Single pellet's reward
## INTERPRET_TYPE -> Agents' intepretation type -> {
    SUGGESTION = 0,
    RESET,
    INTERRUPT,
    TRANSITION,
    DISRUPT,
    IMPEDE
}


## Interpretation type explanation
* *Suggestion*: This interpretation treats the intervention as a suggestion for the new tile. The agent learns from the state-action sequence connected to the new tile, ignoring its own intended action, and uses the actual reward from the new tile.
    * *Learning Rule*: Use $(s_t, a^I, s^I_{t+1}, r^I)$ for Q-update.
    * *Special Case* (Dragged back to $s_t$): No learning triggered because there is no action for that keeps the agent at the same state.

*  *Reset*: This interpretation views the intervention as a neutral reset or relocation. The agent acknowledges its original state-action sequence and learns from it.
    * *Learning Rule*: Use $(s_t, a_t, s^A_{t+1}, r_t)$ for Q-update.

* *Interrupt*: This interpretation treats the intervention as a mere interruption of the agent's autonomy. No learning occurs from the event itself; the agent simply continues its policy from the new state.
    * *Learning Rule*: Performs no Q-update during intervention. Proceeds directly from new state without learning.

* *Transition*: This interpretation treats the intervention as a transition from old state to new state (tile). It uses a fixed positive reward to learn from the state-action sequence connected to the new tile. If the new state is the same as the old state, it uses a fixed negative reward to learn from original state-action sequence instead as interprets it as bad.

    * *Learning Rule*: Use $(s_t, a^I, s^I_{t+1}, 2R_{\text{pellet}})$ for Q-update.
    * *Special Case* (Dragged back to $s_t$): Use $(s_t, a_t, s^A_{t+1}, -2R_{\text{pellet}})$ instead.

* *Disrupt*: This interpretation treats any intervention as an inherently negative or disruptive event, it uses a fixed negative reward to penalizing the agent from the state-action sequence connected to the new tile.

    * *Learning Rule*: Use $(s_t, a^I, s^I_{t+1}, -2R_{\text{pellet}})$ for Q-update.
    * *Special Case* (Dragged back to $s_t$): No learning triggered because there is no action for that keeps the agent at the same state.

* *Impede*: This interpretation punishes the agent's original chosen action, framing the intervention as a consequence of a poor decision. The agent uses a fixed negative reward to learn from its original state-action sequence.
    * *Learning Rule*: Use $(s_t, a_t, s^A_{t+1}, -2R_{\text{pellet}})$ for Q-update.

## PELLET_TILES -> Spawn tiles

Builds on [Ho et al 2017](https://escholarship.org/content/qt8z48f0ms/qt8z48f0ms.pdf)