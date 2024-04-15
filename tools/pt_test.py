import random
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

prop_pool = {}
prop_pool[3] = ["0", "四叶草标记", "挑战徽章", "设置许可证", "初级元素"]
prop_pool[4] = ["0", "铂金会员卡"]
prop_pool[5] = [
    "0",
    "0",
    "10%结算补贴",
    "10%额外奖励",
    "神秘天平",
    "幸运硬币",
]
prop_pool[6] = ["0", "钻石", "道具兑换券", "超级幸运硬币", "重开券"]


def gacha() -> str:
    """
    随机获取道具。
        return: object_code
    """
    rand = random.uniform(0.0, 1.0)
    prob_list = [0.3, 0.1, 0.1, 0.02]
    rare = 3
    for prob in prob_list:
        rand -= prob
        if rand <= 0:
            break
        rare += 1
    if rare_pool := prop_pool.get(rare):
        return 0 if random.choice(rare_pool) == "0" else rare
    return 0


percentiles = [1, 10, 25, 75, 90, 99]

# # 经过拟合发现100次抽卡很适合作为常值
# array = []
# for _ in range(10000):
#     array.append(sum(gacha() for _ in range(100)) / 100)
# print([np.percentile(array, percentile) for percentile in percentiles])
# exit()
input_data = []
output_data = []
for i in range(10, 201, 5):
    array = []
    for _ in range(10000):
        array.append(sum(gacha() for _ in range(i)) / i)
    input_data.append(i)
    output_data.append([np.percentile(array, percentile) for percentile in percentiles])


def func(x, a, b, c, d):
    return a * np.log(b * x) + c * x + d


# 生成拟合曲线的 x 值
x_fit = np.linspace(10, 200, 100)
for i in range(len(percentiles)):
    output_data2 = [j[i] for j in output_data]
    popt, pcov = curve_fit(func, input_data, output_data2)
    a, b, c, d = popt
    print(f"lambda x:{a} * np.log({b} * x) + {c} * x + {d}")
    # 计算拟合曲线的 y 值
    y_fit = func(x_fit, *popt)
    # 绘制原始数据和拟合曲线
    plt.scatter(input_data, output_data2, label="这是中文")
    plt.plot(x_fit, y_fit)

plt.xlabel("input")
plt.ylabel("output")
plt.legend()
plt.show()
