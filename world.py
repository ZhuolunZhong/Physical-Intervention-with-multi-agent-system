import numpy as np
from scipy.stats import norm
from collections import defaultdict
from enum import IntEnum
from typing import Dict, Tuple 
import random

class AgentAction(IntEnum):
    UP = 0        # (dx=0, dy=-1)
    DOWN = 1      # (dx=0, dy=1)
    LEFT = 2      # (dx=-1, dy=0)
    RIGHT = 3     # (dx=1, dy=0)
    UPLEFT = 4    # (dx=-1, dy=-1)
    UPRIGHT = 5   # (dx=1, dy=-1)
    DOWNLEFT = 6  # (dx=-1, dy=1)
    DOWNRIGHT = 7 # (dx=1, dy=1)

class GridWorld:
    def __init__(self, width=8, height=8, 
                 patch_means=[[3, 3], [3, 3]], 
                 patch_vars=[[0.75, 0.75], [0.75, 0.75]],
                 spawn_rate=10,
                 mode=1,
                 random_seed=3,
                 random_grid=16,
                 mode3_centers=[[3, 3]]):
        """
        Grid world core class (top-left corner as (0,0) coordinate system)
        
        Parameters:
            width: Grid width (default 8)
            height: Grid height (default 8)
            patch_means: Normal distribution center coordinates list [[x1,y1], [x2,y2]] 
            patch_vars: Normal distribution variance list [[var_x1,var_y1], [var_x2,var_y2]]
            spawn_rate: Point generation rate (expected points per second)
        """
        # Basic configuration
        self.width = width
        self.height = height
        self.spawn_rate = spawn_rate
        self.mode = mode
        self.random_seed = random_seed
        self.random_grid = min(random_grid, width * height)

        self.mode3_centers = mode3_centers
        self.selected_grids = []  # List of selected grid coordinates
        if self.mode == 2 or self.mode == 3:
            self._init_grid_mode()
        
        # Point generation parameters
        self.patch_means = np.array(patch_means)
        self.patch_vars = np.array(patch_vars)
        self.num_patches = len(patch_means)
        
        # Action direction mapping (note: y-axis positive downward)
        self.action_map = {
            AgentAction.UP: (0, -1),
            AgentAction.DOWN: (0, 1),
            AgentAction.LEFT: (-1, 0),
            AgentAction.RIGHT: (1, 0),
            AgentAction.UPLEFT: (-1, -1),
            AgentAction.UPRIGHT: (1, -1),
            AgentAction.DOWNLEFT: (-1, 1),
            AgentAction.DOWNRIGHT: (1, 1)
        }
        
        # Dynamic state
        self.points = defaultdict(list)  # {(x,y): [Point]}
        self.q_table = {}  # {(x,y): {action: expected_reward}}
        self.optimal_actions = {}  # {(x,y): best_action}
        
        # Initialization validation
        self._validate_params()
        self._precompute_probability_grid() 
        self._build_reference_q_table()   # Initial Q-table generation

        # Evaluation related parameters
        self.eval_steps = 30  # Evaluation steps
        self.eval_episodes = 100  # Evaluation episodes

    def evaluate_policy(self, q_table: Dict[Tuple[int, int], Dict[AgentAction, float]]) -> float:
        """Evaluate expected return for given Q-table"""
        total_value = 0.0
        
        for _ in range(self.eval_episodes):
            # Random initial position
            x, y = np.random.randint(0, self.width), np.random.randint(0, self.height)
            episode_value = 0.0

            for _ in range(self.eval_steps):
                # Select optimal action based on Q-table
                if (x,y) not in q_table:
                    print(x,y,'no!')
                    break
                    
                action_values = q_table[(x,y)]
                max_q = max(action_values.values())
                best_actions = [a for a, q in action_values.items() if q == max_q]
                action = random.choice(best_actions)
                
                # Calculate expected reward
                dx, dy = self.action_map[action]
                new_x, new_y = x + dx, y + dy
                if 0 <= new_x < self.width and 0 <= new_y < self.height:
                    reward = self._calculate_path_reward(x, y, new_x, new_y)
                    episode_value += reward
                
                # Update position
                x, y = new_x, new_y
            
            total_value += episode_value
        
        return total_value 

    def _build_reference_q_table(self):
        """Build static reference Q-table (based on probability grid)"""
        self.q_table = {}
        self.optimal_actions = {}
    
        for y in range(self.height):
            for x in range(self.width):
                state = (x, y)
                self.q_table[state] = {}
            
                for action in AgentAction:
                    dx, dy = self.action_map[action]
                    new_x, new_y = x + dx, y + dy
                
                    if 0 <= new_x < self.width and 0 <= new_y < self.height:
                        # Straight movement
                        if x == new_x or y == new_y:
                            reward = self.prob_grid[new_y, new_x]
                        # Diagonal movement
                        else:
                            reward = (self.prob_grid[new_y, new_x] + 
                                     0.5 * self.prob_grid[y, new_x] + 
                                     0.5 * self.prob_grid[new_y, x])
                        self.q_table[state][action] = reward
            
                # Record optimal actions
                if self.q_table[state]:
                    max_q = max(self.q_table[state].values())
                    self.optimal_actions[state] = [
                        a for a, q in self.q_table[state].items() 
                        if q == max_q
                    ]

    def _validate_params(self):
        """Parameter validation check"""
        if len(self.patch_means) != len(self.patch_vars):
            raise ValueError("patch_means and patch_vars must have same length")
        if not all(len(m) == 2 for m in self.patch_means):
            raise ValueError("Each patch_mean must be in [x,y] format")
        if not all(len(v) == 2 for v in self.patch_vars):
            raise ValueError("Each patch_var must be in [var_x,var_y] format")
        
    def _init_grid_mode(self):
        """Initialize grid selection for mode 2 and 3"""
        all_grids = [(x, y) for x in range(self.width) for y in range(self.height)]
        
        if self.mode == 2:
            rng = np.random.RandomState(self.random_seed)
            self.selected_grids = rng.choice(
                len(all_grids), 
                size=self.random_grid, 
                replace=False
            )
            self.selected_grids = [all_grids[i] for i in self.selected_grids]
        elif self.mode == 3:
            self.selected_grids = []
            centers = np.array(self.mode3_centers)
            num_centers = len(centers)
            grids_per_center = self.random_grid // num_centers
            remaining = self.random_grid % num_centers
            
            for i, center in enumerate(centers):
                # Calculate number of grids allocated per center
                count = grids_per_center + (1 if i < remaining else 0)
                if count == 0:
                    continue
                    
                # Calculate distance from all grid centers to center coordinates
                distances = []
                for x, y in all_grids:
                    # Use grid center coordinates to calculate distance
                    grid_center_x = x + 0.5
                    grid_center_y = y + 0.5
                    dist = np.sqrt((grid_center_x - center[0])**2 + (grid_center_y - center[1])**2)
                    distances.append((dist, (x, y)))
                
                # Sort by distance and select nearest grids
                distances.sort()
                selected = []
                for dist, grid in distances:
                    if grid not in self.selected_grids:
                        selected.append(grid)
                        if len(selected) == count:
                            break
                self.selected_grids.extend(selected)

    def _generate_point_position(self):
        """Generate floating-point coordinates with 2 decimal places"""
        if self.mode == 1:
            while True:
                patch_idx = np.random.choice(self.num_patches)
                mean = self.patch_means[patch_idx]
                var = self.patch_vars[patch_idx]
                
                u1, u2 = np.random.random(2)
                z0 = np.sqrt(-2 * np.log(u1)) * np.cos(2 * np.pi * u2)
                z1 = np.sqrt(-2 * np.log(u1)) * np.sin(2 * np.pi * u2)
                
                x = round(z0 * np.sqrt(var[0]) + mean[0], 2)
                y = round(z1 * np.sqrt(var[1]) + mean[1], 2)
                
                x = np.clip(x, 0, self.width - 1)
                y = np.clip(y, 0, self.height - 1)
                
                return (x, y)
        elif self.mode == 2 or self.mode == 3:
            if not self.selected_grids:
                return (0, 0)  # Return origin if no selected grids
            
            # Randomly select a chosen grid
            grid_x, grid_y = random.choice(self.selected_grids)
            
            # Generate random coordinates within grid (keep 2 decimal places)
            x = round(grid_x + random.random(), 2)
            y = round(grid_y + random.random(), 2)
            
            return (x, y)
        else:
            raise ValueError(f"Unknown generation mode: {self.mode}")

    def update(self, delta_time):
        """
        Update world state
        delta_time: Time interval since last update (seconds)
        """
        # Generate new points (Poisson process)
        expected_points = self.spawn_rate * delta_time
        num_new_points = np.random.poisson(expected_points)
        
        for _ in range(num_new_points):
            pos = self._generate_point_position()
            self.points[pos].append(1)  # Simple point existence recording
        
        # Update Q-table and optimal action table

    def _calculate_path_reward(self, x1, y1, x2, y2):
        """
        Calculate expected reward for path from (x1,y1) to (x2,y2)
        Handle different cases for straight and diagonal movement
        """
        # Target grid probability
        main_prob = self._cell_probability(x2, y2)
        
        # Straight movement
        if x1 == x2 or y1 == y2:
            return main_prob
        
        # Diagonal movement (consider adjacent grids)
        side_prob1 = self._cell_probability(x1, y2)
        side_prob2 = self._cell_probability(x2, y1)
        return (main_prob + 0.5 * side_prob1 + 0.5 * side_prob2) 

    def _cell_probability(self, x, y):
        """Calculate probability of point appearing in grid (x,y) (0-100 range)"""
        return self.prob_grid[int(y), int(x)]
    
    def _precompute_probability_grid(self):
        """Get probability from precomputed grid"""
        if self.mode == 1:
            x_coords = np.arange(self.width)
            y_coords = np.arange(self.height)
            xx, yy = np.meshgrid(x_coords, y_coords)
        
            self.prob_grid = np.zeros((self.height, self.width))
            for i in range(self.num_patches):
                mean_x, mean_y = self.patch_means[i]
                var_x, var_y = self.patch_vars[i]
            
                px = norm.cdf(xx + 1, mean_x, np.sqrt(var_x)) - \
                    norm.cdf(xx, mean_x, np.sqrt(var_x))
                py = norm.cdf(yy + 1, mean_y, np.sqrt(var_y)) - \
                    norm.cdf(yy, mean_y, np.sqrt(var_y))
            
                self.prob_grid += (px * py) / self.num_patches
        elif self.mode == 2 or self.mode == 3:
            self.prob_grid = np.zeros((self.height, self.width))
            if self.selected_grids:
                prob = 1.0 / len(self.selected_grids)  # Total probability per selected grid
                for x, y in self.selected_grids:
                    self.prob_grid[y, x] = prob  # Note: y is row index
        else:
            raise ValueError(f"Unknown generation mode: {self.mode}")

    def check_collision(self, pos):
        """Precise collision detection: delete all points within agent coverage area"""
        x, y = pos  # Agent top-left coordinates
        deleted = 0
    
        # Agent coverage area [x, x+1) x [y, y+1)
        for point_pos in list(self.points.keys()):
            px, py = point_pos
            if (x <= px < x+1) and (y <= py < y+1):
                deleted += len(self.points[point_pos])
                del self.points[point_pos]
            
        return deleted
    
    def get_optimal_actions(self, pos):
        """
        Get all optimal actions list for a position
        Return: [AgentAction] (may contain multiple actions)
        """
        return self.optimal_actions.get(tuple(map(int, pos)), [AgentAction.UP])
    
    def is_optimal_action(self, pos, action):
        """Check if given action is one of optimal actions for current position"""
        return action in self.get_optimal_actions(pos)
    
    def get_spawn_grids(self):
        """Return list of all possible point generation grid coordinates"""
        if self.mode == 2 or self.mode == 3:
            return self.selected_grids
        else:
            return [(x, y) for x in range(self.width) for y in range(self.height)]

    def visualize_probabilities(self):
        """Print probability distribution map (for debugging)"""
        grid = np.zeros((self.height, self.width))
        for y in range(self.height):
            for x in range(self.width):
                grid[y][x] = self._cell_probability(x, y)
        
        print("Probability distribution map (y-axis downward):")
        print(np.round(grid, 1))

    def visualize_selected_grids(self):
        """Visualize selected grids, return matplotlib figure object"""
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        
        fig, ax = plt.subplots(figsize=(self.width, self.height))
        
        # Draw all grids
        for x in range(self.width):
            for y in range(self.height):
                color = 'black' if (x, y) in self.selected_grids else 'white'
                rect = patches.Rectangle(
                    (x, y), 1, 1, 
                    linewidth=1, edgecolor='gray', 
                    facecolor=color
                )
                ax.add_patch(rect)
        
        # Set axes
        ax.set_xlim(0, self.width)
        ax.set_ylim(0, self.height)
        ax.set_aspect('equal')
        ax.invert_yaxis()  # Keep y-axis downward
        ax.set_title(f"Selected Grids (Mode={self.mode})")
        ax.grid(True, which='both', color='gray', linestyle='-', linewidth=0.5)
        
        return fig
    
if __name__ == "__main__":

    size = 8

    # Create test world
    test_world = GridWorld(
        width=size,
        height=size,
        mode=3,
        random_seed=size,
        random_grid=18,
        mode3_centers=[[2.5,2.5],[5.5,5.5]]
    )
    
    # Generate and save visualization
    fig = test_world.visualize_selected_grids()
    fig.savefig(f"selected_grids_mode3_size_{size}_grid_{18}.png", 
               bbox_inches='tight', dpi=100)
    print(f"Visualization saved as selected_grids_mode3_size_{size}_grid_{18}.png")
    print(test_world.selected_grids)