from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from sqlalchemy.orm import Session
from app.models.database import HCPInteraction, SessionLocal
from app.models.schemas import InteractionCreate
from datetime import datetime
import json

@tool
def log_interaction(interaction_data: str) -> str:
    """
    Log a new HCP interaction to the database. 
    Input should be a JSON string with interaction fields.
    Extracts doctor name, topics, sentiment, materials, outcomes, and follow-up actions.
    """
    try:
        data = json.loads(interaction_data) if isinstance(interaction_data, str) else interaction_data
        
        db = SessionLocal()
        try:
            interaction = HCPInteraction(
                hcp_name=data.get("hcp_name", "Unknown"),
                interaction_type=data.get("interaction_type", "Meeting"),
                date=data.get("date", datetime.now().strftime("%Y-%m-%d")),
                time=data.get("time", datetime.now().strftime("%H:%M")),
                attendees=data.get("attendees", ""),
                topics_discussed=data.get("topics_discussed", ""),
                voice_note_summary=data.get("voice_note_summary", ""),
                materials_shared=data.get("materials_shared", ""),
                samples_distributed=data.get("samples_distributed", ""),
                hcp_sentiment=data.get("hcp_sentiment", "Neutral"),
                outcomes=data.get("outcomes", ""),
                follow_up_actions=data.get("follow_up_actions", ""),
                raw_message=data.get("raw_message", "")
            )
            db.add(interaction)
            db.commit()
            db.refresh(interaction)
            
            result = {
                "status": "success",
                "interaction_id": interaction.id,
                "message": f"Interaction with {interaction.hcp_name} logged successfully",
                "data": {
                    "hcp_name": interaction.hcp_name,
                    "interaction_type": interaction.interaction_type,
                    "date": interaction.date,
                    "topics_discussed": interaction.topics_discussed,
                    "hcp_sentiment": interaction.hcp_sentiment,
                    "materials_shared": interaction.materials_shared,
                    "outcomes": interaction.outcomes,
                    "follow_up_actions": interaction.follow_up_actions
                }
            }
            return json.dumps(result)
        finally:
            db.close()
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@tool
def edit_interaction(interaction_id: int, field_name: str, field_value: str) -> str:
    """
    Edit an existing HCP interaction. 
    Provide the interaction ID, field name to edit, and new value.
    """
    try:
        db = SessionLocal()
        try:
            interaction = db.query(HCPInteraction).filter(HCPInteraction.id == interaction_id).first()
            if not interaction:
                return json.dumps({"status": "error", "message": f"Interaction {interaction_id} not found"})
            
            if hasattr(interaction, field_name):
                setattr(interaction, field_name, field_value)
                interaction.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(interaction)
                
                return json.dumps({
                    "status": "success",
                    "message": f"Field '{field_name}' updated successfully",
                    "interaction_id": interaction_id,
                    "field_name": field_name,
                    "field_value": field_value
                })
            else:
                return json.dumps({"status": "error", "message": f"Field '{field_name}' does not exist"})
        finally:
            db.close()
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@tool
def search_hcp(hcp_name: str) -> str:
    """
    Search for HCP interactions by doctor name.
    Returns all interactions matching the name.
    """
    try:
        db = SessionLocal()
        try:
            interactions = db.query(HCPInteraction).filter(
                HCPInteraction.hcp_name.ilike(f"%{hcp_name}%")
            ).all()
            
            if not interactions:
                return json.dumps({"status": "success", "message": f"No interactions found for {hcp_name}", "data": []})
            
            results = []
            for i in interactions:
                results.append({
                    "id": i.id,
                    "hcp_name": i.hcp_name,
                    "interaction_type": i.interaction_type,
                    "date": i.date,
                    "topics_discussed": i.topics_discussed,
                    "hcp_sentiment": i.hcp_sentiment,
                    "created_at": i.created_at.isoformat()
                })
            
            return json.dumps({
                "status": "success",
                "message": f"Found {len(results)} interactions for {hcp_name}",
                "data": results
            })
        finally:
            db.close()
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@tool
def get_interaction_history(interaction_id: int) -> str:
    """
    Get full details of a specific interaction by ID.
    """
    try:
        db = SessionLocal()
        try:
            interaction = db.query(HCPInteraction).filter(HCPInteraction.id == interaction_id).first()
            if not interaction:
                return json.dumps({"status": "error", "message": f"Interaction {interaction_id} not found"})
            
            return json.dumps({
                "status": "success",
                "data": {
                    "id": interaction.id,
                    "hcp_name": interaction.hcp_name,
                    "interaction_type": interaction.interaction_type,
                    "date": interaction.date,
                    "time": interaction.time,
                    "attendees": interaction.attendees,
                    "topics_discussed": interaction.topics_discussed,
                    "voice_note_summary": interaction.voice_note_summary,
                    "materials_shared": interaction.materials_shared,
                    "samples_distributed": interaction.samples_distributed,
                    "hcp_sentiment": interaction.hcp_sentiment,
                    "outcomes": interaction.outcomes,
                    "follow_up_actions": interaction.follow_up_actions,
                    "raw_message": interaction.raw_message,
                    "created_at": interaction.created_at.isoformat(),
                    "updated_at": interaction.updated_at.isoformat()
                }
            })
        finally:
            db.close()
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@tool
def create_follow_up(interaction_id: int, follow_up_note: str) -> str:
    """
    Create or update a follow-up action for an existing interaction.
    """
    try:
        db = SessionLocal()
        try:
            interaction = db.query(HCPInteraction).filter(HCPInteraction.id == interaction_id).first()
            if not interaction:
                return json.dumps({"status": "error", "message": f"Interaction {interaction_id} not found"})
            
            existing = interaction.follow_up_actions or ""
            interaction.follow_up_actions = f"{existing}\n- {follow_up_note}" if existing else follow_up_note
            interaction.updated_at = datetime.utcnow()
            db.commit()
            
            return json.dumps({
                "status": "success",
                "message": "Follow-up action added",
                "interaction_id": interaction_id,
                "follow_up_actions": interaction.follow_up_actions
            })
        finally:
            db.close()
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
