import datetime as dt
import os
from pathlib import Path
from typing import Annotated, Iterable, Literal

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from llm_toolkit.dialog_manager import DialogManager, DialogManagerError
from llm_toolkit.llm_api import OpenAIAPI, MockLLMAPI
from llm_toolkit.message_broker import FileMessageBroker
from llm_toolkit.pydantic_models import Message
from llm_toolkit.utils import config as _CONFIG


app = FastAPI()
message_broker = FileMessageBroker(storage_path = Path(__file__).parent / 'llm_toolkit' / 'dialog')
dialog_manager = DialogManager(message_broker = message_broker)

openai_api_key = os.environ.get('OPENAI_API_KEY')
assert openai_api_key, "There's no OpenAI API key provided"
llm_api = OpenAIAPI(api_key = _CONFIG.get_openai_api_key()) if False else MockLLMAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # React app's URL TODO: restrict
    allow_credentials=True,
    allow_methods=['*'],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=['*'],  # Allow all headers
)

@app.on_event('startup')
async def startup_event() -> None:
    # await init_db(remove_old_data=False)
    pass


@app.on_event('shutdown')
async def shutdown_event() -> None:
    # await stop_engine()
    pass


@app.get('/api/threads/{thread_uid}/messages')
async def get_thread_messages(thread_uid: str | int) -> list[Message]:
    return await dialog_manager.create_thread(thread_uid)

@app.get('/api/threads/{thread_uid}/messages/{message_order}')
async def get_thread_message_by_order(thread_uid: str | int, message_order: int) -> Message:
    try:
        return await dialog_manager.get_message_by_thread_uid_and_order(thread_uid, message_order)
    except DialogManagerError as err:
        raise HTTPException(status_code=err.status_code, detail=str(err))

@app.get('/api/threads/{thread_uid}/instructions/archiving')
async def get_thread_archiving_instruction(thread_uid: str | int) -> Message:
    return await dialog_manager.get_thread_archiving_instruction(thread_uid)

@app.get('/api/threads/{thread_uid}/archives/suggest')
async def suggest_archiving_message(thread_uid: str | int, messages_orders: Annotated[list[int], Query()]) -> Message:

    background_subthread = await dialog_manager.compile_background(thread_uid, min(messages_orders))
    messages_to_archive = await dialog_manager.get_messages_by_orders_list(thread_uid, messages_orders)
    archiving_instruction = await dialog_manager.get_thread_archiving_instruction(thread_uid)

    response = await llm_api.get_archving_message(
        archiving_instruction, background_subthread, messages_to_archive
    )

    return response

@app.post('/api/threads/{thread_uid}/archives')
async def post_archiving_message(thread_uid: str | int, archive_message: Message) -> Message:

    await message_broker.set_archiving_message()
    pass


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=int(os.environ.get('BACKEND_PORT')), reload=False)
