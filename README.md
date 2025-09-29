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
## PELLET_TILES -> Spawn tiles
