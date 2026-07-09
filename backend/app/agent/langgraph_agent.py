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
from langchain_nvidia_ai_endpoints import ChatNVIDIA

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

tools = [log_interaction, edit_interaction, search_hcp, get_interaction_history, create_follow_up]
tools_map = {t.name: t for t in tools}

llm = ChatNVIDIA(
    model="meta/llama-3.1-8b-instruct",
    api_key=NVIDIA_API_KEY,
    temperature=0.2,
    max_tokens=1024
)

llm_with_tools = llm.bind_tools(tools)

system_prompt = """You are an AI assistant for a Healthcare CRM system.

Available tools:
- log_interaction(interaction_data: str) — Save a new HCP interaction. Pass JSON with fields like hcp_name, topics, sentiment, materials, samples, outcomes, follow_up, type.
- edit_interaction(interaction_id, field_name, field_value) — Modify an existing interaction. Use field names like sentiment, topics, materials, hcp_name, outcomes, follow_up.
- search_hcp(hcp_name: str) — Find interactions by doctor name.
- get_interaction_history(interaction_id) — Get full details of a specific interaction.
- create_follow_up(interaction_id, follow_up_note: str) — Add a follow-up action.

RULES:
1. When user describes a meeting, call log_interaction ONCE with all extracted info. Do NOT ask for missing fields.
2. Use today's date as default.
3. When user says "search" or "find", call search_hcp. Do NOT call any other tool.
4. When user says "show me interaction X" or "get interaction X", call get_interaction_history.
5. When user corrects or says "actually", call edit_interaction.
6. When user says "follow-up" or "add follow-up", call create_follow_up.
7. Call ONLY ONE tool per request unless the user's request explicitly needs multiple steps.
8. Respond with a brief 1-line confirmation after tool calls.
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

    edit_keywords = ["edit", "actually", "correct", "change", "update", "wrong", "mistake", "sorry"]
    followup_keywords = ["follow-up", "follow up", "followup"]
    needs_id = any(kw in user_message.lower() for kw in edit_keywords + followup_keywords)
    has_id = any(word.startswith(("interaction", "id", "#")) for word in user_message.lower().split())
    if needs_id and not has_id and last_logged_id:
        user_message = f"{user_message} (Interaction ID: {last_logged_id})"

    truncated_history = history[-6:] if len(history) > 6 else history
    messages = [SystemMessage(content=system_prompt)] + truncated_history + [HumanMessage(content=user_message)]

    max_iterations = 3
    tool_results_all = []
    seen_calls = set()

    for i in range(max_iterations):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if not hasattr(response, "tool_calls") or not response.tool_calls:
            break

        for tc in response.tool_calls:
            tool_name = tc["name"]
            tool_args = dict(tc["args"])

            if tool_name in ("edit_interaction", "create_follow_up", "get_interaction_history"):
                aid = tool_args.get("interaction_id")
                if aid is not None and not isinstance(aid, int):
                    try:
                        tool_args["interaction_id"] = int(str(aid))
                    except (ValueError, TypeError):
                        if last_logged_id:
                            tool_args["interaction_id"] = last_logged_id
                        else:
                            tool_args.pop("interaction_id", None)
                if "interaction_id" not in tool_args and last_logged_id:
                    tool_args["interaction_id"] = last_logged_id

            if tool_name == "log_interaction":
                raw = tool_args.get("interaction_data", "")
                if isinstance(raw, str):
                    try:
                        json.loads(raw)
                    except json.JSONDecodeError:
                        continue

            call_key = f"{tool_name}:{json.dumps(tool_args, sort_keys=True)}"
            if call_key in seen_calls:
                continue
            seen_calls.add(call_key)

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

    successful = [tc for tc in tool_results_all if '"status": "success"' in str(tc.get("result", ""))]
    errors = [tc for tc in tool_results_all if '"status": "error"' in str(tc.get("result", ""))]
    
    if successful:
        last_tool = successful[-1]
        tname = last_tool["tool"]
        if tname == "log_interaction":
            try:
                rid = json.loads(last_tool["result"]).get("interaction_id")
                ai_response = f"Interaction #{rid} logged successfully."
            except:
                ai_response = "Interaction logged successfully."
        elif tname == "edit_interaction":
            ai_response = "Interaction updated successfully."
        elif tname == "search_hcp":
            try:
                data = json.loads(last_tool["result"]).get("data", [])
                ai_response = f"Found {len(data)} interaction(s)."
            except:
                ai_response = "Search complete."
        elif tname == "get_interaction_history":
            ai_response = "Interaction details retrieved."
        elif tname == "create_follow_up":
            ai_response = "Follow-up added successfully."
        else:
            ai_response = "Done."
    elif errors:
        ai_response = "Something went wrong. Try again."
    else:
        ai_response = "How can I help you?"

    return {
        "response": ai_response,
        "tool_calls": tool_results_all,
        "messages": [{"role": m.type, "content": m.content} for m in messages if isinstance(m, (HumanMessage, AIMessage)) and m.content]
    }
