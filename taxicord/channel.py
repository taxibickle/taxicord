from enum import Enum
from .badges import Badges

class ChannelType(Enum):
    guild_text = 0
    dm = 1
    guild_voice = 2
    group_dm = 3
    guild_category = 4
    guild_announcement = 5
    announcement_thread = 10
    public_thread = 11
    private_thread = 12
    guild_stage_voice = 13
    guild_directory = 14
    guild_forum = 15

class Permissions(Enum):
    kick_members = 1 << 1
    ban_members = 1 << 2
    administrator = 1 << 3
    manage_channels = 1 << 4
    manage_guild = 1 << 5
    add_reactions = 1 << 6
    view_audit_log = 1 << 7
    priority_speaker = 1 << 8
    stream = 1 << 9
    view_channel = 1 << 10
    send_messages = 1 << 11
    send_tts_messages = 1 << 12
    manage_messages = 1 << 13
    embed_links = 1 << 14
    attach_files = 1 << 15
    read_message_history = 1 << 16
    mention_everyone = 1 << 17
    use_external_emojis = 1 << 18
    view_guild_insights = 1 << 19
    connect = 1 << 20
    speak = 1 << 21
    mute_members = 1 << 22
    deafen_members = 1 << 23
    move_members = 1 << 24
    use_vad = 1 << 25
    change_nickname = 1 << 26
    manage_nicknames = 1 << 27
    manage_roles = 1 << 28
    manage_webhooks = 1 << 29
    manage_emojis_and_stickers = 1 << 30
    use_application_commands = 1 << 31
    request_to_speak = 1 << 32
    manage_events = 1 << 33
    manage_threads = 1 << 34
    create_public_threads = 1 << 35
    create_private_threads = 1 << 36
    use_external_stickers = 1 << 37
    send_messages_in_threads = 1 << 38
    use_embedded_activities = 1 << 39
    moderate_members = 1 << 40

    @property
    def all():
        permissions = None
        for permission in Permissions:
            permissions = permissions | permission.value
        
        return permissions

    def calculate_overwrites(overwrites: list, base_permisions: int, guild) -> list:
        if base_permisions & Permissions.administrator == Permissions.administrator:
            return Permissions.all

        permissions = base_permisions

        for overwrite in overwrites:
            if overwrite['id'] == guild.id:
                permissions &= ~overwrite['deny']
                permissions |= overwrite['allow']

        allow = None
        deny = None
        for overwrite in overwrites:
            if guild.me.id in overwrite:
                allow |= overwrite['allow']
                deny |= overwrite['deny']

            if overwrite['id'] == guild_id:
                continue
            
            if overwrite['id'] in guild.me.roles:
                allow |= overwrite['allow']
                deny |= overwrite['deny']

        permissions &= ~deny
        permissions |= allow

        return permissions
        
            
        
class Channel:
    def __init__(self, session, raw_data:dict, guild=None):
        self._session = session

        self.id = raw_data.get('id')
        self.type = ChannelType(raw_data.get('type'))
        self.position = raw_data.get('position')
        self.permissions = Permissions.calculate_overwrites(raw_data.get('permission_overwrites'), guild.permissions, self.guild)
        self.name = raw_data.get('name')
        self.guild = guild

    async def message(self):
        if Permissions.send_messages in self.permissions:
            return await self._session.request("POST", f"channels/{self.id}/channels")

class Recipient:
    def __init__(self, id: str, username: str, avatar: str, avatar_decoration: str, discriminator: str, public_flags: list, bot: bool=False):
        self.id = id
        self.username = username
        self.avatar = avatar
        self.avatar_decoration = avatar_decoration
        self.discriminator = discriminator
        self.badges = Badges.calculate(public_flags)
        self.bot = bot

class PrivateChannel:
    def __init__(self, session, raw_data:dict):
        self._session = session

        self.id = raw_data.get('id')
        self.recipients = []
        for recipient in raw_data.get('recipients'):
            self.recipients.append(Recipient(**recipient))

    async def message(self):
        return await self._session.request("POST", f"channels/{self.id}/channels")
