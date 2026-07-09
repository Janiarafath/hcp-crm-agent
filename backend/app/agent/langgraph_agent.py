from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage, ToolMessage
from typing import TypedDict, List
from app.tools.hcp_tools import (
    log_interaction, 
    edit_interaction, 
    search_hcp, 
    get_interaction_history, 
    create_follow_up
)
import json
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

tools = [log_interaction, edit_interaction, search_hcp, get_interaction_history, create_follow_up]
tools_map = {t.name: t for t in tools}

llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama-3.3-70b-versatile",
    temperature=0.3,
    max_tokens=1024
)

llm_with_tools = llm.bind_tools(tools)

system_prompt = """You are an AI assistant for a Healthcare CRM system. Your job is to help field representatives log interactions with Healthcare Professionals (HCPs).

Available tools:
- log_interaction: Save a new HCP interaction. Accepts 'interaction_data' as JSON string.
- edit_interaction: Modify an existing interaction. Accepts 'interaction_id' (int), 'field_name' (str), 'field_value' (str).
- search_hcp: Find interactions by HCP name. Accepts 'hcp_name' (str).
- get_interaction_history: Get full details of a specific interaction. Accepts 'interaction_id' (int).
- create_follow_up: Add follow-up actions. Accepts 'interaction_id' (int), 'follow_up_note' (str).

IMPORTANT RULES:
1. When user describes a new meeting, use log_interaction with all extracted fields as JSON string
2. When user wants to edit/correct a field, use edit_interaction with the field_name and field_value. Valid field names: hcp_name, interaction_type, date, time, attendees, topics_discussed, voice_note_summary, materials_shared, samples_distributed, hcp_sentiment, outcomes, follow_up_actions
3. When user asks to search, use search_hcp
4. When user wants details, use get_interaction_history
5. When user wants follow-up, use create_follow_up

When user says something like "The name was actually Dr. John" or "Actually the sentiment was negative", you should call edit_interaction for each correction.

Always respond in a friendly, professional CRM assistant manner. When logging, confirm what was saved. When editing, confirm what changed.
"""

def execute_tool(tool_name: str, tool_args: dict) -> str:
    tool = tools_map.get(tool_name)
    if not tool:
        return json.dumps({"status": "error", "message": f"Tool {tool_name} not found"})
    try:
        result = tool.invoke(tool_args)
        return result
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

last_logged_id = None

def process_message(user_message: str, history: list = None) -> dict:
    global last_logged_id

    if history is None:
        history = []
    
    messages = [SystemMessage(content=system_prompt)] + history + [HumanMessage(content=user_message)]
    
    max_iterations = 5
    tool_results_all = []
    
    for i in range(max_iterations):
        response = llm_with_tools.invoke(messages)
        messages.append(response)
        
        if not hasattr(response, "tool_calls") or not response.tool_calls:
            break
        
        for tc in response.tool_calls:
            tool_name = tc["name"]
            tool_args = tc["args"]
            
            if tool_name == "edit_interaction" and "interaction_id" not in tool_args and last_logged_id:
                tool_args["interaction_id"] = last_logged_id
            
            tool_result = execute_tool(tool_name, tool_args)
            
            if tool_name == "log_interaction":
                try:
                    res = json.loads(tool_result)
                    if res.get("status") == "success":
                        last_logged_id = res.get("interaction_id")
                except:
                    pass
            
            tool_results_all.append({
                "tool": tool_name,
                "args": tool_args,
                "result": tool_result
            })
            messages.append(ToolMessage(content=tool_result, tool_call_id=tc["id"]))
    
    ai_response = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            ai_response = msg.content
            break
    
    return {
        "response": ai_response,
        "tool_calls": tool_results_all,
        "messages": [{"role": m.type, "content": m.content} for m in messages if isinstance(m, (HumanMessage, AIMessage)) and m.content]
    }