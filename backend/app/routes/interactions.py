from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db, HCPInteraction
from app.models.schemas import (
    InteractionCreate, 
    InteractionResponse, 
    ChatMessage, 
    ChatResponse,
    EditInteractionRequest
)
from app.agent.langgraph_agent import process_message
from typing import List
import json

router = APIRouter()

@router.post("/chat", response_model=dict)
async def chat_with_agent(message: ChatMessage):
    try:
        result = process_message(message.message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/interactions", response_model=InteractionResponse)
async def create_interaction(interaction: InteractionCreate, db: Session = Depends(get_db)):
    db_interaction = HCPInteraction(**interaction.model_dump())
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction

@router.get("/interactions", response_model=List[InteractionResponse])
async def get_interactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    interactions = db.query(HCPInteraction).offset(skip).limit(limit).all()
    return interactions

@router.get("/interactions/{interaction_id}", response_model=InteractionResponse)
async def get_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = db.query(HCPInteraction).filter(HCPInteraction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction

@router.put("/interactions/{interaction_id}", response_model=InteractionResponse)
async def update_interaction(interaction_id: int, interaction: InteractionCreate, db: Session = Depends(get_db)):
    db_interaction = db.query(HCPInteraction).filter(HCPInteraction.id == interaction_id).first()
    if not db_interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    
    for key, value in interaction.model_dump().items():
        setattr(db_interaction, key, value)
    
    db.commit()
    db.refresh(db_interaction)
    return db_interaction

@router.delete("/interactions/{interaction_id}")
async def delete_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = db.query(HCPInteraction).filter(HCPInteraction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    
    db.delete(interaction)
    db.commit()
    return {"message": "Interaction deleted successfully"}

@router.get("/search/{hcp_name}")
async def search_hcp(hcp_name: str, db: Session = Depends(get_db)):
    interactions = db.query(HCPInteraction).filter(
        HCPInteraction.hcp_name.ilike(f"%{hcp_name}%")
    ).all()
    return interactions
