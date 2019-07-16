# aiooss_repair
最新版的oss2包和最新版的aiooss在response格式上有一点小出入，在这里修复

版本
```
aiooss (0.1.2)
oss2 (2.7.0)
```

问题：
虽然aiooss把调用方法变成异步执行，但是resp的验证是调用的oss2里面的models.PutObjectResult方法，会验证一个request_id的属性，但是aiooss里面没有带这个属性，通过对比oss2最新版和aiooss的最新版发现是aiooss少些一个类，把这个类加上就好了

需要添加的类：
```

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
```
