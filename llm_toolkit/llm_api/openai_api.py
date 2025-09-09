import httpx
import itertools
import tiktoken
import yaml
from datetime import datetime as dt
from functools import partial, reduce
from pathlib import Path
from typing import Any, cast, Iterable, TypedDict

# from models.dnd_time import DnDTime, MonthFR
# from models.message import SceneModel, Message, MessageRole
# from llm_api import LLMAPI, LLMMessage, LLMResponse
from openai import AsyncOpenAI
# from .model_prices import MODEL_PRICES
from llm_toolkit.pydantic_models import Message, Role, SceneArchivingThread
from .exceptions import LLMAPIError
from ._llm_requests_logging import log_request, log_response

from .llm_api import LLMAPI, _LLMMessage, _LLMResponse


class OpenAIAPI(LLMAPI):
    def __init__(self, api_key: str, model: str = 'gpt-5', url: str = '',
                 store_logs: str | None = 'http_full_logs', proxy_uri: str | None = None) -> None:

        custom_client = httpx.AsyncClient(
            event_hooks={
                "request": [partial(log_request, store_logs)],
                "response": [partial(log_response, store_logs)],
            },
            # base_url=url,
            transport=httpx.AsyncHTTPTransport(proxy=proxy_uri) if proxy_uri else None
        ) if store_logs else None

        self._client = AsyncOpenAI(
            api_key=api_key,
            # base_url=url,
            http_client=custom_client
        )

        with open(Path(__file__).parent / 'model_prices.yml', 'r') as cfg_fopen:
            MODEL_PRICES: dict[str, dict[str, str | int]] = yaml.safe_load(cfg_fopen.read())
        self._model = model
        self._model_price_for_one_token_input = MODEL_PRICES.get(self._model, {}).get('input')
        self._model_price_for_one_token_cached = MODEL_PRICES.get(self._model, {}).get('cached')
        self._model_price_for_one_token_output = MODEL_PRICES.get(self._model, {}).get('output')
        self._tokenization_encoding_rule_for_model = MODEL_PRICES.get(self._model, {}).get('tokenization')
        assert self._model_price_for_one_token_input is not None
        assert self._model_price_for_one_token_cached is not None
        assert self._model_price_for_one_token_output is not None
        assert self._tokenization_encoding_rule_for_model is not None
        self._encoding = tiktoken.get_encoding(str(self._tokenization_encoding_rule_for_model))

    async def get_archving_message(
        self, archiving_instruction: Message, archiving_thread: SceneArchivingThread,
        few_shots_threads: list[SceneArchivingThread] | None
    ) -> Message:
        """Generate archving message based on given instruciton message and background subthread with optional
           few-shots"""
        openai_msgs = self._make_archiving_gpt_dicts_msgs(
            archiving_instruction, archiving_thread, few_shots_threads
        )
        result = await self.handle_response(openai_msgs)

        archive_for = [ msg.order for msg in archiving_thread.messages ]

        print('RESULT', result)

        return Message(
            thread_uid=archiving_thread.messages[0].thread_uid,
            order=archiving_thread.messages[0].order,
            role=Role.archive,
            text=result['content'],
            archive_for=archive_for
        )


    async def handle_response(
        self, gpt_messages: list[_LLMMessage]# , functions: dict[str, Any] | None = None,
        # function_call: dict[str, str] | None = None
    ) -> _LLMResponse:
        assert gpt_messages

        response = await self._client.chat.completions.create(
            model=self._model, messages=gpt_messages  # , functions=functions, function_call=function_call
        )

        assert len(response.choices) == 1
        choice = response.choices[0]
        gpt_msg = choice.message
        msg_text = gpt_msg.content

        assert msg_text is not None

        return { 'role': Role.assistant.value, 'content': msg_text }

        # if functions:
        #     return LLMResponse(
        #         role=MessageRole.ASSISTANT, content=str(gpt_msg.function_call.arguments),
        #         tokens_number=0, cost=0, model=self._model, created=dt.now()
        #     )


        # assert choice.finish_reason == 'stop'
        # assert gpt_msg.refusal is None
        # assert gpt_msg.role == MessageRole.ASSISTANT.value
        # assert not gpt_msg.annotations
        # assert gpt_msg.audio is None
        # assert gpt_msg.function_call is None
        # assert gpt_msg.tool_calls is None
        # assert response.model.startswith(self._model)
        # assert response.object == 'chat.completion'
        # # assert response.usage.prompt_tokens_details.audio_tokens == 0

        # tokens_number = response.usage.completion_tokens
        # # request_tokens_cached = response.usage.prompt_tokens_details.cached_tokens
        # # request_tokens_uncached = response.usage.prompt_tokens - request_tokens_cached
        # msg_text = gpt_msg.content
        # created = response.created

        # price = (
        #     self._model_price_for_one_token_cached * request_tokens_cached +
        #     self._model_price_for_one_token_input * request_tokens_uncached + 
        #     self._model_price_for_one_token_output * tokens_number
        # )
        # price = 0

        # return LLMResponse(
        #     role=MessageRole.ASSISTANT, content=msg_text, tokens_number=tokens_number, cost=price, model=self._model, created=dt.fromtimestamp(created)
        # )

    # async def get_archivation_result(
    #     self, system_thread: Iterable[Message], context_thread: Iterable[Message], archivation_thread: Iterable[Message], scene: SceneModel
    # ) -> list[Message]:
        


    #     result = await self.handle_response(
    #         [ context_gpt_msg, target_gpt_message, system_gpt_msg ],
    #         archivation_thread[-1].thread_uid, archivation_thread[0].order, is_archive=True, scene=scene
    #     )
    #     for msg in result:
    #         msg.location = scene.location
    #         msg.scene = scene.scene_number

    #     return result


# class OpenAIAPI(LLMAPI):

#     def handle_gpt_response(
#         self, session: int, thread_uid: str, msg: dict[str, Any], **kwargs
#     ):
#         pass

#     def tokens_number_to_cost(self, tokens_number: int) -> float:
#         return self._model_price_for_one_token_input * tokens_number

#     def parse_text_message(
#         self, thread_uid: str, role: MessageRole, text: str, order: int, scene: SceneModel, **kwargs
#     ) -> list[Message]:
#         return Message.from_text(
#             thread_uid, role, text, order, last_scene=scene, count_message_tokens_function=self.count_single_message_tokens, scene=scene.scene_number, **kwargs
#         )

#     def count_single_message_tokens(self, msg: Message) -> int:
#         msg_gpt = self.msg_to_gpt_dict(msg)
#         return len(self._encoding.encode(msg_gpt['role'])) + len(self._encoding.encode(msg_gpt['content'])) + 2

#     def count_messages_request_tokens(self, messages: list[Message]) -> int:
#         return sum(
#             msg.tokens_number or self.count_single_message_tokens(msg) for msg in messages
#         ) + 2

#     @classmethod
#     def msg_to_gpt_dict(cls, msg: Message) -> dict[str, str]:
#         role = msg.role if msg.role != MessageRole.TECHNICAL else MessageRole.USER
#         content = msg.text

#         if role == MessageRole.ASSISTANT and not msg.is_archive:
#             prefix = ''

#             if msg.time:
#                 prefix = f'Time: {str(msg.time)}\n'
#             if msg.location:
#                 prefix += f'Place: {msg.location}\n'
#             if prefix:
#                 content = prefix + '\n' + content

#         return { 'role': role.value, 'content': content }

# @classmethod
# def join_messages_seq_to_gpt_msg(
#     cls, messages: Iterable[Message], role: MessageRole
# ) -> dict[str, str]:
#     return {
#         'role': role.value,
#         'content': '\n\n'.join((cls.msg_to_gpt_dict(msg)['content'] for msg in messages))
#     }

#     @classmethod
#     def messages_seq_to_gpt_list(cls, messages: Iterable[Message]) -> list[dict[str, str]]:
#         return [cls.msg_to_gpt_dict(msg) for msg in messages]

#     async def handle_response(
#         self, gpt_messages: list[LLMMessage], functions: dict[str, Any] | None = None,
#         function_call: dict[str, str] | None = None
#     ) -> LLMResponse:
#         assert gpt_messages

#         response = await self._client.chat.completions.create(
#             model=self._model, messages=[msg.as_dict() for msg in gpt_messages], functions=functions,
#             function_call=function_call
#         )

#         print(response)

#         assert len(response.choices) == 1
        
#         choice = response.choices[0]
#         gpt_msg = choice.message

#         if functions:
#             return LLMResponse(
#                 role=MessageRole.ASSISTANT, content=str(gpt_msg.function_call.arguments),
#                 tokens_number=0, cost=0, model=self._model, created=dt.now()
#             )


#         assert choice.finish_reason == 'stop'
#         assert gpt_msg.refusal is None
#         assert gpt_msg.role == MessageRole.ASSISTANT.value
#         assert not gpt_msg.annotations
#         assert gpt_msg.audio is None
#         assert gpt_msg.function_call is None
#         assert gpt_msg.tool_calls is None
#         assert response.model.startswith(self._model)
#         assert response.object == 'chat.completion'
#         # assert response.usage.prompt_tokens_details.audio_tokens == 0

#         tokens_number = response.usage.completion_tokens
#         # request_tokens_cached = response.usage.prompt_tokens_details.cached_tokens
#         # request_tokens_uncached = response.usage.prompt_tokens - request_tokens_cached
#         msg_text = gpt_msg.content
#         created = response.created

#         # price = (
#         #     self._model_price_for_one_token_cached * request_tokens_cached +
#         #     self._model_price_for_one_token_input * request_tokens_uncached + 
#         #     self._model_price_for_one_token_output * tokens_number
#         # )
#         price = 0

#         return LLMResponse(
#             role=MessageRole.ASSISTANT, content=msg_text, tokens_number=tokens_number, cost=price, model=self._model, created=dt.fromtimestamp(created)
#         )

#     async def get_response(self, messages: Iterable[Message]) -> list[Message]:
#         return await self.handle_response(
#             self.messages_seq_to_gpt_list(messages), messages[-1].thread_uid, messages[-1].order + 1
#         )

# async def get_archivation_result(
#     self, system_thread: Iterable[Message], context_thread: Iterable[Message], archivation_thread: Iterable[Message], scene: SceneModel
# ) -> list[Message]:
#     context_gpt_msg = self.join_messages_seq_to_gpt_msg(context_thread, role=MessageRole.SYSTEM)
#     context_gpt_msg['content'] = '=== BACKGROUND ===\n' + context_gpt_msg['content']
#     target_gpt_message = self.join_messages_seq_to_gpt_msg(archivation_thread, role=MessageRole.USER)
#     target_gpt_message['content'] = '=== CURRENT SCENE ===\n' + target_gpt_message['content']
#     system_gpt_msg = self.join_messages_seq_to_gpt_msg(system_thread, role=MessageRole.USER)
#     system_gpt_msg['content'] = '=== INSTRUCTION ===\n' + system_gpt_msg['content']

#     result = await self.handle_response(
#         [ context_gpt_msg, target_gpt_message, system_gpt_msg ],
#         archivation_thread[-1].thread_uid, archivation_thread[0].order, is_archive=True, scene=scene
#     )
#     for msg in result:
#         msg.location = scene.location
#         msg.scene = scene.scene_number

#     return result
