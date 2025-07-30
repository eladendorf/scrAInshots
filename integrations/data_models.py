"""
Unified data models for integrating multiple data sources
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class DataSourceType(Enum):
    SCREENSHOT = "screenshot"
    MACOS_NOTE = "macos_note"
    OUTLOOK_EMAIL = "outlook_email"
    FIREFLIES_MEETING = "fireflies_meeting"


class ConceptCategory(Enum):
    PROJECT = "project"
    MEETING = "meeting"
    IDEA = "idea"
    TASK = "task"
    COMMUNICATION = "communication"
    RESEARCH = "research"
    PLANNING = "planning"
    REVIEW = "review"
    OTHER = "other"


@dataclass
class UnifiedTimelineItem:
    """Unified data structure for all timeline items"""
    id: str
    source_type: DataSourceType
    title: str
    content: str
    timestamp: datetime
    last_modified: datetime
    metadata: Dict[str, Any]
    extracted_concepts: List[str]
    concept_categories: List[ConceptCategory]
    related_items: List[str]  # IDs of related items
    
    # Source-specific fields
    source_id: str  # Original ID from the source system
    source_metadata: Dict[str, Any]  # Original metadata from source
    
    # Analysis fields
    summary: Optional[str] = None
    key_topics: List[str] = None
    sentiment: Optional[str] = None
    importance_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'source_type': self.source_type.value,
            'title': self.title,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'last_modified': self.last_modified.isoformat(),
            'metadata': self.metadata,
            'extracted_concepts': self.extracted_concepts,
            'concept_categories': [c.value for c in self.concept_categories],
            'related_items': self.related_items,
            'source_id': self.source_id,
            'source_metadata': self.source_metadata,
            'summary': self.summary,
            'key_topics': self.key_topics or [],
            'sentiment': self.sentiment,
            'importance_score': self.importance_score
        }


@dataclass
class ConceptCluster:
    """Represents a cluster of related concepts across time"""
    id: str
    name: str
    description: str
    concepts: List[str]
    timeline_items: List[str]  # IDs of timeline items
    time_range: tuple[datetime, datetime]
    importance_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'concepts': self.concepts,
            'timeline_items': self.timeline_items,
            'time_range': (self.time_range[0].isoformat(), self.time_range[1].isoformat()),
            'importance_score': self.importance_score
        }


@dataclass
class TimeWindow:
    """Represents a time window for grouping related items"""
    start: datetime
    end: datetime
    items: List[UnifiedTimelineItem]
    
    def add_item(self, item: UnifiedTimelineItem):
        self.items.append(item)
        
    def get_concepts(self) -> List[str]:
        """Get all unique concepts in this time window"""
        concepts = set()
        for item in self.items:
            concepts.update(item.extracted_concepts)
        return list(concepts)
    
    def get_sources(self) -> Dict[DataSourceType, int]:
        """Count items by source type"""
        source_counts = {}
        for item in self.items:
            source_counts[item.source_type] = source_counts.get(item.source_type, 0) + 1
        return source_counts