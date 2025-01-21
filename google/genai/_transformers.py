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

"""Transformers for Google GenAI SDK."""

import base64
from collections.abc import Iterable, Mapping
import inspect
import io
import re
import time
import typing
from typing import Any, GenericAlias, Optional, Union

import PIL.Image
import PIL.PngImagePlugin
import pydantic

from . import _api_client
from . import types


def _resource_name(
    client: _api_client.ApiClient,
    resource_name: str,
    *,
    collection_identifier: str,
    collection_hierarchy_depth: int = 2,
):
  # pylint: disable=line-too-long
  """Prepends resource name with project, location, collection_identifier if needed.

  The collection_identifier will only be prepended if it's not present
  and the prepending won't violate the collection hierarchy depth.
  When the prepending condition doesn't meet, returns the input
  resource_name.

  Args:
    client: The API client.
    resource_name: The user input resource name to be completed.
    collection_identifier: The collection identifier to be prepended.
        See collection identifiers in https://google.aip.dev/122.
    collection_hierarchy_depth: The collection hierarchy depth.
        Only set this field when the resource has nested collections.
        For example, `users/vhugo1802/events/birthday-dinner-226`, the
        collection_identifier is `users` and collection_hierarchy_depth is 4.
        See nested collections in https://google.aip.dev/122.

  Example:

    resource_name = 'cachedContents/123'
    client.vertexai = True
    client.project = 'bar'
    client.location = 'us-west1'
    _resource_name(client, 'cachedContents/123', collection_identifier='cachedContents')
    returns: 'projects/bar/locations/us-west1/cachedContents/123'

  Example:

    resource_name = 'projects/foo/locations/us-central1/cachedContents/123'
    # resource_name = 'locations/us-central1/cachedContents/123'
    client.vertexai = True
    client.project = 'bar'
    client.location = 'us-west1'
    _resource_name(client, resource_name, collection_identifier='cachedContents')
    returns: 'projects/foo/locations/us-central1/cachedContents/123'

  Example:

    resource_name = '123'
    # resource_name = 'cachedContents/123'
    client.vertexai = False
    _resource_name(client, resource_name, collection_identifier='cachedContents')
    returns 'cachedContents/123'

  Example:
    resource_name = 'some/wrong/cachedContents/resource/name/123'
    resource_prefix = 'cachedContents'
    client.vertexai = False
    # client.vertexai = True
    _resource_name(client, resource_name, collection_identifier='cachedContents')
    returns: 'some/wrong/cachedContents/resource/name/123'

  Returns:
    The completed resource name.
  """
  should_prepend_collection_identifier = (
      not resource_name.startswith(f'{collection_identifier}/')
      # Check if prepending the collection identifier won't violate the
      # collection hierarchy depth.
      and f'{collection_identifier}/{resource_name}'.count('/') + 1
      == collection_hierarchy_depth
  )
  if client.vertexai:
    if resource_name.startswith('projects/'):
      return resource_name
    elif resource_name.startswith('locations/'):
      return f'projects/{client.project}/{resource_name}'
    elif resource_name.startswith(f'{collection_identifier}/'):
      return f'projects/{client.project}/locations/{client.location}/{resource_name}'
    elif should_prepend_collection_identifier:
      return f'projects/{client.project}/locations/{client.location}/{collection_identifier}/{resource_name}'
    else:
      return resource_name
  else:
    if should_prepend_collection_identifier:
      return f'{collection_identifier}/{resource_name}'
    else:
      return resource_name


def t_model(client: _api_client.ApiClient, model: str):
  if not model:
    raise ValueError('model is required.')
  if client.vertexai:
    if (
        model.startswith('projects/')
        or model.startswith('models/')
        or model.startswith('publishers/')
    ):
      return model
    elif '/' in model:
      publisher, model_id = model.split('/', 1)
      return f'publishers/{publisher}/models/{model_id}'
    else:
      return f'publishers/google/models/{model}'
  else:
    if model.startswith('models/'):
      return model
    elif model.startswith('tunedModels/'):
      return model
    else:
      return f'models/{model}'

def t_models_url(api_client: _api_client.ApiClient, base_models: bool) -> str:
  if api_client.vertexai:
    if base_models:
      return 'publishers/google/models'
    else:
      return 'models'
  else:
    if base_models:
      return 'models'
    else:
      return 'tunedModels'


def t_extract_models(api_client: _api_client.ApiClient, response: dict) -> list[types.Model]:
  if not response:
    return []
  elif response.get('models') is not None:
    return response.get('models')
  elif response.get('tunedModels') is not None:
    return response.get('tunedModels')
  elif response.get('publisherModels') is not None:
    return response.get('publisherModels')
  else:
    raise ValueError('Cannot determine the models type.')


def t_caches_model(api_client: _api_client.ApiClient, model: str):
  model = t_model(api_client, model)
  if not model:
    return None
  if model.startswith('publishers/') and api_client.vertexai:
    # vertex caches only support model name start with projects.
    return (
        f'projects/{api_client.project}/locations/{api_client.location}/{model}'
    )
  elif model.startswith('models/') and api_client.vertexai:
    return f'projects/{api_client.project}/locations/{api_client.location}/publishers/google/{model}'
  else:
    return model


def pil_to_blob(img):
  bytesio = io.BytesIO()
  if isinstance(img, PIL.PngImagePlugin.PngImageFile) or img.mode == 'RGBA':
    img.save(bytesio, format='PNG')
    mime_type = 'image/png'
  else:
    img.save(bytesio, format='JPEG')
    mime_type = 'image/jpeg'
  bytesio.seek(0)
  data = bytesio.read()
  return types.Blob(mime_type=mime_type, data=data)


PartType = Union[types.Part, types.PartDict, str, PIL.Image.Image]


def t_part(client: _api_client.ApiClient, part: PartType) -> types.Part:
  if not part:
    raise ValueError('content part is required.')
  if isinstance(part, str):
    return types.Part(text=part)
  if isinstance(part, PIL.Image.Image):
    return types.Part(inline_data=pil_to_blob(part))
  if isinstance(part, types.File):
    if not part.uri or not part.mime_type:
      raise ValueError('file uri and mime_type are required.')
    return types.Part.from_uri(part.uri, part.mime_type)
  else:
    return part


def t_parts(
    client: _api_client.ApiClient, parts: Union[list, PartType]
) -> list[types.Part]:
  if parts is None:
    raise ValueError('content parts are required.')
  if isinstance(parts, list):
    return [t_part(client, part) for part in parts]
  else:
    return [t_part(client, parts)]


def t_image_predictions(
    client: _api_client.ApiClient,
    predictions: Optional[Iterable[Mapping[str, Any]]],
) -> list[types.GeneratedImage]:
  if not predictions:
    return None
  images = []
  for prediction in predictions:
    if prediction.get('image'):
      images.append(
          types.GeneratedImage(
              image=types.Image(
                  gcs_uri=prediction['image']['gcsUri'],
                  image_bytes=prediction['image']['imageBytes'],
              )
          )
      )
  return images


ContentType = Union[types.Content, types.ContentDict, PartType]


def t_content(
    client: _api_client.ApiClient,
    content: ContentType,
):
  if not content:
    raise ValueError('content is required.')
  if isinstance(content, types.Content):
    return content
  if isinstance(content, dict):
    return types.Content.model_validate(content)
  return types.Content(role='user', parts=t_parts(client, content))


def t_contents_for_embed(
    client: _api_client.ApiClient,
    contents: Union[list[types.Content], list[types.ContentDict], ContentType],
):
  if client.vertexai and isinstance(contents, list):
    # TODO: Assert that only text is supported.
    return [t_content(client, content).parts[0].text for content in contents]
  elif client.vertexai:
    return [t_content(client, contents).parts[0].text]
  elif isinstance(contents, list):
    return [t_content(client, content) for content in contents]
  else:
    return [t_content(client, contents)]


def t_contents(
    client: _api_client.ApiClient,
    contents: Union[list[types.Content], list[types.ContentDict], ContentType],
):
  if not contents:
    raise ValueError('contents are required.')
  if isinstance(contents, list):
    return [t_content(client, content) for content in contents]
  else:
    return [t_content(client, contents)]


def process_schema(data: dict[str, Any],
                   client: Optional[_api_client.ApiClient]=None):
  if isinstance(data, dict):
    # Iterate over a copy of keys to allow deletion
    for key in list(data.keys()):
      # Only delete 'title'for the Gemini API
      if client and not client.vertexai and key == 'title':
        del data[key]
      else:
        process_schema(data[key], client)
  elif isinstance(data, list):
    for item in data:
      process_schema(item, client)

  return data


def _build_schema(fname: str, fields_dict: dict[str, Any]) -> dict[str, Any]:
  parameters = pydantic.create_model(fname, **fields_dict).model_json_schema()
  defs = parameters.pop('$defs', {})

  for _, value in defs.items():
    unpack_defs(value, defs)

  unpack_defs(parameters, defs)
  return parameters['properties']['dummy']


def unpack_defs(schema: dict[str, Any], defs: dict[str, Any]):
    """Unpacks the $defs values in the schema generated by pydantic so they can be understood by the API.

      Example of a schema before and after unpacking:
        Before:

        `schema`

        {'properties': {
            'dummy': {
                'items': {
                    '$ref': '#/$defs/CountryInfo'
                },
                'title': 'Dummy',
                'type': 'array'
                }
            },
            'required': ['dummy'],
            'title': 'dummy',
            'type': 'object'}

        `defs`

        {'CountryInfo': {'properties': {'continent': {'title': 'Continent', 'type': 'string'}, 'gdp': {'title': 'Gdp', 'type': 'integer'}}, 'required': ['continent', 'gdp'], 'title': 'CountryInfo', 'type': 'object'}}

        After:

        `schema`
        {'properties': {
            'continent': {'title': 'Continent', 'type': 'string'},
            'gdp': {'title': 'Gdp', 'type': 'integer'}
          },
          'required': ['continent', 'gdp'],
          'title': 'CountryInfo',
          'type': 'object'
        }

    """
    properties = schema.get('properties', None)
    if properties is None:
        return

    for name, value in properties.items():
        ref_key = value.get('$ref', None)
        if ref_key is not None:
            ref = defs[ref_key.split('defs/')[-1]]
            unpack_defs(ref, defs)
            properties[name] = ref
            continue

        anyof = value.get('anyOf', None)
        if anyof is not None:
            for i, atype in enumerate(anyof):
                ref_key = atype.get('$ref', None)
                if ref_key is not None:
                    ref = defs[ref_key.split('defs/')[-1]]
                    unpack_defs(ref, defs)
                    anyof[i] = ref
            continue

        items = value.get('items', None)
        if items is not None:
            ref_key = items.get('$ref', None)
            if ref_key is not None:
                ref = defs[ref_key.split('defs/')[-1]]
                unpack_defs(ref, defs)
                value['items'] = ref
                continue


def t_schema(
    client: _api_client.ApiClient, origin: Union[types.SchemaUnionDict, Any]
) -> Optional[types.Schema]:
  if not origin:
    return None
  if isinstance(origin, dict):
    return process_schema(origin, client)
  if isinstance(origin, types.Schema):
    if (dict(origin) == dict(types.Schema())):
      # response_schema value was coerced to an empty Schema instance because it did not adhere to the Schema field annotation
      raise ValueError(f'Unsupported schema type.')
    schema = process_schema(origin.model_dump(exclude_unset=True), client)
    return types.Schema.model_validate(schema)
  if (
      isinstance(origin, GenericAlias)
  ):
    if (
        origin.__origin__ is list
    ):
      if (isinstance(origin.__args__[0], typing.types.UnionType)):
        raise ValueError(f'Unsupported schema type: GenericAlias {origin}')
      if (issubclass(origin.__args__[0], pydantic.BaseModel)):
        # Handle cases where response schema is `list[pydantic.BaseModel]`
        list_schema = _build_schema(
            'dummy', {'dummy': (origin, pydantic.Field())}
        )
        list_schema = process_schema(list_schema, client)
        return types.Schema.model_validate(list_schema)
    raise ValueError(f'Unsupported schema type: GenericAlias {origin}')
  if issubclass(origin, pydantic.BaseModel):
    schema = process_schema(origin.model_json_schema(), client)
    return types.Schema.model_validate(schema)
  raise ValueError(f'Unsupported schema type: {origin}')


def t_speech_config(
    _: _api_client.ApiClient, origin: Union[types.SpeechConfigUnionDict, Any]
) -> Optional[types.SpeechConfig]:
  if not origin:
    return None
  if isinstance(origin, types.SpeechConfig):
    return origin
  if isinstance(origin, str):
    return types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=origin)
        )
    )
  if (
      isinstance(origin, dict)
      and 'voice_config' in origin
      and 'prebuilt_voice_config' in origin['voice_config']
  ):
    return types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name=origin['voice_config']['prebuilt_voice_config'].get(
                    'voice_name'
                )
            )
        )
    )
  raise ValueError(f'Unsupported speechConfig type: {type(origin)}')


def t_tool(client: _api_client.ApiClient, origin) -> types.Tool:
  if not origin:
    return None
  if inspect.isfunction(origin) or inspect.ismethod(origin):
    return types.Tool(
        function_declarations=[
            types.FunctionDeclaration.from_callable(client, origin)
        ]
    )
  else:
    return origin


# Only support functions now.
def t_tools(
    client: _api_client.ApiClient, origin: list[Any]
) -> list[types.Tool]:
  if not origin:
    return []
  function_tool = types.Tool(function_declarations=[])
  tools = []
  for tool in origin:
    transformed_tool = t_tool(client, tool)
    # All functions should be merged into one tool.
    if transformed_tool.function_declarations:
      function_tool.function_declarations += (
          transformed_tool.function_declarations
      )
    else:
      tools.append(transformed_tool)
  if function_tool.function_declarations:
    tools.append(function_tool)
  return tools


def t_cached_content_name(client: _api_client.ApiClient, name: str):
  return _resource_name(client, name, collection_identifier='cachedContents')


def t_batch_job_source(client: _api_client.ApiClient, src: str):
  if src.startswith('gs://'):
    return types.BatchJobSource(
        format='jsonl',
        gcs_uri=[src],
    )
  elif src.startswith('bq://'):
    return types.BatchJobSource(
        format='bigquery',
        bigquery_uri=src,
    )
  else:
    raise ValueError(f'Unsupported source: {src}')


def t_batch_job_destination(client: _api_client.ApiClient, dest: str):
  if dest.startswith('gs://'):
    return types.BatchJobDestination(
        format='jsonl',
        gcs_uri=dest,
    )
  elif dest.startswith('bq://'):
    return types.BatchJobDestination(
        format='bigquery',
        bigquery_uri=dest,
    )
  else:
    raise ValueError(f'Unsupported destination: {dest}')


def t_batch_job_name(client: _api_client.ApiClient, name: str):
  if not client.vertexai:
    return name

  pattern = r'^projects/[^/]+/locations/[^/]+/batchPredictionJobs/[^/]+$'
  if re.match(pattern, name):
    return name.split('/')[-1]
  elif name.isdigit():
    return name
  else:
    raise ValueError(f'Invalid batch job name: {name}.')


LRO_POLLING_INITIAL_DELAY_SECONDS = 1.0
LRO_POLLING_MAXIMUM_DELAY_SECONDS = 20.0
LRO_POLLING_TIMEOUT_SECONDS = 900.0
LRO_POLLING_MULTIPLIER = 1.5


def t_resolve_operation(api_client: _api_client.ApiClient, struct: dict):
  if (name := struct.get('name')) and '/operations/' in name:
    operation: dict[str, Any] = struct
    total_seconds = 0.0
    delay_seconds = LRO_POLLING_INITIAL_DELAY_SECONDS
    while operation.get('done') != True:
      if total_seconds > LRO_POLLING_TIMEOUT_SECONDS:
        raise RuntimeError(f'Operation {name} timed out.\n{operation}')
      # TODO(b/374433890): Replace with LRO module once it's available.
      operation: dict[str, Any] = api_client.request(
          http_method='GET', path=name, request_dict={}
      )
      time.sleep(delay_seconds)
      total_seconds += total_seconds
      # Exponential backoff
      delay_seconds = min(
          delay_seconds * LRO_POLLING_MULTIPLIER,
          LRO_POLLING_MAXIMUM_DELAY_SECONDS,
      )
    if error := operation.get('error'):
      raise RuntimeError(
          f'Operation {name} failed with error: {error}.\n{operation}'
      )
    return operation.get('response')
  else:
    return struct


def t_file_name(
    api_client: _api_client.ApiClient, name: Union[str, types.File]
):
  # Remove the files/ prefix since it's added to the url path.
  if isinstance(name, types.File):
    name = name.name

  if name is None:
    raise ValueError('File name is required.')

  if name.startswith('https://'):
    suffix = name.split('files/')[1]
    match = re.match('[a-z0-9]+', suffix)
    if match is None:
      raise ValueError(f'Could not extract file name from URI: {name}')
    name = match.group(0)
  elif name.startswith('files/'):
    name = name.split('files/')[1]

  return name


def t_tuning_job_status(
    api_client: _api_client.ApiClient, status: str
) -> types.JobState:
  if status == 'STATE_UNSPECIFIED':
    return 'JOB_STATE_UNSPECIFIED'
  elif status == 'CREATING':
    return 'JOB_STATE_RUNNING'
  elif status == 'ACTIVE':
    return 'JOB_STATE_SUCCEEDED'
  elif status == 'FAILED':
    return 'JOB_STATE_FAILED'
  else:
    return status


# Some fields don't accept url safe base64 encoding.
# We shouldn't use this transformer if the backend adhere to Cloud Type
# format https://cloud.google.com/docs/discovery/type-format.
# TODO(b/389133914): Remove the hack after Vertex backend fix the issue.
def t_bytes(api_client: _api_client.ApiClient, data: bytes) -> str:
  if not isinstance(data, bytes):
    return data
  if api_client.vertexai:
    return base64.b64encode(data).decode('ascii')
  else:
    return base64.urlsafe_b64encode(data).decode('ascii')
