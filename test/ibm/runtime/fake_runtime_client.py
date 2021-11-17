# This code is part of Qiskit.
#
# (C) Copyright IBM 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Fake RuntimeClient."""

import time
import uuid
import json
import base64
from typing import Optional, Dict
from concurrent.futures import ThreadPoolExecutor

from qiskit_ibm_runtime.credentials import Credentials
from qiskit_ibm_runtime.api.exceptions import RequestsApiError
from qiskit_ibm_runtime.utils import RuntimeEncoder


class BaseFakeProgram:
    """Base class for faking a program."""

    def __init__(self, program_id, name, data, cost, description,
                 backend_requirements=None, parameters=None, return_values=None,
                 interim_results=None, is_public=False):
        """Initialize a fake program."""
        self._id = program_id
        self._name = name
        self._data = data
        self._cost = cost
        self._description = description
        self._backend_requirements = backend_requirements
        self._parameters = parameters
        self._return_values = return_values
        self._interim_results = interim_results
        self._is_public = is_public

    def to_dict(self, include_data=False):
        """Convert this program to a dictionary format."""
        out = {'id': self._id,
               'name': self._name,
               'cost': self._cost,
               'description': self._description,
               'is_public': self._is_public,
               'creation_date': '2021-09-13T17:27:42Z',
               'update_date': '2021-09-14T19:25:32Z'}
        if include_data:
            out['data'] = base64.standard_b64decode(self._data).decode()
        out['spec'] = {}
        if self._backend_requirements:
            out['spec']['backend_requirements'] = self._backend_requirements
        if self._parameters:
            out['spec']['parameters'] = self._parameters
        if self._return_values:
            out['spec']['return_values'] = self._return_values
        if self._interim_results:
            out['spec']['interim_results'] = self._interim_results

        return out


class BaseFakeRuntimeJob:
    """Base class for faking a runtime job."""

    _job_progress = [
        "QUEUED",
        "RUNNING",
        "COMPLETED"
    ]

    _executor = ThreadPoolExecutor()  # pylint: disable=bad-option-value,consider-using-with

    def __init__(self, job_id, program_id, hub, group, project, backend_name, final_status,
                 params, image):
        """Initialize a fake job."""
        self._job_id = job_id
        self._status = final_status or "QUEUED"
        self._program_id = program_id
        self._hub = hub
        self._group = group
        self._project = project
        self._backend_name = backend_name
        self._params = params
        self._image = image
        if final_status is None:
            self._future = self._executor.submit(self._auto_progress)
            self._result = None
        elif final_status == "COMPLETED":
            self._result = json.dumps("foo")
        self._final_status = final_status

    def _auto_progress(self):
        """Automatically update job status."""
        for status in self._job_progress:
            time.sleep(0.5)
            self._status = status

        if self._status == "COMPLETED":
            self._result = json.dumps("foo")

    def to_dict(self):
        """Convert to dictionary format."""
        return {'id': self._job_id,
                'hub': self._hub,
                'group': self._group,
                'project': self._project,
                'backend': self._backend_name,
                'status': self._status,
                'params': [self._params],
                'program': {'id': self._program_id},
                'image': self._image}

    def result(self):
        """Return job result."""
        return self._result


class FailedRuntimeJob(BaseFakeRuntimeJob):
    """Class for faking a failed runtime job."""

    _job_progress = [
        "QUEUED",
        "RUNNING",
        "FAILED"
    ]

    def _auto_progress(self):
        """Automatically update job status."""
        super()._auto_progress()

        if self._status == "FAILED":
            self._result = "Kaboom!"


class FailedRanTooLongRuntimeJob(BaseFakeRuntimeJob):
    """Class for faking a failed runtime job."""

    _job_progress = [
        "QUEUED",
        "RUNNING",
        "CANCELLED - RAN TOO LONG"
    ]

    def _auto_progress(self):
        """Automatically update job status."""
        super()._auto_progress()

        if self._status == "CANCELLED - RAN TOO LONG":
            self._result = "Kaboom!"


class CancelableRuntimeJob(BaseFakeRuntimeJob):
    """Class for faking a cancelable runtime job."""

    _job_progress = [
        "QUEUED",
        "RUNNING"
    ]

    def __init__(self, *args, **kwargs):
        """Initialize a cancellable job."""
        super().__init__(*args, **kwargs)
        self._cancelled = False

    def cancel(self):
        """Cancel the job."""
        self._future.cancel()
        self._cancelled = True

    def to_dict(self):
        """Convert to dictionary format."""
        data = super().to_dict()
        if self._cancelled:
            data['status'] = "CANCELLED"
        return data


class CustomResultRuntimeJob(BaseFakeRuntimeJob):
    """Class for using custom job result."""

    custom_result = "bar"

    def _auto_progress(self):
        """Automatically update job status."""
        super()._auto_progress()

        if self._status == "COMPLETED":
            self._result = json.dumps(self.custom_result, cls=RuntimeEncoder)


class TimedRuntimeJob(BaseFakeRuntimeJob):
    """Class for a job that runs for the input seconds."""

    def __init__(self, **kwargs):
        self._runtime = kwargs.pop('run_time')
        super().__init__(**kwargs)

    def _auto_progress(self):
        self._status = "RUNNING"
        time.sleep(self._runtime)
        self._status = "COMPLETED"

        if self._status == "COMPLETED":
            self._result = json.dumps("foo")


class BaseFakeRuntimeClient:
    """Base class for faking the runtime client."""

    def __init__(self, job_classes=None, final_status=None, job_kwargs=None,
                 hub=None, group=None, project=None):
        """Initialize a fake runtime client."""
        self._programs = {}
        self._jobs = {}
        self._job_classes = job_classes or []
        self._final_status = final_status
        self._job_kwargs = job_kwargs or {}
        self._hub = hub
        self._group = group
        self._project = project

    def set_hgp(self, hub, group, project):
        """Set hub, group and project"""
        self._hub = hub
        self._group = group
        self._project = project

    def set_job_classes(self, classes):
        """Set job classes to use."""
        if not isinstance(classes, list):
            classes = [classes]
        self._job_classes = classes

    def set_final_status(self, final_status):
        """Set job status to passed in final status instantly."""
        self._final_status = final_status

    def list_programs(self, search, limit, skip):
        """List all programs."""
        programs = []
        for prog in self._programs.values():
            if not search:
                programs.append(prog.to_dict())
            if (search in prog.to_dict()['name'].lower()
                    or search in prog.to_dict()['description'].lower()):
                programs.append(prog.to_dict())
        return {"programs": programs[skip:limit+skip], "count": len(programs)}

    def program_create(self, program_data, name, description, max_execution_time,
                       spec=None, is_public=False):
        """Create a program."""
        program_id = name
        if program_id in self._programs:
            raise RequestsApiError("Program already exists.", status_code=409)
        backend_requirements = spec.get('backend_requirements', None)
        parameters = spec.get('parameters', None)
        return_values = spec.get('return_values', None)
        interim_results = spec.get('interim_results', None)
        self._programs[program_id] = BaseFakeProgram(
            program_id=program_id, name=name, data=program_data, cost=max_execution_time,
            description=description, backend_requirements=backend_requirements,
            parameters=parameters, return_values=return_values, interim_results=interim_results,
            is_public=is_public)
        return {'id': program_id}

    def program_update(
            self,
            program_id: str,
            program_data: str = None,
            name: str = None,
            description: str = None,
            max_execution_time: int = None,
            spec: Optional[Dict] = None
    ) -> None:
        """Update a program."""
        if program_id not in self._programs:
            raise RequestsApiError("Program not found", status_code=404)
        program = self._programs[program_id]
        program._data = program_data or program._data
        program._name = name or program._name
        program._description = description or program._description
        program._cost = max_execution_time or program._cost
        if spec:
            program._backend_requirements = \
                spec.get("backend_requirements") or program._backend_requirements
            program._parameters = spec.get("parameters") or program._parameters
            program._return_values = spec.get("return_values") or program._return_values
            program._interim_results = spec.get("interim_results") or program._interim_results

    def program_get(self, program_id: str):
        """Return a specific program."""
        if program_id not in self._programs:
            raise RequestsApiError("Program not found", status_code=404)
        return self._programs[program_id].to_dict(include_data=True)

    def program_run(
            self,
            program_id: str,
            credentials: Credentials,
            backend_name: str,
            params: str,
            image: Optional[str] = ""
    ):
        """Run the specified program."""
        job_id = uuid.uuid4().hex
        job_cls = self._job_classes.pop(0) if len(self._job_classes) > 0 else BaseFakeRuntimeJob
        hub = self._hub or credentials.hub
        group = self._group or credentials.group
        project = self._project or credentials.project
        job = job_cls(job_id=job_id, program_id=program_id,
                      hub=hub, group=group,
                      project=project, backend_name=backend_name,
                      params=params, final_status=self._final_status, image=image,
                      **self._job_kwargs)
        self._jobs[job_id] = job
        return {'id': job_id}

    def program_delete(self, program_id: str) -> None:
        """Delete the specified program."""
        if program_id not in self._programs:
            raise RequestsApiError("Program not found", status_code=404)
        del self._programs[program_id]

    def job_get(self, job_id):
        """Get the specific job."""
        return self._get_job(job_id).to_dict()

    def jobs_get(self, limit=None, skip=None, pending=None, program_id=None,
                 hub=None, group=None, project=None):
        """Get all jobs."""
        pending_statuses = ['QUEUED', 'RUNNING']
        returned_statuses = ['COMPLETED', 'FAILED', 'CANCELLED']
        limit = limit or len(self._jobs)
        skip = skip or 0
        jobs = list(self._jobs.values())
        count = len(self._jobs)
        if pending is not None:
            job_status_list = pending_statuses if pending else returned_statuses
            jobs = [job for job in jobs if job._status in job_status_list]
            count = len(jobs)
        if program_id:
            jobs = [job for job in jobs if job._program_id == program_id]
            count = len(jobs)
        if all([hub, group, project]):
            jobs = [job for job in jobs if
                    job._hub == hub and job._group == group and job._project == project]
            count = len(jobs)
        jobs = jobs[skip:limit+skip]
        return {"jobs": [job.to_dict() for job in jobs],
                "count": count}

    def set_program_visibility(self, program_id: str, public: bool) -> None:
        """Sets a program's visibility.

        Args:
            program_id: Program ID.
            public: If ``True``, make the program visible to all.
                If ``False``, make the program visible to just your account.
        """
        self._programs[program_id]._is_public = public

    def job_results(self, job_id):
        """Get the results of a program job."""
        return self._get_job(job_id).result()

    def job_cancel(self, job_id):
        """Cancel the job."""
        self._get_job(job_id).cancel()

    def job_delete(self, job_id):
        """Delete the job."""
        self._get_job(job_id)
        del self._jobs[job_id]

    def _get_job(self, job_id):
        """Get job."""
        if job_id not in self._jobs:
            raise RequestsApiError("Job not found", status_code=404)
        return self._jobs[job_id]
