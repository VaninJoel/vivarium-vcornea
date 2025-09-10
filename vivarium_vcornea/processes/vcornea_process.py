import subprocess
import os
import pandas as pd
import tempfile
import shutil
import json
import glob
import uuid
from pathlib import Path
from vivarium.core.process import Process

class VCorneaProcess(Process):
    """
    Enhanced Vivarium wrapper for the vCornea CompuCell3D model.
    
    Features:
    - Tracks parameter changes from defaults
    - Generates meaningful run names
    - Saves comprehensive metadata
    - Maintains experiment logs
    - Redirects outputs to external directories
    """

    defaults = {
        'cc3d_project_path': None, # '[path to your vCornea clone parent folder]/vCornea/HPC/Project/paper_version'
        'conda_env_name': 'vc',  # Name of conda environment with CC3D 'v_cornea'
        'python_executable': 'python',  # Usually just 'python' when using conda
        'output_base_dir': None,  # If None, creates temp outputs; otherwise uses this directory
        'keep_outputs': False,  # If True, preserves outputs after simulation
        'run_name': None,  # Custom name for this run; if None, generates descriptive name
        'max_params_in_name': 3,  # Max number of changed parameters to include in auto-generated names
        'replicates': 1,  # Number of times to run the simulation with the same parameters
    }

    def __init__(self, parameters=None):
        super().__init__(parameters)

        # Validate that the project path exists and has the required files
        project_path = Path(self.parameters['cc3d_project_path'])
        if not project_path:
            # Check environment variable
            if 'VCORNEA_PROJECT_PATH' in os.environ:
                project_path = os.environ['VCORNEA_PROJECT_PATH']
                self.parameters['cc3d_project_path'] = project_path
                print(f"Using vCornea project from environment: {project_path}")
            else:
                raise ValueError(
                    "No vCornea project path provided. Either:\n"
                    "1. Set VCORNEA_PROJECT_PATH environment variable, or\n"
                    "2. Pass 'cc3d_project_path' parameter\n"
                    "Example: export VCORNEA_PROJECT_PATH=/path/to/vCornea/Local/Project/paper_version"
                )
        
        # Validate that the project path exists and has required files
        self.project_path = Path(project_path)
        
        if not self.project_path.exists():
            raise FileNotFoundError(f"vCornea project path not found: {self.project_path}")
        
        
        # Check for required files
        required_files = [
            'vCornea_v2.cc3d',
            'Simulation/vCornea_v2.py',
            'Simulation/vCornea_v2Steppables.py', 
            'Simulation/vCornea_v2.xml',
            'Epithelium.piff'
        ]
        
        for req_file in required_files:
            file_path = self.project_path / req_file
            if not file_path.exists():
                raise FileNotFoundError(f"Required vCornea file not found: {file_path}")

    def ports_schema(self):
        """Define inputs and outputs for the vCornea wrapper."""
        return {
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
                    '_default': 3.5,
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
                    '_default': 1,  # Corrected from 5.0 to match vCornea default
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
                    '_default': 500,  # Corrected to match vCornea default
                    '_updater': 'set',
                    '_emit': True,
                },

                # --- Ablation Injury Parameters ---
                'InjuryX_Center': {
                    '_default': 100,
                    '_updater': 'set',
                    '_emit': True,
                },
                'InjuryY_Center': {
                    '_default': 75,
                    '_updater': 'set',
                    '_emit': True,
                },
                'InjuryRadius': {
                    '_default': 45,
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
                    '_default': 65,
                    '_updater': 'set',
                    '_emit': True,
                },
                'SLS_Concentration': {
                    '_default': 750.0,  # Corrected to match vCornea default
                    '_updater': 'set',
                    '_emit': True,
                },
                'SLS_Gaussian_pulse': {
                    '_default': True,  # Corrected to match vCornea default
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
                    '_default': False,  # Disable for headless runs
                    '_updater': 'set',
                    '_emit': True,
                },
                'CellCount': {
                    '_default': True,
                    '_updater': 'set',
                    '_emit': True,
                },
                'PressureTracker': {
                    '_default': True,
                    '_updater': 'set',
                    '_emit': True,
                },
                'EGF_SeenByCell': {
                    '_default': True,
                    '_updater': 'set',
                    '_emit': True,
                },
                'SLS_SeenByCell': {
                    '_default': True,
                    '_updater': 'set',
                    '_emit': True,
                },
                'CenterBias': {
                    '_default': False,
                    '_updater': 'set',
                    '_emit': True,
                },
                'ThicknessPlot': {
                    '_default': True,
                    '_updater': 'set',
                    '_emit': True,
                },
                'SurfactantTracking': {
                    '_default': True,
                    '_updater': 'set',
                    '_emit': True,
                },
                'SnapShot': {
                    '_default': False,
                    '_updater': 'set',
                    '_emit': True,
                },
                'SnapShot_time': {
                    '_default': 10,
                    '_updater': 'set',
                    '_emit': True,
                },

                # --- Simulation Time ---
                'SimTime': {
                    '_default': 7700,  # Corrected to match vCornea default
                    '_updater': 'set',
                    '_emit': True,
                },
            },

            'outputs': {
                # 'cell_counts': {
                #     '_default': {},
                #     '_updater': 'set',
                #     '_emit': True,
                # },
                # 'tissue_thickness': {
                #     '_default': {},
                #     '_updater': 'set',
                #     '_emit': True,
                # },
                # 'healing_time': {
                #     '_default': 0.0,
                #     '_updater': 'set',
                #     '_emit': True,
                # },
                'replicate_results': {
                    '_default': [],
                    '_updater': 'set',
                    '_emit': True,
                },
                'simulation_success': {
                    '_default': False,
                    '_updater': 'set',
                    '_emit': True,
                },
                'output_directory': {
                    '_default': '',
                    '_updater': 'set',
                    '_emit': True,
                },
                'parameter_changes': {
                    '_default': {},
                    '_updater': 'set',
                    '_emit': True,
                },
                'run_metadata': {
                    '_default': {},
                    '_updater': 'set',
                    '_emit': True,
                }
            }
        }

    def next_update(self, timestep, states):
        """Executes a batch of vCornea simulations in parallel and returns results."""
        sim_params = states['inputs']
        num_replicates = self.parameters.get('replicates', 1)
        print(f"VCorneaProcess: Starting batch of {num_replicates} parallel replicate(s).")

        parameter_changes = self._identify_parameter_changes(sim_params)
        run_name = self._generate_run_name(parameter_changes)

        if self.parameters.get('output_base_dir'):
            output_base = Path(self.parameters['output_base_dir'])
        else:
            output_base = Path.cwd() / "vivarium_vcornea_outputs"
        
        batch_output_dir = output_base / run_name
        batch_output_dir.mkdir(parents=True, exist_ok=True)
        
        running_processes = []
        replicate_outputs = []

        # ======================================================
        # PHASE 1: SETUP AND LAUNCH ALL REPLICATES
        # ======================================================
        print("\n--- Phase 1: Launching all replicate processes ---")
        for i in range(num_replicates):
            replicate_id = i + 1
            run_output_dir = batch_output_dir / f"replicate_{replicate_id}"
            run_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Prepare metadata and files for this replicate
            run_metadata = self._create_run_metadata(sim_params, parameter_changes, run_name)
            run_metadata['replicate_id'] = replicate_id
            run_metadata['total_replicates'] = num_replicates
            
            temp_dir = tempfile.mkdtemp()
            
            try:
                # Setup the simulation environment in a temporary directory
                temp_project = Path(temp_dir) / "vcornea_sim"
                shutil.copytree(self.project_path, temp_project)
                self._redirect_outputs_in_copy(temp_project, run_output_dir)
                sim_params_file = temp_project / "Simulation" / "Parameters.py"
                self._write_parameters_file(sim_params_file, sim_params)

                # Launch the simulation and get the process handle
                process, stdout_log, stderr_log = self._run_cc3d_simulation(temp_project, run_output_dir)
                
                if process:
                    # Store the handle and related info to wait on it later
                    running_processes.append({
                        'process': process,
                        'replicate_id': replicate_id,
                        'output_dir': run_output_dir,
                        'temp_dir': temp_dir,
                        'metadata': run_metadata,
                        'stdout_log': stdout_log,
                        'stderr_log': stderr_log,
                    })
                    print(f"  > Replicate {replicate_id} launched (PID: {process.pid}).")
                else:
                    raise RuntimeError("Process launch failed.")

            except Exception as e:
                print(f"  > FAILED to launch replicate {replicate_id}: {e}")
                shutil.rmtree(temp_dir, ignore_errors=True)
                run_metadata['simulation_success'] = False
                run_metadata['error_message'] = f"Failed during setup/launch phase: {e}"
                # Immediately add a failure report for this replicate
                replicate_outputs.append({
                    'replicate_id': replicate_id, 'success': False,
                    'output_directory': str(run_output_dir),
                    'error_message': run_metadata['error_message'], 'results': None
                })
        
        # ======================================================
        # PHASE 2: WAIT FOR PROCESSES AND COLLECT RESULTS
        # ======================================================
        print("\n--- Phase 2: Waiting for processes to complete and collecting results ---")
        for job in running_processes:
            process = job['process']
            replicate_id = job['replicate_id']
            run_output_dir = job['output_dir']
            run_metadata = job['metadata']

            # Wait for this specific process to finish. This is a blocking call.
            process.wait(timeout=7200) # Optional: add a timeout
            
            # Close the log files
            job['stdout_log'].close()
            job['stderr_log'].close()

            print(f"  > Replicate {replicate_id} (PID: {process.pid}) finished with exit code {process.returncode}.")
            
            # Check if the simulation succeeded
            if process.returncode == 0:
                results = self._parse_simulation_results(run_output_dir, sim_params)
                run_metadata.update({'simulation_success': True, 'simulation_completed_at': pd.Timestamp.now().isoformat(), 'healing_time': results.get('healing_time')})
                replicate_outputs.append({'replicate_id': replicate_id, 'success': True, 'output_directory': str(run_output_dir), 'error_message': None, 'results': results})
            else:
                error_message = f"Simulation process failed with exit code {process.returncode}. Check stderr.log in the output directory."
                run_metadata.update({'simulation_success': False, 'error_message': error_message})
                replicate_outputs.append({'replicate_id': replicate_id, 'success': False, 'output_directory': str(run_output_dir), 'error_message': error_message, 'results': None})

            # Clean up and log
            shutil.rmtree(job['temp_dir'], ignore_errors=True)
            with open(run_output_dir / "run_metadata.json", 'w') as f:
                json.dump(run_metadata, f, indent=2)
            self._update_experiment_log(output_base, run_metadata)
            if not self.parameters.get('keep_outputs', False):
                shutil.rmtree(run_output_dir, ignore_errors=True)
        
        # ======================================================
        # PHASE 3: FINALIZE AND RETURN
        # ======================================================
        print(f"\n--- Batch finished ---")
        overall_success = all(rep['success'] for rep in replicate_outputs if 'success' in rep)

        if not self.parameters.get('keep_outputs', False):
             try:
                 if not any(batch_output_dir.iterdir()):
                     batch_output_dir.rmdir()
             except OSError as e:
                 print(f"Could not remove empty batch directory {batch_output_dir}: {e}")

        return {
            'outputs': {
                'replicate_results': sorted(replicate_outputs, key=lambda r: r['replicate_id']), # Sort for consistency
                'simulation_success': overall_success,
                'output_directory': str(batch_output_dir),
                'parameter_changes': parameter_changes,
                'run_metadata': self._create_run_metadata(sim_params, parameter_changes, run_name)
            }
        }
    
    # def next_update(self, timestep, states):
    #     """Execute a complete vCornea simulation and return results."""

    #     sim_params = states['inputs']
        
    #     num_replicates = self.parameters.get('replicates', 1)
    #     print(f"VCorneaProcess: Starting simulation for {num_replicates} replicate(s).")

    #     parameter_changes = self._identify_parameter_changes(sim_params)
    #     run_name = self._generate_run_name(parameter_changes)

    #     if self.parameters.get('output_base_dir'):
    #         output_base = Path(self.parameters['output_base_dir'])
    #     else:
    #         output_base = Path.cwd() / "vivarium_vcornea_outputs"
        
    #     batch_output_dir = output_base / run_name
    #     batch_output_dir.mkdir(parents=True, exist_ok=True)
        
    #     # ---- Initialize a list to hold detailed results for each replicate ----
    #     replicate_outputs = []
        
    #     for i in range(num_replicates):
    #         replicate_id = i + 1
    #         print(f"\n--- Running Replicate {replicate_id}/{num_replicates} ---")

    #         run_output_dir = batch_output_dir / f"replicate_{replicate_id}"
    #         run_output_dir.mkdir(parents=True, exist_ok=True)

    #         run_metadata = self._create_run_metadata(sim_params, parameter_changes, run_name)
    #         run_metadata['replicate_id'] = replicate_id
    #         run_metadata['total_replicates'] = num_replicates

    #         metadata_file = run_output_dir / "run_metadata.json"
    #         with open(metadata_file, 'w') as f:
    #             json.dump(run_metadata, f, indent=2)

    #         temp_dir = tempfile.mkdtemp()
            
    #         try:
    #             temp_project = Path(temp_dir) / "vcornea_sim"
    #             shutil.copytree(self.project_path, temp_project)
                
    #             self._redirect_outputs_in_copy(temp_project, run_output_dir)
    #             sim_params_file = temp_project / "Simulation" / "Parameters.py"
    #             self._write_parameters_file(sim_params_file, sim_params)
                
    #             success = self._run_cc3d_simulation(temp_project)
                
    #             if not success:
    #                 # ---- Handle simulation failure ----
    #                 print(f"VCorneaProcess: Replicate {replicate_id} failed.")
    #                 run_metadata['simulation_success'] = False
    #                 error_message = "Simulation process failed with a non-zero exit code."
    #                 run_metadata['error_message'] = error_message
                    
    #                 # Append a failure report to our results list
    #                 replicate_outputs.append({
    #                     'replicate_id': replicate_id,
    #                     'success': False,
    #                     'output_directory': str(run_output_dir),
    #                     'error_message': error_message,
    #                     'results': None
    #                 })

    #             else:
    #                 # ---- Handle simulation success ----
    #                 results = self._parse_simulation_results(run_output_dir, sim_params)
    #                 run_metadata['simulation_success'] = True
    #                 run_metadata['simulation_completed_at'] = pd.Timestamp.now().isoformat()
    #                 run_metadata['healing_time'] = results.get('healing_time')
                    
    #                 # Append a success report to our results list
    #                 replicate_outputs.append({
    #                     'replicate_id': replicate_id,
    #                     'success': True,
    #                     'output_directory': str(run_output_dir),
    #                     'error_message': None,
    #                     'results': results
    #                 })
    #                 print(f"VCorneaProcess: Replicate {replicate_id} completed. Results in: {run_output_dir}")

    #             # Update metadata file and experiment log for every replicate, regardless of outcome
    #             with open(metadata_file, 'w') as f:
    #                 json.dump(run_metadata, f, indent=2)
    #             self._update_experiment_log(output_base, run_metadata)

    #         except Exception as e:
    #             # ---- Handle exceptions ----
    #             print(f"VCorneaProcess: An exception occurred during replicate {replicate_id}: {e}")
    #             run_metadata['simulation_success'] = False
    #             run_metadata['error_message'] = str(e)

    #             # Append a failure report for the exception
    #             replicate_outputs.append({
    #                 'replicate_id': replicate_id,
    #                 'success': False,
    #                 'output_directory': str(run_output_dir),
    #                 'error_message': str(e),
    #                 'results': None
    #             })
    #             with open(metadata_file, 'w') as f:
    #                 json.dump(run_metadata, f, indent=2)

    #         finally:
    #             shutil.rmtree(temp_dir, ignore_errors=True)
    #             if not self.parameters.get('keep_outputs', False):
    #                 shutil.rmtree(run_output_dir, ignore_errors=True)

    #     # ---- Determine overall success and construct the final output ----
    #     print(f"\n--- All {num_replicates} replicates finished ---")
        
    #     overall_success = all(rep['success'] for rep in replicate_outputs)

    #     if not self.parameters.get('keep_outputs', False):
    #          try:
    #              if not any(batch_output_dir.iterdir()):
    #                  batch_output_dir.rmdir()
    #          except OSError as e:
    #              print(f"Could not remove empty batch directory {batch_output_dir}: {e}")

    #     return {
    #         'outputs': {
    #             'replicate_results': replicate_outputs,
    #             'simulation_success': overall_success,
    #             'output_directory': str(batch_output_dir),
    #             'parameter_changes': parameter_changes,
    #             'run_metadata': self._create_run_metadata(sim_params, parameter_changes, run_name)
    #         }
    #     }

    def _identify_parameter_changes(self, sim_params):
        """Identify which parameters have been changed from their defaults."""
        parameter_changes = {}
        
        # Get default values from the ports schema
        defaults = {}
        for param, schema in self.ports_schema()['inputs'].items():
            defaults[param] = schema['_default']
        
        # Compare current values with defaults
        for param, value in sim_params.items():
            if param in defaults:
                default_value = defaults[param]
                if value != default_value:
                    parameter_changes[param] = {
                        'current_value': value,
                        'default_value': default_value,
                        'change_type': self._classify_change(value, default_value)
                    }
        
        return parameter_changes

    def _classify_change(self, current, default):
        """Classify the type of parameter change."""
        if isinstance(current, (int, float)) and isinstance(default, (int, float)):
            if current > default:
                return 'increased'
            else:
                return 'decreased'
        elif isinstance(current, bool) and isinstance(default, bool):
            return 'toggled'
        else:
            return 'modified'

    def _generate_run_name(self, parameter_changes):
        """Generate a descriptive run name based on parameter changes."""
        
        # If user provided a custom name, use it
        if self.parameters.get('run_name'):
            return self.parameters['run_name']
        
        # If no parameters changed, use default name
        if not parameter_changes:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            return f"default_run_{timestamp}"
        
        # Generate descriptive name based on key parameter changes
        name_parts = []
        max_params = self.parameters.get('max_params_in_name', 3)
        
        # Prioritize certain parameters for naming
        priority_params = [
            'SLS_Concentration', 'InjuryTime', 'SimTime', 'IsInjury', 'InjuryType',
            'EGF_STEM_HalfMaxValue', 'EGF_BASAL_HalfMaxValue'
        ]
        
        # First, add high-priority parameters
        for param in priority_params:
            if param in parameter_changes and len(name_parts) < max_params:
                change = parameter_changes[param]
                name_parts.append(self._format_param_for_name(param, change))
        
        # Then add other parameters if we have space
        for param, change in parameter_changes.items():
            if param not in priority_params and len(name_parts) < max_params:
                name_parts.append(self._format_param_for_name(param, change))
        
        # If we have many changes, add a count
        if len(parameter_changes) > max_params:
            name_parts.append(f"plus{len(parameter_changes) - max_params}more")
        
        # Combine parts
        if name_parts:
            base_name = "_".join(name_parts)
        else:
            base_name = "modified_params"
        
        # Add timestamp for uniqueness
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}"

    def _format_param_for_name(self, param, change):
        """Format a parameter change for inclusion in the run name."""
        value = change['current_value']
        
        # Special formatting for certain parameters
        if param == 'SLS_Concentration':
            return f"SLS{int(value)}"
        elif param == 'InjuryTime':
            return f"InjT{int(value)}"
        elif param == 'SimTime':
            return f"SimT{int(value)}"
        elif param == 'IsInjury':
            return "WithInjury" if value else "NoInjury"
        elif param == 'InjuryType':
            return "Chemical" if value else "Ablation"
        elif isinstance(value, bool):
            return f"{param}_{str(value)}"
        elif isinstance(value, (int, float)):
            if isinstance(value, float) and value.is_integer():
                return f"{param}{int(value)}"
            else:
                return f"{param}{value}"
        else:
            return f"{param}_{str(value)}"

    def _create_run_metadata(self, sim_params, parameter_changes, run_name):
        """Create comprehensive metadata for this run."""
        metadata = {
            'run_name': run_name,
            'created_at': pd.Timestamp.now().isoformat(),
            'vivarium_wrapper_version': '1.0.0',  # You can version your wrapper
            'total_parameters': len(sim_params),
            'parameters_changed': len(parameter_changes),
            'parameter_changes': parameter_changes,
            'simulation_config': {
                'cc3d_project_path': str(self.parameters['cc3d_project_path']),
                'conda_env_name': self.parameters['conda_env_name'],
                'sim_time': sim_params.get('SimTime', 7700),
                'has_injury': sim_params.get('IsInjury', False),
                'injury_type': 'chemical' if sim_params.get('InjuryType', False) else 'ablation'
            },
            'key_parameters': {
                param: sim_params.get(param, 'not_set') 
                for param in ['SLS_Concentration', 'InjuryTime', 'SimTime', 'IsInjury']
            },
            'simulation_success': None,  # Will be updated after simulation
            'simulation_completed_at': None,
            'files_generated': [],
            'healing_time': None
        }
        
        return metadata

    def _update_experiment_log(self, output_base, run_metadata):
        """Update the master experiment log with this run's information."""
        log_file = output_base / "experiment_log.csv"
        
        # Create log entry
        log_entry = {
            'run_name': run_metadata['run_name'],
            'created_at': run_metadata['created_at'],
            'simulation_success': run_metadata['simulation_success'],
            'parameters_changed': run_metadata['parameters_changed'],
            'sim_time': run_metadata['simulation_config']['sim_time'],
            'has_injury': run_metadata['simulation_config']['has_injury'],
            'injury_type': run_metadata['simulation_config']['injury_type'],
            'healing_time': run_metadata.get('healing_time', ''),
            'output_directory': run_metadata['run_name']
        }
        
        # Add key parameter changes to the log
        for param, change in run_metadata.get('parameter_changes', {}).items():
            if param in ['SLS_Concentration', 'InjuryTime', 'EGF_STEM_HalfMaxValue']:
                log_entry[f'{param}_value'] = change['current_value']
                log_entry[f'{param}_default'] = change['default_value']
        
        # Read existing log or create new DataFrame
        if log_file.exists():
            try:
                df = pd.read_csv(log_file)
                # Append new entry
                new_df = pd.concat([df, pd.DataFrame([log_entry])], ignore_index=True)
            except Exception as e:
                print(f"Warning: Could not read existing log file: {e}")
                new_df = pd.DataFrame([log_entry])
        else:
            new_df = pd.DataFrame([log_entry])
        
        # Save updated log
        try:
            new_df.to_csv(log_file, index=False)
            print(f"Updated experiment log: {log_file}")
        except Exception as e:
            print(f"Warning: Could not update experiment log: {e}")

    def _redirect_outputs_in_copy(self, temp_project, external_output_dir):
        """Modify the copied vCornea steppables to redirect outputs to external directory."""
        steppables_file = temp_project / "Simulation" / "vCornea_v2Steppables.py"
        
        if not steppables_file.exists():
            raise FileNotFoundError(f"Steppables file not found: {steppables_file}")
        
        # Read the original steppables file
        with open(steppables_file, 'r') as f:
            content = f.read()
        
        # Replace the output directory line
        old_line = 'output_directory = current_script_directory.joinpath("Output",time.strftime("%m%d%Y_%H%M%S"))'
        new_line = f'output_directory = Path("{str(external_output_dir)}")'
        
        if old_line in content:
            content = content.replace(old_line, new_line)
        else:
            # If the exact line isn't found, try a more flexible approach
            import re
            pattern = r'output_directory = current_script_directory\.joinpath\("Output".*?\)'
            replacement = f'output_directory = Path("{str(external_output_dir)}")'
            content = re.sub(pattern, replacement, content)
        
        # Also ensure Path is imported
        if 'from pathlib import Path' not in content:
            content = 'from pathlib import Path\n' + content
        
        # Write the modified content back
        with open(steppables_file, 'w') as f:
            f.write(content)

    def _write_parameters_file(self, params_file, sim_params):
        """Write parameters to the vCornea Parameters.py file."""
        params_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(params_file, 'w') as f:
            f.write("# Parameters for vCornea simulation\n")
            f.write("# Generated by Vivarium wrapper\n\n")
            
            for param_name, param_value in sim_params.items():
                f.write(f"{param_name}={repr(param_value)}\n")

    def _run_cc3d_simulation(self, project_path, output_dir):
        """
        Launches the CC3D simulation as a separate process using Popen.
        Redirects stdout and stderr to log files in the replicate's output directory.
        """
        cc3d_file = project_path / "vCornea_v2.cc3d"
        conda_env = self.parameters['conda_env_name']
        conda_exe = self.parameters.get('conda_executable_path', 'conda') # Use .get for safety
        
        command = [
            conda_exe, 'run', '-n', conda_env,
            'python', '-m', 'cc3d.run_script',
            '-i', str(cc3d_file)
        ]
        
        print(f"VCorneaProcess: Launching command: {' '.join(command)}")

        # ---- Create log files for stdout and stderr for this specific replicate ----
        stdout_log_path = output_dir / "stdout.log"
        stderr_log_path = output_dir / "stderr.log"

        try:
            # Open the log files
            stdout_log = open(stdout_log_path, 'w')
            stderr_log = open(stderr_log_path, 'w')

            # ---- Use Popen to run the command in the background ----
            process = subprocess.Popen(
                command,
                cwd=str(project_path),
                stdout=stdout_log,
                stderr=stderr_log,
                text=True
            )
            
            # Return the process handle and the log file objects
            return process, stdout_log, stderr_log
            
        except Exception as e:
            print(f"VCorneaProcess: Error trying to launch CC3D: {e}")
            # Ensure files are closed if Popen fails
            if 'stdout_log' in locals() and not stdout_log.closed:
                stdout_log.close()
            if 'stderr_log' in locals() and not stderr_log.closed:
                stderr_log.close()
            return None, None, None
        
    # def _run_cc3d_simulation(self, project_path):
    #     """Run the CC3D simulation using the correct command."""
    #     cc3d_file = project_path / "vCornea_v2.cc3d"
    #     conda_env = self.parameters['conda_env_name']
        
    #     # Build command exactly as the GUI does
    #     command = [
    #         'conda', 'run', '-n', conda_env,
    #         'python', '-m', 'cc3d.run_script',
    #         '-i', str(cc3d_file)
    #     ]
        
    #     print(f"VCorneaProcess: Running command: {' '.join(command)}")
        
    #     try:
    #         result = subprocess.run(
    #             command,
    #             cwd=str(project_path),
    #             capture_output=True,
    #             text=True,
    #             timeout=7200  # 2 hour timeout
    #         )
            
    #         if result.returncode != 0:
    #             print(f"VCorneaProcess: CC3D failed with return code {result.returncode}")
    #             print(f"STDOUT: {result.stdout}")
    #             print(f"STDERR: {result.stderr}")
    #             return False
            
    #         return True
            
    #     except subprocess.TimeoutExpired:
    #         print("VCorneaProcess: Simulation timed out after 2 hours")
    #         return False
    #     except Exception as e:
    #         print(f"VCorneaProcess: Error running CC3D: {e}")
    #         return False

    def _parse_simulation_results(self, output_dir, sim_params):
        """Parse the simulation output files from external output directory."""
        sim_time = sim_params.get('SimTime', 7700)
        
        # Look for output files in the external directory
        cell_count_file = output_dir / f"cell_count_{sim_time + 1}.csv"
        thickness_file = output_dir / f"thickness_rep_{sim_time + 1}.parquet"
        
        results = {
            'simulation_success': True,
            'healing_time': 0.0,
            'cell_counts': {},
            'tissue_thickness': {}
        }
        
        # Parse cell counts
        if cell_count_file.exists():
            try:
                cell_counts_df = pd.read_csv(cell_count_file)
                results['cell_counts'] = cell_counts_df.to_dict('records')
                
                # Calculate healing time if injury occurred
                if sim_params.get('IsInjury', False):
                    results['healing_time'] = self._calculate_healing_time(
                        cell_counts_df, sim_params
                    )
                    
            except Exception as e:
                print(f"Warning: Could not parse cell counts: {e}")
        else:
            print(f"Warning: Cell count file not found: {cell_count_file}")
        
        # Parse thickness data
        if thickness_file.exists():
            try:
                thickness_df = pd.read_parquet(thickness_file)
                results['tissue_thickness'] = thickness_df.to_dict('records')
            except Exception as e:
                print(f"Warning: Could not parse thickness data: {e}")
        else:
            print(f"Warning: Thickness file not found: {thickness_file}")
        
        return results

    def _calculate_healing_time(self, cell_counts_df, sim_params):
        """Calculate healing time from cell count data."""
        if cell_counts_df.empty:
            return 0.0
        
        try:
            injury_time = sim_params.get('InjuryTime', 500)
            
            # Simple healing metric: when total cell count returns to 95% of pre-injury
            pre_injury_data = cell_counts_df[cell_counts_df['Time'] < injury_time]
            if pre_injury_data.empty:
                return 0.0
            
            # Calculate pre-injury baseline (last few time points before injury)
            baseline_data = pre_injury_data.tail(10)
            baseline_total = baseline_data[['Superficial', 'Wing', 'Basal', 'Stem']].sum(axis=1).mean()
            
            # Find when post-injury levels return to 95% of baseline
            post_injury_data = cell_counts_df[cell_counts_df['Time'] > injury_time]
            for idx, row in post_injury_data.iterrows():
                current_total = row[['Superficial', 'Wing', 'Basal', 'Stem']].sum()
                if current_total >= 0.95 * baseline_total:
                    healing_time = row['Time'] - injury_time
                    return max(0.0, healing_time)
            
            return 0.0  # No healing detected
            
        except Exception as e:
            print(f"Warning: Could not calculate healing time: {e}")
            return 0.0