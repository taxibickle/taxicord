import array
import asyncio
import aiohttp
import os
from enum import Enum
from .billing import Billing
from .badges import Badges
from .guild import Guild, GuildUser
from .channel import Channel, PrivateChannel
from .utils import snowflake_time

class Unauthorized(Exception):
    pass  

class Forbidden(Exception):
    pass  

class HTTPClient:
    def __init__(self, token, proxy=None):
        self.token = token
        self._session = aiohttp.ClientSession(headers=self._generate_headers())
        self.proxy = proxy
        self._baseurl = 'https://discordapp.com/api/'

    
    def _generate_headers(self):
        headers = {
            "Authorization": self.token,
            "accept": "*/*",
            "accept-language": "en-US",
            "connection": "keep-alive",
            "cookie": "__cfduid=%s; __dcfduid=%s; locale=en-US" % (os.urandom(43).hex(), os.urandom(32).hex()),
            "DNT": "1",
            "origin": "https://discord.com",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "referer": "https://discord.com/channels/@me",
            "TE": "Trailers",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9001 Chrome/83.0.4103.122 Electron/9.3.5 Safari/537.36",
            "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRGlzY29yZCBDbGllbnQiLCJyZWxlYXNlX2NoYW5uZWwiOiJzdGFibGUiLCJjbGllbnRfdmVyc2lvbiI6IjEuMC45MDAxIiwib3NfdmVyc2lvbiI6IjEwLjAuMTkwNDIiLCJvc19hcmNoIjoieDY0Iiwic3lzdGVtX2xvY2FsZSI6ImVuLVVTIiwiY2xpZW50X2J1aWxkX251bWJlciI6ODMwNDAsImNsaWVudF9ldmVudF9zb3VyY2UiOm51bGx9"
        }
        return headers

    async def request(self, method:str, path:str, payload:str=None) -> dict:
        kwargs={}
        if self.proxy:
            kwargs['proxy'] = 'http://' + self.proxy
        if payload:
            kwargs['json'] = payload
        async with self._session.request(method, self._baseurl + path, **kwargs) as resp:
            if resp.status == 200:
                return await resp.json()
            elif resp.status == 403:
                raise Forbidden()
            elif resp.status == 401: 
                raise Unauthorized("Token invalid")
            elif resp.status == 429:
                pass
            


class DiscordUser:
    def __init__(self, raw_data:dict, session:HTTPClient):
        self.billing = Billing(session)

        self.id =          raw_data.get('id')
        self.username =    raw_data.get('username')
        self.discrim =     raw_data.get('discriminator')
        self.avatar =      raw_data.get('avatar')
        self.mfa_enabled = raw_data.get('mfa_enabled')
        self.email =       raw_data.get('email')
        self.verified =    raw_data.get('verified')
        self.phone =       raw_data.get('phone')
        self.locale =      raw_data.get('locale')
        self.created_at =  snowflake_time(int(self.id))
        self.badges =      Badges.calculate(raw_data.get('public_flags'))


class DiscordClient:
    async def login(self, token: str, proxy=None):
        self.locale = 'en-GB' 
        self.token = token
        self._session = HTTPClient(token, proxy)

        self.user = await self.check_token()
        # for some reason discord doesnt return forbidden on login
        self.user.billing.payment_methods = await self.user.billing.get_payment_methods()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        await self._session._session.close()
        pass

    async def check_token(self) -> DiscordUser:
        resp = await self._session.request("GET", "v9/users/@me")
        return DiscordUser(resp, self._session)

    async def get_guilds(self) -> list:
        raw_guilds = await self._session.request("GET", "users/@me/guilds")

        guilds = []

        for guild in raw_guilds:
            me = await self._session.request("GET", f"/users/@me/guilds/{guild['id']}/member")

            guilds.append(Guild(self._session, guild, GuildUser(me)))

        return guilds
    
    async def get_private_channels(self) -> list:
        raw_channels = await self._session.request("GET", "users/@me/channels")
        channels = []
        for channel in raw_channels:
            channels.append(PrivateChannel(self._session, channel))

        return channels
