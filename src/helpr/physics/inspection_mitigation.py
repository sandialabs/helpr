# Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

from __future__ import annotations

import numpy.random as npr
import numpy as np
import pandas as pd


class InspectionMitigation:
    """
    Inspection Mitigation - Determine when a pipe is inspected for cracks and mitigate cracks
    identified through inspection.

    Attributes
    ----------
    probability_of_detection
    detection_resolution
    inspection_frequency

    """
    def __init__(self,
                 probability_of_detection,
                 detection_resolution,
                 inspection_frequency):
        """
        Parameters
        ------------
        probability_of_detection : float
            Likelihood that an inspection will detect a crack.
        detection_resolution: float
            Minimum size of crack that inspection can identify 
            [0 - 1] as a percentage of total wall thickness.
        inspection_frequency: float
            Frequency at which the pipe is inspected, in number of cycles.

        """
        self.probability_of_detection = probability_of_detection
        self.detection_resolution = detection_resolution
        self.inspection_frequency = inspection_frequency

    def determine_inspection_schedule(self, cycle_count:pd.DataFrame)->tuple[int, np.array]:
        """
        Determines inspection schedule based based on inspection frequency
        and highest number cycle count in results.

        Parameters
        ----------
        cycle_count : pandas.DataFrame
            DataFrame of cycle count results.

        Returns
        -------
        number_of_inspections : int
            Total number of inspections.
        inspection_array : numpy.ndarray
            Array of cycle counts at each inspection time.

        """
        maximum_cycle_count = cycle_count.max().max()
        number_of_inspections = int(np.floor(maximum_cycle_count / self.inspection_frequency))
        inspection_array = np.arange(self.inspection_frequency,
                                     number_of_inspections*self.inspection_frequency+1,
                                     self.inspection_frequency)
        return number_of_inspections, inspection_array

    def determine_inspection_indices(self,
                                     cycle_count:pd.DataFrame,
                                     number_of_inspections:int,
                                     inspection_array:np.array)->pd.DataFrame:
        """Identifies indices corresponding to cycle counts of interest. 
        
        Parameters
        ----------
        cycle_count : pandas.DataFrame
            DataFrame of cycle count results.
        number_of_inspections : int
            Total number of inspections.
        inspection_array : numpy.ndarray
            Array of cycle counts at each inspection time.

        Returns
        -------
        inspection_indices : pandas.DataFrame
            Indices for cycle data corresponding to inspection times.

        """
        inspection_indices = {}
        for i in range(number_of_inspections):
            inspection_indices[i] = cycle_count.ge(inspection_array[i]).idxmax()

        inspection_indices = pd.DataFrame(inspection_indices).T
        inspection_indices.replace(0, np.nan, inplace=True)
        return inspection_indices


    def inspect_then_mitigate(self,
                              load_cycling:dict,
                              failure_criteria:np.array,
                              random_state=npr.default_rng())->tuple(dict, list):
        """Performs inspection and mitigation analysis on crack evolution results.

        Parameters
        ----------
        load_cycling : dict
            Analysis load cycling results.
        failure_criteria : numpy.ndarray
            Analysis failure criteria.
        random_state : numpy.random, optional
            Random state, defaults to standard numpy rng.

        Returns
        -------
        mitigated : list
            List of bool values for each sample indicating whether or not the failure was mitigated.
        mitigation : dict
            Dict of Series describing each sample's mitigation results.

        """
        crack_sizes = load_cycling['a/t']
        cycle_counts = load_cycling['Total cycles']

        number_of_inspections, inspection_array = \
            self.determine_inspection_schedule(cycle_counts)
        inspection_indices = \
            self.determine_inspection_indices(cycle_counts, number_of_inspections, inspection_array)
        mitigation = {}
        mitigated = []
        for i in crack_sizes:
            detectable = inspect_crack(inspection_indices[i],
                                       crack_sizes[i],
                                       failure_criteria[i],
                                       self.detection_resolution,
                                       inspection_array,
                                       cycle_counts[i])
            mitigation[i] = mitigate_crack(detectable,
                                           random_state,
                                           self.probability_of_detection)
            mitigated.append(any(mitigation[i]))

        return mitigated, mitigation


def inspect_crack(inspection_indices:pd.Series,
                  crack_size:pd.Series,
                  failure_criteria:float,
                  detection_resolution:float,
                  inspection_array:pd.DataFrame,
                  cycle_count:pd.DataFrame)->pd.Series:
    """Determines if inspected crack is detectable. """
    inspections = inspection_indices.dropna().astype(int)
    inspected_cracks = []
    for inspection_index, inspection_cycle in zip(inspections, inspection_array):
        inspected_cracks.append(np.interp(inspection_cycle,
                                          cycle_count[inspection_index-1:inspection_index+1],
                                          crack_size[inspection_index-1:inspection_index+1]))

    inspected_cracks = pd.Series(inspected_cracks,
                                 dtype='float')
    detectable = (inspected_cracks.ge(detection_resolution) \
                    & inspected_cracks.lt(failure_criteria))
    return detectable

def mitigate_crack(detectable:pd.Series,
                  random_state:np.random.Generator,
                  probability_of_detection:float)->pd.Series:
    """Determines if mitigation of a crack occurs. """
    detected = random_state.random(len(detectable))
    mitigation = (detected < probability_of_detection) & detectable
    return mitigation
