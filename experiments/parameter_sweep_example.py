# parameter_sweep_example.py
from vivarium.core.engine import Engine
from vivarium.core.composer import Composer
import pandas as pd

from vivarium_vcornea.processes.vcornea_process import VCorneaProcess
from vivarium_vcornea.utils.simple_config import create_vivarium_experiment_state, get_test_config

# Load configuration from a file or fallback to test config
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

if __name__ == '__main__':
    # Parameters to sweep
    sls_concentrations = [500.0, 1500.0, 2500.0]
    num_replicates = 2

    # Prepare to store results
    all_results = []
    
    for conc in sls_concentrations:
        print(f"--- Running sweep for SLS_Concentration: {conc} ---")
        
        # Define simulation parameters for this specific run
        sim_params = {
            'SimTime': 500,
            'IsInjury': True,
            'InjuryTime': 50,
            'InjuryType': True, # Chemical injury
            'SLS_Concentration': conc,
            'CellCount': True,
            'CC3D_PLOT': False,
            'replicates': num_replicates,
        }

        # Create Vivarium engine and run
        composer = VCorneaComposer()
        composite = composer.generate()
        initial_state = create_vivarium_experiment_state(sim_params)
        
        sim = Engine(
            composite=composite,
            initial_state=initial_state
        )
        sim.update(1.0)
        
        # Collect and process results
        output_data = sim.emitter.get_data()
        final_output = output_data[1.0]['outputs']
        
        for rep_result in final_output['replicate_results']:
            if rep_result['success']:
                healing_time = rep_result['results']['healing_time']
            else:
                healing_time = None
            
            all_results.append({
                'SLS_Concentration': conc,
                'replicate_id': rep_result['replicate_id'],
                'healing_time_mcs': healing_time,
                'simulation_success': rep_result['success']
            })

    # Save all results to a CSV file
    results_df = pd.DataFrame(all_results)
    output_filename = "sls_concentration_sweep_results.csv"
    results_df.to_csv(output_filename, index=False)
    
    print(f"\n--- Parameter sweep complete ---")
    print(f"Results saved to {output_filename}")
    print("\nSummary of results:")
    print(results_df)