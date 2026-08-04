from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ToolCallTrace(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    output: Any


class AgentChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class AgentChatResponse(BaseModel):
    response: str
    tool_calls: List[ToolCallTrace] = []
    conversation_id: str
