from httpx import AsyncClient


class ApiAccessor:
    def __init__(self, api_url: str, token: str):
        self.api_url = api_url
        self.token = token
        self.client = AsyncClient()
        self.headers = {"Authorization": f"{self.token}"}

    async def register_new_user(self, name: str, user_id: int, role: str = "user"):
        url = self.api_url + "users/"
        response = await self.client.post(
            url=url,
            json={"name": name, "tg_id": user_id, "role": role},
            headers=self.headers,
        )
        return response

    async def get_user_by_tg_id(self, tg_id: int):
        url = self.api_url + f"users/{tg_id}"
        response = await self.client.get(url=url, headers=self.headers)
        return response

    async def get_mailings(self):
        url = self.api_url + "mailings/"
        response = await self.client.get(
            url=url,
            headers=self.headers,
        )
        return response

    async def get_user_roles(self):
        url = self.api_url + "users/constraints/roles"
        response = await self.client.get(
            url=url,
            follow_redirects=True,
            headers=self.headers,
        )
        return response

    async def update_user_role_by_tg_id(self, tg_id: int, role: str):
        url = self.api_url + f"users/{tg_id}"
        response = await self.client.patch(
            url=url,
            json={"role": role},
            headers=self.headers,
        )
        return response

    async def create_new_mailing(
        self, name: str, creator_id: int, message: str, send_at=None, extra=None
    ):
        url = self.api_url + "mailings/"
        data = {"name": name, "creator_id": creator_id, "message": message}
        if send_at:
            data.update({"send_at": send_at})
        if extra:
            data.update({"extra": extra})
        response = await self.client.post(
            url=url,
            json=data,
            headers=self.headers,
        )
        return response

    async def update_mailing(
        self,
        name: str,
        creator_id: int,
        message: str,
        mailing_id: int,
        send_at=None,
        extra=None,
    ):
        url = self.api_url + f"mailings/{mailing_id}"
        data = {"name": name, "creator_id": creator_id, "message": message}
        if send_at:
            data.update({"send_at": send_at})
        if extra:
            data.update({"extra": extra})
        response = await self.client.patch(
            url=url,
            json=data,
            headers=self.headers,
        )
        return response

    async def delete_mailing(self, mailing_id: int):
        url = self.api_url + f"mailings/{mailing_id}"
        response = await self.client.delete(url=url, headers=self.headers)
        return response
