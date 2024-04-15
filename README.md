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

<img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="python">
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

## 小游戏使用文档

[clovers_leafgame](https://github.com/KarisAya/clovers_leafgame)

## ⚠ 注意

**注意：本插件与[nonebot_plugin_russian](https://github.com/HibiKier/nonebot_plugin_russian)不兼容！如果之前运行过此插件那么需要把之前的数据删掉。**

**注意：2.1+版本与 2.0 版本数据不兼容,如果想恢复数据请参考 data.data 定义的数据结构从旧数据自行迁移**

**注意：3.0+版本与 2.1 版本数据不兼容,可使用本仓库附赠的脚本 /tools/data_update.py 转换成 3.0+可用的数据**
