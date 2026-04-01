---
name: hello-world
description: "A simple example hook that prints hello messages for any event"
metadata:
  openclaw:
    emoji: "👋"
    events: ["message:received", "message:sent", "command:new", "command:reset", "agent:bootstrap", "middleware:before_agent", "middleware:after_agent", "middleware:before_model", "middleware:after_model", "middleware:wrap_tool_call", "middleware:wrap_model_call"]
---

# Hello World Hook

这是一个最简单的钩子示例，用于演示如何创建和使用钩子。

## 功能

- 接收任意事件并打印 Hello 消息
- 显示事件的类型、动作、会话键和时间戳
- 作为其他钩子开发的参考模板

## 支持的事件

- `message:received` - 收到消息时触发
- `message:sent` - 发送消息时触发
- `command:new` - 新建命令时触发
- `command:reset` - 重置命令时触发
- `agent:bootstrap` - Agent 启动时触发

## 示例输出

```
[hello-world] Hello! Event received:
  - Type: message
  - Action: received
  - Session Key: default_session
  - Timestamp: 2026-03-05 10:30:00
  - Messages: ['Hello from user']
[hello-world] World says: Hook executed successfully!
```

## 使用方法

```python
from AutoSAR_Agent.hook.hook_types import HookEvent, HookEventType
from AutoSAR_Agent.hook.manager import HookManager
from datetime import datetime

# 初始化 HookManager
hook_manager = HookManager(workspace_dir="./workspace")
hook_manager.initialize()

# 启用 hello-world 钩子
hook_manager.enable_hook("hello-world")

# 创建并发送事件
event = HookEvent(
    type=HookEventType.MESSAGE,
    action="received",
    session_key="my_session",
    timestamp=datetime.now(),
    messages=["Hello from user"]
)
hook_manager.emit(event)
```

## 无需配置

此钩子不需要任何配置，启用即可使用。
