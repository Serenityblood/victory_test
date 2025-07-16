from typing import Optional

from httpx import AsyncClient


class ApiAccessor:
    def __init__(self, api_url: str, token: str):
        self.api_url = api_url
        self.token = token
        self.client = AsyncClient()

    async def register_new_user(
        self, name: str, user_id: int, role: Optional[str] = "user"
    ):
        url = self.api_url + "users/"
        response = await self.client.post(
            url=url, json={"name": name, "tg_id": user_id, "role": role}
        )
        return response
