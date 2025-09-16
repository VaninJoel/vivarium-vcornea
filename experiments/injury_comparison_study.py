# injury_comparison_study.py
from vivarium.core.engine import Engine
from vivarium.core.composer import Composer
import pandas as pd

from vivarium_vcornea.processes.vcornea_process import VCorneaProcess
from vivarium_vcornea.utils.simple_config import create_vivarium_experiment_state, get_test_config

try:
    config = get_test_config()
except FileNotFoundError as e:
    print(f"Skipping test: {e}")
    exit()

class VCorneaComposer(Composer):
    defaults = {'vcornea_process': config}
    
    def generate_processes(self, config):
        return {'vcornea': VCorneaProcess(config['vcornea_process'])}

    def generate_topology(self, config):
        return {
            'vcornea': {
                'inputs': ('inputs',),
                'outputs': ('outputs',),
            }
        }

def run_experiment(injury_type, replicates):
    """A helper function to run a single experiment with specified parameters."""
    print(f"--- Running experiment: {injury_type} injury ---")

    sim_params = {
        'SimTime': 5000,
        'IsInjury': True,
        'InjuryTime': 500,
        'InjuryType': injury_type == 'chemical', # True for chemical, False for ablation
        'CellCount': True,
        'CC3D_PLOT': False,
        'replicates': replicates,
    }
    
    composer = VCorneaComposer()
    composite = composer.generate()
    initial_state = create_vivarium_experiment_state(sim_params)
    
    sim = Engine(
        composite=composite,
        initial_state=initial_state
    )
    sim.update(1.0)
    
    output_data = sim.emitter.get_data()
    final_output = output_data[1.0]['outputs']
    
    results = []
    for rep_result in final_output['replicate_results']:
        if rep_result['success']:
            healing_time = rep_result['results']['healing_time']
        else:
            healing_time = None
        
        results.append({
            'injury_type': injury_type,
            'replicate_id': rep_result['replicate_id'],
            'healing_time_mcs': healing_time,
            'simulation_success': rep_result['success']
        })
    return results

if __name__ == '__main__':
    all_results = []
    num_replicates_per_group = 3

    # Run the ablation injury group
    ablation_results = run_experiment('ablation', num_replicates_per_group)
    all_results.extend(ablation_results)

    # Run the chemical injury group
    chemical_results = run_experiment('chemical', num_replicates_per_group)
    all_results.extend(chemical_results)
    
    # Analyze and save combined results
    results_df = pd.DataFrame(all_results)
    output_filename = "injury_comparison_results.csv"
    results_df.to_csv(output_filename, index=False)
    
    print("\n--- Comparative study complete ---")
    print(f"Results saved to {output_filename}")
    
    # Print a statistical summary
    summary = results_df.groupby('injury_type')['healing_time_mcs'].agg(['mean', 'std']).reset_index()
    print("\nSummary of healing times:")
    print(summary)