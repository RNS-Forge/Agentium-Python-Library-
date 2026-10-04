"""
Rearranger Module - Organize content logically

This module provides content organization and restructuring capabilities
for better logical flow and readability.
"""

import re
import json
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import networkx as nx

from ..utils.logger_utils import LoggerUtils


class ContentType(Enum):
    """Types of content that can be rearranged"""
    TEXT = "text"
    LIST = "list"
    JSON = "json"
    CODE = "code"
    OUTLINE = "outline"


class ArrangementStrategy(Enum):
    """Strategies for content arrangement"""
    CHRONOLOGICAL = "chronological"
    IMPORTANCE = "importance"
    LOGICAL_FLOW = "logical_flow"
    COMPLEXITY = "complexity"
    ALPHABETICAL = "alphabetical"
    FREQUENCY = "frequency"
    DEPENDENCY = "dependency"


@dataclass
class RearrangerConfig:
    """Configuration for content rearrangement"""
    content_type: ContentType = ContentType.TEXT
    strategy: ArrangementStrategy = ArrangementStrategy.LOGICAL_FLOW
    preserve_structure: bool = True
    group_related: bool = True
    add_transitions: bool = True
    custom_order: List[str] = None


class Rearranger:
    """
    Advanced content rearranger for logical organization.
    
    Features:
    - Multiple arrangement strategies
    - Content type recognition
    - Logical flow optimization
    - Dependency-based ordering
    - Structure preservation
    - Transition generation
    """
    
    def __init__(self, config: Optional[RearrangerConfig] = None):
        self.config = config or RearrangerConfig()
        self.logger = LoggerUtils.get_logger(__name__)
    
    @LoggerUtils.log_operation("rearrange_content")
    def rearrange(self, content: Union[str, List, Dict], **kwargs) -> Union[str, List, Dict]:
        """
        Main rearrangement method
        
        Args:
            content: Content to rearrange
            **kwargs: Override configuration parameters
            
        Returns:
            Rearranged content
        """
        config = self._merge_config(kwargs)
        
        # Detect content type if not specified
        if 'content_type' not in kwargs:
            config.content_type = self._detect_content_type(content)
        
        self.logger.info(f"Rearranging {config.content_type.value} content using {config.strategy.value} strategy")
        
        if config.content_type == ContentType.TEXT:
            return self._rearrange_text(content, config)
        elif config.content_type == ContentType.LIST:
            return self._rearrange_list(content, config)
        elif config.content_type == ContentType.JSON:
            return self._rearrange_json(content, config)
        elif config.content_type == ContentType.CODE:
            return self._rearrange_code(content, config)
        elif config.content_type == ContentType.OUTLINE:
            return self._rearrange_outline(content, config)
        else:
            raise ValueError(f"Unsupported content type: {config.content_type}")
    
    def _detect_content_type(self, content: Union[str, List, Dict]) -> ContentType:
        """Automatically detect content type"""
        if isinstance(content, list):
            return ContentType.LIST
        elif isinstance(content, dict):
            return ContentType.JSON
        elif isinstance(content, str):
            # Check for code patterns
            if self._is_code(content):
                return ContentType.CODE
            # Check for outline patterns
            elif self._is_outline(content):
                return ContentType.OUTLINE
            else:
                return ContentType.TEXT
        else:
            return ContentType.TEXT
    
    def _is_code(self, content: str) -> bool:
        """Check if content appears to be code"""
        code_indicators = [
            r'def\s+\w+\s*\(',  # Python functions
            r'function\s+\w+\s*\(',  # JavaScript functions
            r'class\s+\w+\s*[:{]',  # Class definitions
            r'import\s+\w+',  # Import statements
            r'#include\s*<',  # C/C++ includes
            r'[{}();]',  # Common code punctuation
        ]
        
        return any(re.search(pattern, content) for pattern in code_indicators)
    
    def _is_outline(self, content: str) -> bool:
        """Check if content appears to be an outline"""
        outline_patterns = [
            r'^\s*[\d]+\.',  # Numbered lists
            r'^\s*[a-zA-Z]\.',  # Lettered lists
            r'^\s*[-*+]\s',  # Bullet points
            r'^\s*#{1,6}\s',  # Markdown headers
        ]
        
        lines = content.split('\n')
        outline_lines = sum(1 for line in lines 
                          if any(re.match(pattern, line) for pattern in outline_patterns))
        
        return outline_lines / len(lines) > 0.3 if lines else False
    
    def _rearrange_text(self, text: str, config: RearrangerConfig) -> str:
        """Rearrange text content"""
        if config.strategy == ArrangementStrategy.LOGICAL_FLOW:
            return self._arrange_by_logical_flow(text, config)
        elif config.strategy == ArrangementStrategy.IMPORTANCE:
            return self._arrange_by_importance(text, config)
        elif config.strategy == ArrangementStrategy.CHRONOLOGICAL:
            return self._arrange_chronologically(text, config)
        elif config.strategy == ArrangementStrategy.COMPLEXITY:
            return self._arrange_by_complexity(text, config)
        else:
            return text
    
    def _arrange_by_logical_flow(self, text: str, config: RearrangerConfig) -> str:
        """Arrange text by logical flow"""
        paragraphs = self._split_into_paragraphs(text)
        
        if len(paragraphs) <= 1:
            return text
        
        # Analyze relationships between paragraphs
        relationships = self._analyze_paragraph_relationships(paragraphs)
        
        # Build dependency graph
        graph = self._build_dependency_graph(paragraphs, relationships)
        
        # Find optimal order
        ordered_paragraphs = self._topological_sort(graph, paragraphs)
        
        # Add transitions if requested
        if config.add_transitions:
            ordered_paragraphs = self._add_transitions(ordered_paragraphs, relationships)
        
        return '\n\n'.join(ordered_paragraphs)
    
    def _arrange_by_importance(self, text: str, config: RearrangerConfig) -> str:
        """Arrange text by importance score"""
        paragraphs = self._split_into_paragraphs(text)
        
        # Score paragraphs by importance
        scored_paragraphs = []
        for paragraph in paragraphs:
            score = self._calculate_importance_score(paragraph, text)
            scored_paragraphs.append((paragraph, score))
        
        # Sort by score (highest first)
        scored_paragraphs.sort(key=lambda x: x[1], reverse=True)
        
        # Extract paragraphs in order
        ordered_paragraphs = [p[0] for p in scored_paragraphs]
        
        return '\n\n'.join(ordered_paragraphs)
    
    def _arrange_chronologically(self, text: str, config: RearrangerConfig) -> str:
        """Arrange text chronologically"""
        paragraphs = self._split_into_paragraphs(text)
        
        # Extract temporal indicators
        timestamped_paragraphs = []
        for paragraph in paragraphs:
            timestamp = self._extract_temporal_info(paragraph)
            timestamped_paragraphs.append((paragraph, timestamp))
        
        # Sort by timestamp
        timestamped_paragraphs.sort(key=lambda x: x[1] if x[1] is not None else float('inf'))
        
        # Extract paragraphs in chronological order
        ordered_paragraphs = [p[0] for p in timestamped_paragraphs]
        
        return '\n\n'.join(ordered_paragraphs)
    
    def _arrange_by_complexity(self, text: str, config: RearrangerConfig) -> str:
        """Arrange text by complexity (simple to complex)"""
        paragraphs = self._split_into_paragraphs(text)
        
        # Calculate complexity scores
        scored_paragraphs = []
        for paragraph in paragraphs:
            complexity = self._calculate_complexity_score(paragraph)
            scored_paragraphs.append((paragraph, complexity))
        
        # Sort by complexity (lowest first)
        scored_paragraphs.sort(key=lambda x: x[1])
        
        # Extract paragraphs in order
        ordered_paragraphs = [p[0] for p in scored_paragraphs]
        
        return '\n\n'.join(ordered_paragraphs)
    
    def _rearrange_list(self, items: List, config: RearrangerConfig) -> List:
        """Rearrange list items"""
        if config.strategy == ArrangementStrategy.ALPHABETICAL:
            return sorted(items, key=lambda x: str(x).lower())
        elif config.strategy == ArrangementStrategy.FREQUENCY:
            # This would require frequency analysis context
            return items
        elif config.strategy == ArrangementStrategy.IMPORTANCE:
            # Score items by importance (simplified)
            if isinstance(items[0], str):
                scored_items = [(item, len(item)) for item in items]
                scored_items.sort(key=lambda x: x[1], reverse=True)
                return [item[0] for item in scored_items]
        
        return items
    
    def _rearrange_json(self, data: Dict, config: RearrangerConfig) -> Dict:
        """Rearrange JSON structure"""
        if config.strategy == ArrangementStrategy.ALPHABETICAL:
            return dict(sorted(data.items()))
        elif config.strategy == ArrangementStrategy.IMPORTANCE:
            # Sort by value complexity/size
            scored_items = []
            for key, value in data.items():
                score = self._calculate_json_importance(key, value)
                scored_items.append((key, value, score))
            
            scored_items.sort(key=lambda x: x[2], reverse=True)
            return {item[0]: item[1] for item in scored_items}
        
        return data
    
    def _rearrange_code(self, code: str, config: RearrangerConfig) -> str:
        """Rearrange code structure"""
        if config.strategy == ArrangementStrategy.DEPENDENCY:
            return self._arrange_code_by_dependencies(code)
        elif config.strategy == ArrangementStrategy.LOGICAL_FLOW:
            return self._arrange_code_by_flow(code)
        
        return code
    
    def _rearrange_outline(self, outline: str, config: RearrangerConfig) -> str:
        """Rearrange outline structure"""
        lines = outline.split('\n')
        
        # Parse outline structure
        outline_items = self._parse_outline_structure(lines)
        
        # Rearrange based on strategy
        if config.strategy == ArrangementStrategy.LOGICAL_FLOW:
            outline_items = self._arrange_outline_logically(outline_items)
        elif config.strategy == ArrangementStrategy.IMPORTANCE:
            outline_items = self._arrange_outline_by_importance(outline_items)
        
        # Reconstruct outline
        return self._reconstruct_outline(outline_items)
    
    # Helper methods
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs"""
        paragraphs = re.split(r'\n\s*\n', text.strip())
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _analyze_paragraph_relationships(self, paragraphs: List[str]) -> Dict[Tuple[int, int], float]:
        """Analyze relationships between paragraphs"""
        relationships = {}
        
        for i, para1 in enumerate(paragraphs):
            for j, para2 in enumerate(paragraphs):
                if i != j:
                    # Calculate semantic similarity (simplified)
                    similarity = self._calculate_semantic_similarity(para1, para2)
                    relationships[(i, j)] = similarity
        
        return relationships
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between texts (simplified)"""
        # Get word sets
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        # Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0
    
    def _build_dependency_graph(self, paragraphs: List[str], relationships: Dict[Tuple[int, int], float]) -> nx.DiGraph:
        """Build dependency graph for paragraphs"""
        G = nx.DiGraph()
        
        # Add nodes
        for i in range(len(paragraphs)):
            G.add_node(i)
        
        # Add edges based on relationships
        threshold = 0.3  # Similarity threshold for dependencies
        for (i, j), similarity in relationships.items():
            if similarity > threshold:
                # Determine direction based on content analysis
                if self._should_precede(paragraphs[i], paragraphs[j]):
                    G.add_edge(i, j, weight=similarity)
                else:
                    G.add_edge(j, i, weight=similarity)
        
        return G
    
    def _should_precede(self, para1: str, para2: str) -> bool:
        """Determine if paragraph 1 should precede paragraph 2"""
        # Look for introduction/conclusion indicators
        intro_words = ['first', 'initially', 'begin', 'start', 'introduction']
        conclusion_words = ['finally', 'conclusion', 'summary', 'end', 'last']
        
        para1_lower = para1.lower()
        para2_lower = para2.lower()
        
        # Check for intro/conclusion indicators
        if any(word in para1_lower for word in intro_words):
            return True
        if any(word in para2_lower for word in conclusion_words):
            return True
        if any(word in para2_lower for word in intro_words):
            return False
        if any(word in para1_lower for word in conclusion_words):
            return False
        
        # Default: shorter paragraph first (often introductory)
        return len(para1) < len(para2)
    
    def _topological_sort(self, graph: nx.DiGraph, paragraphs: List[str]) -> List[str]:
        """Perform topological sort on dependency graph"""
        try:
            ordered_indices = list(nx.topological_sort(graph))
            return [paragraphs[i] for i in ordered_indices]
        except nx.NetworkXError:
            # Handle cycles by using original order
            self.logger.warning("Cycle detected in dependency graph, using original order")
            return paragraphs
    
    def _add_transitions(self, paragraphs: List[str], relationships: Dict[Tuple[int, int], float]) -> List[str]:
        """Add transition phrases between paragraphs"""
        transitions = [
            "Furthermore,", "Moreover,", "Additionally,", "However,", 
            "On the other hand,", "In contrast,", "Similarly,", 
            "As a result,", "Consequently,", "Therefore,"
        ]
        
        result = []
        for i, paragraph in enumerate(paragraphs):
            if i > 0:
                # Add appropriate transition based on relationship
                # Simplified: just add "Additionally," for now
                result.append(f"Additionally, {paragraph}")
            else:
                result.append(paragraph)
        
        return result
    
    def _calculate_importance_score(self, paragraph: str, full_text: str) -> float:
        """Calculate importance score for a paragraph"""
        score = 0.0
        
        # Length factor
        score += len(paragraph) * 0.01
        
        # Keyword density
        keywords = ['important', 'key', 'main', 'primary', 'essential', 'critical']
        for keyword in keywords:
            score += paragraph.lower().count(keyword) * 0.5
        
        # Position factor (first and last paragraphs often important)
        paragraphs = self._split_into_paragraphs(full_text)
        if paragraph == paragraphs[0] or paragraph == paragraphs[-1]:
            score += 1.0
        
        return score
    
    def _extract_temporal_info(self, text: str) -> Optional[int]:
        """Extract temporal information from text (simplified)"""
        # Look for years
        year_match = re.search(r'\b(19|20)\d{2}\b', text)
        if year_match:
            return int(year_match.group())
        
        # Look for temporal words and assign rough order
        temporal_indicators = {
            'first': 1, 'initially': 1, 'beginning': 1,
            'then': 2, 'next': 2, 'after': 2,
            'later': 3, 'subsequently': 3,
            'finally': 4, 'lastly': 4, 'conclusion': 4
        }
        
        text_lower = text.lower()
        for indicator, order in temporal_indicators.items():
            if indicator in text_lower:
                return order
        
        return None
    
    def _calculate_complexity_score(self, text: str) -> float:
        """Calculate complexity score for text"""
        score = 0.0
        
        # Sentence length
        sentences = re.split(r'[.!?]', text)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        score += avg_sentence_length * 0.1
        
        # Word complexity (simplified)
        words = text.split()
        long_words = [w for w in words if len(w) > 6]
        score += len(long_words) / len(words) if words else 0
        
        # Technical terms (simplified)
        technical_patterns = [r'\b[A-Z]{2,}\b', r'\b\w+ly\b', r'\b\w+tion\b']
        for pattern in technical_patterns:
            matches = re.findall(pattern, text)
            score += len(matches) * 0.1
        
        return score
    
    def _calculate_json_importance(self, key: str, value: Any) -> float:
        """Calculate importance score for JSON key-value pair"""
        score = 0.0
        
        # Key importance
        important_keys = ['id', 'name', 'title', 'type', 'status', 'priority']
        if key.lower() in important_keys:
            score += 2.0
        
        # Value complexity
        if isinstance(value, dict):
            score += len(value) * 0.1
        elif isinstance(value, list):
            score += len(value) * 0.05
        elif isinstance(value, str):
            score += len(value) * 0.001
        
        return score
    
    def _arrange_code_by_dependencies(self, code: str) -> str:
        """Arrange code by dependencies (simplified)"""
        # This would require proper AST parsing
        return code
    
    def _arrange_code_by_flow(self, code: str) -> str:
        """Arrange code by logical flow (simplified)"""
        # This would require proper AST parsing
        return code
    
    def _parse_outline_structure(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Parse outline structure"""
        items = []
        for line in lines:
            if not line.strip():
                continue
            
            level = self._get_outline_level(line)
            content = self._clean_outline_content(line)
            items.append({'level': level, 'content': content, 'original': line})
        
        return items
    
    def _get_outline_level(self, line: str) -> int:
        """Get outline level from line"""
        # Count leading spaces/tabs
        indent = len(line) - len(line.lstrip())
        
        # Check for numbered/lettered lists
        if re.match(r'^\s*\d+\.', line):
            return 1
        elif re.match(r'^\s*[a-z]\.', line):
            return 2
        elif re.match(r'^\s*[i]+\.', line):
            return 3
        elif re.match(r'^\s*[-*+]', line):
            return max(1, indent // 2)
        elif re.match(r'^\s*#{1,6}', line):
            return len(re.match(r'^\s*(#{1,6})', line).group(1))
        
        return max(1, indent // 2)
    
    def _clean_outline_content(self, line: str) -> str:
        """Clean outline content"""
        # Remove outline markers
        cleaned = re.sub(r'^\s*[\d.a-z.i.#*+-]\s*', '', line)
        return cleaned.strip()
    
    def _arrange_outline_logically(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Arrange outline items logically"""
        # Group by level and sort within each level
        return items  # Simplified
    
    def _arrange_outline_by_importance(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Arrange outline items by importance"""
        # Sort by importance score
        for item in items:
            item['importance'] = self._calculate_outline_importance(item['content'])
        
        # Sort within each level
        items.sort(key=lambda x: (x['level'], -x['importance']))
        return items
    
    def _calculate_outline_importance(self, content: str) -> float:
        """Calculate importance score for outline item"""
        score = 0.0
        
        # Length
        score += len(content) * 0.01
        
        # Important words
        important_words = ['main', 'key', 'important', 'primary', 'essential']
        for word in important_words:
            if word.lower() in content.lower():
                score += 0.5
        
        return score
    
    def _reconstruct_outline(self, items: List[Dict[str, Any]]) -> str:
        """Reconstruct outline from items"""
        lines = []
        for item in items:
            # Reconstruct with proper indentation and markers
            indent = '  ' * (item['level'] - 1)
            marker = f"{len(lines) + 1}." if item['level'] == 1 else '-'
            lines.append(f"{indent}{marker} {item['content']}")
        
        return '\n'.join(lines)
    
    def _merge_config(self, kwargs: Dict[str, Any]) -> RearrangerConfig:
        """Merge kwargs with default config"""
        config_dict = {
            'content_type': kwargs.get('content_type', self.config.content_type),
            'strategy': kwargs.get('strategy', self.config.strategy),
            'preserve_structure': kwargs.get('preserve_structure', self.config.preserve_structure),
            'group_related': kwargs.get('group_related', self.config.group_related),
            'add_transitions': kwargs.get('add_transitions', self.config.add_transitions),
            'custom_order': kwargs.get('custom_order', self.config.custom_order)
        }
        return RearrangerConfig(**config_dict)
    
    def get_arrangement_stats(self, original: Union[str, List, Dict], 
                            rearranged: Union[str, List, Dict]) -> Dict[str, Any]:
        """Get rearrangement statistics"""
        stats = {
            'original_type': type(original).__name__,
            'rearranged_type': type(rearranged).__name__,
            'strategy_used': self.config.strategy.value,
            'content_type': self.config.content_type.value,
        }
        
        if isinstance(original, str) and isinstance(rearranged, str):
            stats.update({
                'original_paragraphs': len(self._split_into_paragraphs(original)),
                'rearranged_paragraphs': len(self._split_into_paragraphs(rearranged)),
                'character_count_change': len(rearranged) - len(original),
            })
        elif isinstance(original, list) and isinstance(rearranged, list):
            stats.update({
                'original_items': len(original),
                'rearranged_items': len(rearranged),
                'order_changed': original != rearranged,
            })
        
        return stats