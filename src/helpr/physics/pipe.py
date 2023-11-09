# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

from helpr.utilities.parameter import Parameter


class Pipe:
    """Class defining physical Pipe properties.
    
    Attributes
    ----------
    outer_diameter 
    wall_thickness
    pipe_avg_radius
    inner_diameter
    
    """
    def __init__(self,
                 outer_diameter,
                 wall_thickness,
                 sample_size=1):
        """
        Parameters
        --------
        outer_diameter : float
            Outer diameter of the pipe.
        wall_thickness : float
            Thickness of the pipe wall.
        sample_size : int
            Analysis sample size.
        
        """
        self.outer_diameter = Parameter('outer_diameter',
                                        outer_diameter,
                                        lower_bound=0,
                                        size=sample_size)
        self.wall_thickness = Parameter('wall_thickness',
                                        wall_thickness,
                                        lower_bound=0,
                                        upper_bound=self.outer_diameter/2,
                                        size=sample_size)
        self.pipe_avg_radius = self.calc_average_radius()
        self.inner_diameter = self.calc_inner_diameter()

    def calc_average_radius(self):
        """Calculates average pipe radius. """
        return (self.outer_diameter - self.wall_thickness)/2

    def calc_inner_diameter(self):
        """Calculates inner diameter. """
        return self.outer_diameter - 2*self.wall_thickness

    def get_single_pipe(self, sample_index):
        """Returns single pipe instance.

        Parameters
        ----------
        sample_index : int
            Index of requested pipe instance.

        Returns
        -------
        Pipe
            Single pipe instance.
        
        """
        outer_diameter = self.outer_diameter[sample_index] \
            if len(self.outer_diameter) > sample_index else self.outer_diameter
        wall_thickness = self.wall_thickness[sample_index] \
            if len(self.wall_thickness) > sample_index else self.wall_thickness
        return Pipe(outer_diameter=outer_diameter,
                    wall_thickness=wall_thickness,
                    sample_size=1)
