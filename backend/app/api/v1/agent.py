from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import uuid
from app.database.session import get_db
from app.models.user import User
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.agents.planning_agent import PlanningAgent
from app.api.deps import get_current_user

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse)
def chat_with_agent(
    req: AgentChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent = PlanningAgent(db, current_user.id)
    response_text, tool_calls = agent.process_message(req.message)

    cid = req.conversation_id or str(uuid.uuid4())
    return AgentChatResponse(
        response=response_text,
        tool_calls=tool_calls,
        conversation_id=cid
    )
