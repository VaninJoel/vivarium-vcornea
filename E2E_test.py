#!/usr/bin/env python3
"""
Comprehensive end-to-end test for vCornea-Vivarium wrapper using pytest.

This test actually runs minimal vCornea simulations to verify the complete workflow:
- Parameter injection
- File creation and naming
- Output parsing
- Vivarium integration
- Multiple replicates

Usage:
    pytest test_vcornea_complete_workflow.py -v
    pytest test_vcornea_complete_workflow.py::TestCompleteWorkflow::test_minimal_simulation -v
"""

import pytest
import tempfile
import shutil
import time
from pathlib import Path
import pandas as pd
import json
import os

# Configuration
VCORNEA_PROJECT_PATH = Path(r'C:\Users\joelv\OneDrive\Desktop\vCornea_suite\vCornea\HPC\Project\paper_version')
CONDA_ENV_NAME = 'vc'

@pytest.fixture
def vcornea_process():
    """Fixture providing a configured VCorneaProcess for testing."""
    from vivarium_vcornea.processes.vcornea_process import VCorneaProcess
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "test_outputs"
        
        parameters = {
            'cc3d_project_path': str(VCORNEA_PROJECT_PATH),
            'conda_env_name': CONDA_ENV_NAME,
            'output_base_dir': str(output_dir),
            'keep_outputs': True,
            'replicates': 1
        }
        
        yield VCorneaProcess(parameters)

@pytest.fixture
def minimal_sim_params():
    """Fixture providing minimal simulation parameters for fast testing."""
    return {
        'SimTime': 50,  # Very short simulation
        'CC3D_PLOT': False,
        'IsInjury': False,
        'CellCount': True,
        'ThicknessPlot': True,
        'SurfactantTracking': False,
        'SnapShot': False
    }

@pytest.fixture
def custom_sim_params():
    """Fixture providing custom simulation parameters for parameter testing."""
    return {
        'SimTime': 30,
        'SLS_Concentration': 1500.0,  # Non-default value
        'InjuryTime': 10,             # Non-default value
        'IsInjury': True,
        'InjuryType': True,           # Chemical injury
        'CC3D_PLOT': False,
        'CellCount': True,
        'ThicknessPlot': True
    }

class TestCompleteWorkflow:
    """Test the complete vCornea-Vivarium workflow with actual simulations."""

    def test_minimal_simulation(self, vcornea_process, minimal_sim_params):
        """Test running a minimal vCornea simulation and verify outputs."""
        # Run the simulation
        states = {'inputs': minimal_sim_params}
        start_time = time.time()
        
        results = vcornea_process.next_update(1.0, states)
        elapsed_time = time.time() - start_time
        
        print(f"Simulation completed in {elapsed_time:.1f} seconds")
        
        # Verify basic result structure
        assert 'outputs' in results
        assert 'simulation_success' in results['outputs']
        assert 'replicate_results' in results['outputs']
        assert 'output_directory' in results['outputs']
        
        # Verify simulation succeeded
        assert results['outputs']['simulation_success'] is True
        
        # Verify replicate results
        replicate_results = results['outputs']['replicate_results']
        assert len(replicate_results) == 1
        assert replicate_results[0]['success'] is True
        assert replicate_results[0]['replicate_id'] == 1
        
        # Verify output directory exists
        output_directory = Path(results['outputs']['output_directory'])
        assert output_directory.exists()
        
        # Verify replicate directory and files
        replicate_dir = output_directory / "replicate_1"
        assert replicate_dir.exists()
        
        # Check for expected output files
        expected_files = [
            f"cell_count_{minimal_sim_params['SimTime'] + 1}.csv",
            f"thickness_rep_{minimal_sim_params['SimTime'] + 1}.parquet",
            "run_metadata.json",
            "stdout.log",
            "stderr.log"
        ]
        
        for expected_file in expected_files:
            file_path = replicate_dir / expected_file
            assert file_path.exists(), f"Missing expected file: {expected_file}"
            assert file_path.stat().st_size > 0, f"Empty file: {expected_file}"

    def test_output_file_content(self, vcornea_process, minimal_sim_params):
        """Test that output files contain valid data."""
        states = {'inputs': minimal_sim_params}
        results = vcornea_process.next_update(1.0, states)
        
        assert results['outputs']['simulation_success'] is True
        
        replicate_dir = Path(results['outputs']['output_directory']) / "replicate_1"
        sim_time = minimal_sim_params['SimTime']
        
        # Test cell count CSV
        cell_count_file = replicate_dir / f"cell_count_{sim_time + 1}.csv"
        assert cell_count_file.exists()
        
        df = pd.read_csv(cell_count_file)
        assert not df.empty
        assert 'Time' in df.columns
        assert all(col in df.columns for col in ['Superficial', 'Wing', 'Basal', 'Stem'])
        assert df['Time'].max() <= sim_time + 1  # Final time point
        assert all(df[col] >= 0 for col in ['Superficial', 'Wing', 'Basal', 'Stem'])  # Cell counts should be non-negative
        
        # Test thickness parquet
        thickness_file = replicate_dir / f"thickness_rep_{sim_time + 1}.parquet"
        assert thickness_file.exists()
        
        df_thickness = pd.read_parquet(thickness_file)
        assert not df_thickness.empty
        assert 'Time' in df_thickness.columns
        
        # Test metadata JSON
        metadata_file = replicate_dir / "run_metadata.json"
        assert metadata_file.exists()
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        assert 'run_name' in metadata
        assert 'created_at' in metadata
        assert 'simulation_success' in metadata
        assert metadata['simulation_success'] is True
        assert 'simulation_config' in metadata
        assert metadata['simulation_config']['sim_time'] == sim_time

    def test_parameter_injection(self, vcornea_process, custom_sim_params):
        """Test that custom parameters are properly injected and detected."""
        # Test parameter change detection
        parameter_changes = vcornea_process._identify_parameter_changes(custom_sim_params)
        
        # Should detect changes for non-default values
        expected_changes = ['SLS_Concentration', 'InjuryTime', 'InjuryType']
        for param in expected_changes:
            assert param in parameter_changes, f"Expected parameter change not detected: {param}"
        
        # Verify specific parameter values
        assert parameter_changes['SLS_Concentration']['current_value'] == 1500.0
        assert parameter_changes['SLS_Concentration']['default_value'] == 750.0
        assert parameter_changes['SLS_Concentration']['change_type'] == 'increased'
        
        assert parameter_changes['InjuryTime']['current_value'] == 10
        assert parameter_changes['InjuryTime']['default_value'] == 500
        assert parameter_changes['InjuryTime']['change_type'] == 'decreased'
        
        assert parameter_changes['InjuryType']['current_value'] is True
        assert parameter_changes['InjuryType']['default_value'] is False
        assert parameter_changes['InjuryType']['change_type'] == 'toggled'

    def test_run_name_generation(self, vcornea_process, custom_sim_params):
        """Test that run names are generated correctly from parameter changes."""
        parameter_changes = vcornea_process._identify_parameter_changes(custom_sim_params)
        run_name = vcornea_process._generate_run_name(parameter_changes)
        
        # Should contain parameter information
        assert 'SLS1500' in run_name
        assert 'InjT10' in run_name
        assert len(run_name) > 10  # Should be descriptive
        
        # Test with no changes
        no_changes = {}
        default_name = vcornea_process._generate_run_name(no_changes)
        assert 'default_run' in default_name
        
        # Test with custom name
        vcornea_process.parameters['run_name'] = 'my_custom_test'
        custom_name = vcornea_process._generate_run_name(parameter_changes)
        assert custom_name == 'my_custom_test'

    def test_simulation_with_custom_parameters(self, vcornea_process, custom_sim_params):
        """Test running simulation with custom parameters and verify they're applied."""
        states = {'inputs': custom_sim_params}
        results = vcornea_process.next_update(1.0, states)
        
        assert results['outputs']['simulation_success'] is True
        
        # Verify parameter changes are recorded
        parameter_changes = results['outputs']['parameter_changes']
        assert 'SLS_Concentration' in parameter_changes
        assert 'InjuryTime' in parameter_changes
        
        # Verify run metadata includes custom parameters
        run_metadata = results['outputs']['run_metadata']
        assert run_metadata['simulation_config']['sim_time'] == custom_sim_params['SimTime']
        assert run_metadata['simulation_config']['has_injury'] == custom_sim_params['IsInjury']
        assert run_metadata['simulation_config']['injury_type'] == 'chemical'  # InjuryType=True means chemical

    @pytest.mark.slow
    def test_multiple_replicates(self):
        """Test running multiple replicates."""
        from vivarium_vcornea.processes.vcornea_process import VCorneaProcess
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "multi_replicate_test"
            
            parameters = {
                'cc3d_project_path': str(VCORNEA_PROJECT_PATH),
                'conda_env_name': CONDA_ENV_NAME,
                'output_base_dir': str(output_dir),
                'keep_outputs': True,
                'replicates': 3  # Multiple replicates
            }
            
            process = VCorneaProcess(parameters)
            
            sim_params = {
                'SimTime': 25,  # Very short for speed
                'CC3D_PLOT': False,
                'IsInjury': False,
                'CellCount': True,
                'ThicknessPlot': False,  # Disable to speed up
                'SurfactantTracking': False
            }
            
            states = {'inputs': sim_params}
            results = process.next_update(1.0, states)
            
            assert results['outputs']['simulation_success'] is True
            
            # Verify all replicates completed
            replicate_results = results['outputs']['replicate_results']
            assert len(replicate_results) == 3
            
            for i, rep in enumerate(replicate_results, 1):
                assert rep['replicate_id'] == i
                assert rep['success'] is True
                
                # Verify each replicate has its own directory
                rep_dir = Path(rep['output_directory'])
                assert rep_dir.exists()
                assert rep_dir.name == f"replicate_{i}"

    def test_error_handling_missing_project(self):
        """Test error handling when project path is missing."""
        from vivarium_vcornea.processes.vcornea_process import VCorneaProcess
        
        with pytest.raises(FileNotFoundError, match="vCornea project path not found"):
            VCorneaProcess({'cc3d_project_path': '/nonexistent/path'})

    def test_error_handling_missing_files(self):
        """Test error handling when required files are missing."""
        from vivarium_vcornea.processes.vcornea_process import VCorneaProcess
        
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_project = Path(temp_dir) / "fake_project"
            fake_project.mkdir()
            
            # Create only some required files
            (fake_project / "vCornea_v2.cc3d").touch()
            
            with pytest.raises(FileNotFoundError, match="Required vCornea file not found"):
                VCorneaProcess({'cc3d_project_path': str(fake_project)})

    def test_parameter_file_writing(self, vcornea_process):
        """Test that parameter files are written correctly."""
        test_params = {
            'SLS_Concentration': 1500.0,
            'SimTime': 100,
            'IsInjury': True,
            'CC3D_PLOT': False
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            params_file = Path(temp_dir) / "test_parameters.py"
            
            vcornea_process._write_parameters_file(params_file, test_params)
            
            assert params_file.exists()
            
            # Verify file content
            content = params_file.read_text()
            
            for param, value in test_params.items():
                expected_line = f"{param}={repr(value)}"
                assert expected_line in content
            
            # Verify it's valid Python
            compile(content, str(params_file), 'exec')
            
            # Verify we can execute it and get the values
            namespace = {}
            exec(content, namespace)
            
            for param, expected_value in test_params.items():
                assert namespace[param] == expected_value

class TestVivarium_integration:
    """Test Vivarium-specific integration features."""

    def test_vivarium_engine_integration(self):
        """Test that VCorneaProcess works properly within Vivarium Engine."""
        from vivarium.core.engine import Engine
        from vivarium.core.composer import Composer
        from vivarium_vcornea.processes.vcornea_process import VCorneaProcess
        
        class TestComposer(Composer):
            defaults = {
                'vcornea_process': {
                    'cc3d_project_path': str(VCORNEA_PROJECT_PATH),
                    'conda_env_name': CONDA_ENV_NAME,
                    'replicates': 1,
                    'keep_outputs': False
                }
            }
            
            def generate_processes(self, config):
                return {'vcornea': VCorneaProcess(config['vcornea_process'])}
            
            def generate_topology(self, config):
                return {
                    'vcornea': {
                        'inputs': ('globals', 'inputs'),
                        'outputs': ('globals', 'outputs'),
                    }
                }
        
        # Create Vivarium engine
        composer = TestComposer()
        composite = composer.generate()
        
        initial_state = {
            'globals': {
                'inputs': {
                    'SimTime': 25,
                    'CC3D_PLOT': False,
                    'IsInjury': False
                }
            }
        }
        
        engine = Engine(composite=composite, initial_state=initial_state)
        
        # Verify engine was created successfully
        assert engine is not None
        assert 'vcornea' in engine.composite['processes']

    def test_ports_schema_completeness(self, vcornea_process):
        """Test that ports schema includes all expected vCornea parameters."""
        schema = vcornea_process.ports_schema()
        
        # Check basic structure
        assert 'inputs' in schema
        assert 'outputs' in schema
        
        # Check for key vCornea parameters
        essential_inputs = [
            'SimTime', 'SLS_Concentration', 'IsInjury', 'InjuryTime',
            'SLS_Threshold', 'SLS_TEARDiffCoef',
            'EGF_STEM_HalfMaxValue', 'EGF_BASAL_HalfMaxValue'
        ]
        
        for param in essential_inputs:
            assert param in schema['inputs'], f"Missing essential input parameter: {param}"
            assert '_default' in schema['inputs'][param]
            assert '_updater' in schema['inputs'][param]
        
        # Check essential outputs
        essential_outputs = [
            'replicate_results', 'simulation_success', 
            'output_directory', 'parameter_changes'
        ]
        
        for param in essential_outputs:
            assert param in schema['outputs'], f"Missing essential output parameter: {param}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])