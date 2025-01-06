# Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
import numpy as np

from probabilistic.capabilities import sampling as Sampling
from probabilistic.capabilities import uncertainty_definitions as Uncertainty

class SamplingTestCase(unittest.TestCase):
    """ class for unit tests of sampling module """

    def setUp(self):
        """ function to specify common sampling inputs """
        self.parameters = {}
        self.parameters['var_a1'] = \
            Uncertainty.NormalDistribution(name='var_a1',
                                           nominal_value=1,
                                           mean=.5,
                                           std_deviation=2,
                                           uncertainty_type='aleatory')
        self.parameters['var_a2'] = \
            Uncertainty.TruncatedNormalDistribution(name='var_a2',
                                           nominal_value=1,
                                           mean=.57,
                                           std_deviation=1,
                                           lower_bound=0,
                                           upper_bound=2,
                                           uncertainty_type='aleatory')
        self.parameters['var_a3'] = \
            Uncertainty.TruncatedLognormalDistribution(name='var_a3',
                                           nominal_value=1,
                                           mu=3,
                                           sigma=.17,
                                           lower_bound=0.001,
                                           upper_bound=40,
                                           uncertainty_type='aleatory')
        self.parameters['var_e1'] = \
            Uncertainty.UniformDistribution(name='var_e1',
                                            nominal_value=0.5,
                                            lower_bound=0,
                                            upper_bound=1,
                                            uncertainty_type='epistemic')
        self.parameters['var_e2'] = \
            Uncertainty.BetaDistribution(name='var_e2',
                                            nominal_value=1,
                                            a=1,
                                            b=2,
                                            loc=0,
                                            scale=1,
                                            uncertainty_type='epistemic')
        self.parameters['var_e3'] = \
            Uncertainty.NormalDistribution(name='var_e3',
                                           nominal_value=1,
                                           mean=.5,
                                           std_deviation=4,
                                           uncertainty_type='epistemic')

        self.parameters['var_d1'] = \
            Uncertainty.DeterministicCharacterization(name='var_d1',
                                                      value=42)

        self.random_state = np.random.default_rng(123)

    def tearDown(self):
        """teardown function"""

    def test_random_sampling_study(self):
        """unit test of random MC sampling study"""
        number_of_aleatory_samples = 3
        number_of_epistemic_samples = 2
        test_study = Sampling.RandomStudy(number_of_aleatory_samples=number_of_aleatory_samples,
                                          number_of_epistemic_samples=number_of_epistemic_samples,
                                          random_state=self.random_state)
        test_study.add_variables(input_parameters=self.parameters)
        study_samples = test_study.create_variable_sample_sheet()

        self.assertEqual(len(study_samples['var_a1']),
                         number_of_aleatory_samples*number_of_epistemic_samples)
        self.assertEqual(len(study_samples['var_e1']),
                         number_of_aleatory_samples*number_of_epistemic_samples)
        self.assertEqual(study_samples['var_a2'][0],
                         study_samples['var_a2'][number_of_aleatory_samples])
        self.assertNotEqual(study_samples['var_a2'][0],
                            study_samples['var_a2'][number_of_aleatory_samples-1])
        self.assertEqual(study_samples['var_e3'][0],
                         study_samples['var_e3'][number_of_aleatory_samples-1])
        self.assertNotEqual(study_samples['var_e3'][0],
                            study_samples['var_e3'][number_of_aleatory_samples])
        self.assertEqual(len(np.unique(study_samples['var_a2'])), number_of_aleatory_samples)
        self.assertEqual(len(np.unique(study_samples['var_e2'])), number_of_epistemic_samples)
        self.assertEqual(test_study.get_total_double_loop_sample_size(),
                         number_of_aleatory_samples*number_of_epistemic_samples)
        self.assertEqual(len(test_study.get_parameter_names()), 7)
        self.assertEqual(len(test_study.get_uncertain_parameter_names()), 6)
        
        self.assertTrue((2 > study_samples['var_a2']).all() and (study_samples['var_a2'] > 0).all())
        self.assertTrue((40 > study_samples['var_a3']).all() and (study_samples['var_a3'] > 0.001).all())

    def test_lhs_sampling_study(self):
        """unit test of LHS study"""
        number_of_aleatory_samples = 3
        number_of_epistemic_samples = 2
        test_study = Sampling.LHSStudy(number_of_aleatory_samples=number_of_aleatory_samples,
                                       number_of_epistemic_samples=number_of_epistemic_samples,
                                       random_state=self.random_state)
        test_study.add_variables(input_parameters=self.parameters)
        study_samples = test_study.create_variable_sample_sheet()

        self.assertEqual(len(study_samples['var_a1']),
                         number_of_aleatory_samples*number_of_epistemic_samples)
        self.assertEqual(len(study_samples['var_e1']),
                         number_of_aleatory_samples*number_of_epistemic_samples)
        self.assertEqual(study_samples['var_a2'][0],
                         study_samples['var_a2'][number_of_aleatory_samples])
        self.assertNotEqual(study_samples['var_a2'][0],
                            study_samples['var_a2'][number_of_aleatory_samples-1])
        self.assertEqual(study_samples['var_e3'][0],
                         study_samples['var_e3'][number_of_aleatory_samples-1])
        self.assertNotEqual(study_samples['var_e3'][0],
                            study_samples['var_e3'][number_of_aleatory_samples])
        self.assertEqual(len(np.unique(study_samples['var_a2'])),
                         number_of_aleatory_samples)
        self.assertEqual(len(np.unique(study_samples['var_e2'])),
                         number_of_epistemic_samples)

    def test_sensitivity_study(self):
        """unit test of sensitivity study"""
        number_of_aleatory_samples = 3
        number_of_epistemic_samples = 2
        test_study = \
            Sampling.SensitivityStudy(number_of_aleatory_samples=number_of_aleatory_samples,
                                      number_of_epistemic_samples=number_of_epistemic_samples,
                                      random_state=self.random_state)
        test_study.add_variables(input_parameters=self.parameters)

        bad_var = Uncertainty.NormalDistribution(name='var_e3',
                                                 nominal_value=1,
                                                 mean=.5,
                                                 std_deviation=4,
                                                 uncertainty_type='bad specification')

        input_parameters = {'var_a1': self.parameters['var_a1'], 'bad_var': bad_var}
        with self.assertRaises(ValueError):
            test_study.add_variables(input_parameters=input_parameters)

    def test_one_at_a_time_sensitivity_study(self):
        """unit test of sensitivity study"""
        number_of_aleatory_samples = 3
        number_of_epistemic_samples = 2
        test_study = \
            Sampling.OneAtATimeSensitivityStudy(number_of_aleatory_samples=number_of_aleatory_samples,
                                                number_of_epistemic_samples=number_of_epistemic_samples,
                                                random_state=self.random_state)
        test_study.add_variables(input_parameters=self.parameters)
        study_samples = test_study.create_variable_sample_sheet()
        number_of_aleatory_variables = \
            test_study.calc_number_of_variables(test_study.aleatory_variables)
        number_of_epistemic_variables = \
            test_study.calc_number_of_variables(test_study.epistemic_variables)

        self.assertEqual(len(study_samples['var_a1']),
                         number_of_aleatory_samples*number_of_aleatory_variables +
                         number_of_epistemic_samples*number_of_epistemic_variables)
        self.assertEqual(len(np.unique(study_samples['var_a2'])),
                         number_of_aleatory_samples + 1)  # +1 for nominal
        self.assertEqual(len(np.unique(study_samples['var_e2'])),
                         number_of_epistemic_samples + 1)

    def test_bounding_sensitivity_study(self):
        """unit test of sensitivity study"""
        number_of_aleatory_samples = 0
        number_of_epistemic_samples = 0
        test_study = \
            Sampling.BoundingStudy(number_of_aleatory_samples=number_of_aleatory_samples,
                                   number_of_epistemic_samples=number_of_epistemic_samples,
                                   random_state=self.random_state)
        test_study.add_variables(input_parameters=self.parameters)
        study_samples = test_study.create_variable_sample_sheet()
        number_of_aleatory_variables = \
            test_study.calc_number_of_variables(test_study.aleatory_variables)
        number_of_epistemic_variables = \
            test_study.calc_number_of_variables(test_study.epistemic_variables)

        self.assertEqual(len(study_samples['var_a1']),
                         2*(number_of_aleatory_variables + number_of_epistemic_variables))
        self.assertEqual(len(np.unique(study_samples['var_a2'])), 2 + 1)  # +1 for nominal
        self.assertEqual(len(np.unique(study_samples['var_e2'])), 2 + 1)

    def test_no_epistemic_variables(self):
        """unit test of random MC sampling with no epistemic variables specified"""
        number_of_aleatory_samples = 3
        test_study = Sampling.RandomStudy(number_of_aleatory_samples=number_of_aleatory_samples,
                                          number_of_epistemic_samples=0,
                                          random_state=self.random_state)
        test_study.add_variables({'var_a1': self.parameters['var_a1'],
                                  'var_a2': self.parameters['var_a2']})
        study_samples = test_study.create_variable_sample_sheet()

        self.assertEqual(len(study_samples['var_a1']), number_of_aleatory_samples)
        self.assertEqual(len(np.unique(study_samples['var_a2'])), number_of_aleatory_samples)

    def test_no_aleatory_variables(self):
        """unit test of random MC sampling with no aleatoric variables specified"""
        number_of_epistemic_samples = 2
        test_study = Sampling.RandomStudy(number_of_aleatory_samples=0,
                                          number_of_epistemic_samples=number_of_epistemic_samples,
                                          random_state=self.random_state)
        test_study.add_variables({'var_e1': self.parameters['var_e1'],
                                  'var_e2': self.parameters['var_e2'],
                                  'var_e3': self.parameters['var_e3']})

        study_samples = test_study.create_variable_sample_sheet()

        self.assertEqual(len(study_samples['var_e1']), number_of_epistemic_samples)
        self.assertEqual(len(np.unique(study_samples['var_e2'])), number_of_epistemic_samples)

    def test_incorrect_uncertainty_type_specified(self):
        """unit test of random MC sampling with no epistemic variables specified"""
        number_of_aleatory_samples = 3
        test_study = Sampling.RandomStudy(number_of_aleatory_samples=number_of_aleatory_samples,
                                          number_of_epistemic_samples=0,
                                          random_state=self.random_state)
        var_a1 = Uncertainty.NormalDistribution(name='var_a1',
                                                nominal_value=1,
                                                mean=.5,
                                                std_deviation=2,
                                                uncertainty_type='random')

        with self.assertRaises(ValueError):
            test_study.add_variables({'var_a1': var_a1})

    def test_no_epistemic_samples_specified(self):
        """unit test for error message when epistemic variable specified with
        no epistemic samples"""
        test_study = Sampling.RandomStudy(number_of_aleatory_samples=0,
                                          number_of_epistemic_samples=0,
                                          random_state=self.random_state)
        var_e1 = Uncertainty.NormalDistribution(name='var_e1',
                                                nominal_value=1,
                                                mean=.5,
                                                std_deviation=2,
                                                uncertainty_type='epistemic')

        with self.assertRaises(ValueError) as error_msg:
            test_study.add_variables({'var_e1': var_e1})

        self.assertEqual(str(error_msg.exception), "Specification of epistemic samples or " +
                         "distribution without the other")

    def test_no_aleatory_samples_specified(self):
        """unit test for error message when aleatory variable specified with no aleatory samples"""
        test_study = Sampling.RandomStudy(number_of_aleatory_samples=0,
                                          number_of_epistemic_samples=0,
                                          random_state=self.random_state)
        var_a1 = Uncertainty.NormalDistribution(name='var_a1',
                                                nominal_value=1,
                                                mean=.5,
                                                std_deviation=2,
                                                uncertainty_type='aleatory')

        with self.assertRaises(ValueError) as error_msg:
            test_study.add_variables({'var_a1': var_a1})

        self.assertEqual(str(error_msg.exception), "Specification of aleatory samples or " +
                         "distribution without the other")

    def test_no_epistemic_variable_specified(self):
        """unit test for error message when epistemic samples specified with
        no epistemic variables"""
        test_study = Sampling.RandomStudy(number_of_aleatory_samples=1,
                                          number_of_epistemic_samples=1,
                                          random_state=self.random_state)
        var_a1 = Uncertainty.NormalDistribution(name='var_a1',
                                                nominal_value=1,
                                                mean=.5,
                                                std_deviation=2,
                                                uncertainty_type='aleatory')

        with self.assertRaises(ValueError) as error_msg:
            test_study.add_variables({'var_a1': var_a1})

        self.assertEqual(str(error_msg.exception), "Specification of epistemic samples or " +
                         "distribution without the other")

    def test_no_aleatory_variable_specified(self):
        """unit test for error message when epistemic samples specified with
        no aleatory variables"""
        test_study = Sampling.RandomStudy(number_of_aleatory_samples=1,
                                          number_of_epistemic_samples=1,
                                          random_state=self.random_state)
        var_e1 = Uncertainty.NormalDistribution(name='var_e1',
                                                nominal_value=1,
                                                mean=.5,
                                                std_deviation=2,
                                                uncertainty_type='epistemic')

        with self.assertRaises(ValueError) as error_msg:
            test_study.add_variables({'var_e1': var_e1})

        self.assertEqual(str(error_msg.exception), "Specification of aleatory samples or " +
                         "distribution without the other")

    def test_distributions_with_same_name(self):
        """unit test for error message when two variables are specified with same name"""
        test_study = Sampling.RandomStudy(number_of_aleatory_samples=1,
                                          number_of_epistemic_samples=1,
                                          random_state=self.random_state)
        var_e1 = Uncertainty.NormalDistribution(name='var_e1',
                                                nominal_value=1,
                                                mean=.5,
                                                std_deviation=2,
                                                uncertainty_type='epistemic')
        var_a1 = Uncertainty.NormalDistribution(name='var_e1',
                                                nominal_value=1,
                                                mean=.5,
                                                std_deviation=2,
                                                uncertainty_type='epistemic')

        with self.assertRaises(ValueError):
            test_study.add_variables({'var_e1': var_e1,
                                      'var_a1': var_a1})

        test_study = Sampling.RandomStudy(number_of_aleatory_samples=1,
                                          number_of_epistemic_samples=1,
                                          random_state=self.random_state)
        var_e1 = Uncertainty.NormalDistribution(name='var_e1',
                                                nominal_value=1,
                                                mean=.5,
                                                std_deviation=2,
                                                uncertainty_type='epistemic')
        var_a1 = Uncertainty.NormalDistribution(name='var_e1',
                                                nominal_value=1,
                                                mean=.5,
                                                std_deviation=2,
                                                uncertainty_type='aleatory')

        with self.assertRaises(ValueError):
            test_study.add_variables({'var_e1': var_e1,
                                      'var_a1': var_a1})

    def test_monte_carlo_random_seed_specification(self):
        """unit test for random seed specification"""
        samples = 5
        seed_1 = 123
        seed_2 = 321
        test_study_1 = Sampling.RandomStudy(number_of_aleatory_samples=samples,
                                            number_of_epistemic_samples=samples,
                                            random_state=np.random.default_rng(seed_1))

        test_study_1.add_variables(input_parameters=self.parameters)
        study_samples_1 = test_study_1.create_variable_sample_sheet()

        test_study_2 = Sampling.RandomStudy(number_of_aleatory_samples=samples,
                                            number_of_epistemic_samples=samples,
                                            random_state=np.random.default_rng(seed_1))
        test_study_2.add_variables(input_parameters=self.parameters)
        study_samples_2 = test_study_2.create_variable_sample_sheet()

        test_study_3 = Sampling.RandomStudy(number_of_aleatory_samples=samples,
                                            number_of_epistemic_samples=samples,
                                            random_state=np.random.default_rng(seed_2))
        test_study_3.add_variables(input_parameters=self.parameters)
        study_samples_3 = test_study_3.create_variable_sample_sheet()

        self.assertIsNone(np.testing.assert_array_equal(study_samples_1['var_a1'],
                                                        study_samples_2['var_a1']))
        self.assertIsNone(np.testing.assert_array_equal(study_samples_1['var_e1'],
                                                        study_samples_2['var_e1']))

        with self.assertRaises(Exception):
            np.testing.assert_array_equal(study_samples_1['var_a2'], study_samples_3['var_a2'])

        with self.assertRaises(Exception):
            np.testing.assert_array_equal(study_samples_1['var_e2'], study_samples_3['var_e2'])

    def test_lhs_random_seed_specification(self):
        """unit test for random seed specification"""
        samples = 5
        seed_1 = 123
        seed_2 = 321
        test_study_1 = Sampling.LHSStudy(number_of_aleatory_samples=samples,
                                         number_of_epistemic_samples=samples,
                                         random_state=np.random.default_rng(seed_1 ))

        test_study_1.add_variables(input_parameters=self.parameters)
        study_samples_1 = test_study_1.create_variable_sample_sheet()

        test_study_2 = Sampling.LHSStudy(number_of_aleatory_samples=samples,
                                         number_of_epistemic_samples=samples,
                                         random_state=np.random.default_rng(seed_1 ))
        test_study_2.add_variables(input_parameters=self.parameters)
        study_samples_2 = test_study_2.create_variable_sample_sheet()

        test_study_3 = Sampling.LHSStudy(number_of_aleatory_samples=samples,
                                         number_of_epistemic_samples=samples,
                                         random_state=np.random.default_rng(seed_2))
        test_study_3.add_variables(input_parameters=self.parameters)
        study_samples_3 = test_study_3.create_variable_sample_sheet()

        self.assertIsNone(np.testing.assert_array_equal(study_samples_1['var_a1'],
                                                        study_samples_2['var_a1']))
        self.assertIsNone(np.testing.assert_array_equal(study_samples_1['var_e1'],
                                                        study_samples_2['var_e1']))

        with self.assertRaises(Exception):
            np.testing.assert_array_equal(study_samples_1['var_a2'], study_samples_3['var_a2'])

        with self.assertRaises(Exception):
            np.testing.assert_array_equal(study_samples_1['var_e2'], study_samples_3['var_e2'])

    def test_deterministic_parameter_specification(self):
        """unit test to check that deterministic variables are placed in sample sheet correctly"""
        number_of_aleatory_samples = 3
        number_of_epistemic_samples = 2
        test_study = Sampling.LHSStudy(number_of_aleatory_samples=number_of_aleatory_samples,
                                       number_of_epistemic_samples=number_of_epistemic_samples,
                                       random_state=self.random_state)
        test_study.add_variables(input_parameters=self.parameters)
        study_samples = test_study.create_variable_sample_sheet()
        self.assertTrue((self.parameters['var_d1'].value == study_samples['var_d1']).all())
        self.assertEqual(len(study_samples['var_d1']),
                         number_of_aleatory_samples*number_of_epistemic_samples)

if __name__ == '__main__':
    unittest.main()
