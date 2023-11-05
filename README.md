<!-- markdownlint-disable MD031 MD033 MD036 MD041 -->

<div align="center">

<a href="https://v2.nonebot.dev/store">
  <img src="https://raw.githubusercontent.com/A-kirami/nonebot-plugin-template/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo">
</a>

<p>
  <img src="https://raw.githubusercontent.com/A-kirami/nonebot-plugin-template/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText">
</p>

# nonebot-plugin-game-collection

_✨ 改自 [nonebot_plugin_russian](https://github.com/HibiKier/nonebot_plugin_russian) 和 [nonebot_plugin_horserace](https://github.com/shinianj/nonebot_plugin_horserace) 的小游戏合集 ✨_

<img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">
<a href="./LICENSE">
  <img src="https://img.shields.io/github/license/KarisAya/nonebot_plugin_game_collection.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot_plugin_game_collection">
  <img src="https://img.shields.io/pypi/v/nonebot_plugin_game_collection.svg" alt="pypi">
</a>
<a href="https://pypi.python.org/pypi/nonebot_plugin_game_collection">
  <img src="https://img.shields.io/pypi/dm/nonebot_plugin_game_collection" alt="pypi download">
</a>

</div>

## 💿 安装

以下提到的方法 任选**其一** 即可

<details open>
<summary>[推荐] 使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

```bash
nb plugin install nonebot_plugin_game_collection
```

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

```bash
pip install nonebot_plugin_game_collection
```

</details>
<details>
<summary>pdm</summary>

```bash
pdm add nonebot_plugin_game_collection
```

</details>
<details>
<summary>poetry</summary>

```bash
poetry add nonebot_plugin_game_collection
```

</details>
<details>
<summary>conda</summary>

```bash
conda install nonebot_plugin_game_collection
```

</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分的 `plugins` 项里追加写入

```toml
[tool.nonebot]
plugins = [
    # ...
    "nonebot_plugin_game_collection"
]
```

</details>

## ⚙️ 配置

在 NoneBot2 项目的 `.env` 文件中按需添加下面的配置项

```properties
# 每日签到的范围
sign_gold = [200, 500]

# 每日补贴的范围
security_gold = [100, 300]

# 重置签到的范围
revolt_gold = [1000, 2000]

# 重置冷却时间，设置为0禁用发起重置
revolt_cd = 28800

# 重置的基尼系数
revolt_gini = 0.68

# 最大赌注
max_bet_gold = 2000

# 默认赌注
bet_gold = 200

# 单抽所需金币
gacha_gold = 50

# 一个测试字符串，不要动（
lucky_clover = "• ＬＵＣＫＹ  ＣＬＯＶＥＲ •"

# 默认显示字体
game_fontname = "simsun"

# 默认备用字体
game_fallback_fonts = [
    "Arial",
    "Tahoma",
    "Microsoft YaHei",
    "Segoe UI",
    "Segoe UI Emoji",
    "Segoe UI Symbol",
    "Helvetica Neue",
    "PingFang SC",
    "Hiragino Sans GB",
    "Source Han Sans SC",
    "Noto Sans SC",
    "Noto Sans CJK JP",
    "WenQuanYi Micro Hei",
    "Apple Color Emoji",
    "Noto Color Emoji",
    ]

# 跑道长度
setting_track_length = 20

# 随机位置事件，最小能到的跑道距离
setting_random_min_length = 0

# 随机位置事件，最大能到的跑道距离
setting_random_max_length = 15

# 每回合基础移动力最小值
base_move_min = 1

# 每回合基础移动力最大值
base_move_max = 3

# 最大支持玩家数
max_player = 8

# 最少玩家数
min_player = 2

# 事件概率 = event_rate / 1000
event_rate = 450

```

**默认资料卡背景**

首次运行本插件之后，会出现 `/data/russian/BG_image/` 这个路径。

插件生成了一个非常 defaul 的 default.png，如果不配置的话，所有人的资料卡背景图片就是这张图了。

随便拖进去一张图片命名为 default.png，这张图就会作为默认资料卡背景。

改图片的时候不用关 bot 也会生效

## 🎉 使用

里面的所有游戏都需要使用金币作为赌注！
注：同一时间群内只能有一场对决

<details>
  
<summary>管理员指令</summary>

`获取金币 数量`

获取金币

`获取道具 道具名 数量`

获取道具

`刷新每日`

刷新每日签到，补贴，金币转移上限，所有人时效道具的剩余时间-1

`保存数据`

在关 bot 前需要保存数据，不然会回档到上次自动保存的时间点

`数据备份`

备份游戏数据文件

`市场重置`

把市场重置为回归值

`数据验证`

修复存档数据

</details>

<details>
  
<summary>获取金币</summary>
    
`金币签到`

玩家每日可签到一次，每日 0 点刷新。

`重置签到`

每次重置后可领取一次，当群内的基尼系数大于设定值可发起重置，重置后可进行一次重置签到。

每日刷新有几率刷新重置签到。

`发起重置`

按比例清空前十名的金币，第一名进入路灯挂件榜。公司等级+1（最高 10 级）。

**每日补贴(不是指令)**

玩家输光所有金币后会触发每日补贴，每日三次，0 点刷新。

`查看元素订单`

如果本群注册了公司，那么每日会刷新一些元素订单，订单数量和公司等级相关。

完成相应的订单可以获得金币。

`完成元素订单 编号`

例如 `完成元素订单 1`

每个元素订单需要随机 10 个元素。元素来源于初级元素炼金。

详细查看[炼金系统](#1)

</details>

<details>
  
<summary>个人账户</summary>

`我的金币`

查看自己的金币数量

`我的道具`

查看自己获得的的道具

`我的股票`

查看自己在本群的股票以及报价

`我的资料卡`

查看个人账户详细资料

`炼金资料卡`

查看个人炼金资料

`设置背景图片[图片]` `设置背景图片(回复一张图片)`

设置我的资料卡显示的背景图片，需要有指定道具。

`删除背景图片`

将资料卡显示的背景图片设置为默认

</details>

<details>

<summary>群金库</summary>

本群的手续费，以及元素订单等都可以使本群金库的金币数增加。

用户也可以向群金库捐款，本群管理员以上权限可以使用群金库里的金币。

`存金币 数量`

向群金库里面存入相应数量的金币。

`取金币 数量`

从群金库里面取出相应数量的金币，需要管理员以上权限。

</details>

<details>
  
<summary>资产管理</summary>

`发红包 金额 at`

给 at 的用户发金币

`送道具 道具名 道具数量 at`

给 at 的用户送指定数量的道具（可以不填道具数量，默认为 1）。可以送路灯挂件牌，道具名：路灯挂件标记。

`金币转移 公司名 金额`

跨群转移金币到自己的账户，每日总转出/转入不能超过本群以及目标公司的 10%

</details>

<details>
  
<summary>道具系统</summary>

`@bot十连抽卡` `@bot100连抽`

抽取道具，在私聊抽卡不用 at。

`使用道具 道具名 参数`

部分道具可使用，可以用此指令使用道具。参数一般是使用数量，也有其他效果。

道具有全局道具，群内道具，永久道具，时效道具。

群内道具最多叠 30 天/个

[道具效果](https://github.com/KarisAya/nonebot_plugin_game_collection/blob/master/resource/props_library.json)

**四叶草标记**

_群内道具,时效道具_

_可以在资料卡上显示四叶草标记，但似乎并没有什么用处。_

**挑战徽章**

_群内道具,时效道具_

_可以发起随机对战，随机游戏，随机赌注。无视赌注上限。_

**设置许可证**

_全局道具,时效道具_

_可以设置背景图片，修改公司名称。_

**初级元素**

_全局道具,永久道具_

_打开可以获得随机 3 个基本元素。_

**钻石会员卡**

_群内道具,时效道具_

_可以在转账，结算等场合免除手续费。_

**10%结算补贴**

_群内道具,时效道具_

_在对局中失败时减少 10%的损失。_

**10%额外奖励**

_群内道具,时效道具_

_在对局中胜利时额外获得 10%的金币。_

**神秘天平**

_群内道具,永久道具_

_与随机一个人平分金币。获得或失去金币的数量不超过两个人金币的最小值_

**幸运硬币**

_群内道具,永久道具_

_有 50%的概率获得一半金币，50%的概率失去一半金币。每次金币获得或失去的上限为 Lv.50 金库。_

_可使用参数 2_`使用道具 幸运硬币 2`_消耗一颗钻石，把成功概率提升至 2/3_

_可使用参数 3_`使用道具 幸运硬币 3`_消耗一颗钻石，使获得金币数翻倍，如失败则不生效。_

**随机红包**

_群内道具,永久道具_

_打开后可以获得【金币签到-重置签到】范围的随机金币。_

**钻石**

_群内道具,永久道具_

_没用_

**道具兑换券**

_群内道具,永久道具_

_兑换任意一个非特殊道具，使用此道具不需要持有本道具。_

_使用道具时，优先扣除道具库存，超出库存的数量用金币补充，每个 50 次抽卡所需金币。_

_使用方法：_

_`使用道具 道具兑换券 超级幸运硬币` 兑换一个超级幸运硬币_

_`使用道具 道具兑换券 10 超级幸运硬币` 兑换 10 个超级幸运硬币_

_`使用道具 道具兑换券 10` 兑换 10 个道具兑换券(一般用来购买本道具)_

**超级幸运硬币**

_全局道具,永久道具_

_有 50%的概率金币翻倍，50%的概率金币清零。没有上限_

**重开券**

_全局道具,永久道具_

_重置自己的本群账户_

**路灯挂件标记**

_群内道具,永久道具_

_可以在资料卡上显示路灯挂件标记_

**测试金库**

_全局道具,永久道具_

_没用_

**被冻结的资产**

_全局道具,永久道具_

_获得价值为 Lv.1 金库 的金币，在高级公司使用会被汇率影响。_

**空气礼包**

_全局道具,永久道具_

_可以获得 10 个随机空气！与抽卡不同的是这样获得的空气可以精炼_

</details>

<details>

<summary>新建道具</summary>

`新建道具@bot`

然后根据提示输入可以创建新道具，只有超管有权限使用此指令。

`删除道具 道具名`

可以删除新建的道具，游戏自带道具无法删除。

</details>

<details>
  
<summary>群内排行</summary>

`总金币排行`

查看本群玩家的跨群所有金币数量的排行

`总资产排行`

查看本群玩家的跨群所有金币和股票总价值的排行

`金币排行`

查看本群玩家在本群的金币排行

`资产排行` `财富排行`

查看本群玩家在本群的金币和股票总价值的排行

`胜率排行`

查看本群玩家的胜率排行

`胜场排行`

查看本群玩家的胜利场次数排行

`败场排行`

查看本群玩家的失败场次数排行

`路灯挂件排行`

查看本群玩家被挂路灯次数排行

</details>

<details>

<summary>总排行</summary>

`金币总排行`

查看所有玩家在本群的金币排行

`资产总排行`

查看所有玩家在本群的金币和股票总价值的排行

`胜率总排行`

查看所有玩家的胜率排行

`胜场总排行`

查看所有玩家的胜利场次数排行

`败场总排行`

查看所有玩家的失败场次数排行

`路灯挂件总排行`

查看所有玩家被挂路灯次数排行

</details>

<details>

<summary>开始游戏</summary>

所有游戏都可以通过下方的指令发起

发起游戏的指令中除了第一个字段剩下的都可以忽略

`子弹数` 忽略为 1

`金额` 忽略为默认赌注

`at` 忽略为全体成员可接受

游戏可以使用如下指令处理

`接受挑战`

`拒绝挑战`

`认输`

`超时结算` （60 秒）

`游戏重置` （需要游戏对局超时）

  <details>

  <summary>随机对战</summary>

`随机对战 金额  at`

无视赌注上限

通过 随机对战 来对其他人发起决斗，随机游戏，随机赌注。

发起随机对战的玩家必须持有挑战徽章（可抽卡获得）

  </details>

  <details>

  <summary>俄罗斯轮盘</summary>

**发起**

`装弹 子弹数 金额 at `

**进行**

`(开枪|咔|嘭|嘣) N（可忽略)`

**规则**

赌注上限为 1 倍赌注上限

通过 装弹 来对其他人发起决斗，轮流开枪，直到运气不好的人先去世。

  </details>

  <details>

  <summary>掷骰子</summary>

**发起**

`(掷色子|摇骰子) 金额 at`

**进行**

`开数` `开点` `取出`

**规则**

赌注上限为 1 倍赌注上限每轮

通过 掷骰子 来对其他人发起决斗，轮流开数比大小，每次开数都会让结算金额上涨，中途结束按照当前金额结算。

轮流开数，先比组合，再比点数。

组合：役满（5 个相同） > 串（4 个相同） > 条（3 个相同） > 两对（2 组 2 个相同） > 对（2 个相同） > 散（全不相同）

~~别问为什么役满，雀魂真好玩~~

  </details>

  <details>

  <summary>扑克对战</summary>

**发起**

`扑克对战 金额 at`

**进行**

`出牌 1/2/3`

**规则**

赌注上限为 5 倍赌注上限

通过 扑克对战 来对其他人对战，打出自己的手牌。当对方的血量小于 1 或者在自己回合出牌前血量>40 即可获胜。

牌库有两副共 104 张牌，当牌库没有牌了就以目前血量结算，结束游戏。

先手初始点数：HP 20 SP 0 DEF 0

后手初始点数：HP 25 SP 2 DEF 0

每回合抽三张牌，打出其中的一张作为行动牌，弃掉剩余手牌。**特别注意：防御牌作为行动牌是攻击**

之后对方摇一个 20 面骰子，如果点数小于对方 SP 则从牌库翻出一张牌作为技能牌打出，按照技能牌点数扣除对方 SP 点。

| 花色 | 描述 | 行动牌效果 | 技能牌效果 |
| ---- | ---- | ---------- | ---------- |
| 黑桃 | 防御 | 打出攻击   | 增加 DEF   |
| 红桃 | 生命 | 恢复 HP    | 恢复 HP    |
| 梅花 | 技能 | 主动技能   | 增加 SP    |
| 方片 | 攻击 | 打出攻击   | 打出反击   |

主动技能：摇一个 20 面骰子，如果点数小于自身 SP 则把剩余两张手牌作为技能牌全部打出，按照技能牌点数扣除自身 SP 点

ACE 技能：摇一个 6 面骰子，把打出的 ACE 牌点替换成摇出的点数，再把三张手牌全部作为技能牌打出，按照技能牌点数扣除自身 SP 点

  </details>

  <details>

  <summary>猜数字</summary>

**发起**

`猜数字 金额 at`

**进行**

`50`（1-100 的数字）

**规则**

赌注上限为每轮 1 倍赌注上限每轮

通过 猜数字 来对其他人对战，轮流猜数字，猜中数字即可获胜。

每轮赌注都会增长一倍

  </details>

  <details>

  <summary>同花顺</summary>

**发起**

`同花顺 金额 等级 at`

等级 1-5，默认为 1，和手牌的大小相关。

**进行**

`看牌`

在加注前可以查看手牌确认自己是否要加注。手牌以私聊形式发送，看牌的玩家需要添加 bot 好友

`认输`

及时止损

`加注 金额`

先手决定本轮加注最小金额，后手决定本轮金额，加注默认为初始金额。

**规则**

赌注上限为单次加注 10 倍赌注上限

通过 同花顺 来对其他人对战，先手看牌加注，后手看牌跟注，直到一方认输或点数大的获胜。

组合：同花顺 > 四条 > 葫芦 > 同花 > 顺子 > 三条 > 两对 > 一对 > 散牌

花色：黑桃 > 红桃 > 梅花 > 方片

  </details>

  <details>

  <summary>21点</summary>

**发起**

`21点 金额 at`

对战双方需要添加 bot 好友

**进行**

`抽牌`

抽一张牌

`停牌`

停止抽牌

`双倍下注`

抽一张牌并停牌，赌注翻倍。

**规则**

赌注上限为单次 5 倍赌注上限

通过 21 点 来对其他人对战，手牌点数大的获胜。

游戏中点数超过 21 会直接失败。

  </details>

  <details>

  <summary>AB牌</summary>

**发起**

`AB牌 金额 at`

对战双方需要添加 bot 好友

**进行（私聊 bot！私聊 bot！私聊 bot！）**

`A` `B` `1` `2` `3`

打出手牌

**规则**

赌注上限为每轮 1 倍赌注上限

双方手牌均为 AB123 五张牌，每轮暗牌发牌（私聊 bot），每轮结束后开牌。

双方出牌相同为平局，此外

A 为必胜牌，B 为必败牌。

1 胜 2，2 胜 3，3 胜 1

本轮胜利者+1 分

打出所有手牌后结算。分数多的胜利

每轮赌注翻倍

玩法标注：因为 B 必败所以在对方出 A 的时候混出去是最优解。总之你需要打出 AB123 全部的牌。

  </details>

  <details>

  <summary>西部对战</summary>

**发起**

`西部对战 金额 at`

对战双方需要添加 bot 好友

**进行（私聊 bot）**

`装弹` `开枪` `闪避` `闪枪` `预判开枪`

**规则**

赌注上限为 5 倍赌注上限

双方私聊 bot 本轮的行动

双方初始 1 发子弹，装弹上限为 6 发子弹（6 发可以继续装弹，但是子弹数不会再增加了）。

如果双方同时`开枪`，那么子弹会发生碰撞。本轮平局

`装弹` 在 **初始位置** 行动，剩余子弹数+1。会被 `开枪` `闪枪` 击杀

`闪避` 去 **闪避位置** ，不会消耗子弹。会被 `预判开枪` 击杀

`开枪` 在 **初始位置** 行动，打对方 **初始位置** ，剩余子弹数-1 击杀 `装弹` `预判开枪`

`闪枪` 去 **闪避位置** ，打对方 **初始位置** ，剩余子弹数-1 击杀 `装弹` `开枪`

`预判开枪` 在 **初始位置** 行动，打对方 **闪避位置** ，剩余子弹数-1 击杀 `闪避` `闪枪`

注：预判开枪不会与闪枪发生子弹碰撞，因为预判开枪速度比闪避开枪速度快。

  </details>

  <details>

  <summary>赛马小游戏</summary>

~~抄~~改自 [nonebot_plugin_horserace](https://github.com/shinianj/nonebot_plugin_horserace)

~~发言复刻~~ 请不要在使用此插件时出现报错去找原作者（冲我来，发 issue，我已经准备好赴死了）

`赛马创建 金额`

第一位玩家发起活动，金额为报名费

`赛马加入 你的马儿名称`

花费报名费，加入你的赛马

`赛马开始`

如果有足够的人加入了游戏，那么可以通过本指令开始游戏

`赛马暂停`

暂停本群的赛马，稍后可以用`赛马开始`继续游戏

**自定义事件包方式**

事件包为 utf-8 编码（不懂的话就别瞎整了）

详细信息请参考：

[事件添加相关.txt](https://github.com/shinianj/nonebot_plugin_horserace/blob/main/%E4%BA%8B%E4%BB%B6%E6%B7%BB%E5%8A%A0%E7%9B%B8%E5%85%B3.txt)

[事件详细模板.txt](https://github.com/shinianj/nonebot_plugin_horserace/blob/main/%E4%BA%8B%E4%BB%B6%E8%AF%A6%E7%BB%86%E6%A8%A1%E6%9D%BF.txt)

写完的 json 文件放入 events/horserace 文件夹中就能跑了（除非你写错了，在加载事件时会失败，但不会影响其他事件加载也不会让你的 bot 崩了）

  </details>

  <details>

  <summary>堡垒战</summary>

待补充

  </details>

</details>

<details>

<summary>市场系统</summary>

`群资料卡`

查看本群的详细信息

`市场信息 公司名`

查看指定公司的详细信息

`市场信息`

查看市场上所有公司的简略信息

`市场价格表`

查看市场上所有公司发行/结算价格

`市场注册 公司名 @bot`

权限：[群主，管理员，超管]

当群内符合条件时，可以使用 `市场注册 公司名 @bot` 把此群号注册到市场。

`公司重命名 公司名 @bot`

权限：[群主，管理员，超管]

修改本公司在市场上的注册名称

`更新公司简介 简介内容`

将`简介内容`添加到本群详细信息的简介中。

`购买 公司名 数量 最高单价`

<details>

<summary>购买指定公司的股票</summary>

公司名和数量必须指定。

购买公司的股票时你的金币会同时补充为公司的资产。

所以大量`购买`某公司股票会使该公司股价明显上涨。同样，大量`结算`某公司股票会使该公司股价明显下跌。

`最高单价`为购买时限制的最高单价

例：

假如文文日报社 10 金币 1 股。

发送指令 `购买 文文日报社 2000` 购买 2000 股该公司股票。

假设购买之后，文文日报社上涨到 15 金币 1 股。

如果发送指令 `购买 文文日报社 2000 12`

那么购买的股票数可能会小于 2000 股，因为`最高单价`参数在 文文日报社 股价为 12 金币时停止继续购买。

</details>

`结算 公司名 数量 最低单价`

<details>

<summary>结算指定公司的股票</summary>

公司名和数量必须指定。

结算公司的股票时公司的金币会同时减少。

所以大量`结算`某公司股票会使该公司股价明显下跌。

`最低单价`为结算时限制的最低单价

例：

假如文文日报社 15 金币 1 股

发送指令 `结算 文文日报社 2000` 结算 2000 股该公司股票

假设结算之后，文文日报社下跌到 10 金币 1 股

如果发送指令 `结算 文文日报社 2000 12`

那么结算的股票数可能会小于 2000 股，因为`最低单价`参数在 文文日报社 股价为 12 金币时停止继续结算。

</details>

`出售 公司名称 报价 数量`

将指定公司的股票以`报价`发布到交易市场`数量`股。

当公司的股价上涨到高于报价时，你发布的股票会自动以报价结算。

`市场购买 公司名称 数量`

从交易市场上以从低到高的报价买入`数量`股将指定公司的股票。

</details>

<details>

<summary>市场监管</summary>

权限：[超管]

`冻结资产@someone`

查封 at 的群友的全部资产。

由于游戏市场机制过于简单导致运营时间长了以后会出现金币数量离谱的玩家

如果金币持有量过于离谱，可以使用`冻结资产`查封。

查封后的用户会持有最多 500 个全局道具【被冻结的资产】，此道具可以在任意群使用，每个【被冻结的资产】使用后会在使用的群获得一倍赌注上限的金币。

上述机制【被冻结的资产】的数量与被冻结前相关。

`清理无效账户@bot`

删除 bot 不在的群，退群的用户等无效账户。

`管理员更新公司简介 公司名 简介内容`

将`简介内容`添加到指定公司详细信息的简介中。

</details>

<details>

<summary>私聊关联群聊账户</summary>

可以在私聊签到、抽卡、使用道具、查看我的金币/道具/资料卡、查看排行，购买或结算股票，以及进行游戏等操作。

不过你直接去的话大概会提示关未联群聊账户（

连接账户的方法

1. 在群里发送`@bot关联账户`私聊账户就会关联到本群里
2. 私聊发送`关联账户`再根据提示输入群号私聊账户就会关联到群号所指的群
3. 进行游戏时账户会连接到游戏正在进行的群。

**如果你正在一场游戏中,然后把账户关联到别的群了，那么你会找不到对局。**

**请不要在游戏中修改关联的账户，如果不慎修改还想继续本场对局的话，那么请关联到对局所在的群。**

**请不要同时在多个群进行游戏，如果非要在多个群进行游戏，那么请注意发送游戏进行的指令之前账户是否关联到了对局所在的群。**

</details>

<p id="1"></p>

<details>

<summary>炼金系统</summary>

基本元素：水 火 土 风

纯净产物：水元素 火元素 土元素 风元素

实体产物：蒸汽 沼泽 寒冰 岩浆 雷电 尘埃

每个初级元素道具可以生成 3 个基本元素。

三个元素相同时会获得纯净产物。

两个元素相同时会获得实体产物。

三个元素不相同时会产生以太，无法收集。

`元素精炼 元素产物名`

消耗全部指定的元素产物（纯净产物/实体产物），获得相同数量的初级元素。

可以指定多个元素产物，如`元素精炼 蒸汽 沼泽 寒冰 岩浆 雷电 尘埃`

`道具精炼 道具名 数量`

消耗道具，获得初级元素，获得的初级元素数量和道具星级相关。

</details>

## 📞 联系

如有建议，bug 反馈，以及讨论新玩法，新机制（或者单纯没有明白怎么用）可以来加群哦~

机器人 bug 研究中心（闲聊群） 744751179

永恒之城（测试群） 724024810

![群号](https://github.com/KarisAya/nonebot_plugin_game_collection/blob/master/%E9%99%84%E4%BB%B6/qrcode_1676538742221.jpg)

## 💡 鸣谢

- [nonebot_plugin_russian](https://github.com/HibiKier/nonebot_plugin_russian) 轮盘小游戏
- [nonebot_plugin_horserace](https://github.com/shinianj/nonebot_plugin_horserace) 赛马小游戏
- [nonebot_plugin_apscheduler](https://github.com/nonebot/plugin-apscheduler) APScheduler 定时任务插件

- fonttools 字体相关的操作
- matplotlib 数据可视化
- mplfinance K 线图
- seaborn 数据可视化拓展

## ⚠ 注意

**注意：本插件与[nonebot_plugin_russian](https://github.com/HibiKier/nonebot_plugin_russian)不兼容！如果之前运行过此插件那么需要把之前的数据删掉。**

**注意：2.1+版本与 2.0 版本数据不兼容**

如果想恢复数据请参考 data.data 定义的数据结构从旧数据自行迁移
