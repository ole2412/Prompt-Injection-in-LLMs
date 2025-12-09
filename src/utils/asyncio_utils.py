import asyncio
from functools import wraps


def asyncio_limit_requests(limit=10):
    """
    Decorator to limit the number of concurrent requests.
    """
    def executor(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            loop = asyncio.get_event_loop()
            if not hasattr(loop, '_semaphore'):
                loop._semaphore = asyncio.Semaphore(limit)
            async with loop._semaphore:
                return await func(*args, **kwargs)
        return wrapper
    return executor