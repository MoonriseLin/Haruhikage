# -*- coding: utf-8 -*-
import asyncio
import os

import botpy
from botpy import logging

from botpy.message import Message
from botpy.ext.cog_yaml import read

test_config = read(os.path.join(os.path.dirname(__file__), "config.yaml"))

_log = logging.get_logger()

# 公域机器人只能收到「@ 机器人」的消息，使用 public_guild_messages + on_at_message_create。
# 私域机器人可收到子频道内全部消息，使用 guild_messages + on_message_create。
# 请勿同时打开两者，否则同一条 @ 消息可能触发两次回调。
USE_GUILD_ALL_MESSAGES = False


class MyClient(botpy.Client):
    async def on_ready(self):
        _log.info(f"robot 「{self.robot.name}」 on_ready!")

    async def on_message_create(self, message: Message):
        """仅私域机器人会收到：子频道内每一条消息。"""
        if not USE_GUILD_ALL_MESSAGES:
            return
        await self._handle_incoming(message, source="message_create")

    async def on_at_message_create(self, message: Message):
        """公域：仅 @ 机器人的消息；私域请勿与 guild_messages 同时订阅，以免重复。"""
        if USE_GUILD_ALL_MESSAGES:
            return
        await self._handle_incoming(message, source="at_message_create")

    async def _handle_incoming(self, message: Message, source: str):
        line = (
            f"[{source}] channel_id={message.channel_id} "
            f"message_id={message.id} content={message.content!r}"
        )
        _log.info(line)
        print(line, flush=True)

        if not self._should_recall_reply(message, source):
            return

        reply_text = f"机器人{self.robot.name}收到你的@消息了: {message.content}"
        _log.info(reply_text)
        print(reply_text, flush=True)
        _message = await message.reply(content=reply_text)
        await self.api.recall_message(message.channel_id, _message.get("id"), hidetip=True)

    def _should_recall_reply(self, message: Message, source: str) -> bool:
        if source == "at_message_create":
            return True
        rid = self.robot.id
        return any(getattr(u, "id", None) == rid for u in message.mentions)


if __name__ == "__main__":
    # macOS 官方 Python 常缺系统 CA，可 pip install certifi 后由下面自动指定
    try:
        import certifi

        os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    except ImportError:
        pass

    # Python 3.12+ 主线程默认无事件循环，botpy.Client 初始化会调用 get_event_loop()
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    # 通过kwargs，设置需要监听的事件通道
    if USE_GUILD_ALL_MESSAGES:
        intents = botpy.Intents(guild_messages=True)
    else:
        intents = botpy.Intents(public_guild_messages=True)
    client = MyClient(intents=intents)
    client.run(appid=test_config["appid"], secret=test_config["secret"])
