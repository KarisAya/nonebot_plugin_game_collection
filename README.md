<p align="center">
  <a href="https://v2.nonebot.dev/"><img src="https://v2.nonebot.dev/logo.png" width="200" height="200" alt="nonebot"></a>
</p>
<div align="center">

# nonebot_plugin_game_collection

改自 [nonebot_plugin_russian](https://github.com/HibiKier/nonebot_plugin_russian) 合并了 [nonebot_plugin_horserace](https://github.com/shinianj/nonebot_plugin_horserace) 还有一些自编玩法的小游戏合集。

</div>

## 需要安装

[nonebot_plugin_imageutils](https://github.com/noneplugin/nonebot-plugin-imageutils) PIL工具插件，方便图片操作，支持文字转图片

[nonebot_plugin_apscheduler](https://github.com/nonebot/plugin-apscheduler) APScheduler 定时任务插件

matplotlib 数据可视化

mplfinance K线图

## 安装

__方法1（推荐）__

    pip install nonebot_plugin_game_collection
    
__方法2__

    git clone https://github.com/KarisAya/nonebot_plugin_game_collection.git

## 使用
    nonebot.load_plugin('nonebot_plugin_game_collection')
    
如果之前运行过[nonebot_plugin_russian](https://github.com/HibiKier/nonebot_plugin_russian)那么需要把之前的数据删掉，不然会报错。。。

__1.4.0 版本 需要安装 matplotlib 和 mplfinance 不然无法运行__

## 配置

    # russain
    RUSSIAN_PATH = ''                     # 数据存储路径，默认路径是此插件目录下
    MAX_BET_GOLD = 2000                   # 赌注的最大上限（防止直接梭哈白给天台见）
    RACE_BET_GOLD = 100                   # 赛马门票
    GACHA_GOLD = 500                      # 十连抽卡需要的金币
    SIGN_GOLD = [100, 300]                # 每日签到可得到的金币范围
    REVOLT_SIGN_GOLD = [800, 1200]        # 重置签到可得到的金币范围
    SECURITY_GOLD = [50, 200]             # 每日补贴可得到的金币范围
    
    MARKET_INFO_CHAIN = TRUE              # 市场信息群聊转发开关 TRUE是开启转发模式，FALSE是关闭转发模式。
    MARKET_INFO_TYPE = "text"             # 市场信息发送形式 "image" 以图片形式发送 "text" 以文字形式发送。

## 功能介绍

里面的所有游戏都需要使用金币作为赌注！
注：同一时间群内只能有一场对决

### 获取金币

    金币签到 # 0点刷新
    重置签到 # 重置后可领取一次
    
__金币签到__

玩家每日可签到一次，每日0点刷新。

__重置签到__

当金币排行榜第一名的金币超过第二名到第十名的总和，可以发起重置。

    发起重置 # 重置效果是前十名的金币数减少80%，群内玩家可以重置签到一次，第一名进入路灯挂件榜。
    

__每日补贴__

玩家输光所有金币后会触发每日补贴，每日三次，0点刷新。

### 个人账户

    我的金币    # 查看自己的金币数量
    我的仓库    # 查看自己获得的的道具
    我的资料卡  # 查看个人账户详细资料
    发红包/打钱 [金额] [at]  # 给at的用户发金币
    金币转移 [公司名] [金额] # 跨群转移金币到自己的账户
    
### 十连抽卡（道具更新中。。。）

    @bot十连/   # 也可以bot昵称十连  

### 排行榜

    金币排行/胜场排行/败场排行/欧洲人排行/慈善家排行/查看路灯挂件

### 俄罗斯轮盘

赌注上限为一倍赌注上限

通过 装弹 来对其他人发起决斗，轮流开枪，直到运气不好的人先去世。

    【开始游戏】：装弹 [子弹数] [金额] [at]（为空则所有群友都可接受）
    【回应】：接受对决/接受挑战/拒绝决斗/拒绝挑战
    【回合中】：开枪/咔/嘭/嘣 [子弹数]（默认1)（轮流开枪）
    【结算】：结算 （当某一方60秒未开枪，可使用该命令结束对决并胜利）

__俄罗斯轮盘特殊技能：开枪0__

### 掷骰子

赌注上限为五倍赌注上限

通过 掷骰子 来对其他人发起决斗，轮流开数比大小，中途可结束。

    【开始游戏】：摇骰子/掷色子 [金额] [at]（为空则所有群友都可接受）
    【回应】：接受对决/接受挑战/拒绝决斗/拒绝挑战
    【回合中】：开数/开点/取出（轮流开数）
    【结束】：结束（只有暂败方可发起）
    【结算】：结算（当某一方60秒没有回应，以目前比分结算）

__规则__

轮流开数，先比组合，再比点数。

组合：役满（5个相同） > 串（4个相同） > 条（3个相同） > 两对（2组2个相同） > 对（2个相同） > 散（全不相同） 

~~别问为什么役满，雀魂真好玩~~

### 扑克对战

赌注上限为一倍赌注上限

通过 扑克对战 来对其他人对战，打出自己的手牌。当对方的血量小于1或者在自己回合出牌前血量>40即可获胜。

牌库一共52张牌，当牌库没有牌了就以目前血量结算，结束游戏。

    【开始游戏】：扑克对战 [金额] [at]（为空则所有群友都可接受）
    【回应】：接受对决/接受挑战/拒绝决斗/拒绝挑战
    【回合中】：出牌 1/2/3（轮流出牌）
    【结算】：结算（当某一方60秒没有回应，以目前血量结算）
    
__规则__

先手初始点数：HP 20 SP 0 DEF 0

后手初始点数：HP 25 SP 2 DEF 0

每回合抽三张牌，打出其中的一张作为行动牌，弃掉剩余手牌。__特别注意：防御牌作为行动牌是攻击__

之后对方摇一个20面骰子，如果点数小于对方SP则从牌库翻出一张牌作为技能牌打出，按照技能牌点数扣除对方SP点。

| 花色 | 描述 | 行动牌效果 | 技能牌效果 |
| --- | --- | --- | --- |
| 黑桃 | 防御 | 打出攻击 | 增加DEF |
| 红桃 | 生命 | 恢复HP | 恢复HP |
| 梅花 | 技能 | 主动技能 | 增加SP |
| 方片 | 攻击 | 打出攻击 | 打出反击 |

主动技能：摇一个20面骰子，如果点数小于自身SP则把剩余两张手牌作为技能牌全部打出，按照技能牌点数扣除自身SP点

ACE技能：摇一个6面骰子，把打出的ACE牌点替换成摇出的点数，再把三张手牌全部作为技能牌打出，按照技能牌点数扣除自身SP点

### 赛马小游戏

~~抄~~改自 [nonebot_plugin_horserace](https://github.com/shinianj/nonebot_plugin_horserace) 

~~发言复刻~~ 请不要在使用此插件时出现报错去找原作者（冲我来，发issue，我已经准备好赴死了）

    赛马创建  # 第一位玩家发起活动
    赛马加入 [你的马儿名称]  # 赛马加入
    赛马开始  # 开始指令
    赛马重置  # 赛马超时重置
    
    管理员指令：
    赛马清空  # 清空马场
    赛马事件重载 # 重新加载赛马事件
    
 __自定义事件包方式__
 
事件包为utf-8编码（不懂的话就别瞎整了）

详细信息请参考：

[事件添加相关.txt](https://github.com/shinianj/nonebot_plugin_horserace/blob/main/%E4%BA%8B%E4%BB%B6%E6%B7%BB%E5%8A%A0%E7%9B%B8%E5%85%B3.txt)

[事件详细模板.txt](https://github.com/shinianj/nonebot_plugin_horserace/blob/main/%E4%BA%8B%E4%BB%B6%E8%AF%A6%E7%BB%86%E6%A8%A1%E6%9D%BF.txt)

写完的json文件放入events/horserace文件夹中就能跑了（除非你写错了，在加载事件时会失败，但不会影响其他事件加载也不会让你的bot崩了）

### 市场经营

1. 当群内的金币数量总和到达20000时 [群主，管理员，超管] 可以使用 ___市场注册__ 把此群号注册到市场。

2. 大量 __发行购买__ 某公司股票会使该公司股价明显上涨。同样，大量 __官方结算__ 某公司股票会使该公司股价明显下跌。

3. __出售__ 指令在本群是覆盖的，比如你在本群账户上有1000股文文日报社，你连续使用如下指令 `出售 文文日报社 0.8 900` `出售 文文日报社 3 100` 最后的结果是你以每股 3 金币的价格在市场上发布了100股（之前以每股 0.8 金币的价格在市场上发布了900股的信息被覆盖了）

4. 不可以买自己上架的股票（跨群也不可以），如果想从交易市场下架可以使用 __出售__ 指令。例如 `出售 文文日报社 3 0`（发布0股）

5. 若要跨群转金币可以使用 __金币转移__ 指令。转移目的地群需要已注册公司，而且转移人在该群创建过账户（签到，收红包，玩游戏等功能会自动创建账户）

6. 玩家在市场上某公司的股票交易未完成时（发布了没人买）不可以使用 __官方结算__ 指令。如果想要结算可以使用 __出售__ 指令把发布数改为0。例如 `出售 文文日报社 0 0`

具体指令如下

    【市场信息/查看市场】   # 查看市场上所有公司的官方结算价格。
    【市场信息/查看市场 [公司名称]】  # 查看市场上出售 [公司名称] 股份的报价。
    【市场行情】  # 查看市场行情。
    【公司信息/公司资料 [公司名称]】  # 查看公司的详细信息
    【发行购买 [公司名称] [N]】 # 以发行价格从 [公司名称] 购买 [N] 股本公司股份。
    【官方结算 [公司名称] [N]】 # 以结算价格向 [公司名称] 卖出 [N] 股本公司股份。
    【购买/买入 [公司名称] [N]】  # 以从低到高的报价买入 [N] 股市场中的 [公司名称] 。
    【出售/卖出 [公司名称] [报价] [N]】 # 将自己手中的 [公司名称] 以 [报价] 发布到市场 [N] 股。
    
管理员、群主、超管

    【市场注册/公司注册 [公司名称] @bot】 # 将本群以 [公司名称] 注册到市场，如果全群金币数小于两万则会注册失败。
    【更新公司简介 [简介内容]】 # 将 [简介内容] 添加到本群公司资料的简介中
    
超管

    【管理员更新公司简介 [公司名称] [简介内容]】 # 将 [简介内容] 添加 [公司名称] 资料的简介中


__注：注册好的公司名称不可修改__ 

其实去 ./data/russian 文件夹用查找和替换功能修改3个json文件也可以实现公司改名就是了。

~~至于为什么没有做在插件里完全是因为懒。。~~

## 其他

如有建议，bug反馈，以及讨论新玩法，新机制（或者单纯没有明白怎么用）可以来加群哦~

![群号](https://github.com/KarisAya/nonebot_plugin_game_collection/blob/master/%E9%99%84%E4%BB%B6/QQ%E5%9B%BE%E7%89%8720220826221034.jpg)

当然也可以发issue...

但是群里回的快！！（疯狂暗示）
