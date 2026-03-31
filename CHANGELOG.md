# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [UNRELEASED] - 20XX-XX-XX

### Added

### Changed

### Removed

## [2.1.0] - 2026-03-31

### Added [2.1.0]

- Added management of parallel crack evolutions to api.py
- Added saving.py module that replaced saving functionality in api.py
- Added life_assessment.py module to solve individual crack evolution calculations
- Added other_stress_state as an input to life_assessment.py to handle user specified residual stress
- Added residual stress stress intensity factor (Kres), minimum primary stress intensity factor (Kmin), and load ratio (R ratio) as tracked quantities in life_assessment.py
- Added function to calculate load ratio (R Ratio) within stress_state.py to account for residual stress intensity factor
- Added minimum primary stress intensity factor as output from stress_instensity_factor calculation within stress_state.py
- Added either a fixed residual stress intensity factor or parameters characterizing a weld residual stress condition as inputs to api.py
- Added residual stress intensity factor as inputs to unit tests to test_api.py
- Added load ratio (R ratio) as input to crack growth rate calculation functions
- Added unit tests for accounting for residual stresses to failure assessment in test_fracture.py
- Added unit test for cases with residual stresses in life_assessment.py
- Added residual_stress.py to support user specified fixed residual stress, stress intensity factor values as well as characterize residual stresses due to welds based on API 579-1
- Added reporting units for weld input parameters to unit_conversion.py
- Added tests to improve coverage throughout helpr
- Added marker for samples and nominal values in sensitivity plots
- Added text to the FAD plot to indicate the FAD calculation method used in the legend title
- Added example csv file for random pressure loading capability
- Added class to environment module to handle random loading pressure data
- Added function to plots.py to plot random loading profile inputs

### Changed [2.1.0]

- Moved api.py module up a level in the code structure
- Changed Physics modules to act primarily on float variables instead of arrays
- Changed parameter.py to be built on floats instead of arrays
- Changed unit tests based on change of physics modules move from array to float operations
- Changed postprocessing.py and plots.py to accomidate data structure from paralllel crack evolutions
- Moved r_ratio calculation from environment.py to stress_state.py
- Changed fracture.py to account for residual stress for both anderson and api FAD calculations
- Moved determine_fad_values, process_fatigue_instance, determine_fad_values, and calculate_failure_assessment functions from postprocessing.py to fracture.py
- Moved calc_combined_stress_intensity_factor function from stress_state.py to fracture.py
- Changed calculation of load ratio to take place in life_assessment.py instead of environment.py
- Changed calculation of critical crack size to account for residual stress in postprocessing.py
- Changed calculation of r_ratio as intermediate parameter in api.py
- Changed inspection mitigation calculations to use a more transparent process based on single crack evaluations
- Change inspection mitigation plot labels to improve clarity
- Changed docstrings throughout helpr to consistent format and level of detail
- Changed test organization so that tests are now classified as a unit or integration test
- Changed y axis of sensitivity plots to min-max of sampled range to avoid issues with nominals at 0
- Changed FAD calculation method to be user specified and apply to any K solution approach
- Changed api.py to handle random pressure loading inputs
- Changed functions in plots.py and postprocessing.py to handle a list of life cycle criteria

### Removed [2.1.0]

- Removed cycle_evolution.py module. This functionality was moved to the api.py and life_assessment.py
- Removed get_singe_x methods out of all physics modules
- Removed environment_specification input from life_assessment.py inputs
- Removed test_r_ratio from test_environment.py

## [2.0.0] - 2024-12-16

### Added [2.0.0]

- Added demo of crack growth rate calculations and advanced user options
- Added warnings to notify users when specified input parameters violate applicability bounds for Anderson and API 579 stress intensity factor calculations
- Added ability to specify crack length growth assumption from being a constant c/a, to being constant, or growing independently based on API 579 calculation method
- Added ability for user to specify maximum number of cycles (currently not fully functional for probabilistic studies where cracks evolved until all meet criteria)
- Added support for truncated lognormal distributions
- Added API 579 stress intensity factor calculations within stress state module for external surface longitudinal direction cracks with semi-elliptical shape, driven by internal pressure.
- Added ability to do level 2 assessment for FAD based on API 579-1
- Added intermediate variable values to nominal results file

### Changed [2.0.0]

- Changed how crack evolution terminates. If a/t values greater than 0.8 reached, 0.8 reported. If stress intensity factor values never reach fracture touchness nan reported.
- Changed crack growth function to takes combination of delta_a, delta_n, or delta_k as inputs to function to calculation delta_a or delta_n
- Changed FAD module to allow specification of different stress intensity calculation methods
- Changed api unit test back to v1.0.0 version due to bad merge prior to v1.1.0

### Removed [2.0.0]

- Removed functions within the crack growth moduled used to update a combination of delta_a, delta_n, or delta_k
- Removed unit test for bad specification of crack growth based on a combination of k, a, or n being specificed

## [1.1.0] - 2024-04-15

### Added [1.1.0]

- Added API 579 stress intensity factor approach within stress state module for internal surface longitudinal direction cracks with semi-elliptical shape, driven by internal pressure. Included table files for coefficient lookup.
- Added unit test to test_postprocessing for specifying Anderson stress intensity method and the default crack growth model being specified as code_case_2938
- Specification of stress intensity method now in API initiation.
- Added use of xarray and netcdf4 python packages for use in API 579 stress intensity approach
- Added a demo of the crack growth curve capability
- Added ability for users to specify save location in gui
- Added ability for users to specify analysis name
- Added displaying of intermediate variables (t/R, percent smys, stress ratio, initial crack depth, and a/2c) in gui during specification of input parameters
- Added intermediate variable percent specified minimum yield strength to results parameter section
- Added unit test to test_plots for plotting crack growth design curves
- Added unit test for simple pipe dimension calculations to test_pipe
- Added unit test to test_cycle_evolution for evolving cracks by cycle
- Added unit tests to test_api for calculating intermediate variables and saving nominal result file

### Changed [1.1.0]

- Changed cycle evolution, postprocessing, and stress state unit test to specify stress intensity factor calculation approach. Also updated deterministic demo notebook to similarly reflection stress intensity method.
- Moved calculation of eta from cycle evolution module to stress state module.
- Moved development of core gui capabilities to a separate submodule which is integrated with the main repo when distributed
- Fixed bug in gui results plot comparing exercised crack growth rates versus crack growth rate curves to show proper crack growth curve
- Changed hoop stress calculation from using average pipe radius to using outer pipe radius
- Changed value error when percent smys is above 100 to being a warning when above 72
- Changed saving deterministic study results in separate file to saving in single file, also include this file in probabilistic studies

### Removed [1.1.0]
