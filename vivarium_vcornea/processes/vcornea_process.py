import subprocess
import os
import pandas as pd
import tempfile
import shutil
import json
from vivarium.core.process import Process

class VCorneaProcess(Process):

    # --- VIVARIUM PROCESS CONFIGURATION ---

    # The 'defaults' dictionary holds parameters for the wrapper itself.
    # These tell the wrapper WHERE to find the CC3D simulation and HOW to run it.
    defaults = {
        'cc3d_project_path': '[path/to/your/vCornea]/clean_paper_version',
        'batch_run_script': 'Batch_Run_vCornea_Paper_version.py',
        'python_executable': 'python',  # Assumes 'python' is in the system PATH
    }

    def __init__(self, parameters=None):
        # The __init__ method is called once when the process is created.
        # We use it to set up file paths and any other initial configuration.
        super().__init__(parameters)

        # Create a full, absolute path to the batch run script.
        # This is more robust than using relative paths.
        self.batch_script_path = os.path.join(
            self.parameters['cc3d_project_path'],
            self.parameters['batch_run_script']
        )

        # Check if the script actually exists to prevent errors later.
        if not os.path.exists(self.batch_script_path):
            raise FileNotFoundError(
                f"The vCornea batch run script was not found at: {self.batch_script_path}"
            )

    # --- VIVARIUM INTERFACE DEFINITION ---
    def ports_schema(self):
        """
        This method defines the inputs and outputs for our vCornea wrapper.
        """
        return {
            # Port 1: 'inputs' will connect to a store holding our experimental parameters           
            'inputs': {
                # --- STEM Cell Parameters ---
                'InitSTEM_LambdaSurface': {
                    '_default': 2.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'InitSTEM_TargetSurface': {
                    '_default': 18.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'InitSTEM_LambdaVolume': {
                    '_default': 2.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'InitSTEM_TargetVolume': {
                    '_default': 25.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'DensitySTEM_HalfMaxValue': {
                    '_default': 125,
                    '_updater': 'set',
                    '_emit': True,
                },
                'EGF_STEM_HalfMaxValue': {
                    '_default': 3.5,  # Using Vanin et al., 2025 default
                    '_updater': 'set',
                    '_emit': True,
                },
                'STEM_beta_EGF': {
                    '_default': 1,
                    '_updater': 'set',
                    '_emit': True,
                },
                'InitSTEM_LambdaChemo': {
                    '_default': 100.0,
                    '_updater': 'set',
                    '_emit': True,
                },

                # --- BASAL Cell Parameters ---
                'InitBASAL_LambdaSurface': {
                    '_default': 2.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'InitBASAL_TargetSurface': {
                    '_default': 20.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'InitBASAL_LambdaVolume': {
                    '_default': 2.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'InitBASAL_TargetVolume': {
                    '_default': 25.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'InitBASAL_LambdaChemo': {
                    '_default': 1000.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'InitBASAL_Division': {
                    '_default': 20000.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'DensityBASAL_HalfMaxValue': {
                    '_default': 125,
                    '_updater': 'set',
                    '_emit': True,
                },
                'EGF_BASAL_HalfMaxValue': {
                    '_default': 7.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'BASAL_beta_EGF': {
                    '_default': 1,
                    '_updater': 'set',
                    '_emit': True,
                },

                # --- WING Cell Parameters ---
                'InitWING_LambdaSurface': {
                    '_default': 5.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'InitWING_TargetSurface': {
                    '_default': 25,
                    '_updater': 'set',
                    '_emit': True,
                },
                'InitWING_LambdaVolume': {
                    '_default': 2.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'InitWING_TargetVolume': {
                    '_default': 25.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'InitWING_EGFLambdaChemo': {
                    '_default': 20.0,
                    '_updater': 'set',
                    '_emit': True,
                },

                # --- SUPERFICIAL Cell Parameters ---
                'InitSUPER_LambdaSurface': {
                    '_default': 5.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'InitSUPER_TargetSurface': {
                    '_default': 25.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'InitSUPER_LambdaVolume': {
                    '_default': 5.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'InitSUPER_TargetVolume': {
                    '_default': 25.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'EGF_SUPERDiffCoef': {
                    '_default': 20.0,
                    '_updater': 'set',
                    '_emit': True,
                },

                # --- Movement Bias Field Parameters ---
                'MovementBiasScreteAmount': {
                    '_default': 5.0,  # Using Vanin et al., 2025 default
                    '_updater': 'set',
                    '_emit': True,
                },
                'MovementBiasUptake': {
                    '_default': 1.0,
                    '_updater': 'set',
                    '_emit': True,
                },

                # --- EGF Field Parameters ---
                'EGF_ScreteAmount': {
                    '_default': 1.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'EGF_FieldUptakeBASAL': {
                    '_default': 0.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'EGF_FieldUptakeSTEM': {
                    '_default': 0.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'EGF_FieldUptakeSuper': {
                    '_default': 0.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'EGF_FieldUptakeWing': {
                    '_default': 0.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'EGF_GlobalDecay': {
                    '_default': 0.5,
                    '_updater': 'set',
                    '_emit': True,
                },

                # --- Link Parameters (SUPER-WALL) ---
                'LINKWALL_lambda_distance': {
                    '_default': 50,
                    '_updater': 'set',
                    '_emit': True,
                },
                'LINKWALL_target_distance': {
                    '_default': 3,
                    '_updater': 'set',
                    '_emit': True,
                },
                'LINKWALL_max_distance': {
                    '_default': 1000,
                    '_updater': 'set',
                    '_emit': True,
                },

                # --- Link Parameters (SUPER-SUPER) ---
                'LINKSUPER_lambda_distance': {
                    '_default': 50,
                    '_updater': 'set',
                    '_emit': True,
                },
                'LINKSUPER_target_distance': {
                    '_default': 3,
                    '_updater': 'set',
                    '_emit': True,
                },
                'LINKSUPER_max_distance': {
                    '_default': 1000,
                    '_updater': 'set',
                    '_emit': True,
                },
                'AutoAdjustLinks': {
                    '_default': True,
                    '_updater': 'set',
                    '_emit': True,
                },
                'Lambda_link_adjustment': {
                    '_default': 1.0,  # You may need to add this to your parameter files
                    '_updater': 'set',
                    '_emit': True,
                },
                'Tension_link_SS': {
                    '_default': 1.0,  # You may need to add this to your parameter files
                    '_updater': 'set',
                    '_emit': True,
                },

                # --- Injury Parameters ---
                'IsInjury': {
                    '_default': True,
                    '_updater': 'set',
                    '_emit': True,
                },
                'InjuryType': {
                    '_default': False,  # False = ablation, True = chemical
                    '_updater': 'set',
                    '_emit': True,
                },
                'InjuryTime': {
                    '_default': 1,  # Using Vanin et al., 2025 default
                    '_updater': 'set',
                    '_emit': True,
                },

                # --- Ablation Injury Parameters ---
                'InjuryX_Center': {
                    '_default': 150,  # Using Vanin et al., 2025 default
                    '_updater': 'set',
                    '_emit': True,
                },
                'InjuryY_Center': {
                    '_default': 60,  # Using Vanin et al., 2025 default
                    '_updater': 'set',
                    '_emit': True,
                },
                'InjuryRadius': {
                    '_default': 25,  # Using Vanin et al., 2025 default
                    '_updater': 'set',
                    '_emit': True,
                },

                # --- Chemical Injury Parameters ---
                'SLS_Injury': {
                    '_default': True,
                    '_updater': 'set',
                    '_emit': True,
                },
                'SLS_X_Center': {
                    '_default': 100,
                    '_updater': 'set',
                    '_emit': True,
                },
                'SLS_Y_Center': {
                    '_default': 75,
                    '_updater': 'set',
                    '_emit': True,
                },
                'SLS_Concentration': {
                    '_default': 1500,  # Using Vanin et al., 2025 default
                    '_updater': 'set',
                    '_emit': True,
                },
                'SLS_Gaussian_pulse': {
                    '_default': False,  # Using Vanin et al., 2025 default (False = coating, True = droplet)
                    '_updater': 'set',
                    '_emit': True,
                },
                'SLS_STEMDiffCoef': {
                    '_default': 5.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'SLS_BASALDiffCoef': {
                    '_default': 5.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'SLS_WINGDiffCoef': {
                    '_default': 5.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'SLS_SUPERDiffCoef': {
                    '_default': 5.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'SLS_MEMBDiffCoef': {
                    '_default': 5.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'SLS_LIMBDiffCoef': {
                    '_default': 5.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'SLS_TEARDiffCoef': {
                    '_default': 5.0,
                    '_updater': 'set',
                    '_emit': True,
                },
                'SLS_Threshold_Method': {
                    '_default': True,
                    '_updater': 'set',
                    '_emit': True,
                },
                'SLS_Threshold': {
                    '_default': 2.0,
                    '_updater': 'set',
                    '_emit': True,
                },

                # --- Function Control Parameters ---
                'GrowthControl': {
                    '_default': True,
                    '_updater': 'set',
                    '_emit': True,
                },
                'MitosisControl': {
                    '_default': True,
                    '_updater': 'set',
                    '_emit': True,
                },
                'DeathControl': {
                    '_default': True,
                    '_updater': 'set',
                    '_emit': True,
                },
                'DifferentiationControl': {
                    '_default': True,
                    '_updater': 'set',
                    '_emit': True,
                },

                # --- Plot and Data Collection Parameters ---
                'CC3D_PLOT': {
                    '_default': True,  # Using Vanin et al., 2025 default
                    '_updater': 'set',
                    '_emit': True,
                },
                'CellCount': {
                    '_default': True,
                    '_updater': 'set',
                    '_emit': True,
                },
                'PressureTracker': {
                    '_default': True,  # Using Vanin et al., 2025 default
                    '_updater': 'set',
                    '_emit': True,
                },
                'EGF_SeenByCell': {
                    '_default': True,  # Using Vanin et al., 2025 default
                    '_updater': 'set',
                    '_emit': True,
                },
                'SLS_SeenByCell': {
                    '_default': True,  # Using Vanin et al., 2025 default
                    '_updater': 'set',
                    '_emit': True,
                },
                'CenterBias': {
                    '_default': False,
                    '_updater': 'set',
                    '_emit': True,
                },
                'ThicknessPlot': {
                    '_default': True,  # Using Vanin et al., 2025 default
                    '_updater': 'set',
                    '_emit': True,
                },
                'SurfactantTracking': {
                    '_default': True,  # Using Vanin et al., 2025 default
                    '_updater': 'set',
                    '_emit': True,
                },
                'SnapShot': {
                    '_default': False,
                    '_updater': 'set',
                    '_emit': True,
                },
                'SnapShot_time': {
                    '_default': 10,  # Using Vanin et al., 2025 default
                    '_updater': 'set',
                    '_emit': True,
                },

                # --- Simulation Time ---
                'SimTime': {
                    '_default': 7500,  # 
                    '_updater': 'set',
                    '_emit': True,
                },
            },

            # Port 2: 'outputs' will connect to a store that will receive the simulation results
            'outputs': {
                'cell_counts': {
                    '_default': {},   # The result will be a dictionary or DataFrame
                    '_updater': 'set', # The process will 'set' this value upon completion
                    '_emit': True,
                },
                'tissue_thickness': {
                    '_default': {},
                    '_updater': 'set',
                    '_emit': True,
                }                
            }
        }
    
    # --- VIVARIUM CORE LOGIC ---
    def next_update(self, timestep, states):
        # Get all simulation parameters from the input store
        sim_params = states['inputs']

        # Create a temporary directory for this specific simulation run
        temp_dir = tempfile.mkdtemp()
        
        try:
            # --- 1. Generate the Parameters.py file ---
            params_path = os.path.join(temp_dir, 'Parameters.py')
            with open(params_path, 'w') as f:
                for param_name, param_value in sim_params.items():
                    # repr() correctly formats strings, numbers, and booleans for Python code
                    f.write(f"{param_name} = {repr(param_value)}\n")

            # --- 2. Execute the CC3D simulation as a subprocess ---
            print(f"VCorneaProcess: Launching CC3D simulation in {temp_dir}...")
            
            # This command assumes your batch script is modified to accept these arguments
            command = [
                self.parameters['python_executable'],
                self.batch_script_path,
                '--parameters', params_path,
                '--output', temp_dir
            ]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False # We will check the return code manually
            )

            if result.returncode!= 0:
                print("--- VCornea Simulation FAILED ---")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return {'outputs': {}} # Return empty update on failure

            print("VCorneaProcess: Simulation completed successfully.")

            # --- 3. Parse the output files ---
            # Note: You may need to adjust these filenames to match what your script outputs
            cell_counts_path = os.path.join(temp_dir, 'cell_count.csv')
            thickness_path = os.path.join(temp_dir, 'thickness.parquet')

            cell_counts_df = pd.read_csv(cell_counts_path)
            thickness_df = pd.read_parquet(thickness_path)
            
            # --- 4. Calculate summary statistics (example) ---
            # This is placeholder logic. You would replace this with your actual
            # method for calculating healing time from the data.
            healing_time = 0.0
            if sim_params.get('IsInjury', False):
                # Example: find the first timepoint where basal cell count returns to 95% of initial
                initial_basal_count = cell_counts_df.iloc
                healed_df = cell_counts_df >= 0.95 * initial_basal_count
                if not healed_df.empty:
                    healing_time = healed_df.iloc - sim_params

            # --- 5. Format results and return the update dictionary ---
            return {
                'outputs': {
                    'cell_counts': cell_counts_df.to_dict('list'),
                    'tissue_thickness': thickness_df.to_dict('list'),
                    'healing_time': healing_time
                }
            }

        finally:
            # --- 6. Clean up the temporary directory ---
            # This 'finally' block ensures the temp directory is always removed,
            # even if the simulation or parsing fails.
            shutil.rmtree(temp_dir)