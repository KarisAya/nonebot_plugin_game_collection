class GameOverException(Exception):
    """
    用于游戏结束，直接跳到输出结果
    """
    def __init__(self, result):
        super().__init__()
        self.result = result
        
class RegEventException(Exception):
    """
    用于处理注册事件时的异常情况
    """

    def __init__(self, message:str, event_name:str):
        super().__init__(message)
        self.event_name = event_name

class ArgException(Exception):
    """
    参数解析错误
    """

    def __init__(self, message:str):
        super().__init__(message)

class SupArgsException(Exception):
    """
    补传参数
        args_name:字典：参数名:获取参数的参数
        function:
    """
    def __init__(self,data,function):
        super().__init__()
        self.data:dict = data
        self.function = function