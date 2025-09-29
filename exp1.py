import pandas as pd
from pathlib import Path
from stimulator import Stimulator
from agent import InterventionType
import numpy as np

def calculate_random_grid_size(world_size):
    """Calculate random_grid count for mode 2, 20% of total grids rounded"""
    total_grids = world_size * world_size
    return round(total_grids * 0.2)

def run_experiment():
    script_dir = Path(__file__).parent
    output_dir = script_dir / "exp1_results"  # Changed to exp1_results
    output_dir.mkdir(exist_ok=True)
    
    # Experiment parameter configuration
    world_sizes = [8, 10, 12]
    intervention_types = list(InterventionType)
    intervention_rates = [0.25, 0.5, 0.75, 1.0]
    intervention_modes = [1,2,3,4]  # Agent intervention modes
    num_runs = 50  # 100 runs
    
    # World mode configuration
    world_modes = [
        {
            'mode': 2, 
            'random_grid': lambda size: calculate_random_grid_size(size)  # Dynamically calculate random_grid
        },
        {
            'mode': 3, 
            'random_grid': 18,  # Mode 3 keeps fixed at 18
            'mode3_centers': lambda size: [[2.5, 2.5], [size-2.5, size-2.5]]
        }
    ]
    
    # Iterate through all experiment conditions
    for size in world_sizes:
        for w_mode in world_modes:
            # Create world_mode subdirectory
            world_dir = output_dir / f"world{w_mode['mode']}_size_{size}"
            world_dir.mkdir(exist_ok=True)
            
            # Configure world parameters
            world_params = {
                'width': size,
                'height': size,
                'mode': w_mode['mode'],
                'random_seed': size,
                'spawn_rate': 10
            }
            
            # Set random_grid parameter
            if callable(w_mode['random_grid']):
                world_params['random_grid'] = w_mode['random_grid'](size)
            else:
                world_params['random_grid'] = w_mode['random_grid']
            
            # Special handling for mode 3
            if w_mode['mode'] == 3:
                world_params['mode3_centers'] = w_mode['mode3_centers'](size)
            
            for int_type in intervention_types:
                for rate in intervention_rates:
                    for int_mode in intervention_modes:
                        # Create type_rate_mode subdirectory
                        condition_dir = world_dir / f"type_{int_type}_rate_{rate}_mode_{int_mode}"
                        condition_dir.mkdir(exist_ok=True)
                        
                        # Run 100 experiments
                        for run in range(num_runs):
                            # Configure two agent parameters (identical)
                            agents_params = [
                                {
                                    'agent_id': 0,
                                    'intervention_type': int_type.value,
                                    'intervention_rate': rate,
                                    'intervention_mode': int_mode,
                                    'max_steps': 1000,
                                    'intervention_stop_step': 500 if run >= 50 else None  # Stop intervention after 500 steps for last 50 runs
                                },
                                {
                                    'agent_id': 1,
                                    'intervention_type': int_type.value,
                                    'intervention_rate': rate,
                                    'intervention_mode': int_mode,
                                    'max_steps': 1000,
                                    'intervention_stop_step': 500 if run >= 50 else None  # Consistent with first agent
                                }
                            ]
                            
                            # Initialize simulator
                            sim = Stimulator(
                                world_params=world_params,
                                agents_params=agents_params
                            )
                            
                            # Run simulation and save results
                            results = sim.run()
                            results = results.drop(columns=['sim_time'])
                            visit_stats = sim.get_visit_statistics()
                            
                            # Save results
                            run_file = condition_dir / f"run_{run}.csv"
                            results.to_csv(run_file, index=False)
                            visit_file = condition_dir / f"visit_stats_{run}.csv"
                            visit_stats.to_csv(visit_file, index=False)
                            print(f"Saved {run_file} and {visit_file}")

if __name__ == "__main__":
    run_experiment()
    print("Experiment completed! Results saved to exp1_results/")