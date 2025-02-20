# Copyright 2024 Google LLC
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
#

"""Replay API client."""

import base64
import copy
import datetime
import inspect
import io
import json
import os
import re
from typing import Any, Literal, Optional, Union

import google.auth
from requests.exceptions import HTTPError

from . import errors
from ._api_client import ApiClient
from ._api_client import HttpOptions
from ._api_client import HttpRequest
from ._api_client import HttpResponse
from ._common import BaseModel


def _redact_version_numbers(version_string: str) -> str:
  """Redacts version numbers in the form x.y.z from a string."""
  return re.sub(r'\d+\.\d+\.\d+', '{VERSION_NUMBER}', version_string)


def _redact_language_label(language_label: str) -> str:
  """Removed because replay requests are used for all languages."""
  return re.sub(r'gl-python/', '{LANGUAGE_LABEL}/', language_label)


def _redact_request_headers(headers):
  """Redacts headers that should not be recorded."""
  redacted_headers = {}
  for header_name, header_value in headers.items():
    if header_name.lower() == 'x-goog-api-key':
      redacted_headers[header_name] = '{REDACTED}'
    elif header_name.lower() == 'user-agent':
      redacted_headers[header_name] = _redact_language_label(
          _redact_version_numbers(header_value)
      )
    elif header_name.lower() == 'x-goog-api-client':
      redacted_headers[header_name] = _redact_language_label(
          _redact_version_numbers(header_value)
      )
    else:
      redacted_headers[header_name] = header_value
  return redacted_headers


def _redact_request_url(url: str) -> str:
  # Redact all the url parts before the resource name, so the test can work
  # against any project, location, version, or whether it's EasyGCP.
  result = re.sub(
      r'.*/projects/[^/]+/locations/[^/]+/',
      '{VERTEX_URL_PREFIX}/',
      url,
  )
  result = re.sub(
      r'.*-aiplatform.googleapis.com/[^/]+/',
      '{VERTEX_URL_PREFIX}/',
      result,
  )
  result = re.sub(
      r'.*aiplatform.googleapis.com/[^/]+/',
      '{VERTEX_URL_PREFIX}/',
      result,
  )
  result = re.sub(
      r'https://generativelanguage.googleapis.com/[^/]+',
      '{MLDEV_URL_PREFIX}',
      result,
  )
  return result


def _redact_project_location_path(path: str) -> str:
  # Redact a field in the request that is known to vary based on project and
  # location.
  if 'projects/' in path and 'locations/' in path:
    result = re.sub(
        r'projects/[^/]+/locations/[^/]+/',
        '{PROJECT_AND_LOCATION_PATH}/',
        path,
    )
    return result
  else:
    return path


def _redact_request_body(body: dict[str, object]) -> dict[str, object]:
  for key, value in body.items():
    if isinstance(value, str):
      body[key] = _redact_project_location_path(value)


def redact_http_request(http_request: HttpRequest):
  http_request.headers = _redact_request_headers(http_request.headers)
  http_request.url = _redact_request_url(http_request.url)
  _redact_request_body(http_request.data)


def _current_file_path_and_line():
  """Prints the current file path and line number."""
  frame = inspect.currentframe().f_back.f_back
  filepath = inspect.getfile(frame)
  lineno = frame.f_lineno
  return f'File: {filepath}, Line: {lineno}'


def _debug_print(message: str):
  print(
      'DEBUG (test',
      os.environ.get('PYTEST_CURRENT_TEST'),
      ')',
      _current_file_path_and_line(),
      ':\n    ',
      message,
  )


class ReplayRequest(BaseModel):
  """Represents a single request in a replay."""

  method: str
  url: str
  headers: dict[str, str]
  body_segments: list[dict[str, object]]


class ReplayResponse(BaseModel):
  """Represents a single response in a replay."""

  status_code: int = 200
  headers: dict[str, str]
  body_segments: list[dict[str, object]]
  byte_segments: Optional[list[bytes]] = None
  sdk_response_segments: list[dict[str, object]]

  def model_post_init(self, __context: Any) -> None:
    # Remove headers that are not deterministic so the replay files don't change
    # every time they are recorded.
    self.headers.pop('Date', None)
    self.headers.pop('Server-Timing', None)


class ReplayInteraction(BaseModel):
  """Represents a single interaction, request and response in a replay."""

  request: ReplayRequest
  response: ReplayResponse


class ReplayFile(BaseModel):
  """Represents a recorded session."""

  replay_id: str
  interactions: list[ReplayInteraction]


class ReplayApiClient(ApiClient):
  """For integration testing, send recorded response or records a response."""

  def __init__(
      self,
      mode: Literal['record', 'replay', 'auto', 'api'],
      replay_id: str,
      replays_directory: Optional[str] = None,
      vertexai: bool = False,
      api_key: Optional[str] = None,
      credentials: Optional[google.auth.credentials.Credentials] = None,
      project: Optional[str] = None,
      location: Optional[str] = None,
      http_options: Optional[HttpOptions] = None,
  ):
    super().__init__(
        vertexai=vertexai,
        api_key=api_key,
        credentials=credentials,
        project=project,
        location=location,
        http_options=http_options,
    )
    self.replays_directory = replays_directory
    if not self.replays_directory:
      self.replays_directory = os.environ.get(
          'GOOGLE_GENAI_REPLAYS_DIRECTORY', None
      )
    # Valid replay modes are replay-only or record-and-replay.
    self.replay_session = None
    self._mode = mode
    self._replay_id = replay_id

  def initialize_replay_session(self, replay_id: str):
    self._replay_id = replay_id
    self._initialize_replay_session()

  def _get_replay_file_path(self):
    return self._generate_file_path_from_replay_id(
        self.replays_directory, self._replay_id
    )

  def _should_call_api(self):
    return self._mode in ['record', 'api'] or (
        self._mode == 'auto'
        and not os.path.isfile(self._get_replay_file_path())
    )

  def _should_update_replay(self):
    return self._should_call_api() and self._mode != 'api'

  def _initialize_replay_session_if_not_loaded(self):
    if not self.replay_session:
      self._initialize_replay_session()

  def _initialize_replay_session(self):
    _debug_print('Test is using replay id: ' + self._replay_id)
    self._replay_index = 0
    self._sdk_response_index = 0
    replay_file_path = self._get_replay_file_path()
    # This should not be triggered from the constructor.
    replay_file_exists = os.path.isfile(replay_file_path)
    if self._mode == 'replay' and not replay_file_exists:
      raise ValueError(
          'Replay files do not exist for replay id: ' + self._replay_id
      )

    if self._mode in ['replay', 'auto'] and replay_file_exists:
      with open(replay_file_path, 'r') as f:
        self.replay_session = ReplayFile.model_validate(json.loads(f.read()))

    if self._should_update_replay():
      self.replay_session = ReplayFile(
          replay_id=self._replay_id, interactions=[]
      )

  def _generate_file_path_from_replay_id(self, replay_directory, replay_id):
    session_parts = replay_id.split('/')
    if len(session_parts) < 3:
      raise ValueError(
          f'{replay_id}: Session ID must be in the format of'
          ' module/function/[vertex|mldev]'
      )
    if replay_directory is None:
      path_parts = []
    else:
      path_parts = [replay_directory]
    path_parts.extend(session_parts)
    return os.path.join(*path_parts) + '.json'

  def close(self):
    if not self._should_update_replay() or not self.replay_session:
      return
    replay_file_path = self._get_replay_file_path()
    os.makedirs(os.path.dirname(replay_file_path), exist_ok=True)
    with open(replay_file_path, 'w') as f:
      f.write(self.replay_session.model_dump_json(exclude_unset=True, indent=2))
    self.replay_session = None

  def _record_interaction(
      self,
      http_request: HttpRequest,
      http_response: Union[HttpResponse, errors.APIError, bytes],
  ):
    if not self._should_update_replay():
      return
    redact_http_request(http_request)
    request = ReplayRequest(
        method=http_request.method,
        url=http_request.url,
        headers=http_request.headers,
        body_segments=[http_request.data],
    )
    if isinstance(http_response, HttpResponse):
      response = ReplayResponse(
          headers=dict(http_response.headers),
          body_segments=list(http_response.segments()),
          byte_segments=[
              seg[:100] + b'...' for seg in http_response.byte_segments()
          ],
          status_code=http_response.status_code,
          sdk_response_segments=[],
      )
    else:
      response = ReplayResponse(
          headers=dict(http_response.response.headers),
          body_segments=[http_response._to_replay_record()],
          status_code=http_response.code,
          sdk_response_segments=[],
      )
    self.replay_session.interactions.append(
        ReplayInteraction(request=request, response=response)
    )

  def _match_request(
      self,
      http_request: HttpRequest,
      interaction: ReplayInteraction,
  ):
    assert http_request.url == interaction.request.url
    assert http_request.headers == interaction.request.headers, (
        'Request headers mismatch:\n'
        f'Actual: {http_request.headers}\n'
        f'Expected: {interaction.request.headers}'
    )
    assert http_request.method == interaction.request.method

    # Sanitize the request body, rewrite any fields that vary.
    request_data_copy = copy.deepcopy(http_request.data)
    # Both the request and recorded request must be redacted before comparing
    # so that the comparison is fair.
    _redact_request_body(request_data_copy)

    actual_request_body = [request_data_copy]
    expected_request_body = interaction.request.body_segments
    assert actual_request_body == expected_request_body, (
        'Request body mismatch:\n'
        f'Actual: {actual_request_body}\n'
        f'Expected: {expected_request_body}'
    )

  def _build_response_from_replay(self, http_request: HttpRequest):
    redact_http_request(http_request)

    interaction = self.replay_session.interactions[self._replay_index]
    # Replay is on the right side of the assert so the diff makes more sense.
    self._match_request(http_request, interaction)
    self._replay_index += 1
    self._sdk_response_index = 0
    errors.APIError.raise_for_response(interaction.response)
    return HttpResponse(
        headers=interaction.response.headers,
        response_stream=[
            json.dumps(segment)
            for segment in interaction.response.body_segments
        ],
        byte_stream=interaction.response.byte_segments,
    )

  def _verify_response(self, response_model: BaseModel):
    if self._mode == 'api':
      return
    # replay_index is advanced in _build_response_from_replay, so we need to -1.
    interaction = self.replay_session.interactions[self._replay_index - 1]
    if self._should_update_replay():
      if isinstance(response_model, list):
        response_model = response_model[0]
      if response_model and 'http_headers' in response_model.model_fields:
        response_model.http_headers.pop('Date', None)
      interaction.response.sdk_response_segments.append(
          response_model.model_dump(exclude_none=True)
      )
      return

    if isinstance(response_model, list):
      response_model = response_model[0]
    print('response_model: ', response_model.model_dump(exclude_none=True))
    actual = response_model.model_dump(exclude_none=True, mode='json')
    expected = interaction.response.sdk_response_segments[
        self._sdk_response_index
    ]
    assert (
        actual == expected
    ), f'SDK response mismatch:\nActual: {actual}\nExpected: {expected}'
    self._sdk_response_index += 1

  def _request(
      self,
      http_request: HttpRequest,
      stream: bool = False,
  ) -> HttpResponse:
    self._initialize_replay_session_if_not_loaded()
    if self._should_call_api():
      _debug_print('api mode request: %s' % http_request)
      try:
        result = super()._request(http_request, stream)
      except errors.APIError as e:
        self._record_interaction(http_request, e)
        raise e
      if stream:
        result_segments = []
        for segment in result.segments():
          result_segments.append(json.dumps(segment))
        result = HttpResponse(result.headers, result_segments)
        self._record_interaction(http_request, result)
        # Need to return a RecordedResponse that rebuilds the response
        # segments since the stream has been consumed.
      else:
        self._record_interaction(http_request, result)
      _debug_print('api mode result: %s' % result.json)
      return result
    else:
      return self._build_response_from_replay(http_request)

  async def _async_request(
      self,
      http_request: HttpRequest,
      stream: bool = False,
  ) -> HttpResponse:
    self._initialize_replay_session_if_not_loaded()
    if self._should_call_api():
      _debug_print('api mode request: %s' % http_request)
      try:
        result = await super()._async_request(http_request, stream)
      except errors.APIError as e:
        self._record_interaction(http_request, e)
        raise e
      if stream:
        result_segments = []
        async for segment in result.async_segments():
          result_segments.append(json.dumps(segment))
        result = HttpResponse(result.headers, result_segments)
        self._record_interaction(http_request, result)
        # Need to return a RecordedResponse that rebuilds the response
        # segments since the stream has been consumed.
      else:
        self._record_interaction(http_request, result)
      _debug_print('api mode result: %s' % result.json)
      return result
    else:
      return self._build_response_from_replay(http_request)

  def upload_file(self, file_path: Union[str, io.IOBase], upload_url: str, upload_size: int):
    if isinstance(file_path, io.IOBase):
      offset = file_path.tell()
      content = file_path.read()
      file_path.seek(offset, os.SEEK_SET)
      request = HttpRequest(
          method='POST',
          url='',
          data={'bytes': base64.b64encode(content).decode('utf-8')},
          headers={}
      )
    else:
      request = HttpRequest(
          method='POST', url='', data={'file_path': file_path}, headers={}
      )
    if self._should_call_api():
      try:
        result = super().upload_file(file_path, upload_url, upload_size)
      except HTTPError as e:
        result = HttpResponse(
            e.response.headers, [json.dumps({'reason': e.response.reason})]
        )
        result.status_code = e.response.status_code
        raise e
      self._record_interaction(request, HttpResponse({}, [json.dumps(result)]))
      return result
    else:
      return self._build_response_from_replay(request).json

  def _download_file_request(self, request):
    self._initialize_replay_session_if_not_loaded()
    if self._should_call_api():
      try:
        result = super()._download_file_request(request)
      except HTTPError as e:
        result = HttpResponse(
            e.response.headers, [json.dumps({'reason': e.response.reason})]
        )
        result.status_code = e.response.status_code
        raise e
      self._record_interaction(request, result)
      return result
    else:
      return self._build_response_from_replay(request)
