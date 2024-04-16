# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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