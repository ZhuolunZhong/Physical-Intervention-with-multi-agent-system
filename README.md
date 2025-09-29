# interrupting roombas 
## Experiment Questions
1. How do people teach a simple task to agents using physical interaction (direct manipulation)?
2. When more than one learner is present, does the teacher teach the second learner differently depending on the second learner's mental state (e.g., observing the first learner being taught and perceived to have having the mental capacity and motivation to learn)?
## TODOs/Status 
### Joe
* Make it so the agent doesn't get a pellet if they are manually moved onto one by participant 
  * Currently drag is blocking, but perhaps add "agent needs to move on its own at least X before it can pickup pellets again" (one self-move?)
* Clean UI and make agent visual access clear, status, and toggleable (as well as other factors, such as getting a pellet reward, when the agent can't get pellets )
  * Looks like refactor for arbitrary agent size is working
### Kesong
* Create "page routing" to make it easy to add consent page, instructions, etc.
  * in progress: probably will use jspsych
* Server-side code to providing starting information for the current participant and store the results. Client-side code to ask/get participant starting params and gather all data to send and make data store requests
  * Server-side mostly done
  * Client-side todo
### Both
* During experiment control logic to make it easy to control what each participant's "trial" is like

## TO JOE: (possible bug)
I think the max # of pellets given by a traj to RL is 1. Need to fix.
## Install
You need to have node.js installed. If you're on windows, I recommend using the linux subsystem and using vs code through that (that's my current development platform).

If you navigate to the directory in terminal and run `npm install` that should install what you need to run the demo. To run it after installed, in the project root directory, run `npm start`. Right now it automatically starts and doesn't do loading, but it's a work in progress :).

## Old TODOs
### Major Importance
~~* still having agents run off from screen. also track down breaking bug.~~
    * think this is fixed now. they may go a bit out of range so it should be tweaked. but if a user places them far away, randMove puts them back. we should make a better solution for this though.
* FIX X/Y reversal
    * is it fixed?
* ~~ add logger that records movements~~
    * first draft done -- still needs pellet data to be added
* Design and implement feature/state space for a RL agent. 
    * Current thought: features = region of grid? distance to each agents and distance to closest pellet in each direction.  Latter may be too good, although probably not if there are punishing pellets too (with associated )
* make a pellet counter so that pellet ids are unique over states and not just within state
* better agent init in Grid
### Medium Importance
* For Q-learner, keep close eye on how NOMOVE action performs... might be too good if agent puts agent on pellet too much
    * In fact it may just make all interventions perform worse than self-learning...
* Improve QLearningAgent's interface s.t. it's easier to switch feature sets with everything else intact.
* Make more robust learning setup (some sort of LearningRoomba abstract class that includes runLearn())
* Make Pellets/Agents size and the Pellet-Agent collision dependent of constants in utils.ts instead of hardcoded
* ~~Pellet~~ What other distributions for producing pellets?
    * distribution for producing them 
    * spatial Poisson process? Hawkes? Maybe check out foraging literature? (start with simplest) 
        - ~~probabaly generate waiting time until next pellet in sagas and then dispatch a creation action.~~
* ~~Pellets~~ Pellet
    *  Color and type 
*  Move agent and pellet initialization
* how to handle multiple pellet pickup on mouse movement?
	* ~~block pellet pick up while mousedrag?~~ (MOUSE_MOVE_BLOCKS_PELLETS is boolean constant defined in utils that toggles this)

* refactor so that agent move is a class or interface so that "plug and play" different types of agents is more natural
* refactor constants, actions, and initializations
* ~~plug in better looking agent sprite~~ 
* visual indicators related ~~to while picked up~~, waiting/thinking of next move, happy/sad from pellet feedback, and waiting for training to complete. 
* make agent size more customizable 
    * right now it is hardcoded to be 1/2 the size of a box (tile)

### Minor Importance
* fix non-breaking todos in code
* cleanup overuse of forcing immutable array/object changes.
* make react code more efficient via best uses of useMemo and the like
