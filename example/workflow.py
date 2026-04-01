from langchain.chat_models import init_chat_model
from datetime import datetime
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from hook.hook_types import HookEvent, HookEventType, HookAction, get_default_workspace_dir
from hook.manager import HookManager

def init_llm(model_name="gpt-5.2"):
    try:
        return init_chat_model(
            model=model_name,
            model_provider="openai",
            base_url="http://192.168.145.16/v1/",
            api_key="sk-LA4KngJCQfVfsSLD7xjkfmxdpvSKUljIL7gEsb2OVKqaaihh"
        )
    except Exception as e:
        raise Exception(f"模型初始化失败：{str(e)}")

# def ask_question(question: str, model_name: str = "gpt-5.2") -> str:
#     try:
#         llm = init_llm(model_name)
#         response = llm.invoke(question)
#         return response.content
#     except Exception as e:
#         raise Exception(f"回答问题时出错：{str(e)}")



def ask_question(question: str, model_name: str = "gpt-5.2") -> str:
    try:
        # 初始化 HookManager
        workspace_dir = get_default_workspace_dir()
        hook_manager = HookManager(workspace_dir=workspace_dir)
        hook_manager.initialize()
        
        # 启用 conversation-saver 钩子
        hook_manager.enable_hook("conversation-saver")
        
        # 发送用户消息事件
        user_event = HookEvent(
            type=HookEventType.MESSAGE,
            action="received",
            session_key="default_session",
            timestamp=datetime.now(),
            context={"content": question}
        )
        hook_manager.emit(user_event)

        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # 调用 LLM
        llm = init_llm(model_name)
        response = llm.invoke(question)
        answer = response.content
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        
        # 回复事件
        assistant_event = HookEvent(
            type=HookEventType.MESSAGE,
            action="sent",
            session_key="default_session",
            timestamp=datetime.now(),
            context={"content": answer}
        )
        hook_manager.emit(assistant_event)
        
        return answer
    except Exception as e:
        raise Exception(f"回答问题时出错：{str(e)}")



if __name__ == "__main__":
    test_question = "什么是kimiclaw？"
    answer = ask_question(test_question)
    print(f"问题：{test_question}")
    print(f"答案：{answer}")