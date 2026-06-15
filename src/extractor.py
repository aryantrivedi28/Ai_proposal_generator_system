"""Updated extractor with cost tracking"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from .models import ExtractedData, ProposalType
from .cost_tracker import CostTracker  # NEW

load_dotenv()

class TranscriptExtractor:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found")
        self.client = OpenAI(api_key=api_key)
        self.cost_tracker = CostTracker()  # NEW
        self.proposal_id = None  # NEW
    
    def set_proposal_id(self, proposal_id: str):  # NEW
        self.proposal_id = proposal_id
    
    def extract(self, transcript: str) -> ExtractedData:
        """Extract structured data with cost tracking"""
        
        prompt = f"""
        Extract proposal information from this meeting transcript.
        
        Transcript:
        {transcript[:4000]}
        
        Return a JSON object with these fields:
        {{
            "client_name": "name or null",
            "contact_person": "name or null",
            "email": "email or null",
            "phone": "phone or null",
            "proposal_type": "wedding/corporate/conference/vip/general",
            "event_name": "name or null",
            "event_date": "date or null",
            "venue": "location or null",
            "guest_count": number or null,
            "budget": "amount or null",
            "estimated_cost": "amount or null",
            "special_requirements": [],
            "services_requested": [],
            "timeline": "text or null",
            "key_notes": []
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract data. Return only JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Track cost (NEW)
            usage = response.usage
            cost = self.cost_tracker.record_usage(
                model="gpt-4o-mini",
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens,
                proposal_id=self.proposal_id,
                endpoint="extraction"
            )
            
            print(f"💰 API Cost: ${cost:.4f} ({usage.total_tokens} tokens)")
            
            extracted_json = json.loads(response.choices[0].message.content)
            return ExtractedData(**extracted_json)
            
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            return ExtractedData()