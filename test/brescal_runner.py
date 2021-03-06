import os
import sys
import numpy as np
import pickle
from scipy.io.matlab import loadmat
from almc.bayesian_rescal import PFBayesianRescal
from almc.bayesian_rescal import PFBayesianCompRescal
from almc.bayesian_rescal import PFBayesianLogitRescal


def load_dataset(dataset):
    if dataset == 'umls':
        mat = loadmat('../data/%s/uml.mat' % (dataset))
        T = np.array(mat['Rs'], np.float32)
    elif dataset == 'nation':
        mat = loadmat('../data/%s/dnations.mat' % (dataset))
        T = np.array(mat['R'], np.float32)
    elif dataset == 'kinship':
        mat = loadmat('../data/%s/alyawarradata.mat' % (dataset))
        T = np.array(mat['Rs'], np.float32)
    elif dataset == 'wordnet':
        T = pickle.load(open('../data/%s/reduced_wordnet.pkl' % (dataset), 'rb'))
    elif dataset == 'freebase':
        T, _, _ = pickle.load(open('../data/freebase/subset_5000.pkl', 'rb'))

    if dataset == 'umls' or dataset == 'nation' or dataset == 'kinship':
        T = np.swapaxes(T, 1, 2)
        T = np.swapaxes(T, 0, 1)  # [relation, entity, entity]
        T[np.isnan(T)] = 0
    return T


if __name__ == '__main__':
    if len(sys.argv) != 9:
        print('usage: python amdc_runner.py model dataset n_dim n_particle var_x var_comp trial_num max_iter')
        raise Exception()

    model = sys.argv[1]
    dataset = sys.argv[2]
    n_dim = int(sys.argv[3])
    n_particle = int(sys.argv[4])
    var_x = float(sys.argv[5])
    var_comp = float(sys.argv[6])
    nt = int(sys.argv[7])
    max_iter = int(sys.argv[8])

    T = load_dataset(dataset)
    n_relation, n_entity, _ = T.shape

    if max_iter == 0:
        # set number of iteration to the size of tensor in case where max_iter = 0
        max_iter = np.prod(T.shape)

    # destination folder where model and log files are saved
    dest = '../result_posterior_variance/%s/%s/' % (dataset, model)

    p_obs = 0.00
    p_test = 0.3

    file = '../data/%s/train_test_%.3f_%.3f_%d.pkl' % (dataset, p_obs, p_test, nt)

    obs_mask, test_mask = pickle.load(open(file, 'rb'))

    if not os.path.exists(dest):
        os.makedirs(dest, exist_ok=True)

    if model == 'brescal':
        model_file = os.path.join(dest, 'train_test_varx_%.2f_dim_%d_par_%d_test_%d.pkl' % (
            var_x, n_dim, n_particle, nt))
    elif model == 'logit':
        model_file = os.path.join(dest, 'train_test_dim_%d_par_%d_test_%d.pkl' % (
            n_dim, n_particle, nt))
    else:
        model_file = os.path.join(dest, 'train_test_var_%.2f_%.2f_dim_%d_par_%d_test_%d.pkl' % (
            var_x, var_comp, n_dim, n_particle, nt))

    if not os.path.exists(model_file):
        # change file extension from pkl to txt for writing log
        log = os.path.splitext(model_file)[0] + ".txt"
        eval_log = os.path.splitext(model_file)[0] + "_eval.txt"
        if os.path.exists(log):
            os.remove(log)
        if os.path.exists(eval_log):
            os.remove(eval_log)

        if model == 'brescal':
            _model = PFBayesianRescal(n_dim, var_x=var_x, n_particles=n_particle, compute_score=False, parallel=False,
                                      log=log, eval_log=eval_log, dest=model_file, sample_all=True)
        elif model == 'bcomp_add':
            _model = PFBayesianCompRescal(n_dim, compositionality='additive', var_x=var_x, var_comp=var_comp,
                                          n_particles=n_particle, compute_score=False, log=log, dest=model_file,
                                          eval_log=eval_log)
        elif model == 'bcomp_mul':
            _model = PFBayesianCompRescal(n_dim, compositionality='multiplicative', var_x=var_x, var_comp=var_comp,
                                          n_particles=n_particle, compute_score=False, log=log, dest=model_file,
                                          eval_log=eval_log)
        elif model == 'logit':
            _model = PFBayesianLogitRescal(n_dim, log=log, dest=model_file, compute_score=False)
        else:
            raise Exception('No such model exists %s' % model)

        seq = _model.fit(T, obs_mask=obs_mask, max_iter=max_iter, test_mask=test_mask)
