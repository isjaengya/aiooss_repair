# -*- coding: utf-8 -*-
import asyncio

from oss2 import defaults, http
from requests.structures import CaseInsensitiveDict

import aiohttp


class Session(object):
    """属于同一个Session的请求共享一组连接池，如有可能也会重用HTTP连接。"""

    def __init__(self, loop=None):
        self._loop = loop or asyncio.get_event_loop()

        psize = defaults.connection_pool_size
        connector = aiohttp.TCPConnector(limit=psize, loop=self._loop)

        self._aio_session = aiohttp.ClientSession(
            connector=connector,
            loop=self._loop)

    async def do_request(self, req, timeout=300):
        resp = await self._aio_session.request(req.method, url=req.url,
                                               data=req.data,
                                               params=req.params,
                                               headers=req.headers,
                                               timeout=timeout)
        return Response(resp)

    async def __aenter__(self):
        await self._aio_session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._aio_session.__aexit__(exc_type, exc_val, exc_tb)

    async def close(self):
        await self._aio_session.close()


class Request(object):
    def __init__(self, method, url,
                 data=None,
                 params=None,
                 headers=None,
                 app_name=''):
        self.method = method
        self.url = url
        self.data = http._convert_request_body(data)
        self.params = params or {}

        if not isinstance(headers, CaseInsensitiveDict):
            self.headers = CaseInsensitiveDict(headers)
        else:
            self.headers = headers

        # tell requests not to add 'Accept-Encoding: gzip, deflate' by default
        # if 'Accept-Encoding' not in self.headers:
        #     self.headers['Accept-Encoding'] = None

        if 'User-Agent' not in self.headers:
            if app_name:
                self.headers['User-Agent'] = http._USER_AGENT + '/' + app_name
            else:
                self.headers['User-Agent'] = http._USER_AGENT


_CHUNK_SIZE = 8 * 1024


class Response(object):
    def __init__(self, resp):
        self.response = resp
        self.status = resp.status
        self.headers = resp.headers
        self.request_id = resp.headers.get('x-oss-request-id', '')

        # When a response contains no body, iter_content() cannot
        # be run twice (requests.exceptions.StreamConsumedError will be raised).
        # For details of the issue, please see issue #82
        #
        # To work around this issue, we simply return b'' when everything has been read.
        #
        # Note you cannot use self.response.raw.read() to implement self.read(), because
        # raw.read() does not uncompress response body when the encoding is gzip etc., and
        # we try to avoid depends on details of self.response.raw.
        self.__all_read = False


    def read(self, amt=None):
        if self.__all_read:
            return b''

        if amt is None:
            content_list = []
            for chunk in self.response.iter_content(_CHUNK_SIZE):
                content_list.append(chunk)
            content = b''.join(content_list)

            self.__all_read = True
            # logger.debug("Get response body, req-id: {0}, content: {1}", self.request_id, content)
            return content
        else:
            try:
                return next(self.response.iter_content(amt))
            except StopIteration:
                self.__all_read = True
                return b''

    def __iter__(self):
        return self.response.iter_content(_CHUNK_SIZE)
