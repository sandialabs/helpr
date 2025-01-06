"""
Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.
"""

import time


def wait_for_analysis(testobj, n_complete=1, t_max=10):
    """ Guarded while-loop to sleep while pooled analysis completes. """
    while testobj.appform.thread._num_complete < n_complete:
        time.sleep(testobj.sleep_t)

        testobj.guard_t += 1
        if testobj.guard_t >= t_max:
            testobj.assertTrue(False)  # analysis is hanging, quit out of test

    time.sleep(testobj.delay_t)

