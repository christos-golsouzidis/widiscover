# main.py
import webbrowser
import threading
import time
import aiofiles
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import os
from widiscover_core import Widiscover
import uvicorn
import dotenv
from groq import PermissionDeniedError, AuthenticationError, BadRequestError, RateLimitError
from pydantic import BaseModel, Field
from typing import Literal


app = FastAPI()
version = '2.0'
app.mount("/_app", StaticFiles(directory="ui/build/_app"), name="_app")
app.mount("/assets", StaticFiles(directory="ui/build/_app/immutable/assets"), name="assets")

DEFAULT_CONFIG = {
    'configResultNumberPerPage' : 3,
    'configChunkLength' : 1800,
    'configChunkOverlap' : 180,
    'configTopKResults' : 4,
    'configThreshold' : 0.3,
    'configDistance' : 1,
    'configGenerativeModel' : 'llama-3.3-70b-versatile',
}

class ConfigModel(BaseModel):
    configResultNumberPerPage: int = Field(ge=1, le=10)
    configChunkLength: int = Field(ge=100, le=10000)
    configChunkOverlap: int = Field(ge=0, le=2000)
    configTopKResults: int = Field(ge=1, le=16)
    configThreshold: float = Field(ge=0.0, le=0.75)
    configDistance: int = Field(ge=0, le=2)
    configGenerativeModel: Literal[
        "compound-beta",
        "compound-beta-mini",
        "gemma2-9b-it",
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        "meta-llama/llama-4-maverick-17b-128e-instruct",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "meta-llama/llama-guard-4-12b",
        "moonshotai/kimi-k2-instruct",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "qwen/qwen3-32b",
    ]

@app.get("/")
async def render_index():
    return FileResponse('ui/build/index.html')

@app.get("/main")
async def render_main():
    return FileResponse('ui/build/main.html')

@app.get("/config")
async def render_config():
    return FileResponse('ui/build/config.html')

@app.get("/api/init")
async def get_init():
    '''
        GET /api/init :
        checks if 'config.json' and '.env' file exist. If '.env' exists check if the groq API key is not empty.
        - both 'config.json' and '.env' exist:

            success:
            {
                status: 303,
                redirects: "/main",
            }
        - either one of 'config.json' or '.env' does not exist or GROQ_API_KEY is empty:

            success:
            {
                status: 303,
                redirects: "/config",
            }

        error:
        HTTPException(403, "Permission denied: cannot write <file>")
    '''
    path = '/main'
    # if there is no config.json create it and set the default values
    if not os.path.exists('config.json'):
        try:
            async with aiofiles.open('config.json', 'w') as f:
                await f.write(json.dumps(DEFAULT_CONFIG))
            path = '/config'
        except Exception:
            raise HTTPException(403, 'Cannot create \'config.json\' file.')
    else:
        # if there is 'config.json' check if it is valid
        try:
            async with aiofiles.open('config.json', 'r') as f:
                content = await f.read()
            data = ConfigModel(**json.loads(content))
            if not data:
                path = '/config'
        except Exception:
            try:
                async with aiofiles.open('config.json', 'w') as f:
                    await f.write(json.dumps(DEFAULT_CONFIG))
                path = '/config'
            except Exception:
                raise HTTPException(403, 'Cannot create \'config.json\' file.')
    # if there is no .env create it with the key having an empty value and send info for redirecting
    if not os.path.exists('.env'):
        try:
            async with aiofiles.open('.env','w') as f:
                await f.write('GROQ_API_KEY=')
            path = '/config'
        except Exception:
            raise HTTPException(403, 'Cannot create \'.env\' file.')
    else:
        try:
            dotenv.load_dotenv(override=True)
            if not os.getenv(key='GROQ_API_KEY'):
                path = '/config'
        except Exception:
            raise HTTPException(403, 'Cannot read from \'.env\' file.')
    return {
        'status': 303,
        'redirects': path,
    }


@app.get("/api/main")
async def get_main():
    '''
    GET /api/main :
    (re)loads the virtual environment and checks if 'config.json' contains valid values.

    - valid json data:

        success:
        {
            status : 200,
            message: "ok",
        }

    - invalid json data:

        success:
        {
            status : 303,
            redirects: "/config",
        }

    error:
    HTTPException(400, <any>)
    '''
    try:
        dotenv.load_dotenv(override=True)
        async with aiofiles.open('config.json', 'r') as f:
            content = await f.read()
        data = json.loads(content)
        try:
            ConfigModel(**data)
            return {
                'status' : 200,
                'message' : 'ok'
            }
        except Exception:
            return {
                    'status' : 303,
                    'warning' : 'Invalid configuration settings.',
                    'redirects' : '/config'
                }
    except Exception as e:
        raise HTTPException(status_code=400, detail=e)

    
@app.get("/api/config")
async def get_config():
    '''
    GET /api/config :
    returns the settings in the 'config.json' if valid, otherwise returns the predefined settings.

    success:
    
    {
        status: 200,
        message: <json object>
    }
    '''
    try:
        async with aiofiles.open('config.json', 'r') as f:
            content = await f.read()
        data = json.loads(content)
        valid_data = ConfigModel(**data)
        print(valid_data.model_dump())
        return valid_data.model_dump()
        
    except Exception:
        return DEFAULT_CONFIG
        

@app.post("/api/config")
async def post_config(request: Request):
    '''
    POST /api/config :
    Accepts a JSON payload.
    If the key 'envGroqKey' in the json is provided, it updates the GROQ_API_KEY in the .env file.
    Otherwise it checks if the API key is set.

    - If GROQ_API_KEY is missing and not provided:

    success:
        {
            'status': 303,
            'warning': 'Groq API key is not set.',
            'redirects': '/config'
        }

    - If settings are successfully saved:

    success:
        {
            'status': 303,
            'redirects': '/main'
        }

    error:
        HTTPException(400, 'Error reading from / writing to file.')
    '''
    try:
        data = await request.json()
        if data.get('envGroqKey'):
            # if the user posts a key overwrite previous settings
            # otherwise leave it as it is
            dotenv.set_key('.env', key_to_set='GROQ_API_KEY', value_to_set=data['envGroqKey'])
        else:
            if not dotenv.get_key('.env', key_to_get='GROQ_API_KEY'):
                return {
                    'status' : 303,
                    'warning' : 'Groq API key is not set.',
                    'redirects' : '/config'
                }

        # remove groq API key from the json before writing the config
        data.pop('envGroqKey')
        # validate data
        try:
            valid_data = ConfigModel(**data)
        except Exception as e:
            return {
                    'status' : 303,
                    'warning' : 'Invalid configuration settings.',
                    'redirects' : '/config'
                }
        async with aiofiles.open('config.json', 'w') as f:
            # overwrite all settings
            await f.write(valid_data.model_dump_json(indent=2))
        return {
                'status' : 303,
                'redirects' : '/main'
            }
    except Exception:
        raise HTTPException(status_code=400, detail='Error reading from / writing to file.')


@app.get('/api/default')
async def get_default_values():
    '''
    GET /api/default :
    returns a json with the default settings
    '''
    return DEFAULT_CONFIG


@app.post("/api/query")
async def root_post(request: Request):
    '''
    POST /api/query :
    Accepts a JSON payload with 'query' and optional 'topic' fields.
    Processes the query through the Widiscover pipeline: keyword extraction,
    Wikipedia search, text processing, and AI-generated answer generation.

    request body:

        {
            "query": "Your question here",
            "topic": "Optional topic for context"
        }

    success:

        {
            "answer": "Generated answer from AI",
            "sources": [Array of source information],
            "usage": {Usage statistics}
        }

    error:
        HTTPException(400, "Bad Request") - Invalid request format
        HTTPException(401, "Authentication error") - Invalid API key
        HTTPException(403, "Access denied") - Permission issues
        HTTPException(429, "Too Many Requests") - Rate limit exceeded
    '''
    try:
        data = await request.json()
        result = await generate_answer(data)
        return result
    except HTTPException as e:
        raise e

async def generate_answer(data):
    '''
    Generates an answer based on the input data.
        Parameters:
            data (dict): A dictionary containing the keys 'query' and 'topic'.
        Returns:
            dict: A dictionary containing the keys 'answer', 'sources' and 'usage'.
    '''
    async with aiofiles.open('config.json', 'r') as f:
        content = await f.read()
    settings = json.loads(content)

    try:
        query = data.get('query')
        topic = data.get('topic')
        wd = Widiscover(generative_model=settings.get('configGenerativeModel'))
        if not topic:
            keywords = wd.extract_keywords(query)
        else:
            keywords = topic.split()
        keys = wd.wikisearch(keywords, result_number_per_page=settings.get('configResultNumberPerPage'))
        docs = wd.extract_text(keys)
        chunks = wd.process_docs(docs, keys, length=settings.get('configChunkLength'), overlap=settings.get('configChunkOverlap'))
        rel_docs = wd.search_chunks(query, chunks, top_k=settings.get('configTopKResults'), threshold=settings.get('configThreshold'))
        wd.clear_data()
        return wd.answer(query, rel_docs, spelling=settings.get('configDistance'))
    except BadRequestError:
        raise HTTPException(status_code=400, detail='Bad Request')
    except AuthenticationError:
        raise HTTPException(status_code=401, detail='Authentication error')
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail='Access denied')
    except RateLimitError:
        raise HTTPException(status_code=429, detail='Too Many Requests')


def open_browser():
    time.sleep(1.5)  # Wait for server to start
    webbrowser.open("http://127.0.0.1:7454")


if __name__ == "__main__":
    threading.Thread(target=open_browser).start()
    uvicorn.run("main:app", host="0.0.0.0", port=7454)

