import datetime as dt
import os
import uvicorn
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Iterable, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from llm_toolkit.dialog_manager import DialogManager, DialogManagerError
from llm_toolkit.llm_api import MockLLMAPI, OpenAIAPI
from llm_toolkit.message_broker import FileMessageBroker
from llm_toolkit.pydantic_models import Message, Role, SceneArchivingThread
from llm_toolkit.utils import config as _CONFIG

app = FastAPI()
message_broker = FileMessageBroker(storage_path = Path(__file__).parent / 'llm_toolkit' / 'dialog')
dialog_manager = DialogManager(message_broker = message_broker)

openai_api_key = os.environ.get('OPENAI_API_KEY')
assert openai_api_key, "There's no OpenAI API key provided"
llm_api = OpenAIAPI(
    api_key = _CONFIG.get_openai_api_key(), proxy_uri=os.environ.get('LLM_PROXY_URI')
) if False else MockLLMAPI()

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
    archiving_instruction = await dialog_manager.get_thread_archiving_instruction(thread_uid)
    few_shots_threads = await dialog_manager.compile_few_shot_threads(thread_uid)
    current_scene_thread = await dialog_manager.compile_current_scene_thread(thread_uid, messages_orders)

    response = await llm_api.get_archving_message(
        archiving_instruction, current_scene_thread, few_shots_threads
    )

    return response

@app.post('/api/threads/{thread_uid}/messages')
async def post_archiving_message(thread_uid: str | int, messages: list[Message]) -> list[Message]:
    if any(msg.thread_uid != thread_uid for msg in messages):
        raise HTTPException(status_code=409, detail='Some message and route thread_uid are not equal')

    for msg in messages:
        if msg.role == Role.archive:
            await message_broker.set_archiving_message(msg)
        else:
            raise HTTPException(status_code=400, detail=f"There's no handler for {msg.role} yet")

    return messages

@app.get('/api/threads/{thread_uid}/compiled')
async def get_compiled_threads_messages(thread_uid: str | int) -> list[Message]:
    return await dialog_manager.compile_and_get_thread(thread_uid)

@app.get('/api/threads/{thread_uid}/analysis')
async def get_current_thread_analysis(
    thread_uid: str | int, order_from: int = 0, order_to: int | None = None
) -> Message:
    analysis_instruction = await dialog_manager.get_thread_analysis_instruction(thread_uid)
    full_origin_thread = await dialog_manager.get_origin_thread(thread_uid, order_from, order_to)

    return await llm_api.get_thread_response([ analysis_instruction ] + full_origin_thread)


class HiddenContextCreationStatus(BaseModel):
    error: int
    tokens_number: int
    consistency_score: float | None = None
    hook_alignment_score: float | None = None
    logical_coherence_score: float | None = None
    token_efficiency_score: float | None = None


@app.post('/api/threads/{thread_uid}/hidden_context')
async def create_hidden_context_for_thread(
    thread_uid: str | int, context_message: Message
) -> HiddenContextCreationStatus:

    hidden_context_creation_instruciton = await dialog_manager.get_thread_hidden_context_creation_instruction(
        thread_uid
    )
    current_thread = await dialog_manager.compile_and_get_thread(thread_uid)
    hidden_context = await llm_api.make_hidden_context_message(
        hidden_context_creation_instruciton, current_thread, context_message
    )

    await message_broker.store_hidden_context_message(hidden_context)
    hidden_context_tokens_number = llm_api.count_single_message_tokens(hidden_context)

    return HiddenContextCreationStatus(error=0, tokens_number=hidden_context_tokens_number)

@app.get('/api/threads/{thread_uid}/hidden_context/consistency_check')
async def check_consistancy_of_created_hidden_context(thread_uid: str | int) -> HiddenContextCreationStatus:

    hidden_context_consistency_check_instruciton = (
        await dialog_manager.get_thread_hidden_context_consistency_check_instruciton(thread_uid)
    )
    current_thread = await dialog_manager.compile_and_get_thread(thread_uid)
    hidden_context = await dialog_manager.get_hidden_context_message(thread_uid)
    hidden_context_tokens_number = llm_api.count_single_message_tokens(hidden_context)
    hidden_context_check_result = await llm_api.make_hidden_context_check(
        hidden_context_consistency_check_instruciton, current_thread, hidden_context
    )

    return HiddenContextCreationStatus(
        error=0, tokens_number=hidden_context_tokens_number, **asdict(hidden_context_check_result)
    )


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=_CONFIG.get_uvicorn_port(), reload=False, workers=1)
