import httpx
import json
import shlex
import uuid
from datetime import datetime as dt
from pathlib import Path
from typing import Any

import aiofiles


def build_curl(method: str, url: str, headers: dict[str, str], body: Any = None):
    curl_parts = [f'curl -X {method} \\']

    for k, v in headers.items():
        curl_parts.append(f'-H {shlex.quote(f"{k}: {v}")} \\')

    if body:
        curl_parts.append(f'--data {shlex.quote(body)} \\')

    curl_parts.append(shlex.quote(url))
    return '\n'.join(curl_parts)


def build_readible_response(status_code: str, headers: dict[str, str], body: Any) -> str:
    respstring_parts = [f'STATUS: {status_code}']
    if headers:
        respstring_parts.append('HEADERS:')

    for k, v in headers.items():
        respstring_parts.append(f'\t{shlex.quote(f"{k}: {v}")}')

    respstring_parts.append(shlex.quote(body))

    return '\n'.join(respstring_parts)


def build_response_json(status_code: str, headers: dict[str, str], body: Any) -> str:
    return json.dumps({
        'status_code': status_code,
        'headers': dict(headers),
        'body': body
    }, indent=4)


async def store_log(folder: str, uuid: str, log: str):
    async with aiofiles.open(Path(__file__).parent / folder / uuid, mode='a+') as fopen:
        await fopen.write(log)


async def log_request(folder: str, request: httpx.Request):
    req_uid = dt.now().strftime('%Y_%m_%d_%H_%M_%S_%f_') + str(uuid.uuid4())
    request.extensions['log_id'] = req_uid

    await store_log(folder, req_uid, 'REQUEST:\n' + build_curl(
        request.method,
        str(request.url),
        request.headers,
        request.content.decode('utf-8', errors='ignore') if request.content else None
    ))


async def log_response(folder: str, response: httpx.Response):
    req_uid = response.request.extensions.get('log_id', 'LOST_REQUEST')

    body = await response.aread()
    response._content = body

    await store_log(folder, req_uid, '\n\n\nRESPONSE:\n' + build_readible_response(
        response.status_code, response.headers, body.decode('utf-8', errors='ignore')
    ))

    await store_log(folder, req_uid, '\n\n\nRESPONSE_JSON:\n' + build_response_json(
        response.status_code, response.headers, body.decode('utf-8', errors='ignore')
    ))