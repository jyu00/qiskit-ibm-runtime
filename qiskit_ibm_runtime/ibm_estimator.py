# This code is part of Qiskit.
#
# (C) Copyright IBM 2022.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from qiskit.quantum_info.primitives.results.estimator_result import EstimatorResult

from .base_primitive import BasePrimitive
from .runtime_session import RuntimeSession


class EstimatorSession(RuntimeSession):

    def __call__(
            self,
            parameters=None,
            **run_options
    ):
        self.write(parameters=parameters, run_options=run_options)
        raw_result = self.read()
        return EstimatorResult(raw_result["values"], raw_result["variances"])


class IBMEstimator(BasePrimitive):

    def __call__(
            self,
            circuits,
            observables,
            grouping=None,
            transpile_options=None
    ):
        inputs = {
            "circuits": circuits,
            "observables": observables,
            "grouping": grouping,
            "transpile_options": transpile_options
        }

        options = {}
        if self._backend:
            options["backend_name"] = self._backend

        # TODO remove
        options["image"] = "expval:748ef50"

        return EstimatorSession(
            runtime=self._service,
            program_id="estimator-X322y4G534",
            inputs=inputs,
            options=options
        )
