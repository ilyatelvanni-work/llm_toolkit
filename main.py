import datetime as dt
import os
from pathlib import Path
from typing import Iterable, Literal

import uvicorn  # type: ignore
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from llm_toolkit.dialog_manager import DialogManager
from llm_toolkit.message_broker import FileMessageBroker
from llm_toolkit.pydantic_models import Message


app = FastAPI()
message_broker = FileMessageBroker(storage_path = Path(__file__).parent / 'llm_toolkit' / 'dialog')
dialog_manager = DialogManager(message_broker = message_broker)

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
    return await dialog_manager.get_message_by_thread_uid_and_order(thread_uid, message_order)

@app.get('/api/threads/{thread_uid}/instructions/archiving')
async def get_thread_archiving_instruction(thread_uid: str | int) -> Message:
    return await dialog_manager.get_thread_archiving_instruction(thread_uid)


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=os.environ.get('BACKEND_PORT'), reload=False)
