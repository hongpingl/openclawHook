"""
Hello World Hook 示例 Workflow

这是一个最简单的钩子使用示例，演示如何:
1. 初始化 HookManager
2. 启用钩子
3. 发送事件触发钩子
"""

from datetime import datetime
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from hook.hook_types import HookEvent, HookEventType, get_default_workspace_dir
from hook.manager import HookManager


def hello_world_workflow():
    """
    演示 Hello World 钩子的基础工作流
    """
    # print("=" * 60)
    # print("Hello World Hook 示例 Workflow")
    # print("=" * 60)
    
    workspace_dir = get_default_workspace_dir()
    hook_manager = HookManager(workspace_dir=workspace_dir)
    hook_manager.initialize()
    
    # print("\n启用 hello-world 钩子")
    hook_manager.enable_hook("hello-world")
    
    print("\n发送 message:received 事件")
    event1 = HookEvent(
        type=HookEventType.MESSAGE,
        action="received",
        session_key="demo_session",
        timestamp=datetime.now(),
        messages=["Hello from user!"],
        context={"from": "user", "content": "Hello from user!"}
    )
    hook_manager.emit(event1)
    
    # print("\n发送 message:sent 事件")
    # event2 = HookEvent(
    #     type=HookEventType.MESSAGE,
    #     action="sent",
    #     session_key="demo_session",
    #     timestamp=datetime.now(),
    #     messages=["Hello from agent!"],
    #     context={"to": "user", "content": "Hello from agent!", "success": True}
    # )
    # hook_manager.emit(event2)
    #
    # print("\n发送 command:new 事件")
    # event3 = HookEvent(
    #     type=HookEventType.COMMAND,
    #     action="new",
    #     session_key="demo_session",
    #     timestamp=datetime.now(),
    #     context={"workspace_dir": workspace_dir}
    # )
    # hook_manager.emit(event3)

    event4 = HookEvent(
        type=HookEventType.MIDDLEWARE,
        action="before_agent",
        session_key="session123",
        timestamp=datetime.now(),
        context={"agent_id": "test_agent"}
    )
    hook_manager.emit(event4)
    
    # print("\n" + "=" * 60)
    # print("Workflow 完成!")
    # print("=" * 60)


if __name__ == "__main__":
    hello_world_workflow()
