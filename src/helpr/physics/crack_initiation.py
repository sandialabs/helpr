# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

from helpr.utilities.parameter import Parameter


class DefectSpecification:
    """
    Definition of crack initiation physics.

    Attributes
    -----------
    flaw_depth
    flaw_length
    surface
    location_factor
    """
    def __init__(self,
                 flaw_depth,
                 flaw_length,
                 surface='inside',
                 location_factor=1):
        """
        Creates initial flaw specification.
    
        Parameters
        ------------
        flaw_depth : float
            Initial crack depth, % of pipe wall thickness.
        flaw_length : float
            Initial crack length, in meters
        surface : str, optional
            Specification on whether the defect is on the inside or outside pipe surface.
            Valid options are `'inside'` or `'outside'`, defaults to `'inside'`
        location_factor: int
            Parameter used in allowable stress calculation, defaults to 1.
        
        Raises
        ------
        ValueError
            If `surface` is not specified as 'inside' or 'outside'.
        """
        self.flaw_depth = Parameter(name='flaw_depth',
                                    value=flaw_depth,
                                    lower_bound=0,
                                    upper_bound=100)
        self.flaw_length = Parameter('flaw_length',
                                     value=flaw_length,
                                     lower_bound=0)
        if surface.lower() in ['inside', 'outside']:
            self.surface = surface.lower()
        else:
            raise ValueError('surface must be specified as `inside` or `outside`')
        self.location_factor = Parameter('location_factor',
                                         value=location_factor)
