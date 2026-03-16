import threading
import os
import autogen

def run_agent():
    try:
        user = autogen.UserProxyAgent(name="user", max_consecutive_auto_reply=0, human_input_mode="NEVER")
        bot = autogen.AssistantAgent(name="bot", system_message="Reply with OK", llm_config={"config_list": [{"model": "gpt-4o-mini", "api_key": os.environ.get("OPENAI_API_KEY", "")}]})
        user.initiate_chat(bot, message="Hello")
        print("THREAD SUCCESS")
    except Exception as e:
        print(f"THREAD ERROR: {e}")

print("STARTING")
t = threading.Thread(target=run_agent)
t.start()
t.join()
