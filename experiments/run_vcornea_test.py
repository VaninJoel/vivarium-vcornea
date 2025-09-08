from vivarium.core.engine import Engine
from vivarium.core.composer import Composer

# 1. Import your newly created VCorneaProcess
#    (Adjust the path if you placed it somewhere other than processes/)
from vivarium_template.processes.vcornea_process import VCorneaProcess

# 2. Create a Composer class to build the simulation
#    A Composer is a Vivarium best practice for assembling models.
class VCorneaComposer(Composer):

    # Set the default configuration for the composer
    defaults = {
        'vcornea_process': {
            'cc3d_project_path': 'C:/path/to/your/GUI_vlab/clean_paper_version',
            
            # --- THIS IS THE CRUCIAL ADDITION ---
            # Provide the full, absolute path to the Python executable
            # in the Conda environment that has CompuCell3D installed.
            'cc3d_python_executable': 'C:/Users/YourUser/miniconda3/envs/v_cornea/python.exe' # <-- CHANGE THIS PATH
        },
    }

    def generate_processes(self, config):
        """
        This method creates an instance of your VCorneaProcess.
        """
        # Get the process-specific configuration
        process_config = config['vcornea_process']
        
        # Create the process instance
        vcornea_process = VCorneaProcess(process_config)
        
        # Return a dictionary of all processes to include in the simulation
        return {
            'vcornea': vcornea_process
        }

    def generate_topology(self, config):
        """
        This method defines the "wiring diagram" for the simulation.
        It connects the ports on your process to the main data stores.
        """
        return {
            'vcornea': {
                'inputs': ('globals', 'inputs'),    # Connect 'inputs' port to a global store
                'outputs': ('globals', 'outputs'),  # Connect 'outputs' port to a global store
            }
        }

# 3. The main block to run the experiment
if __name__ == '__main__':
    # Create an instance of our composer
    composer = VCorneaComposer()

    # Generate the complete composite model (processes + topology)
    vcornea_composite = composer.generate()

    # Define the initial state for the simulation.
    # This is where we set the input parameters for our test run.
    initial_state = {
        'globals': {
            'inputs': {
                'SLS_Concentration': 1500.0,  # Let's test a mild injury
                'InjuryTime': 5000,
            }
        }
    }

    # 4. Create the Vivarium Engine
    sim = Engine(
        composite=vcornea_composite,
        initial_state=initial_state
    )

    # 5. Run the simulation for one "update"
    #    Since your process runs a full CC3D simulation in one go,
    #    we only need to run for a single timestep.
    print("--- LAUNCHING VIVARIUM EXPERIMENT ---")
    sim.update(1.0) # The timestep value (1.0) is a placeholder
    print("--- VIVARIUM EXPERIMENT COMPLETE ---")


    # 6. Retrieve and print the final results
    output_data = sim.emitter.get_data()
    print("\n--- SIMULATION RESULTS ---")
    import json
    print(json.dumps(output_data, indent=4))
