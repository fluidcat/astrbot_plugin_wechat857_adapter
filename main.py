import importlib
import sys

from astrbot.api import logger
from astrbot.api.star import Context, Star
from astrbot.core import AstrBotConfig
from astrbot.core.platform import AstrMessageEvent
from astrbot.core.star.filter.custom_filter import CustomFilter
from pymediainfo import MediaInfo  # 触发astrbot安装requirements.txt

WeChat857Adapter = None
WeChat857Event = None


class WeChat857AdapterFilter(CustomFilter):
    def __init__(self, raise_error: bool = True):
        super().__init__(raise_error)

    def filter(self, event: AstrMessageEvent, cfg: AstrBotConfig) -> bool:
        return event.get_platform_name() == 'wechat857'


class Wechat857AdapterPlugin(Star):

    def __init__(self, context: Context):
        super().__init__(context)
        self.context = context

    async def initialize(self):
        # 强制预清理：在导入适配器前，无条件删除既有 http_endpoint 注册，确保干净状态
        try:
            adapter_name = "wechat857"
            import astrbot.core.platform.register as _core_reg
            _map = getattr(_core_reg, "platform_cls_map", None)
            _list = getattr(_core_reg, "platform_registry", None)
            if _map is not None and (adapter_name in _map):
                del _map[adapter_name]
            for i in reversed(range(len(_list))):
                if _list[i].name == adapter_name:
                    del _list[i]
            logger.debug("强制预清理：已移除 wechat857 既有注册。")
        except Exception:
            pass

        try:
            load_wechat857_modules()
        except ImportError as e:
            logger.error(f"导入 Wechat 857 Adapter 失败，请检查依赖是否安装: {e}")
            raise

    async def terminate(self):
        # 停用wechat857
        for p in self.context.platform_manager.get_insts():
            pm = p.meta()
            if pm.name == 'wechat857':
                await self.context.platform_manager.terminate_platform(pm.id)


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
            logger.info("清除 wechat857_adapter 缓存，触发热加载")

        # 动态导入模块（支持相对路径）
        adapter_module = importlib.import_module(adapter_module_name, package=__name__)
        # 执行初始化函数
        adapter_module._inject_astrbot_field_metadata()
        # 赋值给全局变量
        WeChat857Adapter = adapter_module.WeChat857Adapter

        # 2. 处理 http_endpoint_event 模块
        if hot_reload and event_module_name in sys.modules:
            del sys.modules[event_module_name]
            logger.info("清除 wechat857_event 缓存，触发热加载")

        event_module = importlib.import_module(event_module_name, package=__name__)
        WeChat857Event = event_module.WeChat857Event

        logger.info("WeChat857 模块加载成功（热加载：%s）", hot_reload)

    except ImportError as e:
        logger.error(f"导入 WeChat857 Adapter 失败，请检查依赖是否安装: {e}")
        # 重置全局变量，避免状态不一致
        WeChat857Adapter = None
        WeChat857Event = None
        raise
