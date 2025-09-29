import numpy as np
from enum import IntEnum
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import random
from world import GridWorld, AgentAction

class InterventionType(IntEnum):
    SUGGESTION = 0     
    RESET = 1      
    INTERRUPT = 2   
    TRANSITION = 3  
    DISRUPT = 4     
    IMPEDE = 5      

class QLearningAgent:
    def __init__(self, 
                 world: GridWorld,
                 initial_position: Optional[Tuple[int, int]] = None,
                 max_steps: int = 1000,
                 learning_rate: float = 0.1,
                 discount_factor: float = 0.9,
                 exploration_rate: float = 0.3,
                 intervention_rate: float = 0.2,
                 intervention_type: int = 1,
                 intervention_mode: int = 1,
                 point_value: int = 6,
                 step_cost: float = -1.0,
                 move_time: float = 0.2,
                 intervention_feedback: float = -12.0,
                 agent_id: int = 0,
                 intervention_stop_step: Optional[int] = None):
        """
        Parameters:
            world: Grid world instance
            learning_rate (α): Learning rate (default 0.1)
            discount_factor (γ): Discount factor (default 0.9)
            exploration_rate (ε): Exploration rate (default 0.3)
            intervention_rate: Teacher intervention probability (default 0.2)
            point_value: Value of each point (default 6)
            step_cost: Base movement cost (default 1.0)
            move_time: Movement time cost (seconds) (default 1.0)
        """
        self.world = world
        self.initial_position = initial_position
        self.alpha = learning_rate
        self.gamma = discount_factor
        self.epsilon = exploration_rate
        self.intervention_prob = intervention_rate
        self.point_value = point_value
        self.step_cost = step_cost
        self.move_time = move_time
        self.agent_id = agent_id
        self.eval_history = []

        # Training state control
        self.current_step: int = 0
        self.max_steps: int = max_steps
        self.is_training_done: bool = False  # Termination signal
        self.intervention_stop_step = intervention_stop_step if intervention_stop_step is not None else max_steps
        self.original_intervention_rate = intervention_rate  # Save original intervention rate

        # State tracking
        self.x: int   # Current integer x coordinate
        self.y: int  # Current integer y coordinate
        self.sub_x: float   # Sub-grid x position
        self.sub_y: float   # Sub-grid y position
        self.new_x: int  # Post-intervention integer x coordinate
        self.new_y: int  # Post-intervention integer y coordinate
        self.try_x: int  # Action target integer x coordinate
        self.try_y: int  # Action target integer y coordinate
        self.moving: bool = False
        self.move_progress: float   # Movement progress (0-1)
        self.current_action: Optional[AgentAction] = None
        self._initialize_position()  
        self.accumulated_reward: float = 0.0  # For accumulating current step reward
        self.land_reward: float = 0.0  # For accumulating current step reward
        self.last_position: Tuple[int, int] = (0, 0)  # Record state before learning
        self.last_action: Optional[AgentAction] = None  # Record action before learning
        self.visit_counts = defaultdict(int)  # Visit count dictionary

        # Lock state tracking
        self.lock_remaining: float = 0.0
        self.is_intervened: bool = False
        
        # Learning system
        self._valid_actions_cache = {}
        self.q_table: Dict[Tuple[int, int], Dict[AgentAction, float]] = {
            (x, y): {action: 1.0 for action in self._get_valid_actions(x, y)}
            for x in range(self.world.width)
            for y in range(self.world.height)
        }
        self.policy: Dict[Tuple[int, int], AgentAction] = {
            (x, y): random.choice(self._get_valid_actions(x, y)) 
            for x in range(self.world.width)
            for y in range(self.world.height)
        }
        
        # Intervention system
        self.intervention_log = []
        self.total_reward = 0
        self.intervention_type = InterventionType(intervention_type)
        self.intervention_mode = intervention_mode
        self.intervention_feedback = intervention_feedback

    def _get_step_cost_multiplier(self, action: AgentAction) -> float:
        """Return movement cost coefficient based on action type"""
        if action in [AgentAction.UP, AgentAction.DOWN, 
                       AgentAction.LEFT, AgentAction.RIGHT]:
            return 1.0
        else:  # Diagonal movement
            return 1.414  # √2 approximation

    def _initialize_position(self):
            """Initialize position (modified version)"""
            if self.initial_position is not None:
                # Use specified initial position
                self.x, self.y = self.initial_position
            else:
                # Random initial position
                self.x = random.randint(0, self.world.width - 1)
                self.y = random.randint(0, self.world.height - 1)

            self.sub_x = 0.0
            self.sub_y = 0.0
            self.moving = False
            self.move_progress = 0.0
            self.new_x, self.new_y = self.x, self.y
            self.land_reward = 0.0

    def _intervention(self):
        """Determine placement position after intervention based on intervention_mode"""
        if self.intervention_mode == 1:
            # Mode 1: Drag back to movement start position
            self.new_x, self.new_y = self.x, self.y
            return
        
        # Get grid coordinates within 5x5 range
        x_min = max(0, self.x - 2)
        x_max = min(self.world.width - 1, self.x + 2)
        y_min = max(0, self.y - 2)
        y_max = min(self.world.height - 1, self.y + 2)
        
        candidates = []
        for y in range(y_min, y_max + 1):
            for x in range(x_min, x_max + 1):
                candidates.append((x, y))
        
        if self.intervention_mode == 2 or self.intervention_mode == 3:
            # Mode 2 and 3: Find grid with highest probability
            candidates.sort(key=lambda pos: -self.world.prob_grid[pos[1], pos[0]])
        elif self.intervention_mode == 4:
            # Mode 4: Find grid with lowest probability
            candidates.sort(key=lambda pos: self.world.prob_grid[pos[1], pos[0]])
        
        if not candidates:
            self.new_x, self.new_y = self.x, self.y
            return
        
        # Get grids with highest/lowest probability (may have multiple)
        target_prob = self.world.prob_grid[candidates[0][1], candidates[0][0]]
        best_positions = [pos for pos in candidates 
                         if self.world.prob_grid[pos[1], pos[0]] == target_prob]
        
        if self.intervention_mode == 3:
            # Mode 3: Randomly select from 3x3 grids near best position
            target_pos = random.choice(best_positions)
            x_min = max(0, target_pos[0] - 1)
            x_max = min(self.world.width - 1, target_pos[0] + 1)
            y_min = max(0, target_pos[1] - 1)
            y_max = min(self.world.height - 1, target_pos[1] + 1)
            nearby_positions = [
                (x, y) for x in range(x_min, x_max + 1) 
                for y in range(y_min, y_max + 1)
            ]
            nearby_positions = [
                (x, y) for x in range(x_min, x_max + 1)
                for y in range(y_min, y_max + 1)
                if (x, y) != target_pos and  
                self.world.prob_grid[y, x] != target_prob  
            ]
            if nearby_positions:
                self.new_x, self.new_y = random.choice(nearby_positions)
            else:
                self.new_x, self.new_y = self.x, self.y 
                
        else:
            # Mode 2 and 4: Directly select one of best positions
            self.new_x, self.new_y = random.choice(best_positions)

    def _sync_new_position(self):
        """Synchronize new_x/new_y to x/y"""
        self.x, self.y = self.new_x, self.new_y
        self.sub_x = self.sub_y = 0.0
        self.moving = False
        self.move_progress = 0.0


    def update(self, delta_time: float) -> bool:
        """Update agent state"""
        if self.is_training_done:
            return True
        
        # Handle lock state
        if self.lock_remaining > 0:
            self.lock_remaining -= delta_time
            return False
        
        # Handle post-intervention unlock
        if self.is_intervened:
            self.is_intervened = False
            self._make_decision()
            return False        
        
        if self.moving:
            self._update_movement(delta_time)
        else:
            self._make_decision()

        return self.is_training_done

    def _update_movement(self, delta_time: float):
        """Handle state updates during movement"""
        self.move_progress += delta_time / self.move_time

        # Calculate current sub-grid offset (based on movement progress)
        dx, dy = self.world.action_map[self.current_action]
        self.sub_x = dx * self.move_progress
        self.sub_y = dy * self.move_progress
        
        # Real-time collision detection (using precise position with sub-grid offset)
        current_pos = (self.x + self.sub_x, self.y + self.sub_y)
        reward = self.world.check_collision(current_pos) * self.point_value
        self.accumulated_reward += reward
        self.total_reward += reward

        # Check if intervention needed (trigger when movement past halfway)
        if (self.move_progress >= 0.5 and 
            not self.world.is_optimal_action((self.x, self.y), self.current_action)):
            if random.random() < self.intervention_prob:
                self._apply_intervention()
                return
        
        # Movement completion handling
        if self.move_progress >= 1.0:
            self._complete_movement()

    def _make_decision(self):
        """ε-greedy policy action selection"""
        valid_actions = self._get_valid_actions()
        
        if random.random() < self.epsilon:
            # Random exploration
            self.current_action = random.choice(valid_actions)
        else:
            # Select action with highest Q-value
            q_values = self.q_table[(self.x, self.y)]
            max_q = max(q_values.values())
            best_actions = [a for a, q in q_values.items() if q == max_q and a in valid_actions]
            self.current_action = random.choice(best_actions) if best_actions else random.choice(valid_actions)

        self._try_position()
        self.moving = True
        self.move_progress = 0.0

    def _try_position(self):
        # Calculate new position
        dx, dy = self.world.action_map[self.current_action]
        self.try_x = max(0, min(self.world.width-1, self.x + dx))
        self.try_y = max(0, min(self.world.height-1, self.y + dy))
        
    def _complete_movement(self):
        """State update after movement completion"""

        # Execute learning update
        self._update_q_value(
            self.x,  # Original position (integer coordinates)
            self.y,
            self.current_action,
            self.accumulated_reward,
            self.try_x,
            self.try_y
        )
        
        # Update position and reset sub-grid offset
        self.x, self.y = self.try_x, self.try_y
        self.sub_x, self.sub_y = 0.0, 0.0
        self.accumulated_reward = 0.0
        # Record movement visit
        self.visit_counts[(self.x, self.y)] += 1
        
        self.moving = False
        self.current_action = None
        self._increment_step()

    def _update_q_value(self, x: int, y: int, action: AgentAction, reward: float, new_x: int, new_y: int):
        """Update Q-value (including movement cost)"""
        current_q = self.q_table[(x, y)][action]
        next_valid_actions = self._get_valid_actions(new_x, new_y)
        max_next_q = max([self.q_table[(new_x, new_y)][a] for a in next_valid_actions]) if next_valid_actions else 0
        
        # Calculate movement cost (fully restoring React version logic)
        cost = self.step_cost * self._get_step_cost_multiplier(action)
        td_target = reward + cost + self.gamma * max_next_q
        new_q = current_q + self.alpha * (td_target - current_q)
        
        # Update Q-table and policy
        self.q_table[(x, y)][action] = new_q
        self._update_policy(x, y)

    def _update_policy(self, x: int, y: int):
        """Update policy table"""
        q_values = self.q_table[(x, y)]
        valid_actions = self._get_valid_actions(x, y)
        
        if valid_actions:
            max_q = max(q_values[a] for a in valid_actions)
            best_actions = [a for a in valid_actions if q_values[a] == max_q]
            self.policy[(x, y)] = random.choice(best_actions)

    def _apply_intervention(self):
        self._intervention()
        self._check_intervention_collision()

        # Lock action time and log logic
        self.is_intervened = True
        self.lock_remaining = 0.0
        self.lock_remaining = self.move_time - self.move_progress * self.move_time
        self.intervention_log.append({
            'step': self.current_step,
            'from': (self.x, self.y),
            'to': (self.new_x, self.new_y),
            'original_action': self.current_action,
            'land_reward': self.land_reward
        })
        
        # Execute different handling based on intervention type
        if self.intervention_type == InterventionType.INTERRUPT:
            self._handle_interrupt()
        elif self.intervention_type == InterventionType.RESET:
            self._handle_reset_intervention()
        elif self.intervention_type == InterventionType.TRANSITION:
            self._handle_transition_intervention()
        elif self.intervention_type == InterventionType.DISRUPT:
            self._handle_disrupt_intervention()
        elif self.intervention_type == InterventionType.IMPEDE:
            self._handle_impede_intervention()
        elif self.intervention_type == InterventionType.SUGGESTION:
            self._handle_suggestion()
            

        # Reset state (clear movement state)
        self._sync_new_position()
        # Record visit
        self.visit_counts[(self.x, self.y)] += 1
        self.current_action = None
        self._increment_step()

    def _check_intervention_collision(self):
        """Special handling for intervention collision detection"""
        # Detect collision at new position
        new_pos = (self.new_x, self.new_y)  # Use intervention target position
        reward = self.world.check_collision(new_pos) * self.point_value
        self.land_reward = reward
        self.total_reward += reward

    def _handle_interrupt(self):
        """Interrupt: Completely skip learning"""
        pass  # No Q-table update
    
    def _handle_reset_intervention(self):
        """RESET: Maintain original learning principle"""
        # Learning update (position unchanged)
        self._update_q_value(
            self.x, self.y, 
            self.current_action,
            self.accumulated_reward,
            self.try_x, self.try_y  
        )
        self.accumulated_reward = 0.0

    def _handle_transition_intervention(self):
        """TRANSITION: Encourage action towards intervention target position"""
        if (self.new_x, self.new_y) == (self.x, self.y):
            self._update_q_value(
                self.x, self.y,
                self.current_action,
                self.intervention_feedback,
                self.try_x, self.try_y
            )
        else:
            # Normal learning update
            action_to_target = self._get_action_towards(self.new_x, self.new_y)
            feedback = -self.intervention_feedback
            self._update_q_value(
                self.x, self.y,
                action_to_target,
                feedback,
                self.new_x, self.new_y
            )
        self.accumulated_reward = 0.0

    def _handle_disrupt_intervention(self):
        """DISRUPT: Penalize action towards intervention position"""
        if (self.new_x, self.new_y) == (self.x, self.y):
            return  # No learning when dragged back
        
        # Use intervention feedback instead of accumulated reward
        action_to_target = self._get_action_towards(self.new_x, self.new_y)
        self._update_q_value(
            self.x, self.y,
            action_to_target,
            self.intervention_feedback,  # Fixed negative reward
            self.new_x, self.new_y  # Position unchanged
        )
        self.accumulated_reward = 0.0

    def _handle_impede_intervention(self):
        """IMPEDE: Penalize original action"""
        # Use intervention feedback with position unchanged
        self._update_q_value(
            self.x, self.y,
            self.current_action,
            self.intervention_feedback,  
            self.try_x, self.try_y  
        )
        self.accumulated_reward = 0.0

    def _handle_suggestion(self):
        """Suggestion: Use landing reward to update suggested action"""
        if (self.new_x, self.new_y) == (self.x, self.y):
            return  # No learning when dragged back
        
        action_to_target = self._get_action_towards(self.new_x, self.new_y)

        self._update_q_value(
            self.x, self.y,
            action_to_target,
            self.land_reward,
            self.new_x, self.new_y
        )
        self.accumulated_reward = self.land_reward = 0.0

    def _get_action_towards(self, target_x: int, target_y: int) -> AgentAction:
        """Return closest 8-direction action from current position to target position"""
        dx = target_x - self.x
        dy = target_y - self.y
    
        # Calculate unit direction vector (8-direction normalized)
        norm = max(abs(dx), abs(dy))
        if norm == 0:
            return random.choice(list(AgentAction))  # Return random if stationary
    
        unit_dx = dx / norm
        unit_dy = dy / norm
    
        # Map direction to 8 standard actions
        direction_map = {
            (0, -1): AgentAction.UP,        # Up
            (0, 1): AgentAction.DOWN,       # Down
            (-1, 0): AgentAction.LEFT,      # Left
            (1, 0): AgentAction.RIGHT,      # Right
            (-1, -1): AgentAction.UPLEFT,   # Up-left
            (1, -1): AgentAction.UPRIGHT,   # Up-right
            (-1, 1): AgentAction.DOWNLEFT,  # Down-left
            (1, 1): AgentAction.DOWNRIGHT   # Down-right
        }
    
        # Find closest standard direction
        closest_dir = min(
            direction_map.keys(),
            key=lambda dir: (unit_dx - dir[0])**2 + (unit_dy - dir[1])**2
        )
    
        return direction_map[closest_dir]

    def _increment_step(self):
        """Step increment and termination check"""
        self.current_step += 1

        # Turn off intervention when reaching stop intervention step
        if self.current_step >= self.intervention_stop_step:
            self.intervention_prob = 0.0

        expected_q = self.world.evaluate_policy(self.q_table)
        self.eval_history.append({
            'agentid': self.agent_id,
            'step': self.current_step,
            'ExpectedQvalue': expected_q,
            'CumulativeReward': self.total_reward
        })

        if self.current_step >= self.max_steps:
            self.is_training_done = True
            
    def _save_eval_history(self):
        """Save evaluation results to CSV"""
        import pandas as pd
        df = pd.DataFrame(self.eval_history)
        df.to_csv(f'agent_{self.agent_id}_eval.csv', index=False)

    def _get_valid_actions(self, x: Optional[int] = None, y: Optional[int] = None) -> List[AgentAction]:
        """Get executable action list for specified position"""
        x = x if x is not None else self.x
        y = y if y is not None else self.y
        key = (x, y)
        
        if key not in self._valid_actions_cache:
            valid_actions = []
            for action in AgentAction:
                dx, dy = self.world.action_map[action]
                new_x, new_y = x + dx, y + dy
                if 0 <= new_x < self.world.width and 0 <= new_y < self.world.height:
                    valid_actions.append(action)
            self._valid_actions_cache[key] = valid_actions

        return self._valid_actions_cache[key]

    def get_position(self) -> Tuple[float, float]:
        """Get current precise position (including sub-grid offset)"""
        return (self.x + self.sub_x, self.y + self.sub_y)

    def get_status(self) -> Dict:
        """Get current status summary"""
        return {
            'position': self.get_position(),
            'moving': self.moving,
            'action': self.current_action.name if self.current_action else None,
            'progress': self.move_progress,
            'total_reward': self.total_reward,
            'interventions': len(self.intervention_log)
        }
    
    def get_visit_counts(self):
        """Return copy of visit statistics dictionary"""
        return dict(self.visit_counts)