import asyncio
import io
from pathlib import Path
from typing import TYPE_CHECKING

from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.api.platform import AstrBotMessage, PlatformMetadata
from astrbot.core.message.components import *
from astrbot.core.platform import MessageType
from PIL import Image as PILImage

if TYPE_CHECKING:
    from .wechat857_adapter import WeChat857Adapter


class WeChat857Event(AstrMessageEvent):

    def __init__(
            self,
            message_str: str,
            message_obj: AstrBotMessage,
            platform_meta: PlatformMetadata,
            session_id: str,
            adapter: "WeChat857Adapter",  # 传递适配器实例
    ):
        super().__init__(message_str, message_obj, platform_meta, session_id)
        self.message_obj = message_obj  # Save the full message object
        self.adapter = adapter  # Save the adapter instance

    def get_message_outline(self) -> str:
        """重写此方法以规避核心框架的遍历问题，安全生成消息概要。
        兼容 self.message_obj.message 既可能是 MessageChain 也可能是 list 的情况。
        """
        if not self.message_obj or not self.message_obj.message:
            return ""

        # 核心修复：确保在遍历前调用 .get_chain()
        chain = self.message_obj.message
        if isinstance(chain, MessageChain):
            iterable_chain = chain.chain
        else:  # 如果它已经是列表，则直接使用
            iterable_chain = chain

        return super()._outline_chain(iterable_chain)

    async def send(self, message: MessageChain):
        if self.adapter.mute_bot:
            logger.warning(f"platform[{self.adapter.meta().id}]已开启禁言，停止回复任何消息")
            return
        self.session_id = self.session_id.removesuffix("_wxid")
        if (
                any(isinstance(m, At) for m in message.chain)
                and any(isinstance(m, Plain) for m in message.chain)
        ):
            await self._send_at_text(message)
        else:
            for comp in message.chain:
                await asyncio.sleep(1)
                if isinstance(comp, Plain):
                    await self._send_text(comp)
                elif isinstance(comp, At):
                    await self._send_at(comp)
                elif isinstance(comp, Image):
                    await self._send_image(comp)
                # elif isinstance(comp, WechatEmoji):
                #     await self._send_emoji(comp)
                elif isinstance(comp, Record):
                    await self._send_voice(comp)
                elif isinstance(comp, Video):
                    await self._send_video(comp)
                elif isinstance(comp, File):
                    await self._send_file(comp)
                elif isinstance(comp, Music):
                    await self._send_music(comp)
        self._has_send_oper = True

    async def _send_image(self, comp: Image):
        file_path = await comp.convert_to_file_path()
        session_id = self.get_group_id() or self.get_sender_id() or self.session_id

        if hasattr(comp, "cdn_xml"):
            await self.adapter.client.send_cdn_img_msg(session_id, comp.cdn_xml)
        else:
            await self.adapter.client.send_image_message(session_id, Path(file_path))

    async def _send_at_text(self, message: MessageChain):
        session_id = self.get_group_id() or self.get_sender_id() or self.session_id

        ats = []
        at_text = ""
        plain = ""
        for comp in message.chain:
            if isinstance(comp, At):
                ats.append(comp.qq)
                at_text += f"@{comp.name or comp.qq}\u2005"
            elif isinstance(comp, Plain):
                plain = comp.text
        await self.adapter.client.send_text_message(session_id, at_text + plain, ats)

    async def _send_at(self, comp: At):
        if self.message_obj.type != MessageType.GROUP_MESSAGE:
            return
        ats = comp.name or comp.qq
        at_text = f"@{ats}\u2005"

        session_id = self.get_group_id() or self.get_sender_id() or self.session_id
        await self.adapter.client.send_text_message(session_id, at_text, [ats])

    async def _send_text(self, comp: Plain):
        message_text = comp.text

        session_id = self.get_group_id() or self.get_sender_id() or self.session_id

        await self.adapter.client.send_text_message(session_id, message_text)

    # async def _send_emoji(self, comp: WechatEmoji):
    #     session_id = self.get_group_id() or self.get_sender_id() or self.session_id
    #     await self.adapter.client.send_emoji_message(session_id, comp.md5, comp.md5_len)

    async def _send_voice(self, comp: Record):
        session_id = self.get_group_id() or self.get_sender_id() or self.session_id

        if hasattr(comp, "cdn_xml"):
            await self.adapter.client.send_cdn_file_msg(session_id, comp.cdn_xml)
        else:
            record_path = await comp.convert_to_file_path()
            ext = os.path.splitext(record_path)[1].lower()[1:]
            await self.adapter.client.send_voice_message(session_id, Path(record_path), ext)

    async def _send_video(self, comp: Video):
        session_id = self.get_group_id() or self.get_sender_id() or self.session_id

        if hasattr(comp, "cdn_xml"):
            await self.adapter.client.send_cdn_video_msg(session_id, comp.cdn_xml)
        else:
            record_path = await comp.convert_to_file_path()
            ext = os.path.splitext(record_path)[1].lower()[1:]
            await self.adapter.client.send_voice_message(session_id, Path(record_path), ext)

    async def _send_file(self, comp: File):
        session_id = self.get_group_id() or self.get_sender_id() or self.session_id

        if hasattr(comp, "cdn_xml"):
            await self.adapter.client.send_cdn_file_msg(session_id, comp.cdn_xml)
        else:
            raise NotImplementedError("暂不支持发送本地文件")

    # async def _send_xml(self, comp: Xml):
    #     if self.get_group_id() and "#" in self.session_id:
    #         session_id = self.session_id.split("#")[0]
    #     else:
    #         session_id = self.session_id
    #     await self.adapter.client.send_app_message(session_id, comp.data, comp.resid)

    async def _send_music(self, comp: Music):
        session_id = self.get_group_id() or self.get_sender_id() or self.session_id
        await self.adapter.client.send_app_message(session_id, comp.content, 3)

    @staticmethod
    def _validate_base64(b64: str) -> bytes:
        return base64.b64decode(b64, validate=True)

    @staticmethod
    def _compress_image(data: bytes) -> str:
        img = PILImage.open(io.BytesIO(data))
        buf = io.BytesIO()
        if img.format == "JPEG":
            img.save(buf, "JPEG", quality=80)
        else:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(buf, "JPEG", quality=80)
        # logger.info("图片处理完成！！！")
        return base64.b64encode(buf.getvalue()).decode()
