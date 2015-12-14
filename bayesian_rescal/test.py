import logging
import itertools

import numpy as np
from scipy.io.matlab import loadmat
from scipy.sparse import csr_matrix

import matplotlib
import matplotlib.pyplot as plt

from sklearn.metrics import roc_auc_score

import rescal
from brescal import BayesianRescal
from seq_brescal import PFBayesianRescal


if __name__ == '__main__':
    """
    Test with Kinship dataset
    """
    mat = loadmat('../data/alyawarradata.mat')
    T = np.array(mat['Rs'], np.float32)

    n_dim = 5
    T = np.swapaxes(T, 1, 2)
    T = np.swapaxes(T, 0, 1)  # [relation, entity, entity]
    n_relation, n_entity, _ = T.shape


    maskT = np.zeros_like(T)
    p = 0.1
    for k in range(n_relation):
        for i,j in itertools.product(range(n_entity),repeat=2):
            if T[k, i, j] and np.random.binomial(1, p):
                maskT[k, i, j] = 1

    # model = BayesianRescal(n_dim, eval_fn=roc_auc_score, controlled_var=True, parallelize=True)
    # model.fit(T, max_iter=100)

    model = PFBayesianRescal(n_dim, controlled_var=False, obs_var=.01, unobs_var=10., n_particles=5,
                         eval_fn=roc_auc_score, parallelize=True)
    seq = model.fit(T, obs_mask = maskT.copy(), max_iter=100)
