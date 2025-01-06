# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-12-16

### Added
- Added demo of crack growth rate calculations and advanced user options
- Added warnings to notify users when specified input parameters violate applicability bounds for Anderson and API 579 stress intensity factor calculations
- Added ability to specify crack length growth assumption from being a constant c/a, to being constant, or growing independently based on API 579 calculation method
- Added ability for user to specify maximum number of cycles (currently not fully functional for probabilistic studies where cracks evolved until all meet criteria)
- Added support for truncated lognormal distributions
- Added API 579 stress intensity factor calculations within stress state module for external surface longitudinal direction cracks with semi-elliptical shape, driven by internal pressure.
- Added ability to do level 2 assessment for FAD based on API 579-1
- Added intermediate variable values to nominal results file

### Changed
- Changed how crack evolution terminates. If a/t values greater than 0.8 reached, 0.8 reported. If stress intensity factor values never reach fracture touchness nan reported.
- Changed crack growth function to takes combination of delta_a, delta_n, or delta_k as inputs to function to calculation delta_a or delta_n
- Changed FAD module to allow specification of different stress intensity calculation methods
- Changed api unit test back to v1.0.0 version due to bad merge prior to v1.1.0

### Removed
- Removed functions within the crack growth moduled used to update a combination of delta_a, delta_n, or delta_k
- Removed unit test for bad specification of crack growth based on a combination of k, a, or n being specificed


## [1.1.0] - 2024-04-15

### Added
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

### Changed
- Changed cycle evolution, postprocessing, and stress state unit test to specify stress intensity factor calculation approach. Also updated deterministic demo notebook to similarly reflection stress intensity method.
- Moved calculation of eta from cycle evolution module to stress state module.
- Moved development of core gui capabilities to a separate submodule which is integrated with the main repo when distributed
- Fixed bug in gui results plot comparing exercised crack growth rates versus crack growth rate curves to show proper crack growth curve
- Changed hoop stress calculation from using average pipe radius to using outer pipe radius
- Changed value error when percent smys is above 100 to being a warning when above 72
- Changed saving deterministic study results in separate file to saving in single file, also include this file in probabilistic studies

### Removed