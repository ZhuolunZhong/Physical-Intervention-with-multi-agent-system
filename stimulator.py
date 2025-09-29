import time
import pandas as pd
from typing import List, Dict, Optional
from pathlib import Path

class TimeController:
    """Precision time controller"""
    def __init__(self, time_step: float = 0.1):
        self.time_step = time_step  # Time increment for each update (seconds)
        self.current_time = 0.0
    
    def tick(self) -> float:
        """Advance time and return current time"""
        self.current_time += self.time_step
        return self.current_time

class Stimulator:
    def __init__(
        self,
        world_params: Dict,
        agents_params: List[Dict],
        time_step: float = 0.1,
        max_simulation_time: Optional[float] = None
    ):
        """
        Parameters:
            world_params: Grid world parameter dictionary
            agents_params: Agent parameter dictionary list
            time_step: Time increment for each update (seconds)
            max_simulation_time: Maximum simulation time (seconds), None means unlimited
        """
        from world import GridWorld
        from agent import QLearningAgent
        
        self.world = GridWorld(**world_params)
        self.agents = [
            QLearningAgent(world=self.world, **params) 
            for params in agents_params
        ]
        self.time_controller = TimeController(time_step)
        self.max_simulation_time = max_simulation_time
        self.max_steps = max(params.get('max_steps', 1000) for params in agents_params)
        
        # Experimental data recording
        self.global_log = []
        self.start_wall_time = time.time()

    def run(self) -> pd.DataFrame:
        """Run simulation until all agents complete or timeout"""
        print(f"Starting simulation with {len(self.agents)} agents...")
        
        while not self._should_stop():
            # 1. Advance time
            current_time = self.time_controller.tick()
            
            # 2. Update world state
            self.world.update(self.time_controller.time_step)
            
            # 3. Update agents in parallel
            for agent in self.agents:
                if not agent.is_training_done:
                    agent.update(self.time_controller.time_step)
            
            # 4. Record status (once per second)
            if int(current_time * 10) % 10 == 0:
                self._log_status(current_time)
        
        # 5. Final processing
        return self._finalize()

    def _should_stop(self) -> bool:
        """Check stop conditions"""
        time_exceeded = (self.max_simulation_time is not None and 
                        self.time_controller.current_time >= self.max_simulation_time)
        all_done = all(agent.is_training_done for agent in self.agents)
        return time_exceeded or all_done

    def _log_status(self, current_time: float):
        """Record system status"""
        if int(current_time) % 5 != 0:
            return
        status = {
            'sim_time': round(current_time, 1),
            'wall_time': round(time.time() - self.start_wall_time, 1),
            'active_agents': sum(not a.is_training_done for a in self.agents),
            'total_points': len(self.world.points),
            'avg_reward': sum(a.total_reward for a in self.agents)/len(self.agents)
        }
        self.global_log.append(status)
        
        # Print every 5 seconds
        if int(current_time) % 5 == 0:
            print(
                f"[T+{status['sim_time']}s] "
                f"Active: {status['active_agents']}/{len(self.agents)} | "
                f"Points: {status['total_points']} | "
                f"Avg Reward: {status['avg_reward']:.1f}"
            )

    def get_visit_statistics(self):
        """Return visit statistics for all agents"""
        spawn_grids = self.world.get_spawn_grids()
        visit_data = []
        
        for grid in spawn_grids:
            row = {'grid_x': grid[0], 'grid_y': grid[1]}
            for agent in self.agents:
                visits = agent.get_visit_counts().get(grid, 0)
                row[f'agent_{agent.agent_id}'] = visits
            visit_data.append(row)
        
        return pd.DataFrame(visit_data)

    def _finalize(self) -> pd.DataFrame:
        """Finalize simulation and return data"""
        # 1. Merge evaluation data
        results = pd.concat([
            pd.DataFrame({
                'agentid': agent.agent_id,
                'step': range(1, len(agent.eval_history)+1),
                'sim_time': [i*self.time_controller.time_step for i in range(len(agent.eval_history))],
                'ExpectedQvalue': [x['ExpectedQvalue'] for x in agent.eval_history],
                'CumulativeReward': [x['CumulativeReward'] for x in agent.eval_history] 
            }) for agent in self.agents
        ])        
        
        # 3. Print summary
        duration = time.time() - self.start_wall_time
        print(f"\n=== Simulation completed in {duration:.1f} seconds ===")
        print(f"Results shape: {results.shape}")
        
        return results

if __name__ == "__main__":
    # Example usage
    sim = Stimulator(
        world_params={'width': 8, 'height': 8, 'spawn_rate': 10},
        agents_params=[
            {'agent_id': 0, 'max_steps': 800},
            {'agent_id': 1, 'max_steps': 800}
        ],
        time_step=0.2,
        max_simulation_time=3600  # 1 hour timeout
    )
    results = sim.run()
    results.to_csv("single_run_results.csv", index=False)