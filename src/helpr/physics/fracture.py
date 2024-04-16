# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

class FailureAssessment:
    """Class for failure assessment calculations.
    
    Attributes
    ----------
    fracture_resistance
    yield_stress
    
    """
    def __init__(self,
                 fracture_resistance,
                 yield_stress):
        """Sets up failure assessment parameters.

        Parameters
        ------------
        fracture_resistance : float
            Fracture resistance of the pipe material.
        yield_stress : float
            Yield stress of the pipe material.

        """
        self.fracture_resistance = fracture_resistance
        self.yield_stress = yield_stress

    def assess_failure_state(self,
                             stress_intensity_factor,
                             reference_stress_solution):
        """Calculates failure assessment variables.
        
        Parameters
        ----------
        stress_intensity_factor : pandas.Series
            Series of stress intensity factors from analysis results.
        reference_stress_solution : pandas.Series
            Series of reference stress solutions.

        Returns
        -------
        toughness_ratio : pandas.Series
            Ratio of stress intensity factors to fracture resistance.
        load_ratio : pandas.Series
            Ratio of reference stress solutions to yield stress.
            
        """
        toughness_ratio = stress_intensity_factor/self.fracture_resistance
        load_ratio = reference_stress_solution/self.yield_stress
        return toughness_ratio, load_ratio
