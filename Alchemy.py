from collections import Counter
import random
from .data import UserDict

class Alchemy:
    elements  = ["1","2","3","4"]
    ProductsLibrary = {
        "1":"1",
        "2":"2",
        "3":"3",
        "4":"4",
        "12":"5",
        "21":"5",
        "13":"6",
        "31":"6",
        "14":"7",
        "41":"7",
        "23":"8",
        "32":"8",
        "24":"9",
        "42":"9",
        "34":"0",
        "43":"0",
        }
    ProductsName = {
        "":"以太",
        "1":"水",
        "2":"火",
        "3":"土",
        "4":"风",
        "5":"蒸汽",
        "6":"沼泽",
        "7":"寒冰",
        "8":"岩浆",
        "9":"雷电",
        "0":"尘埃"
        }
    ProductsCode = {v:k for k,v in ProductsName.items()}

    @classmethod
    def do(cls,N:int):
        """
        炼金
        """
        result = Counter()
        for _ in range(N):
            product = cls.ProductsLibrary.get("".join(list(set(random.choices(cls.elements,k = 3)))),"")
            result[product] += 1
        return result

    @classmethod
    def random_products(cls,N:int):
        """
        随机N几个元素
        """
        result = Counter()
        for _ in range(N):
            result[cls.ProductsLibrary["".join(random.sample(cls.elements,k = 2))]] += 1
        return result

    @classmethod
    def status(cls,status:dict):
        """
        元素状态
        """
        result = Counter()
        for product,N in status.items():
            result += {k:v*N for k,v in cls.ProductsProperties[product].items()}
        return result

def refine(user:UserDict, products:list):
    """
    元素精炼
    """
    code_dict = {}
    alchemy = user.alchemy
    msg = "精炼成功！你消耗了："
    sumn = 0
    for product in products:
        if (code := Alchemy.ProductsCode.get(product)) and (n := alchemy.get(code)):
            code_dict[code] = n
            alchemy[code] = 0
            msg += f"\n{product}：{n}个"
            sumn += n
    if not code_dict:
        return "精炼失败。你没有指定的元素。"
    props = user.props
    props["33101"] = sumn + props.get("33101",0)
    return msg