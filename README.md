# Google Gen AI SDK

[![PyPI version](https://img.shields.io/pypi/v/google-genai.svg)](https://pypi.org/project/google-genai/)

--------
**Documentation:** https://googleapis.github.io/python-genai/

-----

Google Gen AI Python SDK provides an interface for developers to integrate Google's generative models into their Python applications. It supports the [Gemini Developer API](https://ai.google.dev/gemini-api/docs) and [Vertex AI](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/overview) APIs.

## Installation

```cmd
pip install google-genai
```

## Imports

```python
from google import genai
from google.genai import types
```

## Create a client

Please run one of the following code blocks to create a client for
different services ([Gemini Developer API](https://ai.google.dev/gemini-api/docs) or [Vertex AI](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/overview)).

```python
# Only run this block for Gemini Developer API
client = genai.Client(api_key='GEMINI_API_KEY')
```

```python
# Only run this block for Vertex AI API
client = genai.Client(
    vertexai=True, project='your-project-id', location='us-central1'
)
```

**(Optional) Using environment variables:**

You can create a client by configuring the necessary environment variables.
Configuration setup instructions depends on whether you're using the Gemini API
on Vertex AI or the ML Dev Gemini API.

**ML Dev Gemini API:** Set `GOOGLE_API_KEY` as shown below:

```bash
export GOOGLE_API_KEY='your-api-key'
```

**Vertex AI API:** Set `GOOGLE_GENAI_USE_VERTEXAI`, `GOOGLE_CLOUD_PROJECT`
and `GOOGLE_CLOUD_LOCATION`, as shown below:

```bash
export GOOGLE_GENAI_USE_VERTEXAI=false
export GOOGLE_CLOUD_PROJECT='your-project-id'
export GOOGLE_CLOUD_LOCATION='us-central1'
```

```python
client = genai.Client()
```

### API Selection

By default, the SDK uses the beta API endpoints provided by Google to support
preview features in the APIs. The stable API endpoints can be selected by
setting the API version to `v1`.

To set the API version use `http_options`. For example, to set the API version
to `v1` for Vertex AI:

```python
client = genai.Client(
    vertexai=True, project='your-project-id', location='us-central1',
    http_options={'api_version': 'v1'}
)
```

To set the API version to `v1alpha` for the Gemini API:

```python
client = genai.Client(api_key='GEMINI_API_KEY',
                      http_options={'api_version': 'v1alpha'})
```

## Types

Parameter types can be specified as either dictionaries(`TypedDict`) or
[Pydantic Models](https://pydantic.readthedocs.io/en/stable/model.html).
Pydantic model types are available in the `types` module.

## Models

The `client.models` modules exposes model inferencing and model getters.

### Generate Content

#### with text content

```python
response = client.models.generate_content(
    model='gemini-2.0-flash-001', contents='why is the sky blue?'
)
print(response.text)
```

#### with uploaded file (Gemini API only)
download the file in console.

```cmd
!wget -q https://storage.googleapis.com/generativeai-downloads/data/a11.txt
```

python code.

```python
file = client.files.upload(file='a11.txt')
response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents=['Could you summarize this file?', file]
)
print(response.text)
```

#### How to structure `contents`
There are several ways to structure the `contents` in your request.

Provide a single string as shown in the text example above:

```python
contents='Can you recommend some things to do in Boston and New York in the winter?'
```

Provide a single `Content` instance with multiple `Part` instances:

```python
contents=types.Content(parts=[
    types.Part.from_text(text='Can you recommend some things to do in Boston in the winter?'),
    types.Part.from_text(text='Can you recommend some things to do in New York in the winter?')
], role='user')
```

When sending more than one input type, provide a list with multiple `Content`
instances:

```python
contents=[
    'What is this a picture of?',
    types.Part.from_uri(
        file_uri='gs://generativeai-downloads/images/scones.jpg',
        mime_type='image/jpeg',
    ),
],
```

### System Instructions and Other Configs

```python
response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents='high',
    config=types.GenerateContentConfig(
        system_instruction='I say high, you say low',
        temperature=0.3,
    ),
)
print(response.text)
```

### Typed Config

All API methods support Pydantic types for parameters as well as
dictionaries. You can get the type from `google.genai.types`.

```python
response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents=types.Part.from_text(text='Why is the sky blue?'),
    config=types.GenerateContentConfig(
        temperature=0,
        top_p=0.95,
        top_k=20,
        candidate_count=1,
        seed=5,
        max_output_tokens=100,
        stop_sequences=['STOP!'],
        presence_penalty=0.0,
        frequency_penalty=0.0,
    ),
)

print(response.text)
```

### List Base Models

To retrieve tuned models, see [list tuned models](#list-tuned-models).

```python
for model in client.models.list():
    print(model)
```

```python
pager = client.models.list(config={'page_size': 10})
print(pager.page_size)
print(pager[0])
pager.next_page()
print(pager[0])
```

#### Async

```python
async for job in await client.aio.models.list():
    print(job)
```

```python
async_pager = await client.aio.models.list(config={'page_size': 10})
print(async_pager.page_size)
print(async_pager[0])
await async_pager.next_page()
print(async_pager[0])
```

### Safety Settings

```python
response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents='Say something bad.',
    config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category='HARM_CATEGORY_HATE_SPEECH',
                threshold='BLOCK_ONLY_HIGH',
            )
        ]
    ),
)
print(response.text)
```

### Function Calling

#### Automatic Python function Support

You can pass a Python function directly and it will be automatically
called and responded.

```python
def get_current_weather(location: str) -> str:
    """Returns the current weather.

    Args:
      location: The city and state, e.g. San Francisco, CA
    """
    return 'sunny'


response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents='What is the weather like in Boston?',
    config=types.GenerateContentConfig(tools=[get_current_weather]),
)

print(response.text)
```

#### Manually declare and invoke a function for function calling

If you don't want to use the automatic function support, you can manually
declare the function and invoke it.

The following example shows how to declare a function and pass it as a tool.
Then you will receive a function call part in the response.

```python
function = types.FunctionDeclaration(
    name='get_current_weather',
    description='Get the current weather in a given location',
    parameters=types.Schema(
        type='OBJECT',
        properties={
            'location': types.Schema(
                type='STRING',
                description='The city and state, e.g. San Francisco, CA',
            ),
        },
        required=['location'],
    ),
)

tool = types.Tool(function_declarations=[function])

response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents='What is the weather like in Boston?',
    config=types.GenerateContentConfig(tools=[tool]),
)

print(response.function_calls[0])
```

After you receive the function call part from the model, you can invoke the function
and get the function response. And then you can pass the function response to
the model.
The following example shows how to do it for a simple function invocation.

```python
user_prompt_content = types.Content(
    role='user',
    parts=[types.Part.from_text(text='What is the weather like in Boston?')],
)
function_call_part = response.function_calls[0]
function_call_content = response.candidates[0].content


try:
    function_result = get_current_weather(
        **function_call_part.function_call.args
    )
    function_response = {'result': function_result}
except (
    Exception
) as e:  # instead of raising the exception, you can let the model handle it
    function_response = {'error': str(e)}


function_response_part = types.Part.from_function_response(
    name=function_call_part.name,
    response=function_response,
)
function_response_content = types.Content(
    role='tool', parts=[function_response_part]
)

response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents=[
        user_prompt_content,
        function_call_content,
        function_response_content,
    ],
    config=types.GenerateContentConfig(
        tools=[tool],
    ),
)

print(response.text)
```

#### Function calling with `ANY` tools config mode

If you configure function calling mode to be `ANY`, then the model will always
return function call parts. If you also pass a python function as a tool, by
default the SDK will perform automatic function calling until the remote calls exceed the
maximum remote call for automatic function calling (default to 10 times).

If you'd like to disable automatic function calling in `ANY` mode:

```python
def get_current_weather(location: str) -> str:
    """Returns the current weather.

    Args:
      location: The city and state, e.g. San Francisco, CA
    """
    return "sunny"

response = client.models.generate_content(
    model="gemini-2.0-flash-001",
    contents="What is the weather like in Boston?",
    config=types.GenerateContentConfig(
        tools=[get_current_weather],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=True
        ),
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode='ANY')
        ),
    ),
)
```

If you'd like to set `x` number of automatic function call turns, you can
configure the maximum remote calls to be `x + 1`.
Assuming you prefer `1` turn for automatic function calling.

```python
def get_current_weather(location: str) -> str:
    """Returns the current weather.

    Args:
      location: The city and state, e.g. San Francisco, CA
    """
    return "sunny"

response = client.models.generate_content(
    model="gemini-2.0-flash-001",
    contents="What is the weather like in Boston?",
    config=types.GenerateContentConfig(
        tools=[get_current_weather],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            maximum_remote_calls=2
        ),
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode='ANY')
        ),
    ),
)
```
### JSON Response Schema

#### Pydantic Model Schema support

Schemas can be provided as Pydantic Models.

```python
from pydantic import BaseModel


class CountryInfo(BaseModel):
    name: str
    population: int
    capital: str
    continent: str
    gdp: int
    official_language: str
    total_area_sq_mi: int


response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents='Give me information for the United States.',
    config=types.GenerateContentConfig(
        response_mime_type='application/json',
        response_schema=CountryInfo,
    ),
)
print(response.text)
```

```python
response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents='Give me information for the United States.',
    config=types.GenerateContentConfig(
        response_mime_type='application/json',
        response_schema={
            'required': [
                'name',
                'population',
                'capital',
                'continent',
                'gdp',
                'official_language',
                'total_area_sq_mi',
            ],
            'properties': {
                'name': {'type': 'STRING'},
                'population': {'type': 'INTEGER'},
                'capital': {'type': 'STRING'},
                'continent': {'type': 'STRING'},
                'gdp': {'type': 'INTEGER'},
                'official_language': {'type': 'STRING'},
                'total_area_sq_mi': {'type': 'INTEGER'},
            },
            'type': 'OBJECT',
        },
    ),
)
print(response.text)
```

### Enum Response Schema

#### Text Response

You can set response_mime_type to 'text/x.enum' to return one of those enum
values as the response.

```python
class InstrumentEnum(Enum):
  PERCUSSION = 'Percussion'
  STRING = 'String'
  WOODWIND = 'Woodwind'
  BRASS = 'Brass'
  KEYBOARD = 'Keyboard'

response = client.models.generate_content(
      model='gemini-2.0-flash-001',
      contents='What instrument plays multiple notes at once?',
      config={
          'response_mime_type': 'text/x.enum',
          'response_schema': InstrumentEnum,
      },
  )
print(response.text)
```

#### JSON Response

You can also set response_mime_type to 'application/json', the response will be identical but in quotes.

```python
from enum import Enum

class InstrumentEnum(Enum):
  PERCUSSION = 'Percussion'
  STRING = 'String'
  WOODWIND = 'Woodwind'
  BRASS = 'Brass'
  KEYBOARD = 'Keyboard'

response = client.models.generate_content(
      model='gemini-2.0-flash-001',
      contents='What instrument plays multiple notes at once?',
      config={
          'response_mime_type': 'application/json',
          'response_schema': InstrumentEnum,
      },
  )
print(response.text)
```

### Streaming

#### Streaming for text content

```python
for chunk in client.models.generate_content_stream(
    model='gemini-2.0-flash-001', contents='Tell me a story in 300 words.'
):
    print(chunk.text, end='')
```

#### Streaming for image content

If your image is stored in [Google Cloud Storage](https://cloud.google.com/storage),
you can use the `from_uri` class method to create a `Part` object.

```python
for chunk in client.models.generate_content_stream(
    model='gemini-2.0-flash-001',
    contents=[
        'What is this image about?',
        types.Part.from_uri(
            file_uri='gs://generativeai-downloads/images/scones.jpg',
            mime_type='image/jpeg',
        ),
    ],
):
    print(chunk.text, end='')
```

If your image is stored in your local file system, you can read it in as bytes
data and use the `from_bytes` class method to create a `Part` object.

```python
YOUR_IMAGE_PATH = 'your_image_path'
YOUR_IMAGE_MIME_TYPE = 'your_image_mime_type'
with open(YOUR_IMAGE_PATH, 'rb') as f:
    image_bytes = f.read()

for chunk in client.models.generate_content_stream(
    model='gemini-2.0-flash-001',
    contents=[
        'What is this image about?',
        types.Part.from_bytes(data=image_bytes, mime_type=YOUR_IMAGE_MIME_TYPE),
    ],
):
    print(chunk.text, end='')
```

### Async

`client.aio` exposes all the analogous [`async` methods](https://docs.python.org/3/library/asyncio.html)
that are available on `client`

For example, `client.aio.models.generate_content` is the `async` version
of `client.models.generate_content`

```python
response = await client.aio.models.generate_content(
    model='gemini-2.0-flash-001', contents='Tell me a story in 300 words.'
)

print(response.text)
```

### Streaming

```python
async for chunk in await client.aio.models.generate_content_stream(
    model='gemini-2.0-flash-001', contents='Tell me a story in 300 words.'
):
    print(chunk.text, end='')
```

### Count Tokens and Compute Tokens

```python
response = client.models.count_tokens(
    model='gemini-2.0-flash-001',
    contents='why is the sky blue?',
)
print(response)
```

#### Compute Tokens

Compute tokens is only supported in Vertex AI.

```python
response = client.models.compute_tokens(
    model='gemini-2.0-flash-001',
    contents='why is the sky blue?',
)
print(response)
```

##### Async

```python
response = await client.aio.models.count_tokens(
    model='gemini-2.0-flash-001',
    contents='why is the sky blue?',
)
print(response)
```

### Embed Content

```python
response = client.models.embed_content(
    model='text-embedding-004',
    contents='why is the sky blue?',
)
print(response)
```

```python
# multiple contents with config
response = client.models.embed_content(
    model='text-embedding-004',
    contents=['why is the sky blue?', 'What is your age?'],
    config=types.EmbedContentConfig(output_dimensionality=10),
)

print(response)
```

### Imagen

#### Generate Images

Support for generate images in Gemini Developer API is behind an allowlist

```python
# Generate Image
response1 = client.models.generate_images(
    model='imagen-3.0-generate-002',
    prompt='An umbrella in the foreground, and a rainy night sky in the background',
    config=types.GenerateImagesConfig(
        negative_prompt='human',
        number_of_images=1,
        include_rai_reason=True,
        output_mime_type='image/jpeg',
    ),
)
response1.generated_images[0].image.show()
```

#### Upscale Image

Upscale image is only supported in Vertex AI.

```python
# Upscale the generated image from above
response2 = client.models.upscale_image(
    model='imagen-3.0-generate-001',
    image=response1.generated_images[0].image,
    upscale_factor='x2',
    config=types.UpscaleImageConfig(
        include_rai_reason=True,
        output_mime_type='image/jpeg',
    ),
)
response2.generated_images[0].image.show()
```

#### Edit Image

Edit image uses a separate model from generate and upscale.

Edit image is only supported in Vertex AI.

```python
# Edit the generated image from above
from google.genai.types import RawReferenceImage, MaskReferenceImage

raw_ref_image = RawReferenceImage(
    reference_id=1,
    reference_image=response1.generated_images[0].image,
)

# Model computes a mask of the background
mask_ref_image = MaskReferenceImage(
    reference_id=2,
    config=types.MaskReferenceConfig(
        mask_mode='MASK_MODE_BACKGROUND',
        mask_dilation=0,
    ),
)

response3 = client.models.edit_image(
    model='imagen-3.0-capability-001',
    prompt='Sunlight and clear sky',
    reference_images=[raw_ref_image, mask_ref_image],
    config=types.EditImageConfig(
        edit_mode='EDIT_MODE_INPAINT_INSERTION',
        number_of_images=1,
        negative_prompt='human',
        include_rai_reason=True,
        output_mime_type='image/jpeg',
    ),
)
response3.generated_images[0].image.show()
```

## Chats

Create a chat session to start a multi-turn conversations with the model.

### Send Message

```python
chat = client.chats.create(model='gemini-2.0-flash-001')
response = chat.send_message('tell me a story')
print(response.text)
```

### Streaming

```python
chat = client.chats.create(model='gemini-2.0-flash-001')
for chunk in chat.send_message_stream('tell me a story'):
    print(chunk.text)
```

### Async

```python
chat = client.aio.chats.create(model='gemini-2.0-flash-001')
response = await chat.send_message('tell me a story')
print(response.text)
```

### Async Streaming

```python
chat = client.aio.chats.create(model='gemini-2.0-flash-001')
async for chunk in await chat.send_message_stream('tell me a story'):
    print(chunk.text)
```

## Files

Files are only supported in Gemini Developer API.

```cmd
!gsutil cp gs://cloud-samples-data/generative-ai/pdf/2312.11805v3.pdf .
!gsutil cp gs://cloud-samples-data/generative-ai/pdf/2403.05530.pdf .
```

### Upload

```python
file1 = client.files.upload(file='2312.11805v3.pdf')
file2 = client.files.upload(file='2403.05530.pdf')

print(file1)
print(file2)
```

### Get

```python
file1 = client.files.upload(file='2312.11805v3.pdf')
file_info = client.files.get(name=file1.name)
```

### Delete

```python
file3 = client.files.upload(file='2312.11805v3.pdf')

client.files.delete(name=file3.name)
```

## Caches

`client.caches` contains the control plane APIs for cached content

### Create

```python
if client.vertexai:
    file_uris = [
        'gs://cloud-samples-data/generative-ai/pdf/2312.11805v3.pdf',
        'gs://cloud-samples-data/generative-ai/pdf/2403.05530.pdf',
    ]
else:
    file_uris = [file1.uri, file2.uri]

cached_content = client.caches.create(
    model='gemini-1.5-pro-002',
    config=types.CreateCachedContentConfig(
        contents=[
            types.Content(
                role='user',
                parts=[
                    types.Part.from_uri(
                        file_uri=file_uris[0], mime_type='application/pdf'
                    ),
                    types.Part.from_uri(
                        file_uri=file_uris[1],
                        mime_type='application/pdf',
                    ),
                ],
            )
        ],
        system_instruction='What is the sum of the two pdfs?',
        display_name='test cache',
        ttl='3600s',
    ),
)
```

### Get

```python
cached_content = client.caches.get(name=cached_content.name)
```

### Generate Content with Caches

```python
response = client.models.generate_content(
    model='gemini-1.5-pro-002',
    contents='Summarize the pdfs',
    config=types.GenerateContentConfig(
        cached_content=cached_content.name,
    ),
)
print(response.text)
```

## Tunings

`client.tunings` contains tuning job APIs and supports supervised fine
tuning through `tune`.

### Tune

-   Vertex AI supports tuning from GCS source
-   Gemini Developer API supports tuning from inline examples

```python
if client.vertexai:
    model = 'gemini-1.5-pro-002'
    training_dataset = types.TuningDataset(
        gcs_uri='gs://cloud-samples-data/ai-platform/generative_ai/gemini-1_5/text/sft_train_data.jsonl',
    )
else:
    model = 'models/gemini-1.0-pro-001'
    training_dataset = types.TuningDataset(
        examples=[
            types.TuningExample(
                text_input=f'Input text {i}',
                output=f'Output text {i}',
            )
            for i in range(5)
        ],
    )
```

```python
tuning_job = client.tunings.tune(
    base_model=model,
    training_dataset=training_dataset,
    config=types.CreateTuningJobConfig(
        epoch_count=1, tuned_model_display_name='test_dataset_examples model'
    ),
)
print(tuning_job)
```

### Get Tuning Job

```python
tuning_job = client.tunings.get(name=tuning_job.name)
print(tuning_job)
```

```python
import time

running_states = set(
    [
        'JOB_STATE_PENDING',
        'JOB_STATE_RUNNING',
    ]
)

while tuning_job.state in running_states:
    print(tuning_job.state)
    tuning_job = client.tunings.get(name=tuning_job.name)
    time.sleep(10)
```

#### Use Tuned Model

```python
response = client.models.generate_content(
    model=tuning_job.tuned_model.endpoint,
    contents='why is the sky blue?',
)

print(response.text)
```

### Get Tuned Model

```python
tuned_model = client.models.get(model=tuning_job.tuned_model.model)
print(tuned_model)
```

### List Tuned Models

To retrieve base models, see [list base models](#list-base-models).

```python
for model in client.models.list(config={'page_size': 10, 'query_base': False}):
    print(model)
```

```python
pager = client.models.list(config={'page_size': 10, 'query_base': False})
print(pager.page_size)
print(pager[0])
pager.next_page()
print(pager[0])
```

#### Async

```python
async for job in await client.aio.models.list(config={'page_size': 10, 'query_base': False}):
    print(job)
```

```python
async_pager = await client.aio.models.list(config={'page_size': 10, 'query_base': False})
print(async_pager.page_size)
print(async_pager[0])
await async_pager.next_page()
print(async_pager[0])
```

### Update Tuned Model

```python
model = pager[0]

model = client.models.update(
    model=model.name,
    config=types.UpdateModelConfig(
        display_name='my tuned model', description='my tuned model description'
    ),
)

print(model)
```


### List Tuning Jobs

```python
for job in client.tunings.list(config={'page_size': 10}):
    print(job)
```

```python
pager = client.tunings.list(config={'page_size': 10})
print(pager.page_size)
print(pager[0])
pager.next_page()
print(pager[0])
```

#### Async

```python
async for job in await client.aio.tunings.list(config={'page_size': 10}):
    print(job)
```

```python
async_pager = await client.aio.tunings.list(config={'page_size': 10})
print(async_pager.page_size)
print(async_pager[0])
await async_pager.next_page()
print(async_pager[0])
```

## Batch Prediction

Only supported in Vertex AI.

### Create

```python
# Specify model and source file only, destination and job display name will be auto-populated
job = client.batches.create(
    model='gemini-1.5-flash-002',
    src='bq://my-project.my-dataset.my-table',
)

job
```

```python
# Get a job by name
job = client.batches.get(name=job.name)

job.state
```

```python
completed_states = set(
    [
        'JOB_STATE_SUCCEEDED',
        'JOB_STATE_FAILED',
        'JOB_STATE_CANCELLED',
        'JOB_STATE_PAUSED',
    ]
)

while job.state not in completed_states:
    print(job.state)
    job = client.batches.get(name=job.name)
    time.sleep(30)

job
```

### List

```python
for job in client.batches.list(config=types.ListBatchJobsConfig(page_size=10)):
    print(job)
```

```python
pager = client.batches.list(config=types.ListBatchJobsConfig(page_size=10))
print(pager.page_size)
print(pager[0])
pager.next_page()
print(pager[0])
```

#### Async

```python
async for job in await client.aio.batches.list(
    config=types.ListBatchJobsConfig(page_size=10)
):
    print(job)
```

```python
async_pager = await client.aio.batches.list(
    config=types.ListBatchJobsConfig(page_size=10)
)
print(async_pager.page_size)
print(async_pager[0])
await async_pager.next_page()
print(async_pager[0])
```

### Delete

```python
# Delete the job resource
delete_job = client.batches.delete(name=job.name)

delete_job
```

## Error Handling

To handle errors raised by the model service, the SDK provides this [APIError](https://github.com/googleapis/python-genai/blob/main/google/genai/errors.py) class.

```python
from google.genai import errors

try:
  client.models.generate_content(
      model="invalid-model-name",
      contents="What is your name?",
  )
except errors.APIError as e:
  print(e.code) # 404
  print(e.message)
```