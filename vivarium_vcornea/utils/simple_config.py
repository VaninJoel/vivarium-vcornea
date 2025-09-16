"""
Simple solution: Just remove hardcoded paths without changing your working architecture.

This creates a minimal configuration helper that works with your existing code.
"""

import json
from pathlib import Path
from typing import Dict, Any, Union, Optional


def create_vcornea_config(vcornea_project_path: Union[str, Path], 
                         conda_env_name: str = "vcornea",
                         output_base_dir: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Create a configuration dictionary for VCorneaProcess.
    
    This replaces hardcoded paths in your existing code.
    
    Args:
        vcornea_project_path: Path to your vCornea project
        conda_env_name: Name of conda environment 
        output_base_dir: Output directory (optional)
    
    Returns:
        Dictionary that can be passed to VCorneaProcess parameters
        
    Example:
        >>> config = create_vcornea_config(
        ...     vcornea_project_path="/path/to/vcornea",
        ...     conda_env_name="my_cc3d_env"
        ... )
        >>> process = VCorneaProcess(config)
    """
    config = {
        'cc3d_project_path': str(Path(vcornea_project_path)),
        'conda_env_name': conda_env_name,
        'replicates': 1,
    }
    
    if output_base_dir:
        config['output_base_dir'] = str(Path(output_base_dir))
    
    return config


def create_vivarium_experiment_state(simulation_parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create the state dictionary expected by Vivarium Engine.
    
    This helps create the properly formatted input state for your VCorneaProcess.
    
    Args:
        simulation_parameters: Your vCornea simulation parameters
        
    Returns:
        Dictionary formatted for Vivarium Engine initial_state
        
    Example:
        >>> sim_params = {
        ...     'SimTime': 1000,
        ...     'IsInjury': True,
        ...     'SLS_Concentration': 1500.0
        ... }
        >>> state = create_vivarium_experiment_state(sim_params)
        >>> engine = Engine(
        ...     processes={'vcornea': process},
        ...     topology={'vcornea': {'inputs': ('inputs',), 'outputs': ('outputs',)}},
        ...     initial_state=state
        ... )
    """
    return {
        'inputs': simulation_parameters,
        'outputs': {}
    }


def save_config_file(config: Dict[str, Any], filepath: Union[str, Path] = "vcornea_config.json"):
    """
    Save configuration to a JSON file for reuse.
    
    Args:
        config: Configuration dictionary from create_vcornea_config()
        filepath: Where to save the config file
    """
    with open(filepath, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"Configuration saved to {filepath}")


def load_config_file(filepath: Union[str, Path] = "vcornea_config.json") -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        filepath: Path to config file
        
    Returns:
        Configuration dictionary
    """
    with open(filepath, 'r') as f:
        return json.load(f)


# For your tests - replace hardcoded paths with this
def get_test_config() -> Dict[str, Any]:
    """
    Get test configuration. Users create a test_config.json file with their paths.
    
    Returns:
        Test configuration dictionary
        
    Raises:
        FileNotFoundError: If test_config.json doesn't exist
    """
    # config_path = Path(r"./test_config.json")
    config_path = Path(__file__).parent / "test_config.json"
    if not config_path.exists():
        raise FileNotFoundError(
            "test_config.json not found. Create it with:\n"
            '{\n'
            '  "vcornea_project_path": "/path/to/your/vcornea",\n'
            '  "conda_env_name": "vcornea"\n'
            '}'
        )
    
    return load_config_file(config_path)