**Physics Documentation**
**************************

The physics modules in HELPR implement models for fracture mechanics, fatigue, materials, and environment-specific pipeline behaviors.

api docu
=========
Provides the public API for accessing HELPR physics models.

.. automodule:: helpr.api
    :members:
    :show-inheritance:

settings docu
==============
Monitors the state of crack evolution calculations.

.. automodule:: helpr.settings
    :members:
    :show-inheritance:

crack_growth docu 
==================
Implements fatigue crack growth models used for damage evolution.

.. automodule:: helpr.physics.crack_growth
    :members:
    :show-inheritance:

crack_initiation docu
======================
Models the initial formation of cracks under cyclic loading.

.. automodule:: helpr.physics.crack_initiation
    :members:
    :show-inheritance:

environment docu
=================
Represents environmental effects (e.g., corrosion) on pipeline behavior.

.. automodule:: helpr.physics.environment
    :members:
    :show-inheritance:

fracture docu
==============
Implements fracture toughness models and failure prediction logic.

.. automodule:: helpr.physics.fracture
    :members:
    :show-inheritance:
 
inspection_mitigation docu
===========================
Models inspection intervals, mitigation strategies, and defect detection.

.. automodule:: helpr.physics.inspection_mitigation
    :members:
    :show-inheritance:

life_assessment docu 
=====================
Handles the evolution of crack growth across loading cycles.

.. automodule:: helpr.physics.life_assessment
    :members:
    :show-inheritance:

material docu
==============
Defines material behavior, fatigue properties, and failure thresholds.

.. automodule:: helpr.physics.material
    :members:
    :show-inheritance:

pipe docu
==========
Defines pipe geometry, dimensions, and structural attributes.

.. automodule:: helpr.physics.pipe
    :members:
    :show-inheritance: 

residual_stress docu
=====================
Defines the residual stress state.

.. automodule:: helpr.physics.residual_stress
    :members:
    :show-inheritance:

stress_state docu
==================
Handles applied loads, internal pressure, and stress calculations.

.. automodule:: helpr.physics.stress_state
    :members:
    :show-inheritance: