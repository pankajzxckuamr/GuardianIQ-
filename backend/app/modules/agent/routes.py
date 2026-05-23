from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.modules.agent.models import Agent
from app.modules.agent.schemas import AgentCreate, AgentUpdate, AgentResponse
from app.shared.responses import StandardResponse
from app.shared.response_utils import ResponseHelper

router = APIRouter(prefix="/api/agents", tags=["Agents"])

@router.post("/", response_model=StandardResponse[AgentResponse], status_code=status.HTTP_201_CREATED)
def create_agent(agent_in: AgentCreate, db: Session = Depends(get_db)):
    db_obj = Agent(**agent_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return ResponseHelper.success(
        message="Agent created successfully",
        data=AgentResponse.model_validate(db_obj).model_dump()
    )

@router.get("/", response_model=StandardResponse[List[AgentResponse]])
def get_agents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    agents = db.query(Agent).offset(skip).limit(limit).all()
    return ResponseHelper.success(
        message="Agents retrieved successfully",
        data=[AgentResponse.model_validate(a).model_dump() for a in agents]
    )

@router.get("/{agent_id}", response_model=StandardResponse[AgentResponse])
def get_agent(agent_id: int, db: Session = Depends(get_db)):
    db_obj = db.query(Agent).filter(Agent.id == agent_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Agent not found")
    return ResponseHelper.success(
        message="Agent retrieved successfully",
        data=AgentResponse.model_validate(db_obj).model_dump()
    )

@router.put("/{agent_id}", response_model=StandardResponse[AgentResponse])
def update_agent(agent_id: int, agent_in: AgentUpdate, db: Session = Depends(get_db)):
    db_obj = db.query(Agent).filter(Agent.id == agent_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    update_data = agent_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    db.commit()
    db.refresh(db_obj)
    return ResponseHelper.success(
        message="Agent updated successfully",
        data=AgentResponse.model_validate(db_obj).model_dump()
    )

@router.delete("/{agent_id}", response_model=StandardResponse[None])
def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    db_obj = db.query(Agent).filter(Agent.id == agent_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    db.delete(db_obj)
    db.commit()
    return ResponseHelper.success(
        message="Agent deleted successfully",
        data=None
    )
