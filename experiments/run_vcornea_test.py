# run_vcornea_test.py
from vivarium.core.engine import Engine
from vivarium.core.composer import Composer

from vivarium_vcornea.processes.vcornea_process import VCorneaProcess
from vivarium_vcornea.utils.simple_config import create_vivarium_experiment_state, get_test_config

# Load a test configuration with hardcoded paths removed
try:
    config = get_test_config()
except FileNotFoundError as e:
    print(f"Skipping test: {e}")
    exit()

class VCorneaComposer(Composer):
    defaults = {
        'vcornea_process': config
    }
    
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
    # Define minimal simulation parameters for a fast run
    sim_params = {
        'SimTime': 100,
        'IsInjury': True,
        'InjuryTime': 50,
        'CellCount': True,
        'CC3D_PLOT': False,
        'replicates': 1,
    }

    # Create the Vivarium composite and initial state
    composer = VCorneaComposer()
    composite = composer.generate()
    initial_state = create_vivarium_experiment_state(sim_params)
    
    # Create and run the engine
    sim = Engine(
        composite=composite,
        initial_state=initial_state
    )
    
    print("--- LAUNCHING VIVARIUM VCORNEA TEST ---")
    sim.update(1.0)
    print("--- TEST COMPLETE ---")

    # Print a summary of the results
    output_data = sim.emitter.get_data()
    print("\n--- SIMULATION RESULTS SUMMARY ---")
    
    final_output = output_data[1.0]['outputs']
    print(f"Simulation Success: {final_output['simulation_success']}")
    print(f"Output Directory: {final_output['output_directory']}")
    
    if 'replicate_results' in final_output:
        replicate_results = final_output['replicate_results'][0]
        if replicate_results['success']:
            print("Replicate 1 Status: SUCCESS")
            print(f"  Healing Time (Approx): {replicate_results['results']['healing_time']:.2f} MCS")
        else:
            print("Replicate 1 Status: FAILED")
            print(f"  Error: {replicate_results['error_message']}")