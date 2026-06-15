"""Data models for the proposal generator"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ProposalType(str, Enum):
    WEDDING = "wedding"
    CORPORATE = "corporate"
    CONFERENCE = "conference"
    VIP = "vip"
    GENERAL = "general"

class ExtractedData(BaseModel):
    """Structured data extracted from transcript"""
    
    # Client Information
    client_name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    
    # Event Details
    proposal_type: ProposalType = ProposalType.GENERAL
    event_name: Optional[str] = None
    event_date: Optional[str] = None
    venue: Optional[str] = None
    guest_count: Optional[int] = None
    
    # Financial
    budget: Optional[str] = None
    estimated_cost: Optional[str] = None
    
    # Requirements
    special_requirements: List[str] = []
    services_requested: List[str] = []
    timeline: Optional[str] = None
    
    # Additional
    key_notes: List[str] = []
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "client_name": self.client_name,
            "contact_person": self.contact_person,
            "email": self.email,
            "phone": self.phone,
            "proposal_type": self.proposal_type,
            "event_name": self.event_name,
            "event_date": self.event_date,
            "venue": self.venue,
            "guest_count": self.guest_count,
            "budget": self.budget,
            "estimated_cost": self.estimated_cost,
            "special_requirements": self.special_requirements,
            "services_requested": self.services_requested,
            "timeline": self.timeline,
            "key_notes": self.key_notes
        }