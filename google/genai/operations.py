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

# Code generated by the Google Gen AI SDK generator DO NOT EDIT.

import logging
from typing import Any, Optional, Union
from urllib.parse import urlencode
from . import _api_module
from . import _common
from . import _transformers as t
from . import types
from ._api_client import BaseApiClient
from ._common import get_value_by_path as getv
from ._common import set_value_by_path as setv

logger = logging.getLogger('google_genai.operations')


def _GetOperationParameters_to_mldev(
    api_client: BaseApiClient,
    from_object: Union[dict, object],
    parent_object: Optional[dict] = None,
) -> dict:
  to_object: dict[str, Any] = {}
  if getv(from_object, ['operation_name']) is not None:
    setv(
        to_object,
        ['_url', 'operationName'],
        getv(from_object, ['operation_name']),
    )

  if getv(from_object, ['config']) is not None:
    setv(to_object, ['config'], getv(from_object, ['config']))

  return to_object


def _GetOperationParameters_to_vertex(
    api_client: BaseApiClient,
    from_object: Union[dict, object],
    parent_object: Optional[dict] = None,
) -> dict:
  to_object: dict[str, Any] = {}
  if getv(from_object, ['operation_name']) is not None:
    setv(
        to_object,
        ['_url', 'operationName'],
        getv(from_object, ['operation_name']),
    )

  if getv(from_object, ['config']) is not None:
    setv(to_object, ['config'], getv(from_object, ['config']))

  return to_object


def _FetchPredictOperationParameters_to_mldev(
    api_client: BaseApiClient,
    from_object: Union[dict, object],
    parent_object: Optional[dict] = None,
) -> dict:
  to_object: dict[str, Any] = {}
  if getv(from_object, ['operation_name']) is not None:
    raise ValueError('operation_name parameter is not supported in Gemini API.')

  if getv(from_object, ['resource_name']) is not None:
    raise ValueError('resource_name parameter is not supported in Gemini API.')

  if getv(from_object, ['config']) is not None:
    raise ValueError('config parameter is not supported in Gemini API.')

  return to_object


def _FetchPredictOperationParameters_to_vertex(
    api_client: BaseApiClient,
    from_object: Union[dict, object],
    parent_object: Optional[dict] = None,
) -> dict:
  to_object: dict[str, Any] = {}
  if getv(from_object, ['operation_name']) is not None:
    setv(to_object, ['operationName'], getv(from_object, ['operation_name']))

  if getv(from_object, ['resource_name']) is not None:
    setv(
        to_object,
        ['_url', 'resourceName'],
        getv(from_object, ['resource_name']),
    )

  if getv(from_object, ['config']) is not None:
    setv(to_object, ['config'], getv(from_object, ['config']))

  return to_object


def _Video_from_mldev(
    api_client: BaseApiClient,
    from_object: Union[dict, object],
    parent_object: Optional[dict] = None,
) -> dict:
  to_object: dict[str, Any] = {}
  if getv(from_object, ['video', 'uri']) is not None:
    setv(to_object, ['uri'], getv(from_object, ['video', 'uri']))

  if getv(from_object, ['video', 'encodedVideo']) is not None:
    setv(
        to_object,
        ['video_bytes'],
        t.t_bytes(api_client, getv(from_object, ['video', 'encodedVideo'])),
    )

  if getv(from_object, ['encoding']) is not None:
    setv(to_object, ['mime_type'], getv(from_object, ['encoding']))

  return to_object


def _Video_from_vertex(
    api_client: BaseApiClient,
    from_object: Union[dict, object],
    parent_object: Optional[dict] = None,
) -> dict:
  to_object: dict[str, Any] = {}
  if getv(from_object, ['gcsUri']) is not None:
    setv(to_object, ['uri'], getv(from_object, ['gcsUri']))

  if getv(from_object, ['bytesBase64Encoded']) is not None:
    setv(
        to_object,
        ['video_bytes'],
        t.t_bytes(api_client, getv(from_object, ['bytesBase64Encoded'])),
    )

  if getv(from_object, ['mimeType']) is not None:
    setv(to_object, ['mime_type'], getv(from_object, ['mimeType']))

  return to_object


def _GeneratedVideo_from_mldev(
    api_client: BaseApiClient,
    from_object: Union[dict, object],
    parent_object: Optional[dict] = None,
) -> dict:
  to_object: dict[str, Any] = {}
  if getv(from_object, ['_self']) is not None:
    setv(
        to_object,
        ['video'],
        _Video_from_mldev(api_client, getv(from_object, ['_self']), to_object),
    )

  return to_object


def _GeneratedVideo_from_vertex(
    api_client: BaseApiClient,
    from_object: Union[dict, object],
    parent_object: Optional[dict] = None,
) -> dict:
  to_object: dict[str, Any] = {}
  if getv(from_object, ['_self']) is not None:
    setv(
        to_object,
        ['video'],
        _Video_from_vertex(api_client, getv(from_object, ['_self']), to_object),
    )

  return to_object


def _GenerateVideosResponse_from_mldev(
    api_client: BaseApiClient,
    from_object: Union[dict, object],
    parent_object: Optional[dict] = None,
) -> dict:
  to_object: dict[str, Any] = {}
  if getv(from_object, ['generatedSamples']) is not None:
    setv(
        to_object,
        ['generated_videos'],
        [
            _GeneratedVideo_from_mldev(api_client, item, to_object)
            for item in getv(from_object, ['generatedSamples'])
        ],
    )

  if getv(from_object, ['raiMediaFilteredCount']) is not None:
    setv(
        to_object,
        ['rai_media_filtered_count'],
        getv(from_object, ['raiMediaFilteredCount']),
    )

  if getv(from_object, ['raiMediaFilteredReasons']) is not None:
    setv(
        to_object,
        ['rai_media_filtered_reasons'],
        getv(from_object, ['raiMediaFilteredReasons']),
    )

  return to_object


def _GenerateVideosResponse_from_vertex(
    api_client: BaseApiClient,
    from_object: Union[dict, object],
    parent_object: Optional[dict] = None,
) -> dict:
  to_object: dict[str, Any] = {}
  if getv(from_object, ['videos']) is not None:
    setv(
        to_object,
        ['generated_videos'],
        [
            _GeneratedVideo_from_vertex(api_client, item, to_object)
            for item in getv(from_object, ['videos'])
        ],
    )

  if getv(from_object, ['raiMediaFilteredCount']) is not None:
    setv(
        to_object,
        ['rai_media_filtered_count'],
        getv(from_object, ['raiMediaFilteredCount']),
    )

  if getv(from_object, ['raiMediaFilteredReasons']) is not None:
    setv(
        to_object,
        ['rai_media_filtered_reasons'],
        getv(from_object, ['raiMediaFilteredReasons']),
    )

  return to_object


def _GenerateVideosOperation_from_mldev(
    api_client: BaseApiClient,
    from_object: Union[dict, object],
    parent_object: Optional[dict] = None,
) -> dict:
  to_object: dict[str, Any] = {}
  if getv(from_object, ['name']) is not None:
    setv(to_object, ['name'], getv(from_object, ['name']))

  if getv(from_object, ['metadata']) is not None:
    setv(to_object, ['metadata'], getv(from_object, ['metadata']))

  if getv(from_object, ['done']) is not None:
    setv(to_object, ['done'], getv(from_object, ['done']))

  if getv(from_object, ['error']) is not None:
    setv(to_object, ['error'], getv(from_object, ['error']))

  if getv(from_object, ['response']) is not None:
    setv(to_object, ['response'], getv(from_object, ['response']))

  if getv(from_object, ['response', 'generateVideoResponse']) is not None:
    setv(
        to_object,
        ['result'],
        _GenerateVideosResponse_from_mldev(
            api_client,
            getv(from_object, ['response', 'generateVideoResponse']),
            to_object,
        ),
    )

  return to_object


def _GenerateVideosOperation_from_vertex(
    api_client: BaseApiClient,
    from_object: Union[dict, object],
    parent_object: Optional[dict] = None,
) -> dict:
  to_object: dict[str, Any] = {}
  if getv(from_object, ['name']) is not None:
    setv(to_object, ['name'], getv(from_object, ['name']))

  if getv(from_object, ['metadata']) is not None:
    setv(to_object, ['metadata'], getv(from_object, ['metadata']))

  if getv(from_object, ['done']) is not None:
    setv(to_object, ['done'], getv(from_object, ['done']))

  if getv(from_object, ['error']) is not None:
    setv(to_object, ['error'], getv(from_object, ['error']))

  if getv(from_object, ['response']) is not None:
    setv(to_object, ['response'], getv(from_object, ['response']))

  if getv(from_object, ['response']) is not None:
    setv(
        to_object,
        ['result'],
        _GenerateVideosResponse_from_vertex(
            api_client, getv(from_object, ['response']), to_object
        ),
    )

  return to_object


class Operations(_api_module.BaseModule):

  def _get_operation(
      self,
      *,
      operation_name: str,
      config: Optional[types.GetOperationConfigOrDict] = None,
  ) -> types.GenerateVideosOperation:
    parameter_model = types._GetOperationParameters(
        operation_name=operation_name,
        config=config,
    )

    request_url_dict: Optional[dict[str, str]]

    if self._api_client.vertexai:
      request_dict = _GetOperationParameters_to_vertex(
          self._api_client, parameter_model
      )
      request_url_dict = request_dict.get('_url')
      if request_url_dict:
        path = '{operationName}'.format_map(request_url_dict)
      else:
        path = '{operationName}'
    else:
      request_dict = _GetOperationParameters_to_mldev(
          self._api_client, parameter_model
      )
      request_url_dict = request_dict.get('_url')
      if request_url_dict:
        path = '{operationName}'.format_map(request_url_dict)
      else:
        path = '{operationName}'
    query_params = request_dict.get('_query')
    if query_params:
      path = f'{path}?{urlencode(query_params)}'
    # TODO: remove the hack that pops config.
    request_dict.pop('config', None)

    http_options: Optional[types.HttpOptions] = None
    if (
        parameter_model.config is not None
        and parameter_model.config.http_options is not None
    ):
      http_options = parameter_model.config.http_options

    request_dict = _common.convert_to_dict(request_dict)
    request_dict = _common.encode_unserializable_types(request_dict)

    response_dict = self._api_client.request(
        'get', path, request_dict, http_options
    )

    if self._api_client.vertexai:
      response_dict = _GenerateVideosOperation_from_vertex(
          self._api_client, response_dict
      )
    else:
      response_dict = _GenerateVideosOperation_from_mldev(
          self._api_client, response_dict
      )

    return_value = types.GenerateVideosOperation._from_response(
        response=response_dict, kwargs=parameter_model.model_dump()
    )
    self._api_client._verify_response(return_value)
    return return_value

  def _fetch_predict_operation(
      self,
      *,
      operation_name: str,
      resource_name: str,
      config: Optional[types.FetchPredictOperationConfigOrDict] = None,
  ) -> types.GenerateVideosOperation:
    parameter_model = types._FetchPredictOperationParameters(
        operation_name=operation_name,
        resource_name=resource_name,
        config=config,
    )

    request_url_dict: Optional[dict[str, str]]
    if not self._api_client.vertexai:
      raise ValueError('This method is only supported in the Vertex AI client.')
    else:
      request_dict = _FetchPredictOperationParameters_to_vertex(
          self._api_client, parameter_model
      )
      request_url_dict = request_dict.get('_url')
      if request_url_dict:
        path = '{resourceName}:fetchPredictOperation'.format_map(
            request_url_dict
        )
      else:
        path = '{resourceName}:fetchPredictOperation'

    query_params = request_dict.get('_query')
    if query_params:
      path = f'{path}?{urlencode(query_params)}'
    # TODO: remove the hack that pops config.
    request_dict.pop('config', None)

    http_options: Optional[types.HttpOptions] = None
    if (
        parameter_model.config is not None
        and parameter_model.config.http_options is not None
    ):
      http_options = parameter_model.config.http_options

    request_dict = _common.convert_to_dict(request_dict)
    request_dict = _common.encode_unserializable_types(request_dict)

    response_dict = self._api_client.request(
        'post', path, request_dict, http_options
    )

    if self._api_client.vertexai:
      response_dict = _GenerateVideosOperation_from_vertex(
          self._api_client, response_dict
      )
    else:
      response_dict = _GenerateVideosOperation_from_mldev(
          self._api_client, response_dict
      )

    return_value = types.GenerateVideosOperation._from_response(
        response=response_dict, kwargs=parameter_model.model_dump()
    )
    self._api_client._verify_response(return_value)
    return return_value

  @_common.experimental_warning(
      'This method is experimental and may change in future versions.'
  )
  def get(
      self,
      operation: types.GenerateVideosOperation,
      *,
      config: Optional[types.GetOperationConfigOrDict] = None,
  ) -> types.GenerateVideosOperation:
    """Gets the status of an operation."""
    # Currently, only GenerateVideosOperation is supported.
    # TODO(b/398040607): Support short form names
    operation_name = operation.name
    if not operation_name:
      raise ValueError('Operation name is empty.')

    # TODO(b/398233524): Cast operation types
    if self._api_client.vertexai:
      resource_name = operation_name.rpartition('/operations/')[0]
      http_options = types.HttpOptions()
      if isinstance(config, dict):
        dict_options = config.get('http_options', None)
        if dict_options is not None:
          http_options = types.HttpOptions(**dict(dict_options))
      elif isinstance(config, types.GetOperationConfig) and config is not None:
        http_options = (
            config.http_options
            if config.http_options is not None
            else types.HttpOptions()
        )
      fetch_operation_config = types.FetchPredictOperationConfig(
          http_options=http_options
      )
      return self._fetch_predict_operation(
          operation_name=operation_name,
          resource_name=resource_name,
          config=fetch_operation_config,
      )
    else:
      return self._get_operation(
          operation_name=operation_name,
          config=config,
      )


class AsyncOperations(_api_module.BaseModule):

  async def _get_operation(
      self,
      *,
      operation_name: str,
      config: Optional[types.GetOperationConfigOrDict] = None,
  ) -> types.GenerateVideosOperation:
    parameter_model = types._GetOperationParameters(
        operation_name=operation_name,
        config=config,
    )

    request_url_dict: Optional[dict[str, str]]

    if self._api_client.vertexai:
      request_dict = _GetOperationParameters_to_vertex(
          self._api_client, parameter_model
      )
      request_url_dict = request_dict.get('_url')
      if request_url_dict:
        path = '{operationName}'.format_map(request_url_dict)
      else:
        path = '{operationName}'
    else:
      request_dict = _GetOperationParameters_to_mldev(
          self._api_client, parameter_model
      )
      request_url_dict = request_dict.get('_url')
      if request_url_dict:
        path = '{operationName}'.format_map(request_url_dict)
      else:
        path = '{operationName}'
    query_params = request_dict.get('_query')
    if query_params:
      path = f'{path}?{urlencode(query_params)}'
    # TODO: remove the hack that pops config.
    request_dict.pop('config', None)

    http_options: Optional[types.HttpOptions] = None
    if (
        parameter_model.config is not None
        and parameter_model.config.http_options is not None
    ):
      http_options = parameter_model.config.http_options

    request_dict = _common.convert_to_dict(request_dict)
    request_dict = _common.encode_unserializable_types(request_dict)

    response_dict = await self._api_client.async_request(
        'get', path, request_dict, http_options
    )

    if self._api_client.vertexai:
      response_dict = _GenerateVideosOperation_from_vertex(
          self._api_client, response_dict
      )
    else:
      response_dict = _GenerateVideosOperation_from_mldev(
          self._api_client, response_dict
      )

    return_value = types.GenerateVideosOperation._from_response(
        response=response_dict, kwargs=parameter_model.model_dump()
    )
    self._api_client._verify_response(return_value)
    return return_value

  async def _fetch_predict_operation(
      self,
      *,
      operation_name: str,
      resource_name: str,
      config: Optional[types.FetchPredictOperationConfigOrDict] = None,
  ) -> types.GenerateVideosOperation:
    parameter_model = types._FetchPredictOperationParameters(
        operation_name=operation_name,
        resource_name=resource_name,
        config=config,
    )

    request_url_dict: Optional[dict[str, str]]
    if not self._api_client.vertexai:
      raise ValueError('This method is only supported in the Vertex AI client.')
    else:
      request_dict = _FetchPredictOperationParameters_to_vertex(
          self._api_client, parameter_model
      )
      request_url_dict = request_dict.get('_url')
      if request_url_dict:
        path = '{resourceName}:fetchPredictOperation'.format_map(
            request_url_dict
        )
      else:
        path = '{resourceName}:fetchPredictOperation'

    query_params = request_dict.get('_query')
    if query_params:
      path = f'{path}?{urlencode(query_params)}'
    # TODO: remove the hack that pops config.
    request_dict.pop('config', None)

    http_options: Optional[types.HttpOptions] = None
    if (
        parameter_model.config is not None
        and parameter_model.config.http_options is not None
    ):
      http_options = parameter_model.config.http_options

    request_dict = _common.convert_to_dict(request_dict)
    request_dict = _common.encode_unserializable_types(request_dict)

    response_dict = await self._api_client.async_request(
        'post', path, request_dict, http_options
    )

    if self._api_client.vertexai:
      response_dict = _GenerateVideosOperation_from_vertex(
          self._api_client, response_dict
      )
    else:
      response_dict = _GenerateVideosOperation_from_mldev(
          self._api_client, response_dict
      )

    return_value = types.GenerateVideosOperation._from_response(
        response=response_dict, kwargs=parameter_model.model_dump()
    )
    self._api_client._verify_response(return_value)
    return return_value

  @_common.experimental_warning(
      'This method is experimental and may change in future versions.'
  )
  async def get(
      self,
      operation: types.GenerateVideosOperation,
      *,
      config: Optional[types.GetOperationConfigOrDict] = None,
  ) -> types.GenerateVideosOperation:
    """Gets the status of an operation."""
    # Currently, only GenerateVideosOperation is supported.
    operation_name = operation.name
    if not operation_name:
      raise ValueError('Operation name is empty.')

    if self._api_client.vertexai:
      resource_name = operation_name.rpartition('/operations/')[0]
      http_options = types.HttpOptions()
      if isinstance(config, dict):
        dict_options = config.get('http_options', None)
        if dict_options is not None:
          http_options = types.HttpOptions(**dict(dict_options))
      elif isinstance(config, types.GetOperationConfig) and config is not None:
        http_options = (
            config.http_options
            if config.http_options is not None
            else types.HttpOptions()
        )
      fetch_operation_config = types.FetchPredictOperationConfig(
          http_options=http_options
      )
      return await self._fetch_predict_operation(
          operation_name=operation_name,
          resource_name=resource_name,
          config=fetch_operation_config,
      )
    else:
      return await self._get_operation(
          operation_name=operation_name,
          config=config,
      )
