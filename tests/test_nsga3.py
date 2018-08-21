import json
import os
import unittest
from unittest.mock import MagicMock

import numpy as np

from pymoo.configuration import Configuration
from pymoo.model.population import Population
from pymoo.operators.survival.reference_line_survival import ReferenceLineSurvival, associate_to_niches
from pymoo.util.non_dominated_rank import NonDominatedRank


class NSGA3Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(os.path.join("resources", "hist.json"), encoding='utf-8') as f:
            cls.data = json.loads(f.read())

    def test_non_dominated_rank(self):
        for i, D in enumerate(self.data['hist']):
            _rank = NonDominatedRank().calc(np.array(D['cand_F']))
            rank = np.array(D['cand_rank']).astype(np.int) - 1
            is_equal = np.all(_rank == rank)
            self.assertTrue(is_equal)

    def test_run(self):

        ref_dirs = np.array(self.data['ref_dir'])
        survival = ReferenceLineSurvival(ref_dirs)

        D = self.data['hist'][0]
        pop = Population()
        pop.X = np.array(D['before_X'])
        pop.F = np.array(D['before_F'])
        survival.do(pop, pop.size())

        for i, D in enumerate(self.data['hist']):

            out = {}
            vars = {'out': out}

            pop = Population()
            pop.X = np.array(D['before_X'])
            pop.F = np.array(D['before_F'])

            off = Population()
            off.X = np.array(D['off_X'])
            off.F = np.array(D['off_F'])

            pop.merge(off)

            cand = Population()
            cand.X = np.array(D['cand_X'])
            cand.F = np.array(D['cand_F'])

            Configuration.rand.randint = MagicMock()
            Configuration.rand.randint.side_effect = D['rnd_niching']

            fronts = []
            ranks = np.array(D['cand_rank'])
            for r in np.unique(ranks):
                fronts.append(np.where(ranks == r)[0].tolist())

            NonDominatedRank.calc_as_fronts = MagicMock()
            NonDominatedRank.calc_as_fronts.return_value = fronts

            cand_copy = cand.copy()

            # necessary because only candidates are provided
            if survival.ideal_point is None:
                survival.ideal_point = np.min(pop.F, axis=0)
            else:
                survival.ideal_point = np.min(np.concatenate([survival.ideal_point[None, :], pop.F], axis=0), axis=0)


            survival.do(cand, pop.size() / 2, **vars)

            is_equal = np.all(survival.extreme_points == np.array(D['extreme']))
            self.assertTrue(is_equal)

            is_equal = np.all(survival.ideal_point == np.array(D['ideal']))
            self.assertTrue(is_equal)

            is_equal = np.all(np.abs(survival.intercepts - np.array(D['intercepts'])) < 0.000001)
            self.assertTrue(is_equal)



            niche_of_individuals, dist_to_niche = associate_to_niches(cand_copy.F, ref_dirs, survival.ideal_point,
                                                                      survival.intercepts)
            for r, v in enumerate(D['ref_dir']):
                self.assertTrue(np.all(ref_dirs[niche_of_individuals[r]] == v))

            is_equal = np.all(np.abs(dist_to_niche - np.array(D['perp_dist'])) < 0.0000001)
            self.assertTrue(is_equal)




            surv_pop = Population()
            surv_pop.X = np.array(D['X'])
            surv_pop.F = np.array(D['F'])

            for k in range(cand.size()):
                is_equal = np.any(np.all(cand.X[k, :] == surv_pop.X, axis=1))
                self.assertTrue(is_equal)

                is_equal = np.any(np.all(surv_pop.X[k, :] == cand.X, axis=1))
                self.assertTrue(is_equal)

if __name__ == '__main__':
    unittest.main()
