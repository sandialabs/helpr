**Tests Documentation**
**************************

These tests are written using `pytest` and can be run from the command line:

- All tests can be evaluated via ``pytest``
- Executing ``pytest`` from the ``tests`` directory or above within the repo will execute all tests
- Executing ``pytest`` within a specific directory will only execute tests in that directory
- Executing ``pytest path/to/text_file.py`` will only execute single specified test

Unit Tests
===========
These tests ensure that individual HELPR components behave as expected.

test_crack_growth docu
-----------------------
Unit tests for crack growth models and their integration in the fatigue pipeline.

.. automodule:: helpr.tests.unit_tests.test_crack_growth
    :members:
    :show-inheritance:

test_crack_initiation docu
---------------------------
Validates models for determining initial crack formation.

.. automodule:: helpr.tests.unit_tests.test_crack_initiation
    :members:
    :show-inheritance:

test_environment docu
------------------------------------
Tests for the environmental effects on material degradation.

.. automodule:: helpr.tests.unit_tests.test_environment
    :members:
    :show-inheritance:

test_fracture docu
-------------------
Tests fracture mechanics models and critical failure logic.

.. automodule:: helpr.tests.unit_tests.test_fracture
    :members:
    :show-inheritance:

test_inspection_mitigation docu
--------------------------------
Tests inspection modeling and mitigation strategy logic.

.. automodule:: helpr.tests.unit_tests.test_inspection_mitigation
    :members:
    :show-inheritance:

test_life_assessment docu
--------------------------
Tests the evolution of crack cycles under fatigue loading.

.. automodule:: helpr.tests.unit_tests.test_life_assessment
    :members:    
    :show-inheritance:

test_material docu
-------------------
Validates material property handling and definitions.

.. automodule:: helpr.tests.unit_tests.test_material
    :members:
    :show-inheritance:

test_parameter docu
--------------------
Tests parameter definitions and handling infrastructure.

.. automodule:: helpr.tests.unit_tests.test_parameter
    :members:
    :show-inheritance:

test_pipe docu
---------------
Tests pipe geometry, features, and structural attributes.

.. automodule:: helpr.tests.unit_tests.test_pipe
    :members:
    :show-inheritance:

test_residual_stress docu
--------------------------
Tests specification of residual stress

.. automodule:: helpr.tests.unit_tests.test_residual_stress
    :members:
    :show-inheritance:

test_stress_state_unit docu
----------------------------
Tests loading and stress conditions applied to pipelines.

.. automodule:: helpr.tests.unit_tests.test_stress_state_unit
    :members:
    :show-inheritance:

test_unit_conversion docu
--------------------------
Tests unit converstions.

.. automodule:: helpr.tests.unit_tests.test_unit_conversion
    :members:
    :show-inheritance:



Integration Tests
==================
These tests check the integration of various modules used to complete a full analysis.

test_api docu
--------------
Tests the internal API of HELPR modules.

.. automodule:: helpr.tests.integration_tests.test_api
    :members:
    :show-inheritance:

test_plots docu
----------------
Tests HELPR plotting functions for visual output consistency.

.. automodule:: helpr.tests.integration_tests.test_plots
    :members:
    :show-inheritance:

test_postprocessing docu
-------------------------
Tests postprocessing utilities for simulation output.

.. automodule:: helpr.tests.integration_tests.test_postprocessing
    :members:
    :show-inheritance:

test_stress_state_integration docu
-----------------------------------
Tests integration of stress state information throughout dependent modules.

.. automodule:: helpr.tests.integration_tests.test_stress_state_integration
    :members:
    :show-inheritance:

Verification Tests
===================
These tests validate HELPR's numerical predictions against known results or benchmarks.

test_verification_crack_growth_rate docu
-----------------------------------------
Verifies that computed crack growth rates match known reference data.

.. automodule:: helpr.tests.verification_tests.test_verification_crack_growth_rate
    :members:
    :show-inheritance: