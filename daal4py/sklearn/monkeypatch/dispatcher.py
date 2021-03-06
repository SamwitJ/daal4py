#
#*******************************************************************************
# Copyright 2014-2020 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#******************************************************************************/

import sys
import warnings
from sklearn import __version__ as sklearn_version
from distutils.version import LooseVersion
import warnings

import sklearn.cluster as cluster_module
import sklearn.svm as svm_module

if LooseVersion(sklearn_version) >= LooseVersion("0.22"):
    import sklearn.linear_model._logistic as logistic_module
    from sklearn.decomposition._pca import PCA
    _patched_log_reg_path_func_name = '_logistic_regression_path'
    from ..linear_model._logistic_path_0_22 import _logistic_regression_path as daal_optimized_logistic_path
else:
    import sklearn.linear_model.logistic as logistic_module
    from sklearn.decomposition.pca import PCA
    if LooseVersion(sklearn_version) >= LooseVersion("0.21.0"):
        _patched_log_reg_path_func_name = '_logistic_regression_path'
        from ..linear_model._logistic_path_0_21 import _logistic_regression_path as daal_optimized_logistic_path
    else:
        _patched_log_reg_path_func_name = 'logistic_regression_path'
        from ..linear_model._logistic_path_0_21 import logistic_regression_path as daal_optimized_logistic_path

import sklearn.linear_model as linear_model_module
import sklearn.decomposition as decomposition_module

from sklearn.metrics import pairwise
from sklearn.utils import validation


if LooseVersion(sklearn_version) >= LooseVersion("0.22"):
    from ._pairwise_0_22 import daal_pairwise_distances
else:
    from ._pairwise_0_21 import daal_pairwise_distances
from ..decomposition.pca import PCA as PCA_daal4py
from ..linear_model.ridge import Ridge as Ridge_daal4py
from ..linear_model.linear import LinearRegression as LinearRegression_daal4py
from ..cluster.k_means import KMeans as KMeans_daal4py
from ..svm.svm import SVC as SVC_daal4py
from ..utils.validation import _daal_assert_all_finite

from daal4py import __version__ as daal4py_version

from daal4py import __daal_run_version__
daal_run_version = tuple(map(int, (__daal_run_version__[0:4], __daal_run_version__[4:8])))

_mapping = {
    'pca':       [[(decomposition_module, 'PCA', PCA_daal4py), None]],
    'kmeans':    [[(cluster_module, 'KMeans', KMeans_daal4py), None]],
    'distances': [[(pairwise, 'pairwise_distances', daal_pairwise_distances), None]],
    'linear':    [[(linear_model_module, 'LinearRegression', LinearRegression_daal4py), None]],
    'ridge':     [[(linear_model_module, 'Ridge', Ridge_daal4py), None]],
    'svm':       [[(svm_module, 'SVC', SVC_daal4py), None]],
    'logistic':  [[(logistic_module, _patched_log_reg_path_func_name, daal_optimized_logistic_path), None]],
}

del _patched_log_reg_path_func_name

try:
    from ..cluster.dbscan import DBSCAN as DBSCAN_daal4py
    _mapping['dbscan'] = [[(cluster_module, 'DBSCAN', DBSCAN_daal4py), None]]
except ImportError:
    pass

if daal_run_version >= (2020, 1):
    _mapping['fin_check'] = [[(validation, '_assert_all_finite', _daal_assert_all_finite), None]]


def do_patch(name):
    lname = name.lower()
    if lname in _mapping:
        for descriptor in _mapping[lname]:
            which, what, replacer = descriptor[0]
            if descriptor[1] is None:
                descriptor[1] = getattr(which, what, None)
            setattr(which, what, replacer)
    else:
        raise ValueError("Has no patch for: " + name)


def do_unpatch(name):
    lname = name.lower()
    if lname in _mapping:
        for descriptor in _mapping[lname]:
            if descriptor[1] is not None:
                which, what, replacer = descriptor[0]
                setattr(which, what, descriptor[1])
    else:
        raise ValueError("Has no patch for: " + name)


def enable(name=None, verbose=True):
    if LooseVersion(sklearn_version) < LooseVersion("0.20.0"):
        raise NotImplementedError("daal4py patches apply  for scikit-learn >= 0.20.0 only ...")
    elif LooseVersion(sklearn_version) > LooseVersion("0.22.1"):
        warn_msg = ("daal4py {daal4py_version} has only been tested " +
                    "with scikit-learn 0.22.0, found version: {sklearn_version}")
        warnings.warn(warn_msg.format(
            daal4py_version=daal4py_version,
            sklearn_version=sklearn_version)
        )

    if name is not None:
        do_patch(name)
    else:
        for key in _mapping:
            do_patch(key)
    if verbose and sys.stderr is not None:
        sys.stderr.write("Intel(R) Data Analytics Acceleration Library (Intel(R) DAAL) solvers for sklearn enabled: "
                         "https://intelpython.github.io/daal4py/sklearn.html\n")


def disable(name=None):
    if name is not None:
        do_unpatch(name)
    else:
        for key in _mapping:
            do_unpatch(key)


def _patch_names():
    return list(_mapping.keys())
