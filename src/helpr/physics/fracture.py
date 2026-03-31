# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.


"""Module to hold fracture assessment diagram (FAD) functionality"""

import math
import numpy as np
#import multiprocessing as mp

from helpr.physics.stress_state import open_nc_table


class FailureAssessment:
    """
    Class for failure assessment calculations.
    
    Attributes
    ----------
    fracture_resistance
    yield_stress
    """

    def __init__(self,
                 fracture_resistance,
                 yield_stress,
                 fad_type):
        """
        Sets up failure assessment parameters.

        Parameters
        ------------
        fracture_resistance : float
            Fracture resistance of the pipe material.
        yield_stress : float
            Yield stress of the pipe material.
        fad_type : str
            A string that indicates the type of FAD diagram to create.
            It should have one of the following values:
            - simple
            - API 579-1 Level 2
        """
        self.fracture_resistance = fracture_resistance
        self.yield_stress = yield_stress
        self.fad_type = fad_type

    def assess_failure_state(self,
                             stress_intensity_factor,
                             reference_stress_solution):
        """
        Calculate location of failure assessment diagram.
        
        Parameters
        ----------
        stress_intensity_factor : float or np.ndarray
            Applied stress intensity factor (K).
        reference_stress_solution : float or np.ndarray
            Reference stress used for calculating load ratio.

        Returns
        -------
        tuple of float
            Tuple containing:
            - toughness_ratio : K / K_IC
            - load_ratio : σ_ref / σ_y
        """
        load_ratio = reference_stress_solution / self.yield_stress
        toughness_ratio = stress_intensity_factor / self.fracture_resistance

        return toughness_ratio, load_ratio

def determine_fad_values(fatigue_instance,
                         stress_state,
                         failure_assessment):
    """
    Determine the toughness and load ratios for a given fatigue instance based on the
    stress state and failure assessment.

    Parameters
    ----------
    fatigue_instance : dict
        A dictionary containing properties of the fatigue instance, including:

        - 'Kmax (MPa m^1/2)': The primary stress intensity factor.
        - 'Kres (MPa m^1/2)': The residual stress intensity factor.
        - 'a (m)': The crack depth.
        - 'c (m)': The crack length.

    stress_state : object
        An object representing the stress state, which should have the following attributes:

        - stress_intensity_method : str
            The method used to calculate stress intensity ('anderson' or 'api').
        - calc_stress_solution : callable
            A method to calculate the stress solution based on crack depth
            for the 'anderson' method.
        - calc_ref_stress_api : callable
            A method to calculate the reference stress for the 'api' method.

    failure_assessment : object
        An object that provides the method to assess the failure state.
        It should have the following method:

        - assess_failure_state(stress_intensity_factor, ref_stress_solution,
                               crack_depth, crack_length)

    Returns
    -------
    tuple
        A tuple containing:

        - toughness_ratio : float
            The calculated toughness ratio for the fatigue instance.
        - load_ratio : float
            The calculated load ratio for the fatigue instance.

    Raises
    ------
    ValueError
        If the specified stress intensity method is not 'anderson' or 'api'.
    """

    if failure_assessment.fad_type == 'simple':
        crack_depth = fatigue_instance['a (m)'].copy()
        # Simple combination of Kmax and Kres with no correction for plasticity
        stress_intensity_factor = np.array(fatigue_instance['Kmax (MPa m^1/2)']) +\
            np.array(fatigue_instance['Kres (MPa m^1/2)'])
        # To not include crack in considerations
        crack_depth[:] = [0 for _ in crack_depth]
        ref_stress_solution = []
        for i, crack_depth_instance in enumerate(crack_depth):
            stress_state.cycle_index = i
            ref_stress_solution.append(stress_state.calc_stress_solution(crack_depth_instance))
    elif failure_assessment.fad_type == 'API 579-1 Level 2':
        stress_intensity_factor = []
        ref_stress_solution = []
        for i in range(len(fatigue_instance['Kmax (MPa m^1/2)'])):
            stress_state.cycle_index = i
            ref_stress_solution.append(stress_state.calc_ref_stress_api(fatigue_instance['a (m)'][i]))
            crack_depth = fatigue_instance['a (m)'][i]
            crack_length = fatigue_instance['c (m)'][i] * 2
            k_prim_max = fatigue_instance['Kmax (MPa m^1/2)'][i]
            k_res = fatigue_instance['Kres (MPa m^1/2)'][i]
            yield_strength = failure_assessment.yield_stress
            # Calculate combined K max that includes K residual and plasticisity factor
            if k_res > 0:
                k_max = calc_combined_stress_intensity_factor(
                            k_primary=k_prim_max,
                            k_secondary_residual=k_res,
                            yield_strength=yield_strength,
                            primary_ref_stress=ref_stress_solution[-1],
                            crack_depth=crack_depth,
                            crack_length=crack_length)
            else:
                k_max = k_prim_max

            stress_intensity_factor.append(k_max)

        stress_intensity_factor = np.array(stress_intensity_factor)
    else:
        raise ValueError(f"FAD type specified as {failure_assessment.fad_type}"
                            + " but needs to be 'simple' or 'API 579-1 Level 2'")  

    toughness_ratio, load_ratio = \
        failure_assessment.assess_failure_state(stress_intensity_factor,
                                                np.array(ref_stress_solution))
    return toughness_ratio.tolist(), load_ratio.tolist()


def process_fatigue_instance(fatigue_instance, fracture_resistance, yield_stress, stress_state, fad_type):
    """
    Process a single fatigue instance to determine toughness and load ratios.

    Parameters
    ----------
    fatigue_instance : dict
        A dictionary representing the fatigue instance data.
    fracture_resistance : float
        The fracture resistance parameter for the failure assessment.
    yield_stress : float
        The yield stress parameter for the failure assessment.
    stress : float
        The stress state associated with the fatigue instance.
    fad_type : str
        Indicates the type of FAD to be computed.

    Returns
    -------
    dict
        The updated fatigue instance with calculated toughness and load ratios.
    """
    failure_assessment = FailureAssessment(fracture_resistance=fracture_resistance,
                                            yield_stress=yield_stress,
                                            fad_type=fad_type)

    toughness_ratio_inst, load_ratio_inst = determine_fad_values(fatigue_instance,
                                                                 stress_state,
                                                                 failure_assessment)

    # Update the fatigue_instance with the results
    fatigue_instance['Toughness ratio'] = toughness_ratio_inst
    fatigue_instance['Load ratio'] = load_ratio_inst

    return fatigue_instance


def calculate_failure_assessment(parameters,
                                 fatigue_results,
                                 stress_state,
                                 fad_type):
    """
    Calculates failure assessment values for load cycling results.
    
    Parameters
    ------------
    parameters : dict
        Analysis input parameters.
    fatigue_results : dict
        Analysis load cycling results.
    stress_state : GenericStressState
        Stress state specification.
    fad_type : str
        Type of FAD calcualtion to be completed.

    """
    args = [(fatigue_instance,
             parameters['fracture_resistance'][i],
             parameters['yield_strength'][i],
             stress_state[i],
             fad_type)
        for i, fatigue_instance in enumerate(fatigue_results)]

    # Initialize pool
    # n_cpu = mp.cpu_count()
    # with mp.Pool(processes=n_cpu) as pool:
    #     fatigue_results = pool.starmap(process_fatigue_instance, args)

    for arg_instance in args:
        process_fatigue_instance(*arg_instance)


def calc_combined_stress_intensity_factor(k_primary,
                                          k_secondary_residual,
                                          yield_strength,
                                          primary_ref_stress,
                                          crack_depth,
                                          crack_length):
    """
    Calculates the combined stress intensity factor based on the
    Level 2 Assessment procedure included in API 579-1
    Section 9.4.3.2.

    Parameters
    ----------
    k_primary : float
        Primary stress intensity factor.
    k_secondary_residual : float
        Secondary/residual stress intensity factor.
    yield_strength : float
        Material yield stress.
    primary_ref_stress : float
        Reference stress due to primary loading.
    crack_depth : float
        Crack depth (a) in meters.
    crack_length : float
        Crack length (2c) in meters.

    Returns
    -------
    float
        Combined maximum stress intensity factor.

    Notes
    -----
    Includes calculation of φ₀ and ζ influence factors from tabulated data.
    """

    def calc_zeta(zeta_table, load_ratio, X):
        """
        Interpolates values for the influence coefficient based
        on Table 9.3 provided in API 579-1. Returns a float
        corresponding to the zeta parameter.

        Parameters
        ----------
        zeta_table : xarray.DataArray
            Pre-loaded table of ζ values from API 579-1, indexed by load ratio and X.
        load_ratio : float
            Ratio of reference stress to yield stress (σ_ref / σ_y).
        X : float
            Dimensionless parameter defined as:  
            X = k_secondary_residual × (load_ratio / k_primary)

        Returns
        -------
        float
            Interpolated ζ (zeta) value from the table.
        """
        return float(zeta_table.interp(
            load_ratio=load_ratio, X=float(X)).values)

    def calc_phi_0(yield_stress, k_i_secondary_residual, a, c):
        """
        Calculate the φ₀ parameter used for modifying residual stress intensity.

        Uses plane strain assumptions from API 579-1 to compute an effective crack size
        and derive φ₀, an amplification factor due to residual stresses.

        Parameters
        ----------
        yield_stress : float
            Yield stress of the material [MPa].
        k_i_secondary_residual : float
            Secondary/residual stress intensity factor [MPa√m].
        a : float
            Crack depth (a) in meters.
        c : float
            Crack half-length (c) in meters.

        Returns
        -------
        float
            Maximum φ₀ value based on crack depth and crack length.

        Notes
        -----
        Returns the more conservative of the φ₀_a and φ₀_c values.
        """
        a_eff = (a + (1/(6*math.pi)) # plane strain conditions
            * (k_i_secondary_residual / yield_stress)**2)
        phi_0_a = math.sqrt(a_eff / a)
        c_eff = (c + (1/(6*math.pi))
            * (k_i_secondary_residual / yield_stress)**2)
        phi_0_c = math.sqrt(c_eff / c)

        # TODO: is taking the more critical phi_0 correct?
        # API is unclear about which one to use.
        return max(phi_0_a, phi_0_c)

    k_primary = 0 if k_primary < 0 else k_primary
    k_secondary_residual = (0 if k_secondary_residual < 0
                            else k_secondary_residual)

    phi_0 = calc_phi_0(yield_strength,
                        k_secondary_residual,
                        crack_depth,
                        crack_length / 2)
    k_secondary_residual = phi_0 * k_secondary_residual
    load_ratio = primary_ref_stress / yield_strength
    if k_primary == 0:
        phi = phi_0
    else:
        x = k_secondary_residual * (load_ratio / k_primary)
        zeta_table = open_nc_table('Table_9.3.nc')
        zeta = calc_zeta(zeta_table, load_ratio, x)
        phi = phi_0 * zeta

    return k_primary + phi*k_secondary_residual
