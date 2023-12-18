import sempler, sempler.generators
import numpy as np
import causalicp as icp

np.random.seed(12)


if __name__ == "__main__":
    # Generate a random graph and construct a linear-Gaussian SCM
    W = sempler.generators.dag_avg_deg(4, 2.5, 0.5, 2)
    scm = sempler.LGANM(W, (-1,1), (1,2))

    # Generate a sample for setting 1: Observational setting
    data = [scm.sample(n=100)]

    # Setting 2: Shift-intervention on X1
    data += [scm.sample(n=130, shift_interventions = {1: (3.1, 5.4)})]

    # Setting 3: Do-intervention on X2
    data += [scm.sample(n=98, do_interventions = {2: (-1, 3)})]

    # ICP
    result = icp.fit(data, 3, alpha=0.05, precompute=True, verbose=True, color=False)
    print(result)
    print(result.estimate)
    # {1}

    print(result.accepted_sets)
    # [{0, 1}, {1, 2}, {0, 1, 2}]

    print(result.rejected_sets)
    # [set(), {0}, {1}, {2}, {0, 2}]

    print(result.pvalues)
    # {0: 0.8433000000649277, 1: 8.374476052441259e-08, 2: 0.7330408066181638, 3: nan}

    print(result.conf_intervals)
    # array([[0.        , 0.57167295, 0.        ,        nan],
    #        [2.11059461, 0.7865869 , 3.87380337,        nan]])