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


"""Tests for models.list."""

from unittest import mock

import pytest

from ... import client as genai_client
from ... import types
from .. import pytest_helper

test_http_options = {'headers': {'test': 'headers'}}

test_table: list[pytest_helper.TestTableItem] = [
    pytest_helper.TestTableItem(
        name='test_tuned_models',
        parameters=types._ListModelsParameters(config={'query_base': False}),
    ),
    pytest_helper.TestTableItem(
        name='test_base_models',
        parameters=types._ListModelsParameters(),
    ),
    pytest_helper.TestTableItem(
        name='test_base_models_with_config',
        parameters=types._ListModelsParameters(config={'query_base': True, 'page_size': 10}),
    ),
    pytest_helper.TestTableItem(
        name='test_with_config',
        parameters=types._ListModelsParameters(config={'page_size': 3}),
    ),
    pytest_helper.TestTableItem(
        name='test_list_models_with_http_options_in_method',
        parameters=types._ListModelsParameters(
            config={'page_size': 3, 'http_options': test_http_options}
        ),
    ),
]
pytestmark = pytest_helper.setup(
    file=__file__,
    globals_for_file=globals(),
    test_method='models.list',
    test_table=test_table,
)


@pytest.fixture()
def mock_api_client():
  api_client = mock.MagicMock(spec=genai_client.ApiClient)
  api_client.api_key = 'fake_api_key'
  api_client._host = lambda: 'fake_host'
  api_client._http_options = {'headers': {}}
  api_client.vertexai = False
  return api_client


def test_tuned_models_pager(client):
  pager = client.models.list(config={'page_size': 10})

  assert pager.name == 'models'
  assert pager.page_size == 10
  assert len(pager) <= 10

  # Iterate through all the pages. Then next_page() should raise an exception.
  for _ in pager:
    pass
  with pytest.raises(IndexError, match='No more pages to fetch.'):
    pager.next_page()


def test_base_models_pager(client):
  pager = client.models.list(config={'page_size': 10, 'query_base': True})

  assert pager.name == 'models'
  assert pager.page_size == 10
  assert len(pager) <= 10

  # Iterate through all the pages. Then next_page() should raise an exception.
  for _ in pager:
    pass
  with pytest.raises(IndexError, match='No more pages to fetch.'):
    pager.next_page()


def test_empty_tuned_models(mock_api_client, client):
  with mock.patch.object(
      genai_client.Client, '_get_api_client'
  ) as patch_api_client:
    patch_api_client.return_value = mock_api_client
    mock_client = genai_client.Client()
    with mock.patch.object(
        mock_api_client, 'request', return_value={}
    ) as patch_request:
      patch_request.return_value = {}
      pager = mock_client.models.list()

      assert len(pager) == 0


@pytest.mark.asyncio
async def test_async_pager(client):
  pager = await client.aio.models.list(config={'page_size': 10})

  assert pager.name == 'models'
  assert pager.page_size == 10
  assert len(pager) <= 10

  # Iterate through all the pages. Then next_page() should raise an exception.
  async for _ in pager:
    pass
  with pytest.raises(IndexError, match='No more pages to fetch.'):
    await pager.next_page()


@pytest.mark.asyncio
async def test_base_models_async_pager(client):
  pager = await client.aio.models.list(config={'page_size': 10, 'query_base': True})

  assert pager.name == 'models'
  assert pager.page_size == 10
  assert len(pager) <= 10

  # Iterate through all the pages. Then next_page() should raise an exception.
  async for _ in pager:
    pass
  with pytest.raises(IndexError, match='No more pages to fetch.'):
    await pager.next_page()
