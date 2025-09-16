# Vivarium vCornea Experiments

This folder contains scientific examples demonstrating how to use the Vivarium vCornea wrapper for different types of computational studies.

## Quick Start

1. **Setup**: Ensure you have the package installed and CC3D configured
   ```bash
   git clone https://github.com/VaninJoel/vivarium-vcornea.git
   cd vivarium-vcornea
   pip install .
   ```

2. **Test Installation**: 
   ```bash
   cd experiments
   python run_vcornea_test.py
   ```

## Experiment Types

### 1. Basic Testing (`run_vcornea_test.py`)
- **Purpose**: Verify wrapper installation and basic functionality
- **Use Case**: First-time setup validation
- **Runtime**: ~40 minutes
- **Parameters**: Minimal injury simulation

### 2. Parameter Sweeps (`parameter_sweep_example.py`)
- **Purpose**: Systematic exploration of parameter space
- **Use Case**: Dose-response studies, sensitivity analysis
- **Runtime**: ~40-360 minutes (depends on parameter combinations)
- **Parameters**: SLS concentration ranges, injury timing
- **Output**: CSV files with statistical summaries

### 3. Comparative Studies (`injury_comparison_study.py`)
- **Purpose**: Compare different experimental conditions
- **Use Case**: Hypothesis testing, treatment comparisons
- **Runtime**: ~45 minutes (multiple conditions with replicates)
- **Parameters**: Ablation vs chemical injuries, size effects
- **Output**: Statistical comparisons between groups

### 4. Batch Processing (`batch_processing_demo.py`)
- **Purpose**: Large-scale simulation workflows
- **Use Case**: High-throughput studies, cluster computing
- **Runtime**: Variable (demonstrates structure for 100s of simulations)
- **Parameters**: Random parameter sampling
- **Output**: Batch configuration files

## Configuration

Each experiment requires CC3D project path configuration. You can:

1. **Edit scripts directly**: Modify the `cc3d_project_path` variable
2. **Use environment variables**:
   ```bash
   export VCORNEA_CC3D_PATH="/path/to/vCornea/clean_paper_version"
   export VCORNEA_PYTHON_PATH="/path/to/cc3d/python"
   ```
3. **Interactive setup**: Scripts will prompt for paths if not configured

## Scientific Workflow Examples

### Single Parameter Study
```python
# Study: Effect of injury timing on healing
python parameter_sweep_example.py /path/to/cc3d sweep
```

### Comparative Analysis
```python
# Study: Ablation vs chemical injury comparison
python injury_comparison_study.py /path/to/cc3d comparison
```

### High-Throughput Pipeline
```python
# Generate batch job configurations
python batch_processing_demo.py /path/to/cc3d batch
```

## Output Files

- `*_results.csv`: Raw simulation results with metadata
- `*_summary.csv`: Statistical summaries and group comparisons
- `batch_config.json`: Parameter configurations for batch jobs
- `experiment_results.json`: Detailed output data structures

## Best Practices

1. **Start Small**: Begin with short simulations to verify setup
2. **Document Parameters**: Keep track of parameter choices and justifications
3. **Use Replicates**: Run multiple replicates for statistical validity
4. **Save Configurations**: Preserve parameter sets for reproducibility
5. **Version Control**: Track experiment scripts alongside results

## Computational Requirements

- **Memory**: 2-4 GB RAM per simulation
- **CPU**: Single core per simulation (parallelizable)
- **Storage**: ~10-2000 MB per simulation output
- **Time**: 30 seconds to 40 minutes per simulation (depends on SimTime)

## Troubleshooting

**Import Errors**: Ensure package is installed with `pip install .`

**CC3D Not Found**: Check CC3D installation and Python environment

**Path Issues**: Use absolute paths for CC3D project directory

**Memory Issues**: Reduce SimTime or run fewer parallel simulations

**Slow Performance**: Disable CC3D_PLOT for batch processing

## Citation

If you use these experimental frameworks in your research, please cite:

```
Vanin, J. et al. (2025). Vivarium vCornea: A computational framework for 
corneal epithelial wound healing studies. [Journal/Preprint]
```

## Contributing

To add new experiment types:

1. Follow the existing pattern in `parameter_sweep_example.py`
2. Include clear documentation and scientific rationale
3. Provide example usage and expected outputs
4. Add appropriate error handling and user guidance

## Support

For questions about experimental design or computational workflows:
- Open an issue on GitHub
- Check the main package documentation
- Review Vivarium core documentation
