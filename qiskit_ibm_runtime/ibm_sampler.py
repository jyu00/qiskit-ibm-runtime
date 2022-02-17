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

from qiskit.quantum_info.primitives.results.sampler_result import SamplerResult

from .base_primitive import BasePrimitive
from .runtime_session import RuntimeSession


class SamplerSession(RuntimeSession):

    def __call__(
            self,
            parameters=None,
            **run_options
    ):
        self.write(parameters=parameters, run_options=run_options)
        raw_result = self.read()
        return SamplerResult(
            quasi_dists=raw_result["quasi_dists"],
            shots=None,
            raw_results=None,
            metadata=None
        )


class IBMSampler(BasePrimitive):

    def __call__(
            self,
            circuits,
            transpile_options=None,
            skip_transpilation=False
    ):
        inputs = {
            "circuits": circuits,
            "transpile_options": transpile_options,
            "skip_transpilation": skip_transpilation
        }

        options = {}
        if self._backend:
            options["backend_name"] = self._backend

        # TODO remove
        options["image"] = "expval:748ef50"

        return SamplerSession(
            runtime=self._service,
            program_id="sampler-Yxk1ZM0Rlm",
            inputs=inputs,
            options=options)
