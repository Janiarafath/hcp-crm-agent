from app.tools.hcp_tools import (
    log_interaction, 
    edit_interaction, 
    search_hcp, 
    get_interaction_history, 
    create_follow_up
)
from typing import TypedDict, Literal
import json
import os
import httpx
import re
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

tools = [log_interaction, edit_interaction, search_hcp, get_interaction_history, create_follow_up]
tools_map = {t.name: t for t in tools}

LLM_EXTRACT_PROMPT = """You extract structured data from CRM meeting descriptions.
Return ONLY a JSON object with these fields if the message describes a meeting:
- "tool": always "log_interaction"
- "args": { "hcp_name": string, "topics": string, "sentiment": "Positive"|"Neutral"|"Negative", "materials": string, "samples": "yes"|"no", "outcomes": string, "follow_up": string, "type": "Meeting"|"Call"|"Email" }

Sentiment: Positive if words like interested/great/positive/excited/good. Negative if concerned/negative/bad/worried. Otherwise Neutral.

If the message is NOT describing a meeting with a doctor/HCP, return empty JSON: {}"""

# ------- LangGraph State -------

class AgentState(TypedDict):
    user_message: str
    tool_name: str
    tool_args: dict
    tool_result: str
    response: str

# ------- Tool Routing (rule-based, no LLM) -------

def _route_tool(user_message: str):
    msg = user_message.lower()
    
    edit_kw = ["edit", "actually", "correct", "change", "update", "wrong", "mistake", "fix", "should be", "not correct", "not right"]
    follow_kw = ["follow-up", "follow up", "followup", "next step", "reminder"]
    search_kw = ["search", "find", "look up", "what do we have", "past interaction", "previous", "history of", "info on", "details on", "tell me about"]
    history_kw = ["last interaction", "last one", "pull up", "show details", "get details", "interaction details", "history of interaction"]
    meeting_kw = [" met ", " meeting", " visited", " talked to", "discussed with", "saw ", "spoke with", " called "]
    
    if any(k in msg for k in edit_kw):
        return "edit_interaction"
    if any(k in msg for k in follow_kw):
        return "create_follow_up"
    if re.search(r'(?:show|get|view)\s+(?:me\s+)?(?:interaction\s*)?#?\s*\d+', msg):
        return "get_interaction_history"
    if any(k in msg for k in history_kw):
        return "get_interaction_history"
    if any(k in msg for k in search_kw):
        return "search_hcp"
    if any(k in msg for k in meeting_kw):
        return "log_interaction"
    
    return None

def _extract_name(msg: str):
    m = re.search(r'(?:dr\.?\s*|doctor\s+)([A-Za-z]+)', msg, re.IGNORECASE)
    return m.group(0).strip() if m else None

def _extract_id(msg: str):
    m = re.search(r'(?:interaction\s*)?#?\s*(\d+)', msg)
    return int(m.group(1)) if m else None

def _llm_extract_meeting(messages, model="mistralai/mixtral-8x7b-instruct-v0.1", max_retries=2):
    """LLM used ONLY for entity extraction from meeting descriptions."""
    msgs = [{"role": "system", "content": LLM_EXTRACT_PROMPT}] + messages
    payload = {"model": model, "messages": msgs, "temperature": 0.1, "max_tokens": 512}
    
    for attempt in range(max_retries):
        for key_name, key_val in [("NVIDIA", NVIDIA_API_KEY), ("Groq", GROQ_API_KEY)]:
            if not key_val:
                continue
            base = "https://integrate.api.nvidia.com/v1" if key_name == "NVIDIA" else "https://api.groq.com/openai/v1"
            try:
                with httpx.Client(timeout=60.0) as client:
                    r = client.post(
                        f"{base}/chat/completions",
                        headers={"Authorization": f"Bearer {key_val}", "Content-Type": "application/json"},
                        json=payload
                    )
                    if r.status_code == 200:
                        text = r.json()["choices"][0]["message"]["content"]
                        m = re.search(r'\{.*\}', text, re.DOTALL)
                        if m:
                            clean = m.group(0).replace('\\_', '_').replace('\\n', '\n')
                            return json.loads(clean)
                    elif r.status_code == 429:
                        continue
            except:
                continue
    return None

def execute_tool(tool_name: str, tool_args: dict) -> str:
    tool = tools_map.get(tool_name)
    if not tool:
        return json.dumps({"status": "error", "message": f"Tool {tool_name} not found"})
    try:
        result = tool.invoke(tool_args)
        return result
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

# ------- LangGraph Nodes -------

_last_id = None

def node_route(state: AgentState) -> AgentState:
    tool_name = _route_tool(state["user_message"])
    return {"user_message": state["user_message"], "tool_name": tool_name or "none", "tool_args": {}, "tool_result": "", "response": ""}

def node_extract(state: AgentState) -> AgentState:
    if state["tool_name"] == "log_interaction":
        extracted = _llm_extract_meeting([{"role": "user", "content": state["user_message"]}])
        if extracted and extracted.get("tool") == "log_interaction":
            fields = {"hcp_name":"","topics":"","sentiment":"Neutral","materials":"","samples":"no","outcomes":"","follow_up":"","type":"Meeting"}
            fields.update(extracted.get("args", {}))
            return {**state, "tool_args": {"interaction_data": json.dumps(fields)}}
        return {**state, "tool_name": "none"}
    return state

def node_build_args(state: AgentState) -> AgentState:
    if state["tool_name"] == "none":
        return state
    global _last_id
    msg = state["user_message"]
    tname = state["tool_name"]
    targs = {}
    
    if tname == "search_hcp":
        targs = {"hcp_name": _extract_name(msg) or "Dr. Name"}
    elif tname == "get_interaction_history":
        aid = _extract_id(msg)
        if aid is None and _last_id:
            aid = _last_id
        if aid:
            targs = {"interaction_id": int(aid)}
        else:
            return {**state, "tool_name": "none", "response": "No interactions logged yet. Try logging a meeting first, or specify an ID like 'show interaction #119'."}
    elif tname == "edit_interaction":
        aid = _extract_id(msg)
        if aid is None and _last_id:
            aid = _last_id
        if not aid:
            return {**state, "tool_name": "none", "response": "Please specify which interaction to edit."}
        field = "sentiment"
        for kw in ["sentiment", "name", "topic", "material", "hcp_name", "topics"]:
            if kw in msg.lower():
                field = kw
                break
        m2 = re.search(r'(?:to|as|should be)\s+(\w+)', msg, re.IGNORECASE)
        value = m2.group(1) if m2 else ""
        targs = {"interaction_id": int(aid), "field_name": field, "field_value": value}
    elif tname == "create_follow_up":
        aid = _extract_id(msg)
        if aid is None and _last_id:
            aid = _last_id
        if not aid:
            return {**state, "tool_name": "none", "response": "Please specify which interaction to add a follow-up to."}
        m3 = re.search(r'(?:follow-up|follow up|followup)[:\s]*(.*)', msg, re.IGNORECASE)
        note = m3.group(1).strip() if m3 else msg
        targs = {"interaction_id": int(aid), "follow_up_note": note}
    
    return {**state, "tool_args": targs}

def node_execute(state: AgentState) -> AgentState:
    global _last_id
    result = execute_tool(state["tool_name"], state["tool_args"])
    
    if state["tool_name"] == "log_interaction":
        try:
            r = json.loads(result)
            if r.get("status") == "success":
                _last_id = r.get("interaction_id")
        except:
            pass
    
    return {**state, "tool_result": result}

def node_respond(state: AgentState) -> AgentState:
    if state.get("response"):
        return state
    
    result_str = state["tool_result"]
    
    if not result_str:
        response = "How can I help you? Try describing a meeting, searching for an HCP, or editing an interaction."
    elif '"status": "success"' in result_str:
        tname = state["tool_name"]
        try:
            data = json.loads(result_str)
            if tname == "log_interaction":
                response = f"Interaction #{data.get('interaction_id', '?')} logged successfully."
            elif tname == "edit_interaction":
                response = "Interaction updated successfully."
            elif tname == "search_hcp":
                response = f"Found {len(data.get('data', []))} past interaction(s)."
            elif tname == "get_interaction_history":
                response = "Interaction details retrieved."
            elif tname == "create_follow_up":
                response = "Follow-up added successfully."
            else:
                response = "Done."
        except:
            response = "Done."
    else:
        try:
            response = f"Error: {json.loads(result_str).get('message', 'unknown')}"
        except:
            response = "An error occurred."
    
    return {**state, "response": response}

def router(state: AgentState) -> Literal["extract", "build_args", "execute", "respond"]:
    tn = state["tool_name"]
    if tn == "log_interaction" and not state["tool_args"]:
        return "extract"
    if tn == "none":
        return "respond"
    if tn != "" and state["tool_args"] and not state["tool_result"]:
        return "execute"
    if tn != "" and state["tool_result"] and not state["response"]:
        return "respond"
    return "build_args"

# ------- Build LangGraph Graph -------

try:
    from langgraph.graph import StateGraph, END
    
    workflow = StateGraph(AgentState)
    
    workflow.add_node("route", node_route)
    workflow.add_node("extract", node_extract)
    workflow.add_node("build_args", node_build_args)
    workflow.add_node("execute", node_execute)
    workflow.add_node("respond", node_respond)
    
    workflow.set_entry_point("route")
    
    for node in ["route", "extract", "build_args"]:
        workflow.add_conditional_edges(node, router, {
            "extract": "extract",
            "build_args": "build_args",
            "execute": "execute",
            "respond": "respond"
        })
    
    workflow.add_edge("execute", "respond")
    workflow.add_edge("respond", END)
    
    langgraph_app = workflow.compile()
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    langgraph_app = None

# ------- Public API -------

def process_message(user_message: str, history: list = None) -> dict:
    global _last_id
    initial = AgentState(
        user_message=user_message,
        tool_name="",
        tool_args={},
        tool_result="",
        response=""
    )
    
    if LANGGRAPH_AVAILABLE and langgraph_app:
        final = langgraph_app.invoke(initial)
        resp = final.get("response", "How can I help you?")
        tc = []
        if final.get("tool_name") and final["tool_name"] != "none" and final.get("tool_result"):
            tc.append({
                "tool": final["tool_name"],
                "args": final.get("tool_args", {}),
                "result": final.get("tool_result", "")
            })
        return {"response": resp, "tool_calls": tc, "messages": [{"role": "user", "content": user_message}]}
    else:
        tool_name = _route_tool(user_message)
        if not tool_name:
            return {"response": "How can I help you? Try describing a meeting, searching for an HCP, or editing an interaction.", "tool_calls": [], "messages": [{"role": "user", "content": user_message}]}
        
        args = {}
        result = ""
        
        if tool_name == "log_interaction":
            extracted = _llm_extract_meeting([{"role": "user", "content": user_message}])
            if extracted and extracted.get("tool") == "log_interaction":
                fields = {"hcp_name":"","topics":"","sentiment":"Neutral","materials":"","samples":"no","outcomes":"","follow_up":"","type":"Meeting"}
                fields.update(extracted.get("args", {}))
                args = {"interaction_data": json.dumps(fields)}
                result = execute_tool("log_interaction", args)
                try:
                    r = json.loads(result)
                    if r.get("status") == "success":
                        _last_id = r.get("interaction_id")
                except:
                    pass
        
        if result and '"status": "success"' in result:
            try:
                data = json.loads(result)
                response = f"Interaction #{data.get('interaction_id', '?')} logged successfully."
            except:
                response = "Done."
        elif not result:
            response = "How can I help you?"
        else:
            response = f"Error: {json.loads(result).get('message', 'unknown')}"
        
        return {"response": response, "tool_calls": [{"tool": tool_name, "args": args, "result": result}] if result else [], "messages": [{"role": "user", "content": user_message}]}