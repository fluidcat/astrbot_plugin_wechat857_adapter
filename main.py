import datetime
import importlib
import sys

from astrbot import logger
from astrbot.api.star import Context, Star, register
from astrbot.core import AstrBotConfig
from astrbot.core.star.filter.custom_filter import CustomFilter
from pymediainfo import MediaInfo  # noqa: F401 触发astrbot安装requirements.txt
from astrbot.api.event import filter, AstrMessageEvent

WeChat857Adapter = None
WeChat857Event = None
PLUGIN_ADAPTER_NAME = "wechat857"


class WeChat857AdapterFilter(CustomFilter):
    def __init__(self, raise_error: bool = True):
        super().__init__(raise_error)

    def filter(self, event: AstrMessageEvent, cfg: AstrBotConfig) -> bool:
        return event.get_platform_name() == PLUGIN_ADAPTER_NAME


@register(
    "astrbot_plugin_wechat857_adapter",
    "fluidcat",
    "wechat857 接入插件，在机器人中可添加wechat857机器人使用",
    "1.0.0")
class Wechat857AdapterPlugin(Star):

    def __init__(self, context: Context):
        super().__init__(context)
        self.context = context

    @filter.command("wx857_qrcode")
    async def list_wechat_login_qrcode(self, event: AstrMessageEvent):
        insts = self.get_wechat857_insts()
        urls = []
        for inst in insts:
            if (qrcode := getattr(inst, "login_qrcode_url")) and qrcode.startswith("http"):
                urls.append(f"#### 「{inst.meta().id}」实例登录二维码")
                urls.append(f"![{inst.meta().id}]({qrcode})")
        yield event.plain_result("\n".join(urls or ["没有需要登录的wx857实例"]))

    async def initialize(self):
        # 强制预清理：在导入适配器前，无条件删除既有 http_endpoint 注册，确保干净状态
        try:
            import astrbot.core.platform.register as _core_reg
            _map = getattr(_core_reg, "platform_cls_map", None)
            _list = getattr(_core_reg, "platform_registry", None)
            if _map is not None and (PLUGIN_ADAPTER_NAME in _map):
                del _map[PLUGIN_ADAPTER_NAME]
            for i in reversed(range(len(_list))):
                if _list[i].name == PLUGIN_ADAPTER_NAME:
                    del _list[i]
            logger.debug(f"强制预清理：已移除 {PLUGIN_ADAPTER_NAME} 既有注册。")
        except Exception:
            pass

        try:
            load_wechat857_modules()
        except ImportError as e:
            logger.error(f"导入 {PLUGIN_ADAPTER_NAME} Adapter 失败，请检查依赖是否安装: {e}")
            raise

        self.context.cron_manager.scheduler.add_job(
            self.load_platform,
            next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=5)
        )

    async def load_platform(self):
        running_ids = [inst.meta().id for inst in self.context.platform_manager.get_insts()]
        for config in self.context.platform_manager.platforms_config:
            platform_id = config.get("id")
            platform_type = config.get("type")
            if platform_id not in running_ids and platform_type == PLUGIN_ADAPTER_NAME:
                await self.context.platform_manager.load_platform(config)

    def get_wechat857_insts(self):
        return [p for p in self.context.platform_manager.get_insts() if p.meta().name == PLUGIN_ADAPTER_NAME]

    async def terminate(self):
        # 停用wechat857
        for p in self.get_wechat857_insts():
            await self.context.platform_manager.terminate_platform(p.meta().id)


def load_wechat857_modules(hot_reload: bool = True):
    """
    加载 wechat857 相关模块（支持热加载）
    :param hot_reload: 是否清除缓存重新导入（热加载）
    """
    global WeChat857Adapter, WeChat857Event

    try:
        adapter_module_name = "..wechat857_adapter"
        event_module_name = "..wechat857_event"

        # 1. 处理 http_endpoint_adapter 模块
        if hot_reload and adapter_module_name in sys.modules:
            del sys.modules[adapter_module_name]
            logger.info(f"清除 {PLUGIN_ADAPTER_NAME} adapter 缓存，触发热加载")

        # 动态导入模块（支持相对路径）
        adapter_module = importlib.import_module(adapter_module_name, package=__name__)
        # 执行初始化函数
        adapter_module._astrbot_inject()
        # 赋值给全局变量
        WeChat857Adapter = adapter_module.WeChat857Adapter

        # 2. 处理 http_endpoint_event 模块
        if hot_reload and event_module_name in sys.modules:
            del sys.modules[event_module_name]
            logger.info(f"清除 {PLUGIN_ADAPTER_NAME}_event 缓存，触发热加载")

        event_module = importlib.import_module(event_module_name, package=__name__)
        WeChat857Event = event_module.WeChat857Event

        logger.info(f"{PLUGIN_ADAPTER_NAME} 模块加载成功（热加载：%s）", hot_reload)

    except ImportError as e:
        logger.error(f"导入 {PLUGIN_ADAPTER_NAME} Adapter 失败，请检查依赖是否安装: {e}")
        # 重置全局变量，避免状态不一致
        WeChat857Adapter = None
        WeChat857Event = None
        raise
