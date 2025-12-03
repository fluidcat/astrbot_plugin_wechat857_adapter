import base64
import io
import os

import aiohttp
import binascii
import pysilk
from pydub import AudioSegment

from .base import *
from .errors import *


class ToolMixin(WechatAPIClientBase):

    async def download_image(self, from_user_name: str, to_user_name: str, msg_id: int) -> str:
        """
        异步分块下载图片，返回完整的Base64字符串
        :param from_user_name: 发送方wxid（对应ToWxid）
        :param to_user_name: 接收方wxid（对应Wxid）
        :param msg_id: 消息ID
        :return: 图片完整的Base64编码字符串
        """
        if not self.wxid:
            raise UserLoggedOut("请先登录")

        # 1. 初始化请求参数，先获取图片总长度
        payload = {
            "CompressType": 0,
            "Wxid": to_user_name,
            "MsgId": msg_id,
            "Section": {"DataLen": 0, "StartPos": 0},
            "ToWxid": from_user_name,
            "DataLen": 0,
        }

        async with aiohttp.ClientSession() as session:
            # 首次请求获取图片总长度
            response = await session.post(Uri.DownloadImg, json=payload)
            json_resp = await response.json()

            if not json_resp.get("Success"):
                self.error_handler(json_resp)

            data = json_resp.get("Data", {})
            # 验证微信基础响应
            base_resp = data.get("BaseResponse", {})
            if base_resp.get("ret") != 0:
                err_msg = base_resp.get("errMsg", {}).get("string", "微信接口返回错误")
                raise Exception(f"微信接口错误: {err_msg}")

            # 获取图片总长度
            total_len = data.get("totalLen", 0)
            if total_len <= 0:
                raise Exception("获取图片总长度失败")

            # 更新payload为分块下载参数
            payload["DataLen"] = total_len
            payload["Section"]["DataLen"] = total_len  # Section.DataLen传最大值
            payload["Section"]["StartPos"] = 0

            # 2. 分块下载并收集二进制数据
            img_bytes_list = []  # 存储所有分块的二进制数据
            total_received = 0

            while total_received < total_len:
                # 发送分块请求
                chunk_resp = await session.post(Uri.DownloadImg, json=payload)
                chunk_json = await chunk_resp.json()

                if not chunk_json.get("Success"):
                    self.error_handler(chunk_json)

                chunk_data = chunk_json.get("Data", {})
                # 提取分块核心数据
                chunk_info = chunk_data.get("data", {})
                chunk_len = chunk_info.get("iLen", 0)
                chunk_buffer = chunk_info.get("buffer", "")

                if chunk_len <= 0 or not chunk_buffer:
                    raise Exception(f"空分块数据 - 起始位置: {payload['Section']['StartPos']}")

                # Base64解码分块数据（修复异常捕获）
                try:
                    chunk_bytes = base64.b64decode(chunk_buffer)
                except binascii.Error as e:  # 直接使用binascii模块的Error
                    raise Exception(f"分块Base64解码失败: {str(e)}")
                except Exception as e:  # 兜底捕获其他解码异常
                    raise Exception(f"分块解码异常: {str(e)}")

                # 验证解码后长度是否匹配
                if len(chunk_bytes) != chunk_len:
                    raise Exception(
                        f"分块长度不匹配 - 预期:{chunk_len}, 实际:{len(chunk_bytes)}"
                    )

                # 添加到二进制数据列表
                img_bytes_list.append(chunk_bytes)
                total_received += chunk_len

                # 更新下一分块起始位置
                current_start_pos = chunk_data.get("startPos", 0)
                payload["Section"]["StartPos"] = current_start_pos + chunk_len

                # 下载完成则退出循环
                if total_received >= total_len:
                    break

            # 3. 拼接所有二进制数据并编码为完整Base64字符串
            full_img_bytes = b"".join(img_bytes_list)
            full_base64 = base64.b64encode(full_img_bytes).decode("utf-8")

            return full_base64

    async def download_image_bak(self, from_user_name: str, to_user_name: str, msg_id: int) -> str:
        if not self.wxid:
            raise UserLoggedOut("请先登录")
        payload = {
            "CompressType": 0,
            "Wxid": to_user_name,
            "MsgId": msg_id,
            "Section": {"DataLen": 0, "StartPos": 0},
            "ToWxid": from_user_name,
            "DataLen": 0,
        }
        async with aiohttp.ClientSession() as session:
            response = await session.post(Uri.DownloadImg, json=payload)
            json_resp = await response.json()

            if json_resp.get("Success"):
                return json_resp.get("Data", {}).get('data', {}).get('buffer')
            else:
                self.error_handler(json_resp)

    async def download_voice(self, msg_id: str, voiceurl: str, length: int, bufid: str, fromId: str) -> str:
        """下载语音文件。

        Args:
            msg_id (str): 消息的msgid
            voiceurl (str): 语音的url，从xml获取
            length (int): 语音长度，从xml获取

        Returns:
            str: 语音的base64编码字符串

        Raises:
            UserLoggedOut: 未登录时调用
            根据error_handler处理错误
        """
        if not self.wxid:
            raise UserLoggedOut("请先登录")

        async with aiohttp.ClientSession() as session:
            json_param = {"Wxid": self.wxid, "FromUserName": fromId, "Bufid": bufid, "MsgId": msg_id,
                          "Voiceurl": voiceurl, "Length": length}
            response = await session.post(Uri.DownloadVoice, json=json_param)
            json_resp = await response.json()

            if json_resp.get("Success"):
                return json_resp.get("Data").get("data").get("buffer")
            else:
                self.error_handler(json_resp)

    async def download_attach(self, attach_id: str) -> dict:
        """下载附件。

        Args:
            attach_id (str): 附件ID

        Returns:
            dict: 附件数据

        Raises:
            UserLoggedOut: 未登录时调用
            根据error_handler处理错误
        """
        if not self.wxid:
            raise UserLoggedOut("请先登录")

        async with aiohttp.ClientSession() as session:
            json_param = {"Wxid": self.wxid, "AttachId": attach_id}
            response = await session.post(Uri.DownloadFile, json=json_param)
            json_resp = await response.json()

            if json_resp.get("Success"):
                return json_resp.get("Data").get("data").get("buffer")
            else:
                self.error_handler(json_resp)

    async def download_video(self, msg_id) -> str:
        """下载视频。

        Args:
            msg_id (str): 消息的msg_id

        Returns:
            str: 视频的base64编码字符串

        Raises:
            UserLoggedOut: 未登录时调用
            根据error_handler处理错误
        """
        if not self.wxid:
            raise UserLoggedOut("请先登录")

        async with aiohttp.ClientSession() as session:
            json_param = {"Wxid": self.wxid, "MsgId": msg_id}
            response = await session.post(Uri.DownloadVideo, json=json_param)
            json_resp = await response.json()

            if json_resp.get("Success"):
                return json_resp.get("Data").get("data").get("buffer")
            else:
                self.error_handler(json_resp)

    async def set_step(self, count: int) -> bool:
        """设置步数。

        Args:
            count (int): 要设置的步数

        Returns:
            bool: 成功返回True，失败返回False

        Raises:
            UserLoggedOut: 未登录时调用
            BanProtection: 风控保护: 新设备登录后4小时内请挂机
            根据error_handler处理错误
        """
        if not self.wxid:
            raise UserLoggedOut("请先登录")
        elif not self.ignore_protect and self.check(14400):
            raise BanProtection("风控保护: 新设备登录后4小时内请挂机")

        async with aiohttp.ClientSession() as session:
            json_param = {"Wxid": self.wxid, "Number": count}
            response = await session.post(Uri.UpdateStepNumberApi, json=json_param)
            json_resp = await response.json()

            if json_resp.get("Success"):
                return True
            else:
                self.error_handler(json_resp)

    async def set_proxy(self, proxy: Proxy) -> bool:
        """设置代理。

        Args:
            proxy (Proxy): 代理配置对象

        Returns:
            bool: 成功返回True，失败返回False

        Raises:
            UserLoggedOut: 未登录时调用
            根据error_handler处理错误
        """
        if not self.wxid:
            raise UserLoggedOut("请先登录")

        async with aiohttp.ClientSession() as session:
            json_param = {"Wxid": self.wxid,
                          "Proxy": {"ProxyIp": f"{proxy.ip}:{proxy.port}",
                                    "ProxyUser": proxy.username,
                                    "ProxyPassword": proxy.password}}
            response = await session.post(Uri.setproxy, json=json_param)
            json_resp = await response.json()

            if json_resp.get("Success"):
                return True
            else:
                self.error_handler(json_resp)

    @staticmethod
    def base64_to_file(base64_str: str, file_name: str, file_path: str) -> bool:
        """将base64字符串转换为文件并保存。

        Args:
            base64_str (str): base64编码的字符串
            file_name (str): 要保存的文件名
            file_path (str): 文件保存路径

        Returns:
            bool: 转换成功返回True，失败返回False
        """
        try:
            os.makedirs(file_path, exist_ok=True)

            # 拼接完整的文件路径
            full_path = os.path.join(file_path, file_name)

            # 移除可能存在的 base64 头部信息
            if ',' in base64_str:
                base64_str = base64_str.split(',')[1]

            # 解码 base64 并写入文件
            with open(full_path, 'wb') as f:
                f.write(base64.b64decode(base64_str))

            return True

        except Exception as e:
            return False

    @staticmethod
    def file_to_base64(file_path: str) -> str:
        """将文件转换为base64字符串。

        Args:
            file_path (str): 文件路径

        Returns:
            str: base64编码的字符串
        """
        with open(file_path, 'rb') as f:
            return base64.b64encode(f.read()).decode()

    @staticmethod
    def base64_to_byte(base64_str: str) -> bytes:
        """将base64字符串转换为bytes。

        Args:
            base64_str (str): base64编码的字符串

        Returns:
            bytes: 解码后的字节数据
        """
        # 移除可能存在的 base64 头部信息
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]

        return base64.b64decode(base64_str)

    @staticmethod
    def byte_to_base64(byte: bytes) -> str:
        """将bytes转换为base64字符串。

        Args:
            byte (bytes): 字节数据

        Returns:
            str: base64编码的字符串
        """
        return base64.b64encode(byte).decode("utf-8")

    @staticmethod
    async def silk_byte_to_byte_wav_byte(silk_byte: bytes) -> bytes:
        """将silk字节转换为wav字节。

        Args:
            silk_byte (bytes): silk格式的字节数据

        Returns:
            bytes: wav格式的字节数据
        """
        return await pysilk.async_decode(silk_byte, to_wav=True)

    @staticmethod
    def wav_byte_to_amr_byte(wav_byte: bytes) -> bytes:
        """将WAV字节数据转换为AMR格式。

        Args:
            wav_byte (bytes): WAV格式的字节数据

        Returns:
            bytes: AMR格式的字节数据

        Raises:
            Exception: 转换失败时抛出异常
        """
        try:
            # 从字节数据创建 AudioSegment 对象
            audio = AudioSegment.from_wav(io.BytesIO(wav_byte))

            # 设置 AMR 编码的标准参数
            audio = audio.set_frame_rate(8000).set_channels(1)

            # 创建一个字节缓冲区来存储 AMR 数据
            output = io.BytesIO()

            # 导出为 AMR 格式
            audio.export(output, format="amr")

            # 获取字节数据
            return output.getvalue()

        except Exception as e:
            raise Exception(f"转换WAV到AMR失败: {str(e)}")

    @staticmethod
    def wav_byte_to_amr_base64(wav_byte: bytes) -> str:
        """将WAV字节数据转换为AMR格式的base64字符串。

        Args:
            wav_byte (bytes): WAV格式的字节数据

        Returns:
            str: AMR格式的base64编码字符串
        """
        return base64.b64encode(ToolMixin.wav_byte_to_amr_byte(wav_byte)).decode()

    @staticmethod
    async def wav_byte_to_silk_byte(wav_byte: bytes) -> bytes:
        """将WAV字节数据转换为silk格式。

        Args:
            wav_byte (bytes): WAV格式的字节数据

        Returns:
            bytes: silk格式的字节数据
        """
        # get pcm data
        audio = AudioSegment.from_wav(io.BytesIO(wav_byte))
        pcm = audio.raw_data
        return await pysilk.async_encode(pcm, data_rate=audio.frame_rate, sample_rate=audio.frame_rate)

    @staticmethod
    async def wav_byte_to_silk_base64(wav_byte: bytes) -> str:
        """将WAV字节数据转换为silk格式的base64字符串。

        Args:
            wav_byte (bytes): WAV格式的字节数据

        Returns:
            str: silk格式的base64编码字符串
        """
        return base64.b64encode(await ToolMixin.wav_byte_to_silk_byte(wav_byte)).decode()

    @staticmethod
    async def silk_base64_to_wav_byte(silk_base64: str) -> bytes:
        """将silk格式的base64字符串转换为WAV字节数据。

        Args:
            silk_base64 (str): silk格式的base64编码字符串

        Returns:
            bytes: WAV格式的字节数据
        """
        return await ToolMixin.silk_byte_to_byte_wav_byte(base64.b64decode(silk_base64))