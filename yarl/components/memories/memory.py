# Copyright 2018 The YARL-Project, All Rights Reserved.
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

from yarl.components import Component
from yarl.spaces import Space


class Memory(Component):
    """
    Abstract memory component.
    """

    def __init__(
        self,
        capacity=1000,
        name="",
        scope="memory",
    ):
        """
        Abstract memory.
        Args:
            capacity (int): Maximum capacity.
        """
        super(Memory, self).__init__(name=name, scope=scope)

        # Variables (will be populated in create_variables).
        self.record_space = None
        self.record_registry = None
        self.capacity = capacity

        # Add default Sockets and the insert Computation.
        self.define_inputs("records", "num_records")
        self.define_outputs("insert", "sample")

        self.add_computation(inputs="records", outputs="insert", method=self._computation_insert)
        self.add_computation(inputs="num_records", outputs="sample", method=self._computation_get_records)

    def create_variables(self, input_spaces):
        # Store our record-space for convenience.
        self.record_space = input_spaces["records"]
        # Create the main memory as a flattened OrderedDict from any arbitrarily nested Space.
        self.record_registry = self.get_variable(name="replay-buffer", trainable=False,
                                                 from_space=self.record_space, flatten=True,
                                                 add_batch_rank=self.capacity)

    def _computation_insert(self, records):
        """
        Inserts one or more complex records.

        Args:
            records (OrderedDict): OrderedDict containing record data. Keys must match keys in flattened record
                space, values must be tensors. Use the Component's flatten options to .
        """
        raise NotImplementedError

    def _computation_get_records(self, num_records):
        """
        Returns a number of records according to the retrieval strategy implemented by
        the memory.

        Args:
            num_records (int): Number of records to return.

        Returns: The retrieved records.
        """
        raise NotImplementedError

    def _computation_get_episodes(self, num_episodes):
        """
        Retrieves a given number of episodes.

        Args:
            num_episodes (int): Number of episodes to retrieve.

        Returns: The retrieved episodes.
        """
        pass

    def _computation_clear(self):
        """
        Removes all entries from memory.
        """
        # Optional?
        pass

    def _computation_update_records(self, update):
        """
        Optionally ipdates memory records using information such as losses, e.g. to
        compute priorities.

        Args:
            update (dict): Any information relevant to update records, e.g. losses
                of most recently read batch of records.
        """
        pass

    def get_variables(self, name=None):
        """
        Utility method to retrieve internal variables from the registry
        for debugging purposes.

        Args:
            names (list): List of variables to retrieve. Variables must be identified via
                their str name in the registry.

        Returns:
            list: List of variables which the model can run to fetch their values.
        """
        pass
