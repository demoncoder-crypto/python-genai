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


"""Base client for calling HTTP APIs sending and receiving JSON.

The BaseApiClient is intended to be a private module and is subject to change.
"""

import asyncio
import copy
from dataclasses import dataclass
import datetime
import http
import io
import json
import logging
import os
import sys
import time
from typing import Any, AsyncIterator, Optional, Tuple, Union
from urllib.parse import urlparse, urlunparse
import anyio
import google.auth
import google.auth.credentials
from google.auth.credentials import Credentials
from google.auth.transport.requests import Request
import httpx
from pydantic import BaseModel, Field, ValidationError
from . import _common
from . import errors
from . import version
from .types import HttpOptions, HttpOptionsDict, HttpOptionsOrDict

logger = logging.getLogger('google_genai._api_client')
CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB chunk size


def _append_library_version_headers(headers: dict[str, str]) -> None:
  """Appends the telemetry header to the headers dict."""
  library_label = f'google-genai-sdk/{version.__version__}'
  language_label = 'gl-python/' + sys.version.split()[0]
  version_header_value = f'{library_label} {language_label}'
  if (
      'user-agent' in headers
      and version_header_value not in headers['user-agent']
  ):
    headers['user-agent'] += f' {version_header_value}'
  elif 'user-agent' not in headers:
    headers['user-agent'] = version_header_value
  if (
      'x-goog-api-client' in headers
      and version_header_value not in headers['x-goog-api-client']
  ):
    headers['x-goog-api-client'] += f' {version_header_value}'
  elif 'x-goog-api-client' not in headers:
    headers['x-goog-api-client'] = version_header_value


def _patch_http_options(
    options: HttpOptions, patch_options: HttpOptions
) -> HttpOptions:
  copy_option = options.model_copy()

  options_headers = copy_option.headers or {}
  patch_options_headers = patch_options.headers or {}
  copy_option.headers = {
      **options_headers,
      **patch_options_headers,
  }

  http_options_keys = HttpOptions.model_fields.keys()

  for key in http_options_keys:
    if key == 'headers':
      continue
    patch_value = getattr(patch_options, key, None)
    if patch_value is not None:
      setattr(copy_option, key, patch_value)
    else:
      setattr(copy_option, key, getattr(options, key))

  if copy_option.headers is not None:
    _append_library_version_headers(copy_option.headers)
  return copy_option


def _join_url_path(base_url: str, path: str) -> str:
  parsed_base = urlparse(base_url)
  base_path = (
      parsed_base.path[:-1]
      if parsed_base.path.endswith('/')
      else parsed_base.path
  )
  path = path[1:] if path.startswith('/') else path
  return urlunparse(parsed_base._replace(path=base_path + '/' + path))


def _load_auth(*, project: Union[str, None]) -> Tuple[Credentials, str]:
  """Loads google auth credentials and project id."""
  credentials, loaded_project_id = google.auth.default(
      scopes=['https://www.googleapis.com/auth/cloud-platform'],
  )

  if not project:
    project = loaded_project_id

  if not project:
    raise ValueError(
        'Could not resolve project using application default credentials.'
    )

  return credentials, project


def _refresh_auth(credentials: Credentials) -> Credentials:
  credentials.refresh(Request())
  return credentials


def _get_timeout_in_seconds(
    timeout: Optional[Union[float, int]],
) -> Optional[float]:
  """Converts the timeout to seconds."""
  if timeout:
    # HttpOptions.timeout is in milliseconds. But httpx.Client.request()
    # expects seconds.
    timeout_in_seconds = timeout / 1000.0
  else:
    timeout_in_seconds = None
  return timeout_in_seconds


@dataclass
class HttpRequest:
  headers: dict[str, str]
  url: str
  method: str
  data: Union[dict[str, object], bytes]
  timeout: Optional[float] = None


# TODO(b/394358912): Update this class to use a SDKResponse class that can be
# generated and used for all languages.
class BaseResponse(_common.BaseModel):
  http_headers: Optional[dict[str, str]] = Field(
      default=None, description='The http headers of the response.'
  )

  json_payload: Optional[Any] = Field(
      default=None, description='The json payload of the response.'
  )


class HttpResponse:

  def __init__(
      self,
      headers: Union[dict[str, str], httpx.Headers],
      response_stream: Union[Any, str] = None,
      byte_stream: Union[Any, bytes] = None,
  ):
    self.status_code = 200
    self.headers = headers
    self.response_stream = response_stream
    self.byte_stream = byte_stream

  # Async iterator for async streaming.
  def __aiter__(self):
    self.segment_iterator = self.async_segments()
    return self

  async def __anext__(self):
    try:
      return await self.segment_iterator.__anext__()
    except StopIteration:
      raise StopAsyncIteration

  @property
  def json(self) -> Any:
    if not self.response_stream[0]:  # Empty response
      return ''
    return json.loads(self.response_stream[0])

  def segments(self):
    if isinstance(self.response_stream, list):
      # list of objects retrieved from replay or from non-streaming API.
      for chunk in self.response_stream:
        yield json.loads(chunk) if chunk else {}
    elif self.response_stream is None:
      yield from []
    else:
      # Iterator of objects retrieved from the API.
      for chunk in self.response_stream.iter_lines():
        if chunk:
          # In streaming mode, the chunk of JSON is prefixed with "data:" which
          # we must strip before parsing.
          if not isinstance(chunk, str):
            chunk = chunk.decode('utf-8')
          if chunk.startswith('data: '):
            chunk = chunk[len('data: ') :]
          yield json.loads(chunk)

  async def async_segments(self) -> AsyncIterator[Any]:
    if isinstance(self.response_stream, list):
      # list of objects retrieved from replay or from non-streaming API.
      for chunk in self.response_stream:
        yield json.loads(chunk) if chunk else {}
    elif self.response_stream is None:
      async for c in []:  # type: ignore[attr-defined]
        yield c
    else:
      # Iterator of objects retrieved from the API.
      if hasattr(self.response_stream, 'aiter_lines'):
        async for chunk in self.response_stream.aiter_lines():
          # This is httpx.Response.
          if chunk:
            # In async streaming mode, the chunk of JSON is prefixed with
            # "data:" which we must strip before parsing.
            if not isinstance(chunk, str):
              chunk = chunk.decode('utf-8')
            if chunk.startswith('data: '):
              chunk = chunk[len('data: ') :]
            yield json.loads(chunk)
      else:
        raise ValueError('Error parsing streaming response.')

  def byte_segments(self):
    if isinstance(self.byte_stream, list):
      # list of objects retrieved from replay or from non-streaming API.
      yield from self.byte_stream
    elif self.byte_stream is None:
      yield from []
    else:
      raise ValueError(
          'Byte segments are not supported for streaming responses.'
      )

  def _copy_to_dict(self, response_payload: dict[str, object]):
    # Cannot pickle 'generator' object.
    delattr(self, 'segment_iterator')
    for attribute in dir(self):
      response_payload[attribute] = copy.deepcopy(getattr(self, attribute))


class SyncHttpxClient(httpx.Client):
  """Sync httpx client."""

  def __init__(self, **kwargs: Any) -> None:
    """Initializes the httpx client."""
    kwargs.setdefault('follow_redirects', True)
    super().__init__(**kwargs)

  def __del__(self) -> None:
    """Closes the httpx client."""
    if self.is_closed:
      return
    try:
      self.close()
    except Exception:
      pass


class AsyncHttpxClient(httpx.AsyncClient):
  """Async httpx client."""

  def __init__(self, **kwargs: Any) -> None:
    """Initializes the httpx client."""
    kwargs.setdefault('follow_redirects', True)
    super().__init__(**kwargs)

  def __del__(self) -> None:
    if self.is_closed:
      return
    try:
      asyncio.get_running_loop().create_task(self.aclose())
    except Exception:
      pass


class BaseApiClient:
  """Base client for calling HTTP APIs sending and receiving JSON."""

  def __init__(
      self,
      vertexai: Optional[bool] = None,
      modelgarden: Optional[bool] = None,
      api_key: Optional[str] = None,
      credentials: Optional[google.auth.credentials.Credentials] = None,
      project: Optional[str] = None,
      location: Optional[str] = None,
      http_options: Optional[HttpOptionsOrDict] = None,
  ):
    self.vertexai = vertexai
    self.modelgarden = modelgarden
    
    if self.vertexai is None:
      if os.environ.get('GOOGLE_GENAI_USE_VERTEXAI', '0').lower() in [
          'true',
          '1',
      ]:
        self.vertexai = True
        
    if self.modelgarden is None:
      if os.environ.get('GOOGLE_GENAI_USE_MODELGARDEN', '0').lower() in [
          'true',
          '1',
      ]:
        self.modelgarden = True
    
    # If modelgarden is True, then vertexai must also be True
    if self.modelgarden:
      self.vertexai = True

    # Validate explicitly set initializer values.
    if (project or location) and api_key:
      # API cannot consume both project/location and api_key.
      raise ValueError(
          'Project/location and API key are mutually exclusive in the client'
          ' initializer.'
      )
    elif credentials and api_key:
      # API cannot consume both credentials and api_key.
      raise ValueError(
          'Credentials and API key are mutually exclusive in the client'
          ' initializer.'
      )

    # Validate http_options if it is provided.
    validated_http_options = HttpOptions()
    if isinstance(http_options, dict):
      try:
        validated_http_options = HttpOptions.model_validate(http_options)
      except ValidationError as e:
        raise ValueError(f'Invalid http_options: {e}')
    elif isinstance(http_options, HttpOptions):
      validated_http_options = http_options

    # Retrieve implicitly set values from the environment.
    env_project = os.environ.get('GOOGLE_CLOUD_PROJECT', None)
    env_location = os.environ.get('GOOGLE_CLOUD_LOCATION', None)
    env_api_key = os.environ.get('GOOGLE_API_KEY', None)
    self.project = project or env_project
    self.location = location or env_location
    self.api_key = api_key or env_api_key

    self._credentials = credentials
    self._http_options = HttpOptions()
    # Initialize the lock. This lock will be used to protect access to the
    # credentials. This is crucial for thread safety when multiple coroutines
    # might be accessing the credentials at the same time.
    try:
      self._auth_lock = asyncio.Lock()
    except RuntimeError:
      asyncio.set_event_loop(asyncio.new_event_loop())
      self._auth_lock = asyncio.Lock()

    # Handle when to use Vertex AI in express mode (api key).
    # Explicit initializer arguments are already validated above.
    if self.vertexai:
      if credentials:
        # Explicit credentials take precedence over implicit api_key.
        logger.info(
            'The user provided Google Cloud credentials will take precedence'
            + ' over the API key from the environment variable.'
        )
        self.api_key = None
      elif (env_location or env_project) and api_key:
        # Explicit api_key takes precedence over implicit project/location.
        logger.info(
            'The user provided Vertex AI API key will take precedence over the'
            + ' project/location from the environment variables.'
        )
        self.project = None
        self.location = None
      elif (project or location) and env_api_key:
        # Explicit project/location takes precedence over implicit api_key.
        logger.info(
            'The user provided project/location will take precedence over the'
            + ' Vertex AI API key from the environment variable.'
        )
        self.api_key = None
      elif (env_location or env_project) and env_api_key:
        # Implicit project/location takes precedence over implicit api_key.
        logger.info(
            'The project/location from the environment variables will take'
            + ' precedence over the API key from the environment variables.'
        )
        self.api_key = None
      if not self.project and not self.api_key:
        credentials, self.project = _load_auth(project=None)
        if not self._credentials:
          self._credentials = credentials
      if not ((self.project and self.location) or self.api_key):
        raise ValueError(
            'Project and location or API key must be set when using the Vertex '
            'AI API.'
        )
      if self.api_key or self.location == 'global':
        self._http_options.base_url = f'https://aiplatform.googleapis.com/'
      else:
        self._http_options.base_url = (
            f'https://{self.location}-aiplatform.googleapis.com/'
        )
      
      # If using modelgarden, use v1 API version
      if self.modelgarden:
        if not (self.project and self.location):
          raise ValueError(
              'Project and location must be set when using ModelGarden models.'
          )
        self._http_options.api_version = 'v1'
      else:
        self._http_options.api_version = 'v1beta1'
    else:  # Implicit initialization or missing arguments.
      if not self.api_key:
        raise ValueError(
            'Missing key inputs argument! To use the Google AI API,'
            'provide (`api_key`) arguments. To use the Google Cloud API,'
            ' provide (`vertexai`, `project` & `location`) arguments.'
        )
      self._http_options.base_url = 'https://generativelanguage.googleapis.com/'
      self._http_options.api_version = 'v1beta'
    # Default options for both clients.
    self._http_options.headers = {'Content-Type': 'application/json'}
    if self.api_key:
      if self._http_options.headers is not None:
        self._http_options.headers['x-goog-api-key'] = self.api_key
    # Update the http options with the user provided http options.
    if http_options:
      self._http_options = _patch_http_options(
          self._http_options, validated_http_options
      )
    else:
      if self._http_options.headers is not None:
        _append_library_version_headers(self._http_options.headers)
    # Initialize the httpx client.
    self._httpx_client = SyncHttpxClient()
    self._async_httpx_client = AsyncHttpxClient()

  def _websocket_base_url(self):
    url_parts = urlparse(self._http_options.base_url)
    return url_parts._replace(scheme='wss').geturl()

  def _access_token(self) -> str:
    """Retrieves the access token for the credentials."""
    if not self._credentials:
      self._credentials, project = _load_auth(project=self.project)
      if not self.project:
        self.project = project

    if self._credentials:
      if self._credentials.expired or not self._credentials.token:
        # Only refresh when it needs to. Default expiration is 3600 seconds.
        _refresh_auth(self._credentials)
      if not self._credentials.token:
        raise RuntimeError('Could not resolve API token from the environment')
      return self._credentials.token
    else:
      raise RuntimeError('Could not resolve API token from the environment')

  async def _async_access_token(self) -> str:
    """Retrieves the access token for the credentials asynchronously."""
    if not self._credentials:
      async with self._auth_lock:
        # This ensures that only one coroutine can execute the auth logic at a
        # time for thread safety.
        if not self._credentials:
          # Double check that the credentials are not set before loading them.
          self._credentials, project = await asyncio.to_thread(
              _load_auth, project=self.project
          )
          if not self.project:
            self.project = project

    if self._credentials:
      if self._credentials.expired or not self._credentials.token:
        # Only refresh when it needs to. Default expiration is 3600 seconds.
        async with self._auth_lock:
          if self._credentials.expired or not self._credentials.token:
            # Double check that the credentials expired before refreshing.
            await asyncio.to_thread(_refresh_auth, self._credentials)

      if not self._credentials.token:
        raise RuntimeError('Could not resolve API token from the environment')

      return self._credentials.token
    else:
      raise RuntimeError('Could not resolve API token from the environment')

  def _build_request(
      self,
      http_method: str,
      path: str,
      request_dict: dict[str, object],
      http_options: Optional[HttpOptionsOrDict] = None,
  ) -> HttpRequest:
    # Remove all special dict keys such as _url and _query.
    keys_to_delete = [key for key in request_dict.keys() if key.startswith('_')]
    for key in keys_to_delete:
      del request_dict[key]
    # patch the http options with the user provided settings.
    if http_options:
      if isinstance(http_options, HttpOptions):
        patched_http_options = _patch_http_options(
            self._http_options,
            http_options,
        )
      else:
        patched_http_options = _patch_http_options(
            self._http_options, HttpOptions.model_validate(http_options)
        )
    else:
      patched_http_options = self._http_options
    # Skip adding project and locations when getting Vertex AI base models.
    query_vertex_base_models = False
    if (
        self.vertexai
        and http_method == 'get'
        and path.startswith('publishers/google/models')
    ):
      query_vertex_base_models = True
    if (
        self.vertexai
        and not path.startswith('projects/')
        and not query_vertex_base_models
        and not self.api_key
    ):
      path = f'projects/{self.project}/locations/{self.location}/' + path

    if patched_http_options.api_version is None:
      versioned_path = f'/{path}'
    else:
      versioned_path = f'{patched_http_options.api_version}/{path}'

    if (
        patched_http_options.base_url is None
        or not patched_http_options.base_url
    ):
      raise ValueError('Base URL must be set.')
    else:
      base_url = patched_http_options.base_url

    url = _join_url_path(
        base_url,
        versioned_path,
    )

    timeout_in_seconds = _get_timeout_in_seconds(patched_http_options.timeout)

    if patched_http_options.headers is None:
      raise ValueError('Request headers must be set.')
    return HttpRequest(
        method=http_method,
        url=url,
        headers=patched_http_options.headers,
        data=request_dict,
        timeout=timeout_in_seconds,
    )

  def _request(
      self,
      http_request: HttpRequest,
      stream: bool = False,
  ) -> HttpResponse:
    data: Optional[Union[str, bytes]] = None
    if self.vertexai and not self.api_key:
      http_request.headers['Authorization'] = f'Bearer {self._access_token()}'
      if self._credentials and self._credentials.quota_project_id:
        http_request.headers['x-goog-user-project'] = (
            self._credentials.quota_project_id
        )
      data = json.dumps(http_request.data) if http_request.data else None
    else:
      if http_request.data:
        if not isinstance(http_request.data, bytes):
          data = json.dumps(http_request.data) if http_request.data else None
        else:
          data = http_request.data

    if stream:
      httpx_request = self._httpx_client.build_request(
          method=http_request.method,
          url=http_request.url,
          content=data,
          headers=http_request.headers,
          timeout=http_request.timeout,
      )
      response = self._httpx_client.send(httpx_request, stream=stream)
      errors.APIError.raise_for_response(response)
      return HttpResponse(
          response.headers, response if stream else [response.text]
      )
    else:
      response = self._httpx_client.request(
          method=http_request.method,
          url=http_request.url,
          headers=http_request.headers,
          content=data,
          timeout=http_request.timeout,
      )
      errors.APIError.raise_for_response(response)
      return HttpResponse(
          response.headers, response if stream else [response.text]
      )

  async def _async_request(
      self, http_request: HttpRequest, stream: bool = False
  ):
    data: Optional[Union[str, bytes]] = None
    if self.vertexai and not self.api_key:
      http_request.headers['Authorization'] = (
          f'Bearer {await self._async_access_token()}'
      )
      if self._credentials and self._credentials.quota_project_id:
        http_request.headers['x-goog-user-project'] = (
            self._credentials.quota_project_id
        )
      data = json.dumps(http_request.data) if http_request.data else None
    else:
      if http_request.data:
        if not isinstance(http_request.data, bytes):
          data = json.dumps(http_request.data) if http_request.data else None
        else:
          data = http_request.data

    if stream:
      httpx_request = self._async_httpx_client.build_request(
          method=http_request.method,
          url=http_request.url,
          content=data,
          headers=http_request.headers,
          timeout=http_request.timeout,
      )
      response = await self._async_httpx_client.send(
          httpx_request,
          stream=stream,
      )
      await errors.APIError.raise_for_async_response(response)
      return HttpResponse(
          response.headers, response if stream else [response.text]
      )
    else:
      response = await self._async_httpx_client.request(
          method=http_request.method,
          url=http_request.url,
          headers=http_request.headers,
          content=data,
          timeout=http_request.timeout,
      )
      await errors.APIError.raise_for_async_response(response)
      return HttpResponse(
          response.headers, response if stream else [response.text]
      )

  def get_read_only_http_options(self) -> dict[str, Any]:
    if isinstance(self._http_options, BaseModel):
      copied = self._http_options.model_dump()
    else:
      copied = self._http_options
    return copied

  def request(
      self,
      http_method: str,
      path: str,
      request_dict: dict[str, object],
      http_options: Optional[HttpOptionsOrDict] = None,
  ):
    http_request = self._build_request(
        http_method, path, request_dict, http_options
    )
    response = self._request(http_request, stream=False)
    json_response = response.json
    if not json_response:
      return BaseResponse(http_headers=response.headers).model_dump(
          by_alias=True
      )
    return json_response

  def request_streamed(
      self,
      http_method: str,
      path: str,
      request_dict: dict[str, object],
      http_options: Optional[HttpOptionsOrDict] = None,
  ):
    http_request = self._build_request(
        http_method, path, request_dict, http_options
    )

    session_response = self._request(http_request, stream=True)
    for chunk in session_response.segments():
      yield chunk

  async def async_request(
      self,
      http_method: str,
      path: str,
      request_dict: dict[str, object],
      http_options: Optional[HttpOptionsOrDict] = None,
  ) -> dict[str, object]:
    http_request = self._build_request(
        http_method, path, request_dict, http_options
    )

    result = await self._async_request(http_request=http_request, stream=False)
    json_response = result.json
    if not json_response:
      return BaseResponse(http_headers=result.headers).model_dump(by_alias=True)
    return json_response

  async def async_request_streamed(
      self,
      http_method: str,
      path: str,
      request_dict: dict[str, object],
      http_options: Optional[HttpOptionsOrDict] = None,
  ):
    http_request = self._build_request(
        http_method, path, request_dict, http_options
    )

    response = await self._async_request(http_request=http_request, stream=True)

    async def async_generator():
      async for chunk in response:
        yield chunk

    return async_generator()

  def upload_file(
      self,
      file_path: Union[str, io.IOBase],
      upload_url: str,
      upload_size: int,
      *,
      http_options: Optional[HttpOptionsOrDict] = None,
  ) -> HttpResponse:
    """Transfers a file to the given URL.

    Args:
      file_path: The full path to the file or a file like object inherited from
        io.BytesIO. If the local file path is not found, an error will be
        raised.
      upload_url: The URL to upload the file to.
      upload_size: The size of file content to be uploaded, this will have to
        match the size requested in the resumable upload request.
      http_options: The http options to use for the request.

    returns:
          The HttpResponse object from the finalize request.
    """
    if isinstance(file_path, io.IOBase):
      return self._upload_fd(
          file_path, upload_url, upload_size, http_options=http_options
      )
    else:
      with open(file_path, 'rb') as file:
        return self._upload_fd(
            file, upload_url, upload_size, http_options=http_options
        )

  def _upload_fd(
      self,
      file: io.IOBase,
      upload_url: str,
      upload_size: int,
      *,
      http_options: Optional[HttpOptionsOrDict] = None,
  ) -> HttpResponse:
    """Transfers a file to the given URL.

    Args:
      file: A file like object inherited from io.BytesIO.
      upload_url: The URL to upload the file to.
      upload_size: The size of file content to be uploaded, this will have to
        match the size requested in the resumable upload request.
      http_options: The http options to use for the request.

    returns:
          The HttpResponse object from the finalize request.
    """
    offset = 0
    # Upload the file in chunks
    while True:
      file_chunk = file.read(CHUNK_SIZE)
      chunk_size = 0
      if file_chunk:
        chunk_size = len(file_chunk)
      upload_command = 'upload'
      # If last chunk, finalize the upload.
      if chunk_size + offset >= upload_size:
        upload_command += ', finalize'
      http_options = http_options if http_options else self._http_options
      timeout = (
          http_options.get('timeout')
          if isinstance(http_options, dict)
          else http_options.timeout
      )
      if timeout is None:
        # Per request timeout is not configured. Check the global timeout.
        timeout = (
            self._http_options.timeout
            if isinstance(self._http_options, dict)
            else self._http_options.timeout
        )
      timeout_in_seconds = _get_timeout_in_seconds(timeout)
      response = self._httpx_client.request(
          method='POST',
          url=upload_url,
          headers={
              'X-Goog-Upload-Command': upload_command,
              'X-Goog-Upload-Offset': str(offset),
              'Content-Length': str(chunk_size),
          },
          content=file_chunk,
          timeout=timeout_in_seconds,
      )
      offset += chunk_size
      if response.headers['x-goog-upload-status'] != 'active':
        break  # upload is complete or it has been interrupted.
      if upload_size <= offset:  # Status is not finalized.
        raise ValueError(
            f'All content has been uploaded, but the upload status is not'
            f' finalized.'
        )

    if response.headers['x-goog-upload-status'] != 'final':
      raise ValueError(
          'Failed to upload file: Upload status is not finalized.'
      )
    return HttpResponse(response.headers, response_stream=[response.text])

  def download_file(
      self,
      path: str,
      *,
      http_options: Optional[HttpOptionsOrDict] = None,
  ):
    """Downloads the file data.

    Args:
      path: The request path with query params.
      http_options: The http options to use for the request.

    returns:
          The file bytes
    """
    http_request = self._build_request(
        'get', path=path, request_dict={}, http_options=http_options
    )

    data: Optional[Union[str, bytes]] = None
    if http_request.data:
      if not isinstance(http_request.data, bytes):
        data = json.dumps(http_request.data)
      else:
        data = http_request.data

    response = self._httpx_client.request(
        method=http_request.method,
        url=http_request.url,
        headers=http_request.headers,
        content=data,
        timeout=http_request.timeout,
    )

    errors.APIError.raise_for_response(response)
    return HttpResponse(
        response.headers, byte_stream=[response.read()]
    ).byte_stream[0]

  async def async_upload_file(
      self,
      file_path: Union[str, io.IOBase],
      upload_url: str,
      upload_size: int,
      *,
      http_options: Optional[HttpOptionsOrDict] = None,
  ) -> HttpResponse:
    """Transfers a file asynchronously to the given URL.

    Args:
      file_path: The full path to the file. If the local file path is not found,
        an error will be raised.
      upload_url: The URL to upload the file to.
      upload_size: The size of file content to be uploaded, this will have to
        match the size requested in the resumable upload request.
      http_options: The http options to use for the request.

    returns:
          The HttpResponse object from the finalize request.
    """
    if isinstance(file_path, io.IOBase):
      return await self._async_upload_fd(
          file_path, upload_url, upload_size, http_options=http_options
      )
    else:
      file = anyio.Path(file_path)
      fd = await file.open('rb')
      async with fd:
        return await self._async_upload_fd(
            fd, upload_url, upload_size, http_options=http_options
        )

  async def _async_upload_fd(
      self,
      file: Union[io.IOBase, anyio.AsyncFile],
      upload_url: str,
      upload_size: int,
      *,
      http_options: Optional[HttpOptionsOrDict] = None,
  ) -> HttpResponse:
    """Transfers a file asynchronously to the given URL.

    Args:
      file: A file like object inherited from io.BytesIO.
      upload_url: The URL to upload the file to.
      upload_size: The size of file content to be uploaded, this will have to
        match the size requested in the resumable upload request.
      http_options: The http options to use for the request.

    returns:
          The HttpResponse object from the finalized request.
    """
    offset = 0
    # Upload the file in chunks
    while True:
      if isinstance(file, io.IOBase):
        file_chunk = file.read(CHUNK_SIZE)
      else:
        file_chunk = await file.read(CHUNK_SIZE)
      chunk_size = 0
      if file_chunk:
        chunk_size = len(file_chunk)
      upload_command = 'upload'
      # If last chunk, finalize the upload.
      if chunk_size + offset >= upload_size:
        upload_command += ', finalize'
      http_options = http_options if http_options else self._http_options
      timeout = (
          http_options.get('timeout')
          if isinstance(http_options, dict)
          else http_options.timeout
      )
      if timeout is None:
        # Per request timeout is not configured. Check the global timeout.
        timeout = (
            self._http_options.timeout
            if isinstance(self._http_options, dict)
            else self._http_options.timeout
        )
      timeout_in_seconds = _get_timeout_in_seconds(timeout)
      response = await self._async_httpx_client.request(
          method='POST',
          url=upload_url,
          content=file_chunk,
          headers={
              'X-Goog-Upload-Command': upload_command,
              'X-Goog-Upload-Offset': str(offset),
              'Content-Length': str(chunk_size),
          },
          timeout=timeout_in_seconds,
      )
      offset += chunk_size
      if response.headers.get('x-goog-upload-status') != 'active':
        break  # upload is complete or it has been interrupted.

      if upload_size <= offset:  # Status is not finalized.
        raise ValueError(
            'All content has been uploaded, but the upload status is not'
            f' finalized.'
        )
    if response.headers.get('x-goog-upload-status') != 'final':
      raise ValueError(
          'Failed to upload file: Upload status is not finalized.'
      )
    return HttpResponse(response.headers, response_stream=[response.text])

  async def async_download_file(
      self,
      path: str,
      *,
      http_options: Optional[HttpOptionsOrDict] = None,
  ):
    """Downloads the file data.

    Args:
      path: The request path with query params.
      http_options: The http options to use for the request.

    returns:
          The file bytes
    """
    http_request = self._build_request(
        'get', path=path, request_dict={}, http_options=http_options
    )

    data: Optional[Union[str, bytes]] = None
    if http_request.data:
      if not isinstance(http_request.data, bytes):
        data = json.dumps(http_request.data)
      else:
        data = http_request.data

    response = await self._async_httpx_client.request(
        method=http_request.method,
        url=http_request.url,
        headers=http_request.headers,
        content=data,
        timeout=http_request.timeout,
    )
    await errors.APIError.raise_for_async_response(response)

    return HttpResponse(
        response.headers, byte_stream=[response.read()]
    ).byte_stream[0]

  # This method does nothing in the real api client. It is used in the
  # replay_api_client to verify the response from the SDK method matches the
  # recorded response.
  def _verify_response(self, response_model: _common.BaseModel):
    pass
