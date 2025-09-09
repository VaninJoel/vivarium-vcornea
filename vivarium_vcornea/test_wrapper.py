# File: vivarium_vcornea/test_wrapper.py
"""
Test module for the Vivarium vCornea wrapper.
This allows users to test the installation after pip install.
"""

import os
import sys
from vivarium.core.engine import Engine
from vivarium.core.composer import Composer
from .processes.vcornea_process import VCorneaProcess


class VCorneaTestComposer(Composer):
    """Simple composer for testing the vCornea wrapper"""
    
    defaults = {
        'vcornea_process': {
            'cc3d_project_path': None,  # Must be provided by user
            'python_executable': 'python',
        },
    }

    def generate_processes(self, config):
        process_config = config['vcornea_process']
        
        if not process_config.get('cc3d_project_path'):
            raise ValueError(
                "CC3D project path must be provided. Example:\n"
                "test_wrapper('/path/to/vCornea/clean_paper_version')"
            )
        
        vcornea_process = VCorneaProcess(process_config)
        return {'vcornea': vcornea_process}

    def generate_topology(self, config):
        return {
            'vcornea': {
                'inputs': ('globals', 'inputs'),
                'outputs': ('globals', 'outputs'),
            }
        }


def test_wrapper(cc3d_project_path, python_executable='python'):
    """
    Test the vCornea Vivarium wrapper with a minimal simulation.
    
    Args:
        cc3d_project_path (str): Path to the vCornea CC3D project directory
        python_executable (str): Python executable with CC3D installed
    
    Returns:
        dict: Test results
    """
    print("=== Testing Vivarium vCornea Wrapper ===")
    print(f"CC3D Project Path: {cc3d_project_path}")
    print(f"Python Executable: {python_executable}")
    
    if not os.path.exists(cc3d_project_path):
        print(f"ERROR: CC3D project path does not exist: {cc3d_project_path}")
        return {'success': False, 'error': 'Invalid CC3D path'}
    
    try:
        # Create composer with test configuration
        composer = VCorneaTestComposer()
        composer.defaults['vcornea_process'].update({
            'cc3d_project_path': cc3d_project_path,
            'python_executable': python_executable,
        })
        
        # Generate composite
        vcornea_composite = composer.generate()
        
        # Minimal test state
        test_state = {
            'globals': {
                'inputs': {
                    'SimTime': 100,        # Very short for testing
                    'IsInjury': False,     # No injury for basic test
                    'CC3D_PLOT': False,    # Disable plotting
                }
            }
        }
        
        print("Running test simulation...")
        
        # Create and run simulation
        sim = Engine(
            composite=vcornea_composite,
            initial_state=test_state
        )
        
        sim.update(1.0)
        
        print("✓ Test completed successfully!")
        
        # Get results
        output_data = sim.emitter.get_data()
        
        return {
            'success': True,
            'message': 'Wrapper test passed',
            'outputs': output_data
        }
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        print("\nTroubleshooting:")
        print("1. Verify CC3D project path exists")
        print("2. Ensure Python environment has CC3D installed")
        print("3. Check batch script exists in project directory")
        
        return {
            'success': False,
            'error': str(e)
        }


def quick_test():
    """
    Interactive test that prompts user for configuration.
    """
    print("=== Quick Test Setup ===")
    
    cc3d_path = input("Enter CC3D vCornea project path: ").strip()
    if not cc3d_path:
        print("Error: CC3D path is required")
        return False
    
    python_path = input("Python executable (default: python): ").strip()
    if not python_path:
        python_path = 'python'
    
    result = test_wrapper(cc3d_path, python_path)
    return result['success']


if __name__ == '__main__':
    # Allow running as: python -m vivarium_vcornea.test_wrapper
    if len(sys.argv) > 1:
        cc3d_path = sys.argv[1]
        python_exe = sys.argv[2] if len(sys.argv) > 2 else 'python'
        test_wrapper(cc3d_path, python_exe)
    else:
        quick_test()