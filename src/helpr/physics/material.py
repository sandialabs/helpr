# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

from helpr.utilities.parameter import Parameter


class MaterialSpecification:
    """
    Class defining material specifications for base material and welds.
    
    Attributes
    ----------
    yield_strength
    fracture_resistance
    """
    
    def __init__(self,
                 yield_strength,
                 fracture_resistance):
        """
        Initializes the material specification parameters.

        Parameters
        ----------
        yield_strength : float
            Yield strength of the pipe material.
        fracture_resistance : float
            Fracture resistance of the pipe material.
        """
        self.yield_strength = Parameter('yield_strength',
                                        value=yield_strength,
                                        lower_bound=0)
        self.fracture_resistance = Parameter('fracture_resistance',
                                             value=fracture_resistance,
                                             lower_bound=0)
