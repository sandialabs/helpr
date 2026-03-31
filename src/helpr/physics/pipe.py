# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

from helpr.utilities.parameter import Parameter


class Pipe:
    """
    Class defining physical Pipe properties.
    
    Attributes
    ----------
    outer_diameter 
    wall_thickness
    pipe_avg_radius
    inner_diameter
    """

    def __init__(self,
                 outer_diameter,
                 wall_thickness):
        """
        Initialize the pipe with geometric parameters.

        Parameters
        --------
        outer_diameter : float, m
            Outer diameter of the pipe.
        wall_thickness : float, m
            Thickness of the pipe wall.
        """
        self.outer_diameter = Parameter('outer_diameter',
                                        value=outer_diameter,
                                        lower_bound=0)
        self.wall_thickness = Parameter('wall_thickness',
                                        value=wall_thickness,
                                        lower_bound=0,
                                        upper_bound=self.outer_diameter/2)
        self.pipe_avg_radius = self.calc_average_radius()
        self.inner_diameter = self.calc_inner_diameter()

    def calc_average_radius(self):
        """
        Calculates the average pipe radius.

        Returns
        -------
        float
            The average radius of the pipe.
        """
        return (self.outer_diameter - self.wall_thickness)/2

    def calc_inner_diameter(self):
        """
        Calculates the inner diameter of the pipe.

        Returns
        -------
        float
            The inner diameter of the pipe.
        """
        return self.outer_diameter - 2*self.wall_thickness

    def calc_t_over_r(self):
        """
        Calculates the ratio of wall thickness to inner radius.

        Returns
        -------
        float
            The ratio of wall thickness to inner radius.
        """
        return self.wall_thickness/(self.inner_diameter/2)
