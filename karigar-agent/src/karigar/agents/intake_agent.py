"""
IntakeAgent: Parses user input and extracts structured material request data.
This is the FIRST agent in the workflow.
"""

import json
import os
import re
from typing import Any, Dict

from langchain_openai import ChatOpenAI

from karigar.memory.sql_memory import get_session
from karigar.schemas.models import Artisan, MaterialRequest
from karigar.schemas.state import KarigarState


class IntakeAgent:
    """
    Processes raw user input and creates structured material requests.
    """
    
    def __init__(self, llm: Any = None):
        """Initialize the agent.

        Args:
            llm: Optional injected LLM instance for testing.
        """
        if llm is not None:
            self.llm = llm
        else:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.llm = ChatOpenAI(
                    model="gpt-4",
                    temperature=0,
                    api_key=api_key
                )
            else:
                self.llm = None
    
    def process(self, state: KarigarState) -> dict:
        """
        Process the state and extract material request.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with updates to state
        """
        try:
            # Get the last user message
            messages = state.get("messages", [])
            if messages:
                last_message = messages[-1]
                if isinstance(last_message, dict):
                    user_input = last_message.get("content", "")
                else:
                    user_input = getattr(last_message, "content", str(last_message))
            else:
                user_input = ""

            user_input = user_input or ""
            if not user_input.strip():
                return {"status": "error", "error": "No input provided"}
            
            print(f"\n[IntakeAgent] Processing input: {user_input}")
            
            # Create prompt for LLM to extract structured data
            prompt = f"""
            You are a material request extraction assistant. 
            Extract structured information from the following request:
            
            "{user_input}"            
            Extract:
            1. material (type of material needed, e.g., cement, bricks, steel)
            2. quantity (numeric value)
            3. unit (e.g., kg, bags, pieces, tons)
            4. budget (numeric value in rupees, if mentioned)
            5. timeline (when needed, e.g., "3 days", "next week")
            6. location (city or area, if mentioned)
            
            Return ONLY a JSON object with these fields. If any field is not mentioned, use null.
            Example: {{'material': 'cement', 'quantity': 100, 'unit': 'kg', 'budget': 5000, 'timeline': '3 days', 'location': 'Delhi'}}
            
            JSON:
            """
            
            # Call LLM
            material_data: Dict[str, Any]
            if self.llm:
                response = self.llm.invoke(prompt)
                response_text = response.content.strip()
                print(f"[IntakeAgent] LLM response: {response_text}")

                try:
                    if "```json" in response_text:
                        response_text = response_text.split("```json", 1)[1].split("```", 1)[0]
                    elif "```" in response_text:
                        response_text = response_text.split("```", 1)[1].rsplit("```", 1)[0]
                    material_data = json.loads(response_text.strip())
                except json.JSONDecodeError as e:
                    print(f"[IntakeAgent] JSON parse error: {e}")
                    return {
                        "status": "error",
                        "error": "Failed to parse material request"
                    }
            else:
                material_data = self._fallback_extract(user_input)
            
            # Validate required fields
            if not material_data.get("material"):
                return {
                    "status": "error",
                    "error": "Material type not specified"
                }
            
            if not material_data.get("quantity"):
                return {
                    "status": "error",
                    "error": "Quantity not specified"
                }

            # Normalise data
            material = str(material_data.get("material", "")).lower()
            quantity = float(material_data.get("quantity", 0))
            unit = material_data.get("unit") or "units"
            budget = float(material_data.get("budget") or 0)
            timeline = material_data.get("timeline") or "ASAP"
            location = material_data.get("location") or state.get("artisan_location")
            
            # Save to database
            session = get_session()
            try:
                # Get or create artisan
                artisan_id = state.get("artisan_id")
                if not artisan_id:
                    # For MVP, use phone as ID
                    artisan_id = state.get("artisan_phone", "default-artisan")
                
                artisan = session.query(Artisan).filter_by(id=artisan_id).first()
                if not artisan:
                    artisan = Artisan(
                        id=artisan_id,
                        name=state.get("artisan_name", "Unknown"),
                        phone=state.get("artisan_phone", "0000000000"),
                        location=location
                    )
                    session.add(artisan)
                    session.commit()
                
                # Create material request
                material_request = MaterialRequest(
                    artisan_id=artisan_id,
                    material=material,
                    quantity=quantity,
                    unit=unit,
                    budget=budget,
                    timeline=timeline,
                    status="pending"
                )
                
                session.add(material_request)
                session.commit()
                session.refresh(material_request)
                
                request_id = material_request.id
                
                print(f"[IntakeAgent] Created request {request_id} for {material_data['material']}")
                
                # Return state updates
                return {
                    "material_request": {
                        "material": material,
                        "quantity": quantity,
                        "unit": unit,
                        "budget": budget,
                        "timeline": timeline,
                        "location": location
                    },
                    "request_id": request_id,
                    "artisan_id": artisan_id,
                    "status": "intake_complete"
                }
                
            except Exception as e:
                session.rollback()
                print(f"[IntakeAgent] Database error: {e}")
                return {
                    "status": "error",
                    "error": f"Database error: {str(e)}"
                }
            finally:
                session.close()
                
        except Exception as e:
            print(f"[IntakeAgent] Error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    @staticmethod
    def _fallback_extract(text: str) -> Dict[str, Any]:
        """Simple rule-based extractor when no LLM is available."""
        lowered = text.lower()

        # Materials keyword search
        materials = [
            "cement", "bricks", "steel", "sand", "tiles", "wood", "paint"
        ]
        material = next((m for m in materials if m in lowered), None)

        # Quantity and unit
        quantity = None
        unit = None
        quantity_match = re.search(r"(\d+(?:\.\d+)?)\s*(kg|kilograms?|bags?|tons?|pieces?|units?)?", lowered)
        if quantity_match:
            quantity = float(quantity_match.group(1))
            if quantity_match.group(2):
                raw_unit = quantity_match.group(2)
                unit_map = {
                    "kilogram": "kg",
                    "kilograms": "kg",
                    "kg": "kg",
                    "bag": "bags",
                    "bags": "bags",
                    "ton": "tons",
                    "tons": "tons",
                    "piece": "pieces",
                    "pieces": "pieces",
                    "unit": "units",
                    "units": "units"
                }
                unit = unit_map.get(raw_unit, raw_unit)

        # Budget
        budget = None
        budget_match = re.search(r"(?:budget|rs|rupees|₹)\s*(\d+(?:\.\d+)?)", lowered)
        if budget_match:
            budget = float(budget_match.group(1))

        # Timeline heuristics
        timeline_phrases = [
            "today", "tomorrow", "next week", "next month", "in 2 days", "in two days"
        ]
        timeline = next((phrase for phrase in timeline_phrases if phrase in lowered), None)

        # Location
        location = None
        location_match = re.search(r"in\s+([A-Za-z][A-Za-z\s]+)", text)
        if location_match:
            location = location_match.group(1).strip()
            for stop_word in [" by", " within", " for", " on", " at", " next", " this", ",", "."]:
                if stop_word in location:
                    location = location.split(stop_word)[0].strip()
                    break

        return {
            "material": material,
            "quantity": quantity,
            "unit": unit,
            "budget": budget,
            "timeline": timeline,
            "location": location
        }
