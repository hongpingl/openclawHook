# OpenClaw Hooks System

一个灵活可扩展的 OpenClaw Hook 系统，允许您通过自定义处理器拦截和响应系统事件。

## 概述

OpenClaw Hooks System 提供了一个插件架构，使您能够通过创建自定义 Hook 来扩展 OpenClaw 的功能，这些 Hook 可以响应各种系统事件。Hook 可以使用 Python 或 TypeScript 编写，并在匹配事件发生时被动态发现、加载和执行。

## 目录结构

```
hook/
├── __init__.py              # 模块初始化文件
├── hook_types.py            # 类型定义（核心数据结构）
├── manager.py               # Hook 管理器（核心协调器）
├── discovery.py             # Hook 发现模块
├── eligibility.py           # Hook 资格检查模块
├── emitter.py               # 事件发射器
├── loader.py                # Hook 处理器加载器
├── frontmatter.py           # HOOK.md 前置元数据解析器
├── bundled.py               # 内置 Hook 实现
├── cli.py                   # 命令行接口
├── bundled_hooks/           # 内置 Hook 目录
│   ├── __init__.py
│   ├── command-logger/      # 命令日志 Hook
│   ├── conversation-saver/  # 对话保存 Hook
│   ├── daily-report-saver/  # 每日报告 Hook
│   ├── message-logger/      # 消息日志 Hook
│   └── session-memory/      # 会话记忆 Hook
├── example/                 # 示例代码
│   ├── __init__.py
│   └── agent_conversation_example.py
└── workspace/               # 工作目录（存储所有 Hook 产生的文件）
    ├── logs/                # 日志文件
    ├── reports/             # 报告文件
    ├── conversations/       # 对话记录
    └── memory/              # 会话记忆
```

## 架构

Hook 系统围绕多个核心组件构建，这些组件协同工作以提供无缝的插件体验：

### 核心组件

#### 1. HookManager
协调整个 Hook 系统的中央协调器：
- 从多个目录发现 Hook
- 加载和初始化 Hook 处理器
- 根据要求检查 Hook 的资格
- 向已注册的处理器发出事件
- 管理 Hook 生命周期（启用/禁用/重新加载）

#### 2. HookDiscovery
按优先级顺序从多个目录发现 Hook：
- **Workspace hooks**: `<workspace>/hooks/` - 每个 Agent 的 Hook，优先级最高
- **Bundled hooks**: `hook/bundled_hooks/` - 内置的 Hook
- **Extra directories**: 配置中指定的额外目录

#### 3. HandlerLoader
从 Python 模块动态加载 Hook 处理器：
- 使用 Python 的 `importlib` 进行动态模块加载
- 支持多个导出名称（`export`、`handler`、`default`）
- 处理模块缓存和重新加载
- 提供旧版处理器支持以保持向后兼容性

#### 4. EventEmitter
用于 Hook 执行的事件驱动架构：
- 支持同步和异步处理器
- 三种事件注册类型：
  - 特定事件：`on("command:new", handler)`
  - 事件类型：`on_type("command", handler)`
  - 通配符：`on_any(handler)`
- 为常见事件类型提供便捷方法

#### 5. EligibilityChecker
验证 Hook 在执行前是否满足其要求：
- **二进制依赖**：检查所需的可执行文件是否在 PATH 中
- **环境变量**：验证所需的环境变量是否已设置
- **配置**：验证所需的配置值是否存在
- **操作系统兼容性**：确保 Hook 支持当前操作系统

#### 6. Frontmatter Parser
解析 `HOOK.md` 文件以提取 Hook 元数据：
- 包含 Hook 配置的 YAML 前置元数据
- Markdown 文档正文
- 验证必需和可选字段

### 事件系统

Hook 系统使用分层事件结构：

#### 事件类型
- `command` - 命令生命周期事件（new、reset、stop）
- `session` - 会话管理事件
- `agent` - Agent 生命周期事件（bootstrap）
- `gateway` - 网关启动事件
- `message` - 消息事件（received、sent）

#### 事件动作
- `new` - 创建新命令/会话
- `reset` - 重置命令/会话
- `stop` - 停止命令/会话
- `bootstrap` - Agent 引导
- `startup` - 网关启动
- `received` - 收到消息
- `sent` - 发送消息
- `start` - 进程启动
- `end` - 进程结束
- `error` - 发生错误

#### 事件格式
事件表示为具有以下结构的 `HookEvent` 对象：
```python
@dataclass
class HookEvent:
    type: HookEventType
    action: str
    session_key: str
    timestamp: datetime
    messages: List[str]
    context: EventContext
```

## Hook 结构

每个 Hook 是一个包含以下内容的目录：

```
hook-name/
├── HOOK.md          # 元数据和文档
├── handler.py       # Python 处理器实现
└── __init__.py      # Python 模块初始化
```

### HOOK.md 格式

```yaml
---
name: my-hook
description: "用于演示的自定义 Hook"
homepage: https://example.com/docs
metadata:
  openclaw:
    emoji: "🎯"
    events: ["command:new", "command:reset"]
    export: "default"
    requires:
      bins: ["git"]
      env: ["HOME"]
      config: ["workspace.dir"]
      os: ["linux", "darwin"]
    always: false
---

# My Hook

关于此 Hook 功能的详细文档...
```

### 处理器实现

```python
"""
my-hook hook 的处理器。
"""

import os
import sys

# 添加 hook 目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hook_types import HookEvent


def handler(event: HookEvent) -> None:
    """
    处理 Hook 事件。

    参数:
        event: Hook 事件
    """
    if event.type != "command":
        return

    print("[my-hook] 触发:", event.type, event.action)

    # 在这里添加您的自定义逻辑


export = handler
```

## 使用方法

### 基本用法

```python
import os
import sys

# 添加 hook 目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hook_types import HookEvent, HookEventType, get_default_workspace_dir
from manager import HookManager
from datetime import datetime

# 初始化 Hook 管理器
config = {
    "hooks": {
        "internal": {
            "enabled": True,
            "entries": {
                "session-memory": {"enabled": True},
                "command-logger": {"enabled": True},
                "conversation-saver": {"enabled": True},
            }
        }
    }
}

manager = HookManager(config=config)
manager.initialize()

# 发出事件
event = HookEvent(
    type=HookEventType.COMMAND,
    action="new",
    session_key="test-session-123",
    timestamp=datetime.now(),
    context={
        "workspace_dir": get_default_workspace_dir(),
        "sender_id": "+1234567890",
        "command_source": "telegram",
    },
)

messages = manager.emit(event)
```

### CLI 命令

```bash
# 列出所有 Hook
openclaw hooks list

# 列出详细信息
openclaw hooks list --verbose

# 显示 Hook 详情
openclaw hooks info command-logger

# 检查资格
openclaw hooks check

# 启用 Hook
openclaw hooks enable session-memory

# 禁用 Hook
openclaw hooks disable command-logger

# 创建新 Hook
openclaw hooks create my-hook \
  --description "自定义 Hook" \
  --events command:new command:reset \
  --emoji "🎯"
```

### 事件发射器

```python
from emitter import EventEmitter
from hook_types import HookEventType

emitter = EventEmitter()

# 注册处理器
def on_new_command(event):
    print(f"新命令: {event.session_key}")

emitter.on("command:new", on_new_command)

# 发出事件
emitter.emit_command("new", "session-123", context={"sender_id": "user"})
emitter.emit_message_received("session-123", "+1234567890", "你好!", "whatsapp")
```

## 内置 Hook

系统包含以下内置 Hook：

### session-memory 💾
当您发出 `/new` 时将会话上下文保存到内存
- 事件：`command:new`
- 输出：`workspace/memory/YYYY-MM-DD-HHMM.md`

### command-logger 📝
将所有命令事件记录到集中审计文件
- 事件：`command:*`
- 输出：`workspace/logs/commands.log`

### message-logger 📨
记录所有消息事件
- 事件：`message:received`、`message:sent`
- 输出：控制台

### conversation-saver �
保存对话记录到 JSONL 文件
- 事件：`message:received`、`message:sent`
- 输出：`workspace/conversations/session_YYYYMMDD_HHMMSS.jsonl`

### daily-report-saver �
保存每日报告到 Markdown 文件
- 事件：`message:sent`
- 输出：`workspace/reports/YYYY-MM-DD.md`

## 配置

Hook 配置存储在主 OpenClaw 配置文件中：

```json
{
  "hooks": {
    "internal": {
      "enabled": true,
      "entries": {
        "session-memory": {"enabled": true},
        "command-logger": {"enabled": true},
        "conversation-saver": {"enabled": true},
        "daily-report-saver": {"enabled": true},
        "message-logger": {"enabled": true},
        "my-custom-hook": {
          "enabled": true,
          "env": {"CUSTOM_VAR": "value"},
          "paths": ["/custom/path"]
        }
      },
      "load": {
        "extraDirs": ["/additional/hooks/directory"]
      },
      "handlers": [
        {
          "event": "command:new",
          "module": "./custom_handler.py",
          "export": "default"
        }
      ]
    }
  }
}
```

## 要求系统

Hook 可以声明在运行之前必须满足的要求：

### 二进制依赖
```yaml
requires:
  bins: ["git", "node"]        # 全部必需
  anyBins: ["python3", "python"]  # 至少需要一个
```

### 环境变量
```yaml
requires:
  env: ["HOME", "OPENCLAW_API_KEY"]
```

### 配置
```yaml
requires:
  config: ["workspace.dir", "api.endpoint"]
```

### 操作系统兼容性
```yaml
requires:
  os: ["linux", "darwin"]  # 支持的平台
```

### 始终运行
```yaml
always: true  # 跳过所有资格检查
```

## 开发

### 创建新 Hook

```python
from discovery import HookDiscovery
from hook_types import get_default_hooks_dir

discovery = HookDiscovery(managed_hooks_dir=get_default_hooks_dir())

hook_path = discovery.create_hook_directory(
    name="my-custom-hook",
    description="用于演示的自定义 Hook",
    events=["command:new", "command:reset"],
    emoji="🎯",
)
```

### 测试 Hook

```python
from hook_types import HookEvent, HookEventType, get_default_workspace_dir
from manager import HookManager
from datetime import datetime

manager = HookManager()
manager.initialize()

# 测试事件发射
event = HookEvent(
    type=HookEventType.COMMAND,
    action="new",
    session_key="test-session",
    timestamp=datetime.now(),
    context={
        "workspace_dir": get_default_workspace_dir(),
    },
)

messages = manager.emit(event)
print(f"消息: {messages}")
```

### 检查资格

```python
from eligibility import EligibilityChecker
from hook_types import HookMetadata, RequiresConfig

checker = EligibilityChecker(config={"workspace": {"dir": "/workspace"}})

metadata = HookMetadata(
    name="test-hook",
    description="具有要求的 Hook",
    events=["command:new"],
    requires=RequiresConfig(
        bins=["git"],
        env=["HOME"],
        config=["workspace.dir"],
    ),
)

result = checker.check(metadata)
print(f"符合资格: {result.eligible}")
if result.reasons:
    print(f"原因: {result.reasons}")
```

## API 参考

### HookManager

```python
class HookManager:
    def __init__(workspace_dir, config, managed_hooks_dir, bundled_hooks_dir)
    def initialize() -> None
    def reload() -> None
    def get_hooks() -> Dict[str, HookInfo]
    def get_enabled_hooks() -> Dict[str, HookInfo]
    def get_hook(name) -> Optional[HookInfo]
    def enable_hook(name) -> bool
    def disable_hook(name) -> bool
    def emit(event) -> List[str]
    async def emit_async(event) -> List[str]
    def get_status() -> List[HookStatus]
    def check_eligibility(name) -> Optional[Dict[str, Any]]
    def create_hook(name, description, events, directory, emoji) -> Optional[str]
    def save_config(path) -> bool
    def load_config(path) -> bool
```

### EventEmitter

```python
class EventEmitter:
    def on(event, handler) -> None
    def on_type(event_type, handler) -> None
    def on_any(handler) -> None
    def off(event, handler) -> bool
    def off_type(event_type, handler) -> bool
    def off_any(handler) -> bool
    def emit(event) -> List[str]
    async def emit_async(event) -> List[str]
    def create_event(event_type, action, session_key, context) -> HookEvent
    def emit_command(action, session_key, context) -> List[str]
    def emit_message_received(session_key, from_, content, channel_id, **kwargs) -> List[str]
    def emit_message_sent(session_key, to, content, success, channel_id, **kwargs) -> List[str]
    def emit_agent_bootstrap(session_key, context) -> List[str]
    def emit_gateway_startup(session_key, context) -> List[str]
    def get_registered_events() -> Set[str]
    def get_handler_count(event) -> int
    def clear() -> None
```

### HookDiscovery

```python
class HookDiscovery:
    def __init__(workspace_dir, managed_hooks_dir, bundled_hooks_dir, extra_dirs)
    def discover_all() -> Dict[str, HookInfo]
    def get_hook(name) -> Optional[HookInfo]
    def get_all_hooks() -> Dict[str, HookInfo]
    def get_discovery_order() -> List[str]
    def is_hook_pack(directory) -> bool
    def discover_hook_pack(directory) -> List[HookInfo]
    def create_hook_directory(name, description, events, directory, emoji) -> str
```

### EligibilityChecker

```python
class EligibilityChecker:
    def __init__(config)
    def check(metadata) -> EligibilityResult
    def check_multiple(hooks) -> Dict[str, EligibilityResult]
    def get_eligible_hooks(hooks) -> List[HookMetadata]
```

## 示例

查看 `example/` 目录以获取完整示例：
- `example/agent_conversation_example.py` - Agent 对话示例，展示如何在对话过程中使用钩子系统

### 运行示例

```bash
# 模拟对话模式
python example/agent_conversation_example.py

# 交互模式
python example/agent_conversation_example.py -i
```

## 文件模块说明

### 文件作用说明

#### 1. __init__.py
- **作用**：模块初始化文件，导出核心类和函数
- **关联**：导入并重新导出其他模块的核心类，如 `HookManager`、`HookEvent`、`EventEmitter` 等
- **使用场景**：用户通过 `from hook import HookManager` 导入核心功能

#### 2. hook_types.py
- **作用**：定义系统中使用的所有数据类型和枚举
- **关联**：被所有其他模块导入，提供基础数据结构
- **核心类型**：`HookEvent`、`HookMetadata`、`HookInfo`、`HookStatus`、`EligibilityResult` 等
- **核心函数**：
  - `get_default_hooks_dir()` - 获取默认 Hook 目录
  - `get_default_workspace_dir()` - 获取默认工作目录
  - `get_default_logs_dir()` - 获取默认日志目录
- **使用场景**：其他模块使用这些类型进行数据传递和处理

#### 3. manager.py
- **作用**：Hook 管理器，整个系统的核心协调器
- **关联**：
  - 依赖 `discovery.py` 进行 Hook 发现
  - 依赖 `eligibility.py` 进行资格检查
  - 依赖 `loader.py` 加载处理器
  - 依赖 `emitter.py` 发出事件
  - 依赖 `hook_types.py` 提供类型定义
- **使用场景**：应用程序通过 `HookManager` 初始化和管理整个 Hook 系统

#### 4. discovery.py
- **作用**：从多个目录发现 Hook
- **关联**：
  - 依赖 `frontmatter.py` 解析 HOOK.md 文件
  - 依赖 `hook_types.py` 提供 HookInfo 等类型
- **使用场景**：`HookManager` 使用它来发现和加载 Hook

#### 5. eligibility.py
- **作用**：检查 Hook 是否满足运行要求
- **关联**：
  - 依赖 `hook_types.py` 提供 `EligibilityResult` 等类型
- **使用场景**：`HookManager` 在加载 Hook 前使用它检查资格

#### 6. loader.py
- **作用**：动态加载 Hook 处理器
- **关联**：
  - 依赖 `hook_types.py` 提供 `HookInfo` 等类型
- **使用场景**：`HookManager` 使用它加载和管理 Hook 处理器

#### 7. emitter.py
- **作用**：事件发射器，管理事件监听和触发
- **关联**：
  - 依赖 `hook_types.py` 提供 `HookEvent` 等类型
- **使用场景**：`HookManager` 使用它发出事件到 Hook 处理器

#### 8. frontmatter.py
- **作用**：解析 HOOK.md 文件的 YAML 前置元数据
- **关联**：
  - 依赖 `hook_types.py` 提供 `HookMetadata` 类型
- **使用场景**：`discovery.py` 使用它解析 Hook 的元数据

#### 9. bundled.py
- **作用**：提供内置的 Hook 实现
- **关联**：
  - 依赖 `hook_types.py` 提供 `HookEvent` 等类型
- **使用场景**：`HookManager` 加载和使用内置 Hook

#### 10. cli.py
- **作用**：命令行接口，提供 Hook 管理命令
- **关联**：
  - 依赖 `manager.py` 提供 Hook 管理功能
  - 依赖 `hook_types.py` 提供类型定义
- **使用场景**：用户通过命令行管理 Hook

### 模块关联关系

```
+----------------+     +----------------+     +----------------+
|  cli.py        | --> |  manager.py    | --> |  emitter.py    |
+----------------+     +----------------+     +----------------+
        |                      |                     |
        |                      v                     v
        |              +----------------+     +----------------+
        |              |  discovery.py  | --> |  frontmatter.py|
        |              +----------------+     +----------------+
        |                      |
        |                      v
        |              +----------------+
        |              |  eligibility.py|
        |              +----------------+
        |                      |
        v                      v
+----------------+     +----------------+
|  bundled.py    |     |  loader.py     |
+----------------+     +----------------+
        |                      |
        +----------------------+
                      |
                      v
              +----------------+
              |  hook_types.py |
              +----------------+
```

### 核心工作流程

1. **初始化**：`HookManager` 初始化，创建各个组件实例
2. **发现**：`HookDiscovery` 从多个目录发现 Hook
3. **解析**：`frontmatter.py` 解析 HOOK.md 文件获取元数据
4. **检查**：`EligibilityChecker` 检查 Hook 资格
5. **加载**：`HandlerLoader` 加载 Hook 处理器
6. **注册**：将处理器注册到 `EventEmitter`
7. **触发**：当事件发生时，`EventEmitter` 触发相应的处理器

### 依赖关系

- **hook_types.py**：所有模块的基础，提供类型定义
- **manager.py**：核心协调器，依赖其他所有模块
- **discovery.py**：依赖 frontmatter.py 和 hook_types.py
- **eligibility.py**：依赖 hook_types.py
- **loader.py**：依赖 hook_types.py
- **emitter.py**：依赖 hook_types.py
- **frontmatter.py**：依赖 hook_types.py
- **bundled.py**：依赖 hook_types.py
- **cli.py**：依赖 manager.py 和 hook_types.py

## 工作目录说明

所有 Hook 产生的文件统一存储在 `workspace/` 目录下：

```
workspace/
├── logs/                    # 日志文件
│   └── commands.log         # 命令日志
├── reports/                 # 报告文件
│   └── YYYY-MM-DD.md        # 每日报告
├── conversations/           # 对话记录
│   └── session_*.jsonl      # 会话对话记录
└── memory/                  # 会话记忆
    └── YYYY-MM-DD-HHMM.md   # 会话记忆文件
```

### 获取默认路径

```python
from hook_types import (
    get_default_hooks_dir,      # 获取 Hook 目录
    get_default_workspace_dir,  # 获取工作目录
    get_default_logs_dir,       # 获取日志目录
)

print(get_default_hooks_dir())      # .../hook/bundled_hooks
print(get_default_workspace_dir())  # .../hook/workspace
print(get_default_logs_dir())       # .../hook/workspace/logs
```
