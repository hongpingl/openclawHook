"""
Agent Conversation Example with Hooks

This example demonstrates how to use the hook system in an agent conversation scenario.
It simulates a chat agent that processes user messages and triggers various hooks.
"""

import os
import sys
import json
from datetime import datetime
from typing import Optional, Dict, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from hook.hook_types import HookEvent, HookEventType, get_default_workspace_dir
from hook.manager import HookManager


class ChatAgent:
    """
    A simple chat agent that uses hooks for various events.
    """
    
    def __init__(self, agent_name: str = "AutoSAR Agent"):
        self.agent_name = agent_name
        self.session_key = f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.conversation_history = []
        
        # Initialize hook manager with configuration
        self._init_hooks()
    
    def _init_hooks(self):
        """Initialize the hook manager with enabled hooks."""
        config = {
            "hooks": {
                "internal": {
                    "enabled": True,
                    "entries": {
                        "session-memory": {"enabled": True},
                        "command-logger": {"enabled": True},
                        "message-logger": {"enabled": True},
                        "daily-report-saver": {"enabled": True},
                        "conversation-saver": {"enabled": True},
                    }
                }
            }
        }
        
        self.hook_manager = HookManager(config=config)
        self.hook_manager.initialize()
        
        print(f"[{self.agent_name}] Hook system initialized")
        print(f"[{self.agent_name}] Session key: {self.session_key}")
        
        # Display discovered hooks
        hooks = self.hook_manager.get_hooks()
        print(f"[{self.agent_name}] Active hooks: {len(hooks)}")
        for name, hook_info in hooks.items():
            if hook_info.enabled:
                emoji = hook_info.metadata.emoji or "•"
                print(f"  {emoji} {name}")
    
    def start_session(self):
        """Start a new conversation session."""
        print(f"\n{'='*60}")
        print(f"[{self.agent_name}] Starting new session...")
        print(f"{'='*60}\n")
        
        # Trigger command:new event for session-memory hook
        event = HookEvent(
            type=HookEventType.COMMAND,
            action="new",
            session_key=self.session_key,
            timestamp=datetime.now(),
            context={
                "workspace_dir": get_default_workspace_dir(),
                "sender_id": "user",
                "command_source": "cli",
            },
        )
        
        messages = self.hook_manager.emit(event)
        if messages:
            for msg in messages:
                print(f"  [Hook] {msg}")
    
    def receive_message(self, content: str, sender_id: str = "user"):
        """
        Process an incoming message from the user.
        
        Args:
            content: The message content
            sender_id: The sender identifier
        """
        print(f"\n[User]: {content}")
        
        # Store in conversation history
        self.conversation_history.append({
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        
        # Trigger message:received event
        event = HookEvent(
            type=HookEventType.MESSAGE,
            action="received",
            session_key=self.session_key,
            timestamp=datetime.now(),
            context={
                "from": sender_id,
                "content": content,
                "channelId": "cli",
                "conversation_id": self.session_key,
            },
        )
        
        messages = self.hook_manager.emit(event)
        if messages:
            for msg in messages:
                print(f"  [Hook] {msg}")
    
    def send_message(self, content: str):
        """
        Send a response message to the user.
        
        Args:
            content: The response content
        """
        print(f"[{self.agent_name}]: {content}")
        
        # Store in conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        
        # Trigger message:sent event
        event = HookEvent(
            type=HookEventType.MESSAGE,
            action="sent",
            session_key=self.session_key,
            timestamp=datetime.now(),
            context={
                "to": "user",
                "content": content,
                "success": True,
                "channelId": "cli",
                "conversation_id": self.session_key,
            },
        )
        
        messages = self.hook_manager.emit(event)
        if messages:
            for msg in messages:
                print(f"  [Hook] {msg}")
    
    def process_command(self, command: str):
        """
        Process a command from the user.
        
        Args:
            command: The command string (e.g., "/help", "/reset")
        """
        print(f"\n[Command]: {command}")
        
        # Parse command
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # Trigger command event
        action = cmd.lstrip("/")
        event = HookEvent(
            type=HookEventType.COMMAND,
            action=action,
            session_key=self.session_key,
            timestamp=datetime.now(),
            context={
                "workspace_dir": get_default_workspace_dir(),
                "command_source": "cli",
                "sender_id": "user",
                "args": args,
            },
        )
        
        messages = self.hook_manager.emit(event)
        if messages:
            for msg in messages:
                print(f"  [Hook] {msg}")
        
        # Handle specific commands
        if cmd == "/help":
            self._show_help()
        elif cmd == "/reset":
            self._reset_conversation()
        elif cmd == "/history":
            self._show_history()
        elif cmd == "/report":
            self._generate_report()
    
    def _show_help(self):
        """Show available commands."""
        help_text = """
Available commands:
  /help     - Show this help message
  /reset    - Reset the conversation
  /history  - Show conversation history
  /report   - Generate a daily report
  /quit     - Exit the conversation
        """
        self.send_message(help_text.strip())
    
    def _reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
        self.send_message("Conversation has been reset. Starting fresh!")
    
    def _show_history(self):
        """Show the conversation history."""
        if not self.conversation_history:
            self.send_message("No conversation history yet.")
            return
        
        history_text = "Conversation History:\n" + "-" * 40 + "\n"
        for msg in self.conversation_history:
            role = msg["role"].upper()
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            history_text += f"[{role}]: {content}\n"
        
        self.send_message(history_text)
    
    def _generate_report(self):
        """Generate a daily report."""
        report_content = f"""
# Daily Report - {datetime.now().strftime('%Y-%m-%d')}

## Session Information
- Session Key: {self.session_key}
- Agent: {self.agent_name}
- Messages: {len(self.conversation_history)}

## Conversation Summary
Total exchanges: {len([m for m in self.conversation_history if m['role'] == 'user'])}
        """
        
        # Trigger message:sent event with report content for daily-report-saver hook
        event = HookEvent(
            type=HookEventType.MESSAGE,
            action="sent",
            session_key=self.session_key,
            timestamp=datetime.now(),
            context={
                "to": "user",
                "content": report_content,
                "success": True,
                "channelId": "cli",
            },
        )
        
        self.hook_manager.emit(event)
        self.send_message(f"Report generated! Check the workspace/reports directory.")
    
    def end_session(self):
        """End the current session."""
        print(f"\n{'='*60}")
        print(f"[{self.agent_name}] Ending session...")
        print(f"{'='*60}")
        
        # Trigger command:stop event
        event = HookEvent(
            type=HookEventType.COMMAND,
            action="stop",
            session_key=self.session_key,
            timestamp=datetime.now(),
            context={
                "workspace_dir": get_default_workspace_dir(),
            },
        )
        
        self.hook_manager.emit(event)


def simulate_conversation():
    """Simulate a conversation with the agent."""
    print("\n" + "="*60)
    print("Agent Conversation Example with Hooks")
    print("="*60)
    
    # Create the agent
    agent = ChatAgent(agent_name="AutoSAR Assistant")
    
    # Start session
    agent.start_session()
    
    # Simulate conversation
    agent.receive_message("Hello! Can you help me with something?")
    agent.send_message("Hello! I'm the AutoSAR Assistant. I'm here to help you with your questions. What would you like to know?")
    
    agent.receive_message("What commands are available?")
    agent.process_command("/help")
    
    agent.receive_message("Tell me about the hook system.")
    agent.send_message(
        "The hook system allows you to extend the agent's functionality by attaching "
        "handlers to various events. For example:\n"
        "- session-memory: Saves session context\n"
        "- message-logger: Logs all messages\n"
        "- command-logger: Logs all commands\n"
        "- daily-report-saver: Saves daily reports"
    )
    
    agent.receive_message("Let me see the conversation history.")
    agent.process_command("/history")
    
    agent.receive_message("Can you generate a report?")
    agent.process_command("/report")
    
    # End session
    agent.end_session()
    
    print("\n" + "="*60)
    print("Conversation simulation completed!")
    print("="*60)
    
    # Show where files are stored
    workspace_dir = get_default_workspace_dir()
    print(f"\nFiles are stored in: {workspace_dir}")
    print("\nGenerated files:")
    
    # Check for generated files
    logs_dir = os.path.join(workspace_dir, "logs")
    reports_dir = os.path.join(workspace_dir, "reports")
    memory_dir = os.path.join(workspace_dir, "memory")
    
    for directory in [logs_dir, reports_dir, memory_dir]:
        if os.path.exists(directory):
            print(f"\n{os.path.basename(directory)}/")
            for file in os.listdir(directory):
                filepath = os.path.join(directory, file)
                size = os.path.getsize(filepath)
                print(f"  - {file} ({size} bytes)")


def interactive_mode():
    """Run the agent in interactive mode."""
    print("\n" + "="*60)
    print("Interactive Agent Conversation (type '/quit' to exit)")
    print("="*60)
    
    agent = ChatAgent(agent_name="AutoSAR Assistant")
    agent.start_session()
    
    agent.send_message("Hello! I'm your AutoSAR Assistant. Type '/help' for available commands.")
    
    while True:
        try:
            user_input = input("\n[You]: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "/quit":
                agent.send_message("Goodbye! Have a great day!")
                break
            
            if user_input.startswith("/"):
                agent.process_command(user_input)
            else:
                agent.receive_message(user_input)
                # Simple echo response for demonstration
                agent.send_message(f"I received your message: '{user_input}'. How can I help you further?")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted by user.")
            break
    
    agent.end_session()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Conversation Example with Hooks")
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
    else:
        simulate_conversation()
