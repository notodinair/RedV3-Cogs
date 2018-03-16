from datetime import datetime

import discord
from redbot.core import Config
from redbot.core.bot import Red


conf = Config.get_conf(None, identifier=441356724, force_registration=True, cog_name="Quotes")
conf.register_guild(quotes=[])


class Quote:
    bot: Red = None

    def __init__(self, **kwargs):
        """Create a new Quote

        Keyword args
        ------------
        id: int
            This quote's ID
        guild_id: int
            The guild ID that this quote belongs to
        author_id: int
            The snowflake ID of the author
        message_author_id: int
            The message author ID
        timestamp: int
            A datetime timestamp of when this quote was initially created. Defaults to unix epoch (``0``)
        edited: bool
            A boolean value indicating if this quote has been edited before. Default value is ``False``.
            This value, along with `edit_timestamp` is not properly displayed just yet.
        edit_timestamp: int
            A datetime timestamp of when this quote was last edited. Defaults to ``None``
        """
        self.guild = self.bot.get_guild(kwargs.get("guild_id"))
        self.author = self.guild.get_member(kwargs.get("author_id"))
        self.message_author = self.guild.get_member(kwargs.get("message_author_id"))
        self.text = kwargs.get("text")
        self.id = kwargs.get("id")
        self.timestamp = datetime.fromtimestamp(kwargs.get("timestamp", 0))
        # The following two fields are saved & properly modified when necessary,
        # but not displayed to end-users just yet
        self.edited = kwargs.get("edited", False)
        self._edit_timestamp = kwargs.get("edit_timestamp", None)

    @property
    def edit_timestamp(self):
        return self._edit_timestamp

    @edit_timestamp.setter
    def edit_timestamp(self, val: datetime):
        self._edit_timestamp = val.timestamp()

    @property
    def embed(self):
        colour = discord.Colour.blurple() if not self.message_author else self.message_author.colour
        embed = discord.Embed(colour=colour, description=self.text, timestamp=self.timestamp)

        if self.message_author:  # Check if we found the message author
            embed.set_author(name=self.message_author.display_name, icon_url=self.message_author.avatar_url)
        elif self.author:  # Attempt to fall back to the quote creator
            embed.set_author(name=self.author.display_name, icon_url=self.author.avatar_url)
        else:
            embed.set_author(name="Unknown quote author", icon_url=self.guild.icon_url)

        footer_str = f"Quote #{self.id}"
        if self.author != self.message_author:
            footer_str += f" | Quoted by {self.author!s}"
        embed.set_footer(text=footer_str)

        return embed

    def to_dict(self) -> dict:
        return {
            'author_id': self.author.id,
            'message_author_id': self.message_author.id,
            'text': self.text,
            'guild_id': self.guild.id,  # yes, this is redundant, but also necessary
            'timestamp': datetime.utcnow().timestamp(),
            'edited': self.edited,
            'edit_timestamp': self.edit_timestamp
        }

    async def can_modify(self, member: discord.Member) -> bool:
        return any([self.message_author and self.message_author.id == member.id,
                    await self.bot.is_mod(member), await self.bot.is_owner(member)])

    async def save(self):
        self.edit_timestamp = datetime.utcnow()
        async with conf.guild(self.guild).quotes() as quotes:
            quotes[self.id - 1].update(self.to_dict())

    async def delete(self):
        async with conf.guild(self.guild).quotes() as quotes:
            del quotes[self.id - 1]

    # noinspection PyShadowingBuiltins
    @classmethod
    async def get(cls, guild: discord.Guild, id: int):
        quotes = list(await conf.guild(guild).quotes())
        if 0 < len(quotes) >= id:
            return cls(**quotes[id - 1], id=id)
        return None

    @classmethod
    async def create(cls, text: str, author: discord.Member, message_author: discord.Member):
        guild = author.guild
        quote = {
            'author_id': author.id,
            'text': text,
            'message_author_id': message_author.id,
            'guild_id': guild.id,
            'timestamp': datetime.utcnow().timestamp()
        }
        async with conf.guild(guild).quotes() as quotes:
            quotes.append(quote)
            return cls(**quote, id=len(quotes))