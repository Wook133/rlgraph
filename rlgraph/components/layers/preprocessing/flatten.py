# Copyright 2018 The RLgraph authors. All Rights Reserved.
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
# ==============================================================================

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np

from rlgraph import RLGraphError, get_backend
from rlgraph.spaces import IntBox, FloatBox
from rlgraph.components.layers.preprocessing import PreprocessLayer
from rlgraph.utils.ops import flatten_op, unflatten_op

if get_backend() == "tf":
    import tensorflow as tf


class Flatten(PreprocessLayer):
    """
    Flattens the input by reshaping it, excluding the batch-rank (if there is one).
    e.g. input FloatBox(shape=(None, 2, 3, 4)) -> flatten -> FloatBox(shape=(None, 24))

    If the input is an IntBox, will (optionally) flatten for categories as well.
    e.g. input Space=IntBox(4) -> flatten -> FloatBox(shape=(4,)).
    """

    def __init__(self, flatten_categories=True, scope="flatten", **kwargs):
        """
        Args:
            flatten_categories (bool): Whether to flatten also IntBox categories. Default: True.
        """
        super(Flatten, self).__init__(scope=scope, add_auto_key_as_first_param=True, **kwargs)

        self.flatten_categories = flatten_categories
        # Stores the number of categories in IntBoxes.
        self.num_categories = dict()

        # The output spaces after preprocessing (per flat-key).
        self.output_spaces = None

    def get_preprocessed_space(self, space):
        ret = dict()
        for k, v in space.flatten().items():
            flat_dim = v.flat_dim_with_categories if self.flatten_categories is True and v.__class__ == IntBox \
                else v.flat_dim
            ret[k] = FloatBox(shape=(flat_dim,), add_batch_rank=v.has_batch_rank, add_time_rank=v.has_time_rank)
        return unflatten_op(ret)

    def check_input_spaces(self, input_spaces, action_space):
        super(Flatten, self).check_input_spaces(input_spaces, action_space)

        # Check whether our input space has-batch or not and store this information here.
        in_space = input_spaces["apply"][0]  # type: Dict

        # Store the mapped output Spaces (per flat key).
        self.output_spaces = flatten_op(self.get_preprocessed_space(in_space))

        # Check whether we have to flatten the incoming categories of an IntBox into a FloatBox with additional
        # rank (categories rank). Store the dimension of this additional rank in the `self.num_categories` dict.
        if self.flatten_categories is True:
            def mapping_func(key, space):
                if isinstance(space, IntBox):
                    # Must have global bounds (bounds valid for all axes).
                    if space.num_categories is False:
                        raise RLGraphError("ERROR: Cannot flatten categories if one of the IntBox spaces ({}={}) does not "
                                        "have global bounds (its `num_categories` is False)!".format(key, space))
                    return space.num_categories
                # No categories. Keep as is.
                return 1
            self.num_categories = in_space.flatten(mapping=mapping_func)

    def _graph_fn_apply(self, key, input_):
        if self.backend == "python" or get_backend() == "python":
            from rlgraph.utils.numpy import one_hot

            # Create a one-hot axis for the categories at the end?
            if self.num_categories[key] > 1:
                input_ = one_hot(input_, depth=self.num_categories[key])
            reshaped = np.reshape(a=input_, newshape=self.output_spaces[key].get_shape(with_batch_rank=-1,
                                                                                       with_time_rank=-1))
            return reshaped

        elif get_backend() == "tf":
            # Create a one-hot axis for the categories at the end?
            if self.num_categories[key] > 1:
                input_ = tf.one_hot(indices=input_, depth=self.num_categories[key], axis=-1)
            reshaped = tf.reshape(tensor=input_, shape=self.output_spaces[key].get_shape(with_batch_rank=-1,
                                                                                         with_time_rank=-1))
            return tf.identity(reshaped, name="flattened")
