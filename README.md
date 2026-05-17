# 逐字拾光 LumiType

一款手绘可爱风格的中文打字练习应用，基于 PyQt6 构建。

## 功能

- **跟打练习** — 逐字跟打原文，支持诗词、成语、文章、新闻素材
- **掉落消除** — 汉字从天而降，输入拼音即可消除，锻炼键盘熟练度
- **限时挑战** — 限时冲刺模式，连击加分机制
- **素材库管理** — 内置诗词/成语，支持 RSS 新闻自动抓取更新
- **统计系统** — 历史记录、正确率、CPM 实时统计
- **自定义设置** — 字体、难度、音效、显示模式

## 安装

```bash
pip install -r requirements.txt
python main.py
```

## 依赖

- Python 3.10+
- PyQt6
- pypinyin
- requests / beautifulsoup4 / feedparser

## 打包

```bash
pip install pyinstaller
pyinstaller typehan.spec
```

生成文件在 `dist/逐字拾光/` 目录。

## 项目结构

```
├── main.py              # 入口
├── src/
│   ├── app.py           # 单例 App（配置 + 数据库）
│   ├── config.py        # QSettings 配置管理
│   ├── constants.py     # 颜色、常量
│   ├── core/            # 游戏引擎、计分、音效
│   ├── db/              # SQLite 存储
│   ├── materials/       # 素材管理与抓取
│   ├── modes/           # 三种游戏模式
│   └── ui/              # 界面组件
├── data/builtin/        # 内置素材（诗词、成语）
└── requirements.txt
```

## 截图

![主界面](https://raw.githubusercontent.com/HuanSun321/LumiType/main/screenshot_menu.png)

## 许可证

MIT License
