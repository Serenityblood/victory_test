import logging
import jwt

from typing import Callable, Optional

from httpx import Response

from backend.bot.config import SECRET_KEY


logger = logging.getLogger("UtilsLogger")


def get_api_token():
    return jwt.encode({}, SECRET_KEY, algorithm="HS256")


async def make_safe_request(method: Callable, *args, **kwargs) -> Optional[Response]:
    try:
        response: Response = await method(*args, **kwargs)
        if response.status_code not in [200, 201, 400, 409]:
            logger.error(
                f"Что-то случилось с запросом на {response.url}, code={response.status_code}, data={response.json()}"
            )
            return None
        return response
    except Exception as e:
        logger.error(e)
