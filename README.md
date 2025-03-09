# GameWiki Fetcher 使用指南

## 简介

GameWiki Fetcher 是一个用于获取游戏Wiki资料并保存到本地的工具。它可以抓取Wiki页面的文本内容、图片、表格等资源，并以结构化的方式保存到本地，方便离线查阅和使用。

## 系统要求

- Python 3.6 或更高版本
- 网络连接
- 足够的磁盘空间（取决于Wiki的大小）

## 快速开始

### Windows 用户

1. 双击 `run.bat` 文件
2. 首次运行时，程序会自动创建虚拟环境并安装依赖
3. 程序将使用 `.env` 文件中的配置开始抓取Wiki

### Linux/Mac 用户

1. 打开终端，进入程序目录
2. 执行 `./run.sh` 命令
3. 首次运行时，程序会自动创建虚拟环境并安装依赖
4. 程序将使用 `.env` 文件中的配置开始抓取Wiki

## 配置选项

你可以通过编辑 `.env` 文件或使用命令行参数来配置程序的行为。

### 必填配置

- `WIKI_URL`: Wiki网站的基础URL，例如 `https://minecraft.fandom.com/zh/wiki/Minecraft_Wiki`
- `OUTPUT_DIR`: 本地保存数据的目录，例如 `./wiki_data`

### 可选配置

- `MAX_DEPTH`: 抓取的最大深度（默认为3）
- `DOWNLOAD_IMAGES`: 是否下载图片（默认为True）
- `DOWNLOAD_TABLES`: 是否下载表格数据（默认为True）
- `USER_AGENT`: 自定义User-Agent
- `DELAY`: 请求之间的延迟（秒）（默认为1）
- `THREADS`: 并发下载线程数（默认为3）
- `SAVE_HTML`: 是否保存原始HTML（默认为False）
- `LOG_LEVEL`: 日志级别（默认为INFO）

## 命令行参数

你也可以使用命令行参数来覆盖 `.env` 文件中的配置：

```
python run.py --wiki-url https://game-wiki-url.com --output-dir ./wiki_data
```

可用的命令行参数与 `.env` 文件中的配置项对应。

## 输出结构

程序会在指定的输出目录中创建以下结构：

```
wiki_data/
├── pages/           # 页面内容（Markdown格式）
│   ├── page1.md
│   ├── page1.json   # 页面元数据
│   ├── page1_tables.json  # 表格数据
│   └── ...
├── images/          # 图片资源
│   ├── image1.jpg
│   ├── image2.png
│   └── ...
├── html/            # 原始HTML（如果配置了保存HTML）
│   ├── page1.html
│   └── ...
└── index.md         # 内容索引
```

## 常见问题

### 程序运行速度很慢

- 尝试减小 `MAX_DEPTH` 值
- 增加 `THREADS` 值可以提高并发下载数量
- 如果不需要图片，可以设置 `DOWNLOAD_IMAGES=False`

### 抓取过程中出现错误

- 检查网络连接
- 增加 `DELAY` 值，减少请求频率
- 查看 `wiki_fetcher.log` 文件了解详细错误信息

### 如何只抓取特定页面

- 将 `MAX_DEPTH` 设置为0，这样只会抓取起始URL指定的页面

## 高级用法

### 增量更新

如果你想定期更新已下载的Wiki内容，可以：

1. 保留之前的输出目录
2. 重新运行程序，它会跳过已下载的页面
3. 新的或更改的页面会被更新

### 自定义解析规则

如果你需要针对特定Wiki定制解析规则，可以修改 `src/parser.py` 文件中的相关代码。

## 许可证

本程序使用 MIT 许可证。请注意，从Wiki获取的内容可能受到版权保护，使用时请遵守相关法律法规和Wiki的使用条款。 
