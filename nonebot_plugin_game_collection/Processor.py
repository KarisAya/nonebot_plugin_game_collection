from typing import Union, Tuple, List, Dict, Set, Callable, Coroutine
from io import BytesIO
from PIL import Image
import re
import time
from .utils.utils import download_url
from .Exceptions import (
    RegEventException,
    ArgException,
    SupArgsException,
)

PreEventData = Tuple[str, str, List[str], str, str, Set[str]]
Result = Union[str, BytesIO, list, Coroutine]


class Event:
    event_name: str = None
    """事件名"""
    raw_command: str = None
    """事件原指令"""
    args: list = None
    """事件参数"""
    user_id: str = None
    """事件用户"""
    group_id: str = None
    """事件所在群组，默认为private"""
    nickname: str = None
    """事件用户昵称"""
    extra_args: dict = {}

    EVENTS_DICT: Dict[str, Union[Set[str], re.Pattern]] = {}
    """事件字典"""

    COMMANDS_DICT: Dict[str, Set[str]] = {}
    """指令字典"""

    REGEX_DICT: Dict[re.Pattern, Set[str]] = {}
    """正则指令字典"""

    GOT_ARG: dict = {}
    """等待指令"""
    FUNCTIONS_DICT: Dict[str, Callable] = {}

    NEED_EXTRA_ARGS: Dict[str, set] = {}
    """
    需要额外的参数
        "avatar":头像url
        "group_info":群头像url,群名
        "permission":权限等级
            用户：0
            群管：1
            群主：2
            超管：3
        "image_list":图片url
        "to_me":bool
        "at":list

    """

    def __init__(
        self,
        event_name: str,
        raw_command: str,
        args: str,
        user_id: str,
        group_id: str = None,
        nickname: str = None,
        extra_args: dict = {},
    ):
        self.event_name = event_name
        self.raw_command = raw_command
        self.args = args
        self.user_id = user_id
        self.group_id = group_id
        self.nickname = nickname
        self.extra_args = extra_args

    @classmethod
    def is_command(
        cls, command: str, user_id: str, group_id: str
    ) -> List[PreEventData]:
        """
        判断是否为指令
        """
        if not (command_list := command.strip().split()):
            return []
        command_start = command_list[0]
        for cmd, event_name_set in cls.COMMANDS_DICT.items():
            if command_start.startswith(cmd):
                break
        else:
            return []
        if cmd == command_start:
            args = command_list[1:]
        else:
            command_list[0] = command_list[0][len(cmd) :]
            args = command_list
        return [
            (
                event_name,
                cmd,
                args,
                user_id,
                group_id,
                cls.NEED_EXTRA_ARGS.get(event_name),
            )
            for event_name in event_name_set
        ]

    @classmethod
    def is_regex(cls, command: str, user_id: str, group_id: str) -> List[PreEventData]:
        """
        判断是否为正则指令
        """
        for pattern, event_name_set in cls.REGEX_DICT.items():
            if re.match(pattern, command):
                break
        else:
            return []
        return [
            (
                event_name,
                command,
                [],
                user_id,
                group_id,
                cls.NEED_EXTRA_ARGS.get(event_name),
            )
            for event_name in event_name_set
        ]

    @classmethod
    def is_got(cls, command: str, user_id: str, group_id: str) -> List[PreEventData]:
        """
        判断是否为等待指令
        """
        if not (got := cls.GOT_ARG.get(user_id)):
            return []
        if not (event_tuple := got.get(group_id)):
            return []
        event_name, event_time = event_tuple
        if time.time() - event_time > 60:
            del Event.GOT_ARG[user_id][group_id]
            del Event.FUNCTIONS_DICT[event_name]
            return []
        return [
            (
                event_name,
                command,
                command.strip().split(),
                user_id,
                group_id,
                cls.NEED_EXTRA_ARGS.get(event_name),
            )
        ]

    @classmethod
    def check(cls, *args) -> List[PreEventData]:
        """
        return list of
            event_name,raw_command,args,user_id,group_id,need_extra_args
        """
        return cls.is_command(*args) + cls.is_regex(*args) + cls.is_got(*args)

    async def run(self) -> Result:
        try:
            return await self.FUNCTIONS_DICT.get(self.event_name)(self)
        except ArgException:
            pass

    def got(self, need_extra_args: dict = {}):
        """
        注册等待指令事件
        """

        def decorator(function: Coroutine):
            event_name = f"{self.user_id}:{self.group_id}:{self.event_name}"
            Event.GOT_ARG.setdefault(self.user_id, {})[self.group_id] = (
                event_name,
                time.time(),
            )
            if need_extra_args:
                Event.NEED_EXTRA_ARGS[event_name] = need_extra_args

            async def wrapper(event: Event):
                result = await function(event)
                event.finish()
                return result

            Event.FUNCTIONS_DICT[event_name] = wrapper

        return decorator

    def whisper(self, need_extra_args: dict = {}):
        """
        注册私信触发事件
        """

        def decorator(function: Coroutine):
            event_name = f"{self.user_id}:private:{self.event_name}"
            Event.GOT_ARG.setdefault(self.user_id, {})["private"] = (
                event_name,
                time.time(),
            )
            if need_extra_args:
                Event.NEED_EXTRA_ARGS[event_name] = need_extra_args

            async def wrapper(event: Event):
                result = await function(event)
                event.finish()
                return result

            Event.FUNCTIONS_DICT[event_name] = wrapper

        return decorator

    def finish(self):
        event_name = Event.GOT_ARG.get(self.user_id, {}).get(self.group_id)
        if not event_name:
            return
        del Event.GOT_ARG[self.user_id][self.group_id]
        del Event.FUNCTIONS_DICT[event_name[0]]

    async def avatar(self) -> BytesIO:
        url = self.extra_args.get("avatar")
        if url:
            return await download_url(url)
        else:
            output = BytesIO()
            Image.new("RGBA", (300, 300), color="gray").save(output, format="png")
            return output

    async def image(self, x: int = 0) -> BytesIO:
        url_list = self.extra_args.get("image_list")
        if url_list and len(url_list) > x:
            return await download_url(url_list[x])
        else:
            return None

    def permission(self) -> int:
        return self.extra_args.get("permission", 0)

    def to_me(self) -> bool:
        return self.extra_args.get("to_me", False)

    def at(self) -> list:
        return self.extra_args.get("at")

    def is_private(self) -> bool:
        return self.group_id == "private"

    def args_parse(self):
        args = self.args
        if not args:
            raise ArgException(str(self.args))
        L = len(args)
        if L == 1:
            return args[0], 1, None
        name = args[0]
        count = args[1]
        if count.isdigit():
            count = int(count)
        elif name.isdigit():
            name, count = count, name
            count = int(count)
        else:
            count = 1
        limit = None
        if L > 2:
            try:
                limit = float(args[2])
            except:
                pass
        return name, count, limit

    def args_to_int(self, default: str = None):
        try:
            return abs(int(self.args[0]))
        except:
            if default != None:
                return default
            else:
                raise ArgException(str(self.args))

    def single_arg(self, default: str = None):
        if not self.args:
            if default != None:
                return default
            else:
                raise ArgException(str(self.args))
        else:
            return self.args[0]


async def build_event(data: PreEventData, Adapters: dict, bot, event) -> Event:
    """
    解析预处理数据，创建事件实例
    """
    event_name, raw_command, args, user_id, group_id, need_extra_args = data
    extra_args = (
        {k: await Adapters[k](bot, event) for k in need_extra_args}
        if need_extra_args
        else {}
    )
    return Event(
        event_name,
        raw_command,
        args,
        user_id,
        group_id,
        await Adapters["nickname"](bot, event),
        extra_args,
    )


async def run(data: PreEventData, Adapters: dict, bot, event):
    """
    执行事件，返回事件结果
    """
    try:
        result = await (await build_event(data, Adapters, bot, event)).run()
    except SupArgsException as e:
        result = await e.function(
            **{k: await Adapters[k](bot, event, v) for k, v in e.data.items()}
        )
    return result


def reg_command(event_name: str, commands: Set[str], need_extra_args: set = None):
    """
    注册指令事件
        event_name:事件名
        commands:事件指令
        function:事件处理函数
    """

    def decorator(function: Callable):
        if event_name in Event.EVENTS_DICT:
            raise RegEventException(f"事件名{event_name}已被注册", event_name)
        for command in commands:
            Event.COMMANDS_DICT.setdefault(command, set()).add(event_name)
            Event.FUNCTIONS_DICT[event_name] = function
        Event.EVENTS_DICT[event_name] = commands
        if need_extra_args:
            Event.NEED_EXTRA_ARGS[event_name] = need_extra_args

    return decorator


def reg_regex(event_name: str, regex: str, need_extra_args: dict = {}):
    """
    注册正则指令事件
        event_name:事件名
        regex:事件正则指令
        function:事件处理函数
    """

    def decorator(function: Callable):
        if event_name in Event.EVENTS_DICT:
            raise RegEventException(f"事件名{event_name}已被注册", event_name)
        pattern = re.compile(regex)
        Event.REGEX_DICT.setdefault(pattern, set()).add(event_name)
        Event.FUNCTIONS_DICT[event_name] = function
        Event.EVENTS_DICT[event_name] = [pattern]
        if need_extra_args:
            Event.NEED_EXTRA_ARGS[event_name] = need_extra_args

    return decorator


def reg_auto_event(
    event_name: str, commands: Union[Set[str], str], need_extra_args: dict = {}
):
    """
    自动注册事件
    """
    if isinstance(commands, set):
        return reg_command(event_name, commands, need_extra_args)
    else:
        return reg_regex(event_name, commands, need_extra_args)


def reg_off(event_name: str):
    """
    注销事件
    """
    commands = Event.EVENTS_DICT.get(event_name)
    if not commands:
        raise RegEventException(f"不存在{event_name}", event_name)
    if isinstance(command, set):
        DICT = Event.COMMANDS_DICT
    else:
        DICT = Event.REGEX_DICT
        commands = {commands}
    for command in commands:
        DICT[command].discard(event_name)
    if event_name in Event.NEED_EXTRA_ARGS:
        del Event.NEED_EXTRA_ARGS[event_name]
    del Event.EVENTS_DICT[event_name]
    DICT = {k: v for k, v in DICT if v}
