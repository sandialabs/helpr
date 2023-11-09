# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

from helpr.utilities.parameter import Parameter


class MaterialSpecification:
    """Class defining material specifications for base material and welds.
    
    Attributes
    ----------
    fracture_resistance
    yield_strength
    
    """
    def __init__(self,
                 yield_strength,
                 fracture_resistance,
                 sample_size=1):
        """
        Parameters
        ------------
        yield_strength : float
            Yield strength of the pipe material.
        fracture_resistance : float
            Fracture resistance of the pipe material.

        """
        self.yield_strength = Parameter('yield_strength',
                                        yield_strength,
                                        lower_bound=0,
                                        size=sample_size)
        self.fracture_resistance = Parameter('fracture_resistance',
                                             fracture_resistance,
                                             lower_bound=0,
                                             size=sample_size)

    def get_single_material(self, sample_index):
        """Returns single material specification from ensemble object.

        Parameters
        ----------
        sample_index : int
            Index of requested pipe instance.

        Returns
        -------
        MaterialSpecification
            Specification for the pipe instance.
        
        """
        single_yield_strength = self.yield_strength[sample_index] \
            if len(self.yield_strength) > sample_index else self.yield_strength
        single_fracture_resistance = self.fracture_resistance[sample_index] \
            if len(self.fracture_resistance) > sample_index else self.fracture_resistance
        return MaterialSpecification(yield_strength=single_yield_strength,
                                     fracture_resistance=single_fracture_resistance,
                                     sample_size=1)
