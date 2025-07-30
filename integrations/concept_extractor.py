"""
Concept extraction and categorization using LLM
"""
import re
import json
import logging
from typing import List, Dict, Any, Set, Tuple
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from .data_models import UnifiedTimelineItem, ConceptCategory, ConceptCluster, TimeWindow

logger = logging.getLogger(__name__)


class ConceptExtractor:
    """Extract and analyze concepts from timeline items"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client  # Can be LM Studio or local LLM client
        
        # Common stop words to filter out
        self.stop_words = {
            'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but',
            'in', 'with', 'to', 'for', 'of', 'as', 'by', 'that', 'this',
            'it', 'from', 'be', 'are', 'been', 'was', 'were', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'shall'
        }
        
        # Keywords for categorization
        self.category_keywords = {
            ConceptCategory.PROJECT: ['project', 'initiative', 'program', 'development', 'implementation'],
            ConceptCategory.MEETING: ['meeting', 'discussion', 'call', 'conference', 'presentation'],
            ConceptCategory.IDEA: ['idea', 'concept', 'proposal', 'suggestion', 'innovation'],
            ConceptCategory.TASK: ['task', 'todo', 'action', 'assignment', 'deadline'],
            ConceptCategory.COMMUNICATION: ['email', 'message', 'response', 'question', 'answer'],
            ConceptCategory.RESEARCH: ['research', 'analysis', 'study', 'investigation', 'finding'],
            ConceptCategory.PLANNING: ['plan', 'strategy', 'roadmap', 'timeline', 'milestone'],
            ConceptCategory.REVIEW: ['review', 'feedback', 'evaluation', 'assessment', 'retrospective']
        }
    
    def extract_concepts_from_text(self, text: str, use_llm: bool = True) -> List[str]:
        """Extract key concepts from text"""
        concepts = []
        
        if use_llm and self.llm_client:
            # Use LLM for intelligent concept extraction
            concepts = self._llm_extract_concepts(text)
        else:
            # Fallback to rule-based extraction
            concepts = self._rule_based_extraction(text)
        
        return concepts
    
    def _llm_extract_concepts(self, text: str) -> List[str]:
        """Use LLM to extract concepts"""
        try:
            prompt = f"""Extract the main concepts, topics, and entities from the following text.
Return only the key concepts as a comma-separated list. Focus on:
- Project names
- Technology terms
- People names
- Company names
- Important topics
- Key actions or decisions

Text: {text[:2000]}  # Limit text length

Concepts:"""
            
            # This would call your LLM client
            # response = self.llm_client.generate(prompt)
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"LLM concept extraction failed: {e}")
            return self._rule_based_extraction(text)
    
    def _rule_based_extraction(self, text: str) -> List[str]:
        """Rule-based concept extraction"""
        # Convert to lowercase and split into words
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        # Filter out stop words and short words
        meaningful_words = [w for w in words if len(w) > 3 and w not in self.stop_words]
        
        # Count word frequency
        word_freq = Counter(meaningful_words)
        
        # Extract top concepts based on frequency
        concepts = []
        for word, freq in word_freq.most_common(20):
            if freq > 1:  # Word appears more than once
                concepts.append(word)
        
        # Also extract capitalized words (potential proper nouns)
        capitalized = re.findall(r'\b[A-Z][a-zA-Z]+\b', text)
        for word in set(capitalized):
            if word.lower() not in self.stop_words and word.lower() not in concepts:
                concepts.append(word)
        
        return concepts[:15]  # Limit to top 15 concepts
    
    def categorize_item(self, item: UnifiedTimelineItem) -> List[ConceptCategory]:
        """Categorize a timeline item based on its content"""
        categories = []
        
        # Combine title and content for analysis
        full_text = f"{item.title} {item.content}".lower()
        
        # Check for category keywords
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in full_text:
                    categories.append(category)
                    break
        
        # Add source-specific categories
        if item.source_type.value == 'fireflies_meeting':
            if ConceptCategory.MEETING not in categories:
                categories.append(ConceptCategory.MEETING)
        elif item.source_type.value == 'outlook_email':
            if ConceptCategory.COMMUNICATION not in categories:
                categories.append(ConceptCategory.COMMUNICATION)
        
        # Default to OTHER if no categories found
        if not categories:
            categories.append(ConceptCategory.OTHER)
        
        return categories
    
    def analyze_timeline_items(self, items: List[UnifiedTimelineItem]) -> List[UnifiedTimelineItem]:
        """Analyze all timeline items and extract concepts"""
        for item in items:
            # Extract concepts
            concepts = self.extract_concepts_from_text(f"{item.title} {item.content}")
            item.extracted_concepts = concepts
            
            # Categorize
            categories = self.categorize_item(item)
            item.concept_categories = categories
            
            # Calculate importance score based on various factors
            item.importance_score = self._calculate_importance(item)
        
        return items
    
    def _calculate_importance(self, item: UnifiedTimelineItem) -> float:
        """Calculate importance score for an item"""
        score = 0.0
        
        # Factor 1: Number of concepts
        score += min(len(item.extracted_concepts) * 0.1, 0.5)
        
        # Factor 2: Source type weights
        source_weights = {
            'fireflies_meeting': 0.3,
            'outlook_email': 0.2,
            'macos_note': 0.25,
            'screenshot': 0.15
        }
        score += source_weights.get(item.source_type.value, 0.1)
        
        # Factor 3: Has action items (for meetings)
        if item.metadata.get('has_action_items'):
            score += 0.2
        
        # Factor 4: Content length (normalized)
        content_length = len(item.content)
        if content_length > 1000:
            score += 0.1
        elif content_length > 500:
            score += 0.05
        
        return min(score, 1.0)  # Cap at 1.0
    
    def find_related_items(self, items: List[UnifiedTimelineItem], 
                          time_window_hours: int = 24) -> List[UnifiedTimelineItem]:
        """Find related items based on time proximity and concept overlap"""
        
        for i, item in enumerate(items):
            related = []
            
            for j, other_item in enumerate(items):
                if i == j:
                    continue
                
                # Check time proximity
                time_diff = abs((item.timestamp - other_item.timestamp).total_seconds() / 3600)
                if time_diff <= time_window_hours:
                    # Check concept overlap
                    common_concepts = set(item.extracted_concepts) & set(other_item.extracted_concepts)
                    if len(common_concepts) >= 2:  # At least 2 common concepts
                        related.append(other_item.id)
            
            item.related_items = related
        
        return items
    
    def create_concept_clusters(self, items: List[UnifiedTimelineItem]) -> List[ConceptCluster]:
        """Create clusters of related concepts across time"""
        
        # Group concepts by co-occurrence
        concept_graph = defaultdict(set)
        concept_items = defaultdict(set)
        
        for item in items:
            for concept in item.extracted_concepts:
                concept_items[concept].add(item.id)
                for other_concept in item.extracted_concepts:
                    if concept != other_concept:
                        concept_graph[concept].add(other_concept)
        
        # Find concept clusters using simple algorithm
        clusters = []
        processed_concepts = set()
        
        for concept, related_concepts in concept_graph.items():
            if concept in processed_concepts:
                continue
            
            # Create cluster with this concept and its most related concepts
            cluster_concepts = {concept}
            cluster_concepts.update(list(related_concepts)[:5])  # Top 5 related
            
            # Get all items that contain these concepts
            cluster_item_ids = set()
            for c in cluster_concepts:
                cluster_item_ids.update(concept_items[c])
            
            # Get time range
            cluster_items = [item for item in items if item.id in cluster_item_ids]
            if cluster_items:
                time_range = (
                    min(item.timestamp for item in cluster_items),
                    max(item.timestamp for item in cluster_items)
                )
                
                cluster = ConceptCluster(
                    id=f"cluster_{concept}_{len(clusters)}",
                    name=concept.title(),
                    description=f"Cluster around {concept} and related concepts",
                    concepts=list(cluster_concepts),
                    timeline_items=list(cluster_item_ids),
                    time_range=time_range,
                    importance_score=len(cluster_item_ids) / len(items)  # Simple importance
                )
                
                clusters.append(cluster)
                processed_concepts.update(cluster_concepts)
        
        return sorted(clusters, key=lambda x: x.importance_score, reverse=True)
    
    def create_time_windows(self, items: List[UnifiedTimelineItem], 
                           window_hours: int = 24) -> List[TimeWindow]:
        """Group items into time windows"""
        if not items:
            return []
        
        # Sort items by timestamp
        sorted_items = sorted(items, key=lambda x: x.timestamp)
        
        windows = []
        current_window = TimeWindow(
            start=sorted_items[0].timestamp,
            end=sorted_items[0].timestamp + timedelta(hours=window_hours),
            items=[sorted_items[0]]
        )
        
        for item in sorted_items[1:]:
            if item.timestamp <= current_window.end:
                current_window.add_item(item)
            else:
                windows.append(current_window)
                current_window = TimeWindow(
                    start=item.timestamp,
                    end=item.timestamp + timedelta(hours=window_hours),
                    items=[item]
                )
        
        windows.append(current_window)
        return windows