"""
测试新添加的 middleware 事件类型和动作
"""

from datetime import datetime
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from hook.hook_types import HookEvent, HookEventType, HookAction, get_default_workspace_dir
from hook.manager import HookManager


def test_middleware_events():
    """
    测试新添加的 middleware 事件类型和动作
    """
    print("=" * 60)
    print("测试 Middleware 事件类型和动作")
    print("=" * 60)
    
    workspace_dir = get_default_workspace_dir()
    hook_manager = HookManager(workspace_dir=workspace_dir)
    hook_manager.initialize()
    
    # 启用 hello-world 钩子来测试事件
    hook_manager.enable_hook("hello-world")
    
    # 获取 EventEmitter 实例
    emitter = hook_manager.get_event_emitter()
    
    session_key = "test_middleware_session"
    
    print("\n[1] 测试 middleware:before_agent 事件")
    emitter.emit_middleware_before_agent(
        session_key=session_key,
        context={"agent_id": "test_agent", "task": "test_task"}
    )
    
    print("\n[2] 测试 middleware:after_agent 事件")
    emitter.emit_middleware_after_agent(
        session_key=session_key,
        context={"agent_id": "test_agent", "result": "success"}
    )
    
    print("\n[3] 测试 middleware:before_model 事件")
    emitter.emit_middleware_before_model(
        session_key=session_key,
        context={"model_name": "gpt-4", "prompt": "Hello"}
    )
    
    print("\n[4] 测试 middleware:after_model 事件")
    emitter.emit_middleware_after_model(
        session_key=session_key,
        context={"model_name": "gpt-4", "response": "Hello back!"}
    )
    
    print("\n[5] 测试 middleware:wrap_tool_call 事件")
    emitter.emit_middleware_wrap_tool_call(
        session_key=session_key,
        context={"tool_name": "search", "args": {"query": "Python"}}
    )
    
    print("\n[6] 测试 middleware:wrap_model_call 事件")
    emitter.emit_middleware_wrap_model_call(
        session_key=session_key,
        context={"model_name": "gpt-4", "call_args": {"temperature": 0.7}}
    )
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    test_middleware_events()
