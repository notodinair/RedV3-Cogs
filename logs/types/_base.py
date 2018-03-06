from abc import ABC, abstractmethod

from typing import Dict, Hashable


class BaseLog(ABC):
    """Log type common base"""
    name: str = NotImplemented
    descriptions: Dict[str, str] = {}

    # noinspection PyUnusedLocal
    def __init__(self, guild, **kwargs):
        from logs.guildlog import GuildLog
        self.guild: GuildLog = guild

    def __str__(self):
        return self.name

    @property
    def settings(self) -> Dict[str, bool]:
        return self.guild.settings.get(self.name, {})

    def has_changed(self, before, after, config_setting: str):
        if isinstance(before, Hashable) and isinstance(after, Hashable):
            before = hash(before)
            after = hash(after)
        return before != after and self.settings.get(config_setting, False) is not False

    @abstractmethod
    async def create(self, created, **kwargs):
        return NotImplemented

    @abstractmethod
    async def update(self, before, after, **kwargs):
        return NotImplemented

    @abstractmethod
    async def delete(self, deleted, **kwargs):
        return NotImplemented
