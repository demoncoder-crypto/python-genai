# Copyright 2025 Google LLC
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


"""Tests for client behavior when issuing requests."""


from ... import _api_client
from ... import types


def test_patch_http_options_with_copies_all_fields():
  patch_options = types.HttpOptions(
      base_url='https://fake-url.com/',
      api_version='v1',
      headers={'X-Custom-Header': 'custom_value'},
      timeout=10000,
  )
  options = types.HttpOptions()
  patched = _api_client._patch_http_options(options, patch_options)
  http_options_keys = types.HttpOptions.model_fields.keys()

  for key in http_options_keys:
    assert hasattr(patched, key) and getattr(patched, key) is not None
  assert patched.base_url == 'https://fake-url.com/'
  assert patched.api_version == 'v1'
  assert patched.headers['X-Custom-Header'] == 'custom_value'
  assert patched.timeout == 10000


def test_patch_http_options_merges_headers():
  original_options = types.HttpOptions(
      headers={
          'X-Custom-Header': 'different_value',
          'X-different-header': 'different_value',
      }
  )
  patch_options = types.HttpOptions(
      base_url='https://fake-url.com/',
      api_version='v1',
      headers={'X-Custom-Header': 'custom_value'},
      timeout=10000,
  )
  patched = _api_client._patch_http_options(original_options, patch_options)
  # If the header is present in both the original and patch options, the patch
  # options value should be used
  assert patched.headers['X-Custom-Header'] == 'custom_value'

  assert patched.headers['X-different-header'] == 'different_value'


def test_patch_http_options_appends_version_headers():
  original_options = types.HttpOptions(
      headers={
          'X-Custom-Header': 'different_value',
          'X-different-header': 'different_value',
      }
  )
  patch_options = types.HttpOptions(
      base_url='https://fake-url.com/',
      api_version='v1',
      headers={'X-Custom-Header': 'custom_value'},
      timeout=10000,
  )
  patched = _api_client._patch_http_options(original_options, patch_options)
  assert 'user-agent' in patched.headers
  assert 'x-goog-api-client' in patched.headers
