# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

from helpr.utilities.parameter import Parameter


class DefectSpecification:
    """Definition of crack initiation physics.

    Attributes
    -----------
    flaw_depth
    flaw_length
    location_factor
    a_over_c

    """
    def __init__(self,
                 flaw_depth,
                 flaw_length,
                 sample_size=1,
                 location_factor=1):
        """Creates initial flaw specification.
    
        Parameters
        ------------
        flaw_depth : list
            List of initial crack depths, % of pipe wall thickness.
        flaw_length : list
            List of initial crack lengths, in meters
        sample_size: int, optional
            Study sample size, defaults to 1.
        location_factor: int
            Parameter used in allowable stress calculation, defaults to 1.
        
        """
        self.flaw_depth = Parameter(name='flaw_depth',
                                   values=flaw_depth,
                                   lower_bound=0,
                                   upper_bound=100,
                                   size=sample_size)
        self.flaw_length = Parameter('flaw_length',
                                     flaw_length,
                                     lower_bound=0)
        self.location_factor = Parameter('location_factor',
                                         location_factor,
                                         size=sample_size)
        self.a_over_c = None  # set by stress module

    def set_a_over_c(self, flaw_depth):
        """
        Sets the a/c (depth/length) value using crack depth.
        Currently assumed to be a constant ratio.
        """
        self.a_over_c = flaw_depth/(self.flaw_length/2)

    def get_single_defect(self, sample_index):
        """Returns single defect instance from ensemble defect object.

        Parameters
        ----------
        sample_index : int
            Index of requested pipe instance.

        Returns
        -------
        DefectSpecification
            Specification for the pipe instance.
        
        """
        single_flaw_depth = self.flaw_depth[sample_index] \
            if len(self.flaw_depth) > sample_index else self.flaw_depth
        single_flaw_length = self.flaw_length[sample_index] \
            if len(self.flaw_length) > sample_index else self.flaw_length
        single_location_factor = self.location_factor[sample_index] \
            if len(self.location_factor) > sample_index else self.location_factor
        return DefectSpecification(flaw_depth=single_flaw_depth,
                                   flaw_length=single_flaw_length,
                                   location_factor=single_location_factor,
                                   sample_size=1)
