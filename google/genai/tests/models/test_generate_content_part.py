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


"""Tests for generate_content_part."""

import base64
import os

import PIL.Image
from pydantic import ValidationError
import pytest

from ... import _transformers as t
from ... import errors
from ... import types
from .. import pytest_helper


IMAGE_PNG_FILE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../data/google.png')
)
IMAGE_JPEG_FILE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../data/google.jpg')
)
APPLICATION_PDF_FILE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../data/story.pdf')
)
VIDEO_MP4_FILE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../data/animal.mp4')
)
AUDIO_MP3_FILE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../data/pixel.m4a')
)
image_png = PIL.Image.open(IMAGE_PNG_FILE_PATH)
image_jpeg = PIL.Image.open(IMAGE_JPEG_FILE_PATH)
with open(IMAGE_PNG_FILE_PATH, 'rb') as image_file:
  image_bytes = image_file.read()
  image_string = base64.b64encode(image_bytes).decode('utf-8')
with open(APPLICATION_PDF_FILE_PATH, 'rb') as pdf_file:
  pdf_bytes = pdf_file.read()
with open(VIDEO_MP4_FILE_PATH, 'rb') as video_file:
  video_bytes = video_file.read()
with open(AUDIO_MP3_FILE_PATH, 'rb') as audio_file:
  audio_bytes = audio_file.read()

test_table: list[pytest_helper.TestTableItem] = [
    pytest_helper.TestTableItem(
        name='test_image_uri',
        parameters=types._GenerateContentParameters(
            model='gemini-1.5-flash',
            contents=[
                t.t_content(None, 'What is this image about?'),
                t.t_content(
                    None,
                    {
                        'role': 'user',
                        'parts': [
                            types.PartDict({
                                'file_data': {
                                    'file_uri': 'gs://generativeai-downloads/images/scones.jpg',
                                    'mime_type': 'image/jpeg',
                                }
                            })
                        ],
                    },
                ),
            ],
        ),
        exception_if_mldev='400',
    ),
    pytest_helper.TestTableItem(
        name='test_external_file_uri',
        parameters=types._GenerateContentParameters(
            model='gemini-1.5-flash',
            contents=[
                t.t_content(None, 'What is this image about?'),
                t.t_content(
                    None,
                    {
                        'role': 'user',
                        'parts': [
                            types.PartDict({
                                'file_data': {
                                    'file_uri': 'https://storage.googleapis.com/cloud-samples-data/generative-ai/image/scones.jpg',
                                    'mime_type': 'image/jpeg',
                                }
                            })
                        ],
                    },
                ),
            ],
        ),
        exception_if_mldev='400',
    ),
    pytest_helper.TestTableItem(
        name='test_image_png_file_uri',
        skip_in_api_mode=(
            'Name of the file is hardcoded, only supporting replay mode.'
        ),
        parameters=types._GenerateContentParameters(
            model='gemini-1.5-flash',
            contents=[
                t.t_content(None, 'What is this image about?'),
                t.t_content(
                    None,
                    {
                        'role': 'user',
                        'parts': [
                            types.PartDict({
                                'file_data': {
                                    'file_uri': 'https://generativelanguage.googleapis.com/v1beta/files/q08l9on9u7d',
                                    'mime_type': 'image/png',
                                }
                            })
                        ],
                    },
                ),
            ],
        ),
        exception_if_vertex='403',
    ),
    pytest_helper.TestTableItem(
        name='test_image_jpg_file_uri',
        skip_in_api_mode=(
            'Name of the file is hardcoded, only supporting replay mode.'
        ),
        parameters=types._GenerateContentParameters(
            model='gemini-1.5-flash',
            contents=[
                t.t_content(None, 'What is this image about?'),
                t.t_content(
                    None,
                    {
                        'role': 'user',
                        'parts': [
                            types.PartDict({
                                'file_data': {
                                    'file_uri': 'https://generativelanguage.googleapis.com/v1beta/files/tqbern1jkicb',
                                    'mime_type': 'image/jpeg',
                                }
                            })
                        ],
                    },
                ),
            ],
        ),
        exception_if_vertex='403',
    ),
    pytest_helper.TestTableItem(
        name='test_application_pdf_file_uri',
        skip_in_api_mode=(
            'Name of the file is hardcoded, only supporting replay mode.'
        ),
        parameters=types._GenerateContentParameters(
            model='gemini-1.5-flash',
            contents=[
                t.t_content(
                    None, 'Summarize the pdf in concise and professional tone.'
                ),
                t.t_content(
                    None,
                    {
                        'role': 'user',
                        'parts': [
                            types.PartDict({
                                'file_data': {
                                    'file_uri': 'https://generativelanguage.googleapis.com/v1beta/files/yiskd41szkfm',
                                    'mime_type': 'application/pdf',
                                }
                            })
                        ],
                    },
                ),
            ],
        ),
        exception_if_vertex='403',
    ),
    pytest_helper.TestTableItem(
        name='test_video_mp4_file_uri',
        skip_in_api_mode=(
            'Name of the file is hardcoded, only supporting replay mode.'
        ),
        parameters=types._GenerateContentParameters(
            model='gemini-1.5-flash',
            contents=[
                t.t_content(
                    None,
                    """
                    summarize the video in concise and professional tone.
                    the summary should include all important information said in the video.
                    """,
                ),
                t.t_content(
                    None,
                    {
                        'role': 'user',
                        'parts': [
                            types.PartDict({
                                'file_data': {
                                    'file_uri': 'https://generativelanguage.googleapis.com/v1beta/files/yu45gkirc8go',
                                    'mime_type': 'video/mp4',
                                }
                            })
                        ],
                    },
                ),
            ],
        ),
        exception_if_vertex='403',
    ),
    pytest_helper.TestTableItem(
        name='test_audio_m4a_file_uri',
        skip_in_api_mode=(
            'Name of the file is hardcoded, only supporting replay mode.'
        ),
        parameters=types._GenerateContentParameters(
            model='gemini-1.5-flash',
            contents=[
                t.t_content(
                    None,
                    """
                    Provide a summary for the audio in the beginning of the transcript.
                    Provide concise chapter titles with timestamps.
                    Do not make up any information that is not part of the audio.
                """,
                ),
                t.t_content(
                    None,
                    {
                        'role': 'user',
                        'parts': [
                            types.PartDict({
                                'file_data': {
                                    'file_uri': 'https://generativelanguage.googleapis.com/v1beta/files/wqnax2ohl9bp',
                                    'mime_type': 'audio/mp4',
                                }
                            })
                        ],
                    },
                ),
            ],
        ),
        exception_if_vertex='403',
    ),
    pytest_helper.TestTableItem(
        name='test_video_gcs_file_uri',
        skip_in_api_mode=(
            'Name of the file is hardcoded, only supporting replay mode.'
        ),
        parameters=types._GenerateContentParameters(
            model='gemini-1.5-flash',
            contents=[
                t.t_content(None, 'what is the video about?'),
                t.t_content(
                    None,
                    {
                        'role': 'user',
                        'parts': [
                            types.PartDict({
                                'file_data': {
                                    'file_uri': (
                                        'gs://vertexsdk-gcs/test_video2.mp4'
                                    ),
                                    'mime_type': 'video/mp4',
                                },
                                'video_metadata': {
                                    'start_offset': '0s',
                                    'end_offset': '10s',
                                }
                            })
                        ],
                    },
                ),
            ],
        ),
        exception_if_mldev='not supported',
    ),
    pytest_helper.TestTableItem(
        name='test_image_base64',
        parameters=types._GenerateContentParameters(
            model='gemini-1.5-flash-001',
            contents=[
                t.t_content(None, 'What is this image about?'),
                t.t_content(
                    None,
                    {
                        'role': 'user',
                        'parts': [
                            types.Part(
                                inline_data=types.Blob(
                                    data=image_string, mime_type='image/png'
                                )
                            )
                        ],
                    },
                ),
            ],
        ),
    ),
    pytest_helper.TestTableItem(
        name='test_union_none_part',
        parameters=types._GenerateContentParameters(
            model='gemini-1.5-flash-001',
            contents=[],
        ),
        exception_if_mldev='contents',
        exception_if_vertex='contents',
        has_union=True,
    ),
    pytest_helper.TestTableItem(
        name='test_dict_content',
        parameters=types._GenerateContentParameters(
            model='gemini-1.5-flash-001',
            contents=t.t_contents(
                None,
                types.ContentDict(
                    {'role': 'user', 'parts': [{'text': 'what is your name?'}]}
                ),
            ),
        ),
    ),
    pytest_helper.TestTableItem(
        name='test_union_part_list',
        parameters=types._GenerateContentParameters(
            model='gemini-1.5-flash-001',
            contents=['What is your name?'],
        ),
        has_union=True,
    ),
]
pytestmark = pytest_helper.setup(
    file=__file__,
    globals_for_file=globals(),
    test_method='models.generate_content',
    test_table=test_table,
)
pytest_plugins = ('pytest_asyncio',)


def test_empty_part(client):
  with pytest.raises(ValueError):
    client.models.generate_content(
        model='gemini-1.5-flash-001',
        contents=t.t_contents(None, ['']),
    )


def test_none_list_part(client):
  # pydantic will raise ValidationError
  with pytest.raises(ValidationError):
    client.models.generate_content(
        model='gemini-1.5-flash-001',
        contents=[None],
    )


def test_image_file(client):
  client.models.generate_content(
      model='gemini-1.5-flash',
      contents=[
          'What is this image about?',
          {'inline_data': {'data': image_bytes, 'mimeType': 'image/png'}},
      ],
  )


def test_image_jpeg(client):
  client.models.generate_content(
      model='gemini-1.5-flash',
      contents=['What is this image about?', image_jpeg],
  )


def test_from_uri(client):
  # gs://generativeai-downloads/images/scones.jpg isn't supported in MLDev
  with pytest_helper.exception_if_mldev(client, errors.ClientError):
    client.models.generate_content(
        model='gemini-1.5-flash',
        contents=[
            'What is this image about?',
            types.Part.from_uri(
                file_uri='gs://generativeai-downloads/images/scones.jpg',
                mime_type='image/jpeg',
            ),
        ],
    )


def test_from_uploaded_file_uri(client):
  with pytest_helper.exception_if_vertex(client, errors.ClientError):
    client.models.generate_content(
        model='gemini-1.5-flash',
        contents=[
            'Summarize this file',
            types.Part.from_uri(
                file_uri='https://generativelanguage.googleapis.com/v1beta/files/w1l20sq33nwn',
                mime_type='text/plain',
            ),
        ],
    )


def test_from_uri_error(client):
  # missing mime_type
  with pytest.raises(TypeError):
    client.models.generate_content(
        model='gemini-1.5-flash',
        contents=[
            'What is this image about?',
            types.Part.from_uri(
                file_uri='gs://generativeai-downloads/images/scones.jpg'
            ),
        ],
    )


def test_audio_uri(client):
  with pytest_helper.exception_if_mldev(client, errors.ClientError):
    client.models.generate_content(
        model='gemini-1.5-flash',
        contents=[
            """
        Provide a summary for the audio in the beginning of the transcript.
        Provide concise chapter titles with timestamps.
        Do not make up any information that is not part of the audio.
        """,
            types.Part.from_uri(
                file_uri='gs://cloud-samples-data/generative-ai/audio/pixel.mp3',
                mime_type='audio/mpeg',
            ),
        ],
        config={
            'system_instruction': (
                'You are a helpful assistant for audio transcription.'
            )
        },
    )


def test_pdf_uri(client):
  with pytest_helper.exception_if_mldev(client, errors.ClientError):
    client.models.generate_content(
        model='gemini-1.5-flash',
        contents=[
            'summarize the pdf in concise and professional tone',
            types.Part.from_uri(
                file_uri='gs://cloud-samples-data/generative-ai/pdf/2403.05530.pdf',
                mime_type='application/pdf',
            ),
        ],
        config={
            'system_instruction': (
                'You are a helpful assistant for academic literature review.'
            )
        },
    )


def test_video_uri(client):
  with pytest_helper.exception_if_mldev(client, errors.ClientError):
    client.models.generate_content(
        model='gemini-1.5-flash',
        contents=[
            """
            summarize the video in concise and professional tone.
            the summary should include all important information said in the video.
            """,
            types.Part.from_uri(
                file_uri='gs://cloud-samples-data/generative-ai/video/pixel8.mp4',
                mime_type='video/mp4',
            ),
        ],
        config={
            'system_instruction': (
                'you are a helpful assistant for market research.'
            )
        },
    )


def test_video_audio_uri(client):
  with pytest_helper.exception_if_mldev(client, errors.ClientError):
    client.models.generate_content(
        model='gemini-1.5-flash',
        contents=[
            """
            Is the audio related to the video?
            If so, how?
            What are the common themes?
            What are the different emphases?
            """,
            types.Part.from_uri(
                file_uri='gs://cloud-samples-data/generative-ai/video/pixel8.mp4',
                mime_type='video/mp4',
            ),
            types.Part.from_uri(
                file_uri='gs://cloud-samples-data/generative-ai/audio/pixel.mp3',
                mime_type='audio/mpeg',
            ),
        ],
        config={
            'system_instruction': (
                'you are a helpful assistant for people with visual and hearing'
                ' disabilities.'
            )
        },
    )


def test_file(client):
  with pytest_helper.exception_if_vertex(client, errors.ClientError):
    file = types.File(
        uri='https://generativelanguage.googleapis.com/v1beta/files/cmpqbqoptyaa',
        mime_type='text/plain',
    )
    client.models.generate_content(
        model='gemini-1.5-flash',
        contents=[
            'Summarize this file',
            file,
        ],
    )


def test_file_error(client):
  # missing mime_type
  with pytest.raises(ValueError):
    file = types.File(
        uri='https://generativelanguage.googleapis.com/v1beta/files/cmpqbqoptyaa',
    )
    client.models.generate_content(
        model='gemini-1.5-flash',
        contents=[
            'Summarize this file',
            file,
        ],
    )


def test_from_text(client):
  client.models.generate_content(
      model='gemini-1.5-flash',
      contents=[types.Part.from_text(text='What is your name?')],
  )


def test_from_bytes_image(client):
  client.models.generate_content(
      model='gemini-1.5-flash',
      contents=[
          'What is this image about?',
          types.Part.from_bytes(data=image_bytes, mime_type='image/png'),
      ],
  )


def test_from_bytes_image_dict(client):
  client.models.generate_content(
      model='gemini-1.5-flash',
      contents=[
          {'text': 'What is this image about?'},
          {'inline_data': {'data': image_bytes, 'mimeType': 'image/png'}},
      ],
  )


def test_from_bytes_image_none(client):
  with pytest.raises(errors.ClientError) as e:
    client.models.generate_content(
        model='gemini-1.5-flash',
        contents=[
            {'text': 'What is this image about?'},
            {'inline_data': {'data': None, 'mimeType': 'image/png'}},
        ],
    )
  assert 'INVALID_ARGUMENT' in str(e)


def test_from_bytes_video(client):
  client.models.generate_content(
      model='gemini-1.5-flash',
      contents=[
          'What is this video about?',
          types.Part.from_bytes(data=video_bytes, mime_type='video/mp4'),
      ],
  )


def test_from_bytes_audio(client):
  client.models.generate_content(
      model='gemini-1.5-flash',
      contents=[
          'What is this audio about?',
          types.Part.from_bytes(data=audio_bytes, mime_type='audio/mpeg'),
      ],
  )


def test_from_bytes_pdf(client):
  client.models.generate_content(
      model='gemini-1.5-flash',
      contents=[
          'What is this pdf about?',
          types.Part.from_bytes(data=pdf_bytes, mime_type='application/pdf'),
      ],
  )


def test_from_function_call_response(client):
  function_call = types.Part.from_function_call(
      name='get_weather', args={'location': 'Boston'}
  )
  function_response = types.Part.from_function_response(
      name='get_weather', response={'weather': 'sunny'}
  )
  response = client.models.generate_content(
      model='gemini-1.5-flash',
      contents=[
          'what is the weather in Boston?',
          function_call,
          function_response,
      ],
  )

  assert 'sunny' in response.text
  assert 'Boston' in response.text


@pytest.mark.asyncio
async def test_image_base64_stream_async(client):
  async for part in client.aio.models.generate_content_stream(
      model='gemini-1.5-flash-001',
      contents=[
          'What is this image about?',
          {'inline_data': {'data': image_string, 'mimeType': 'image/png'}},
      ],
  ):
    pass


# function_call and function_response are tested in generate_content_tools.py
