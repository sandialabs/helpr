# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

from __future__ import annotations

# from multiprocessing.pool import Pool
import numpy.random as npr
import numpy as np
# import multiprocessing as mp


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
        Initialize inspection and mitigation parameters.

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


    def inspect_then_mitigate(self,
                              load_cycling:list,
                              failure_criteria:np.array,
                              random_state=npr.default_rng())->list:
        """
        Perform inspection and mitigation analysis on crack evolution results.

        Parameters
        ----------
        load_cycling : list
            Analysis load cycling results.
        failure_criteria : numpy.ndarray
            Analysis failure criteria.
        random_state : numpy.random, optional
            Random state, defaults to standard numpy rng.

        Returns
        -------
        mitigated_cracks : list
            List of bool values for each sample indicating whether or not the failure was mitigated.
        """
        mitigated_cracks = []
        for sample, single_evolution in enumerate(load_cycling):
            cycle_counts = single_evolution['Total cycles']
            crack_sizes = single_evolution['a/t']

            inspection_schedule = self.determine_inspection_schedule(cycle_counts,
                                                                  self.inspection_frequency)

            detection_state = \
                self.inspect_crack(inspection_schedule,
                                   crack_sizes,
                                   failure_criteria[sample],
                                   self.detection_resolution,
                                   cycle_counts)

            mitigation_state = self.mitigate_crack(detection_state,
                                                   random_state,
                                                   self.probability_of_detection)

            cycles_till_mitigation = self.count_inspections_until_mitigated(mitigation_state,
                                                                           inspection_schedule)

            mitigated_cracks.append(cycles_till_mitigation)

        return mitigated_cracks

        # TODO : Parallel version appears to be less computationally efficient than loop
        # instance_data = []
        # for sample, single_evolution in enumerate(load_cycling):
        #     instance_data.append((single_evolution,
        #                           failure_criteria[sample],
        #                           self.inspection_frequency,
        #                           self.detection_resolution,
        #                           self.probability_of_detection,
        #                           random_state))

        # # Initialize pool
        # n_cpu = mp.cpu_count()
        # with Pool(processes=n_cpu) as pool:
        #     mitigated_cracks = pool.starmap(self.inspect_mitigate_calculation, instance_data)

        # return mitigated_cracks

    # @staticmethod
    # def inspect_mitigate_calculation(single_evolution,
    #                                  failure_criteria,
    #                                  inspection_frequency,
    #                                  detection_resolution,
    #                                  probability_of_detection,
    #                                  random_state):
    #     '''Performs inspection and mitigation calculations for single crack evolution'''
    #     cycle_counts = single_evolution['Total cycles']
    #     crack_sizes = single_evolution['a/t']

    #     inspection_array =\
    #         InspectionMitigation.determine_inspection_schedule(cycle_counts,
    #                                                            inspection_frequency)

    #     detectable = InspectionMitigation.inspect_crack(inspection_array,
    #                                                     crack_sizes,
    #                                                     failure_criteria,
    #                                                     detection_resolution,
    #                                                     cycle_counts)

    #     mitigation = InspectionMitigation.mitigate_crack(detectable,
    #                                                      random_state,
    #                                                      probability_of_detection)
    #     return mitigation


    @staticmethod
    def determine_inspection_schedule(cycle_count:list, inspection_frequency)->np.array:
        """
        Determines the cycle counts where inspection occurs. 

        Parameters
        ----------
        cycle_count : list
            List of total cycle values for a single sample.
        inspection_frequency : float
            Frequency (in cycles) at which inspections are performed.

        Returns
        -------
        np.ndarray
            Array of cycle numbers when inspections occur.
        """
        maximum_cycle_count = max(cycle_count)
        inspection_array = np.arange(inspection_frequency,
                                     maximum_cycle_count+1,
                                     inspection_frequency)
        return inspection_array

    @staticmethod
    def inspect_crack(inspection_schedule: list,
                      crack_size: list,
                      failure_criteria: float,
                      detection_resolution: float,
                      cycle_count: list) -> tuple[int, np.ndarray]:
        """
        Simulates an inspection of a pipe to determine the number of inspections
        where a crack is detectable but not failed yet,
        and returns an array indicating the state of the crack for each inspection.

        Parameters
        ----------
        inspection_schedule : list
            Cycle numbers at which inspections occur.
        crack_size : list
            Crack size (a/t) values corresponding to cycle_count.
        failure_criteria : float
            Crack size threshold for failure (a/t).
        detection_resolution : float
            Crack size threshold for detectability (a/t).
        cycle_count : list
            Total cycles corresponding to crack sizes.

        Returns
        -------
        np.ndarray
            Array of inspection states: 'Not Detectable', 'Detectable', or 'Failed'.
        """

        # Interpolate crack sizes for all inspection occurrences
        interpolated_crack_sizes = np.interp(inspection_schedule, cycle_count, crack_size)

        # Create a boolean mask for when the crack is detectable
        detectable_mask = interpolated_crack_sizes >= detection_resolution

        # Create a boolean mask for when the crack reached the failure criteria
        failed_crack_mask = interpolated_crack_sizes >= failure_criteria

        # Create an array to indicate the state of the crack for each inspection
        # Marking of all cracks defaults to not detectable
        state_array = np.full(len(inspection_schedule), 'Not Detectable', dtype=object)

        # Update the state array based on the masks
        state_array[detectable_mask] = 'Detectable'  # Mark detectable cracks
        state_array[failed_crack_mask] = 'Failed'  # Mark failed cracks

        return state_array

    @staticmethod
    def mitigate_crack(state_array: np.ndarray,
                       random_state: np.random.Generator,
                       probability_of_detection: float) -> None:
        """
        Determines if mitigation of a crack occurs based on the state array 
        and probability of detection, and modifies the state_array directly 
        to reflect mitigation.

        Parameters
        ----------
        state_array : np.ndarray
            Array of inspection states ('Detectable', etc.).
        random_state : np.random.Generator
            Random generator for applying detection probability.
        probability_of_detection : float
            Probability of mitigating a detected crack.

        Returns
        -------
        np.ndarray
            Modified state array with entries possibly updated to 'Mitigated'.
        """

        # Create mitigation tracking array
        mitigation_array = state_array.copy()

        # Find indices of 'Detected' entries in the state_array
        detected_indices = np.where(state_array == 'Detectable')[0]

        # Generate random samples for the number of 'Detectable' entries
        detected_count = len(detected_indices)
        if detected_count > 0:
            detected_random_samples = random_state.random(detected_count)

            # Determine if mitigation occurs for each detected entry
            mitigation_occurred = detected_random_samples < probability_of_detection

            # Check if any mitigation occurred
            if np.any(mitigation_occurred):
                # Find the first index where mitigation occurred
                first_mitigation_index = detected_indices[np.where(mitigation_occurred)[0][0]]

                # Update the mitigation_array to 'Mitigated' for all subsequent entries
                mitigation_array[first_mitigation_index:] = 'Mitigated'

        return mitigation_array

    @staticmethod
    def count_inspections_until_mitigated(mitigation_state: np.array,
                                          inspection_schedule: list):
        """
        Determines the number of inspections until the first 'Mitigated' state.

        Parameters
        ----------
        mitigation_state : np.ndarray
            State labels after mitigation ('Mitigated', etc.).
        inspection_schedule : list
            Corresponding cycle numbers for each inspection.

        Returns
        -------
        int or float
            Cycle number when mitigation first occurred, or np.nan if none occurred.
        """
        # Iterate through the mitigation_array to find the first occurrence of 'Mitigated'
        for index, state in enumerate(mitigation_state):
            if state == 'Mitigated':
                # Return the number of cycles before 'Mitigated'
                return inspection_schedule[index]

        return np.nan  # Return np.nan if never 'Mitigated'
