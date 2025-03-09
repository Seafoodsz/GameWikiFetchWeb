# Stoneshard Wiki 数据整理程序

这是一个用于处理从 Stoneshard Wiki 抓取的数据，并将其转化为结构化的游戏数据库的程序。

## 功能特点

- 支持处理多种游戏数据类型：角色、技能、物品、敌人、地点、任务等
- 自动提取数据之间的关系，如角色-技能、物品-敌人、地点-任务、任务-奖励等
- 支持多种数据存储方式：JSON、MongoDB、SQLite
- 灵活的配置系统，可以根据需要启用或禁用特定的处理器
- 详细的日志记录，方便调试和追踪处理过程
- 支持导出多种格式的数据：JSON、CSV、HTML

## 系统要求

- Python 3.6 或更高版本
- 依赖库：BeautifulSoup4、pymongo（可选，用于 MongoDB 支持）

## 安装

1. 克隆或下载本仓库
2. 安装依赖库：

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
python stoneshard_data_processor.py
```

这将使用默认配置文件 `config.json` 运行程序。

### 指定配置文件

```bash
python stoneshard_data_processor.py --config path/to/config.json
```

### 指定输入和输出目录

```bash
python stoneshard_data_processor.py --input path/to/input --output path/to/output
```

### 指定日志级别

```bash
python stoneshard_data_processor.py --log-level DEBUG
```

可选的日志级别：DEBUG、INFO、WARNING、ERROR

## 配置文件

配置文件使用 JSON 格式，包含以下主要部分：

- 基本配置：输入/输出目录、日志级别等
- 数据库配置：数据库类型、连接信息等
- 处理器配置：各种处理器的配置信息
- 分析配置：数据分析和可视化选项
- 导出配置：数据导出格式和选项

详细的配置选项请参考 `config.json` 文件。

## 目录结构

```
stoneshard_data_processor/
├── stoneshard_data_processor.py  # 主程序
├── config.json                   # 配置文件
├── requirements.txt              # 依赖库列表
├── README.md                     # 说明文档
├── processors/                   # 处理器模块
│   ├── base_processor.py         # 基础处理器
│   ├── character_processor.py    # 角色处理器
│   ├── skill_processor.py        # 技能处理器
│   ├── item_processor.py         # 物品处理器
│   ├── enemy_processor.py        # 敌人处理器
│   ├── location_processor.py     # 地点处理器
│   ├── quest_processor.py        # 任务处理器
│   └── relation_processor.py     # 关系处理器
└── utils/                        # 工具模块
    ├── config.py                 # 配置模块
    ├── database.py               # 数据库模块
    └── logger.py                 # 日志模块
```

## 数据结构

程序处理后的数据将按照以下结构组织：

### 角色数据

```json
{
  "id": "warrior",
  "name": "战士",
  "type": "character",
  "description": "...",
  "attributes": {
    "strength": 12,
    "dexterity": 8,
    "...": "..."
  },
  "skills": [...],
  "traits": [...],
  "starting_items": [...]
}
```

### 技能数据

```json
{
  "id": "cleave",
  "name": "横扫",
  "type": "skill",
  "skill_type": "active",
  "skill_tree": "combat",
  "description": "...",
  "effects": [...],
  "requirements": {...},
  "cooldown": 3,
  "energy_cost": 15,
  "level_requirements": [...]
}
```

### 物品数据

```json
{
  "id": "iron_sword",
  "name": "铁剑",
  "type": "item",
  "category": "weapon",
  "item_type": "one_handed_sword",
  "description": "...",
  "attributes": {
    "damage": 10,
    "...": "..."
  },
  "effects": [...],
  "requirements": {...},
  "value": 100,
  "weight": 2.5
}
```

### 敌人数据

```json
{
  "id": "wolf",
  "name": "狼",
  "type": "enemy",
  "enemy_type": "beast",
  "description": "...",
  "stats": {
    "health": 50,
    "...": "..."
  },
  "resistances": {...},
  "weaknesses": [...],
  "abilities": [...],
  "drops": [...]
}
```

### 地点数据

```json
{
  "id": "osbrook",
  "name": "奥斯布鲁克",
  "type": "location",
  "location_type": "town",
  "description": "...",
  "coordinates": {
    "x": 100,
    "y": 200
  },
  "npcs": [...],
  "enemies": [...],
  "resources": [...],
  "quests": [...]
}
```

### 任务数据

```json
{
  "id": "first_blood",
  "name": "初次杀戮",
  "type": "quest",
  "quest_type": "main",
  "description": "...",
  "giver": "村长",
  "location": "奥斯布鲁克",
  "prerequisites": [...],
  "objectives": [...],
  "steps": [...],
  "rewards": [...]
}
```

### 关系数据

```json
{
  "id": "warrior_cleave",
  "source_type": "character",
  "source_id": "warrior",
  "target_type": "skill",
  "target_id": "cleave",
  "relation_type": "character_skill",
  "data": {
    "character_name": "战士",
    "skill_name": "横扫",
    "...": "..."
  }
}
```

## 许可证

本项目采用 MIT 许可证。详情请参阅 LICENSE 文件。

## 贡献

欢迎提交 Issue 和 Pull Request。

## 优化说明

本项目已进行了以下优化，以提高性能、可维护性和用户体验：

### 已实施的优化

1. **多线程数据处理**
   - 使用ThreadPoolExecutor实现并行处理不同数据类型
   - 添加并发度配置选项，默认使用CPU核心数的一半
   - 独立处理器并行执行，依赖处理器顺序执行
   - 显著提高了数据处理速度，特别是在多核CPU上

2. **增强错误处理**
   - 添加全局异常处理装饰器，捕获并记录详细的异常信息
   - 实现上下文日志记录器，提供更好的日志上下文
   - 改进错误消息，包含更多上下文信息
   - 提高了系统稳定性和问题诊断能力

3. **统一配置管理**
   - 支持多种配置源（默认配置、配置文件、环境变量）
   - 实现配置验证和类型转换
   - 添加配置覆盖机制（命令行 > 环境变量 > 配置文件 > 默认值）
   - 使配置管理更加灵活和健壮

4. **内存优化**
   - 实现数据流处理，使用生成器而不是列表
   - 添加批处理机制，控制内存使用
   - 使用ijson进行大型JSON文件的流式解析
   - 添加内存监控和自动垃圾回收
   - 显著减少了内存占用，提高了大数据集处理能力

### 后续优化建议

1. **代码结构优化**
   - 创建统一的CLI工具，整合所有功能
   - 简化目录结构，提高可维护性
   - 标准化模块命名和导入

2. **用户体验优化**
   - 更新Web界面，使用现代化前端框架
   - 添加数据可视化功能
   - 提供更多数据导出选项

3. **性能进一步优化**
   - 实现异步网络请求，使用aiohttp替代requests
   - 添加缓存机制，减少重复计算
   - 优化数据库操作，减少IO开销

## 内存优化详情

为了处理大型Wiki数据集，本项目实施了以下内存优化措施：

1. **批量处理**：数据处理分批进行，每批处理固定数量的项目，避免一次性加载所有数据到内存。

2. **流式JSON处理**：使用ijson库进行大型JSON文件的流式解析，避免一次性加载整个文件到内存。

3. **内存监控**：实时监控程序内存使用情况，当内存使用超过配置的限制时，自动触发垃圾回收。

4. **内存使用统计**：记录处理过程中的内存使用情况，包括峰值内存使用和平均内存使用，方便用户了解程序的资源需求。

5. **生成器模式**：使用生成器替代列表，实现惰性计算，减少内存占用。

这些优化措施使程序能够处理更大规模的数据集，同时保持较低的内存占用。