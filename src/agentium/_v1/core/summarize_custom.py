"""
Custom Summarizer Module - Custom summaries per user need

This module provides advanced summarization capabilities with
customizable parameters and multiple summarization strategies.
"""

import re
import json
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import statistics
from collections import Counter
import heapq
from datetime import datetime

from ..utils.logger_utils import LoggerUtils


class SummaryType(Enum):
    """Types of summaries"""
    EXTRACTIVE = "extractive"
    ABSTRACTIVE = "abstractive"
    BULLET_POINTS = "bullet_points"
    KEYWORD = "keyword"
    STATISTICAL = "statistical"
    ENTITY_FOCUSED = "entity_focused"
    TIMELINE = "timeline"
    COMPARATIVE = "comparative"


class SummaryLength(Enum):
    """Summary length presets"""
    BRIEF = "brief"      # 1-2 sentences
    SHORT = "short"      # 3-5 sentences
    MEDIUM = "medium"    # 1-2 paragraphs
    LONG = "long"        # 3+ paragraphs
    CUSTOM = "custom"    # User-defined length


@dataclass
class SummaryConfig:
    """Configuration for summarization"""
    summary_type: SummaryType = SummaryType.EXTRACTIVE
    length: SummaryLength = SummaryLength.MEDIUM
    max_sentences: Optional[int] = None
    max_words: Optional[int] = None
    focus_keywords: List[str] = None
    preserve_order: bool = True
    include_statistics: bool = False
    custom_weights: Dict[str, float] = None
    language: str = "en"


class CustomSummarizer:
    """
    Advanced custom summarization system.
    
    Features:
    - Multiple summarization strategies
    - Customizable length and focus
    - Entity and keyword-based summaries
    - Statistical summaries
    - Timeline extraction
    - Comparative analysis
    - User preference learning
    """
    
    def __init__(self, config: Optional[SummaryConfig] = None):
        self.config = config or SummaryConfig()
        self.logger = LoggerUtils.get_logger(__name__)
        self.user_preferences: Dict[str, Dict] = {}
        self._setup_summarizers()
    
    def _setup_summarizers(self):
        """Setup summarization strategies"""
        self.summarizers = {
            SummaryType.EXTRACTIVE: self._extractive_summary,
            SummaryType.ABSTRACTIVE: self._abstractive_summary,
            SummaryType.BULLET_POINTS: self._bullet_point_summary,
            SummaryType.KEYWORD: self._keyword_summary,
            SummaryType.STATISTICAL: self._statistical_summary,
            SummaryType.ENTITY_FOCUSED: self._entity_focused_summary,
            SummaryType.TIMELINE: self._timeline_summary,
            SummaryType.COMPARATIVE: self._comparative_summary,
        }
    
    @LoggerUtils.log_operation("create_summary")
    def summarize(self, content: Union[str, List[str], Dict], **kwargs) -> Dict[str, Any]:
        """
        Create a summary of the content
        
        Args:
            content: Content to summarize
            **kwargs: Override configuration parameters
            
        Returns:
            Summary with metadata
        """
        config = self._merge_config(kwargs)
        user_id = kwargs.get('user_id')
        
        # Apply user preferences if available
        if user_id and user_id in self.user_preferences:
            config = self._apply_user_preferences(config, user_id)
        
        self.logger.info(f"Creating {config.summary_type.value} summary")
        
        # Preprocess content
        processed_content = self._preprocess_content(content)
        
        # Generate summary using specified strategy
        summarizer_func = self.summarizers[config.summary_type]
        summary_result = summarizer_func(processed_content, config)
        
        # Post-process and format
        formatted_summary = self._format_summary(summary_result, config)
        
        # Add metadata
        metadata = self._generate_metadata(content, formatted_summary, config)
        
        result = {
            'summary': formatted_summary,
            'type': config.summary_type.value,
            'length': config.length.value,
            'word_count': len(formatted_summary.split()) if isinstance(formatted_summary, str) else 0,
            'compression_ratio': metadata.get('compression_ratio', 0),
            'metadata': metadata,
            'config_used': self._config_to_dict(config)
        }
        
        # Learn from user interaction if user_id provided
        if user_id:
            self._update_user_preferences(user_id, config, result)
        
        return result
    
    def _preprocess_content(self, content: Union[str, List[str], Dict]) -> str:
        """Preprocess content for summarization"""
        if isinstance(content, str):
            return self._clean_text(content)
        elif isinstance(content, list):
            # Join list items
            return self._clean_text(' '.join(str(item) for item in content))
        elif isinstance(content, dict):
            # Extract text from dictionary
            text_parts = []
            for key, value in content.items():
                if isinstance(value, str):
                    text_parts.append(f"{key}: {value}")
                elif isinstance(value, (list, dict)):
                    text_parts.append(f"{key}: {json.dumps(value, default=str)}")
                else:
                    text_parts.append(f"{key}: {str(value)}")
            return self._clean_text(' '.join(text_parts))
        else:
            return str(content)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:()-]', '', text)
        
        return text.strip()
    
    def _extractive_summary(self, content: str, config: SummaryConfig) -> str:
        """Create extractive summary by selecting key sentences"""
        sentences = self._split_sentences(content)
        
        if len(sentences) <= 2:
            return content
        
        # Score sentences
        sentence_scores = self._score_sentences(sentences, content, config)
        
        # Determine number of sentences to include
        target_sentences = self._get_target_sentence_count(sentences, config)
        
        # Select top sentences
        top_sentences = heapq.nlargest(target_sentences, sentence_scores.items(), key=lambda x: x[1])
        
        if config.preserve_order:
            # Maintain original order
            selected_sentences = []
            for sentence in sentences:
                if any(sentence == s[0] for s in top_sentences):
                    selected_sentences.append(sentence)
        else:
            selected_sentences = [s[0] for s in top_sentences]
        
        return ' '.join(selected_sentences)
    
    def _abstractive_summary(self, content: str, config: SummaryConfig) -> str:
        """Create abstractive summary (simplified implementation)"""
        # This is a simplified version - in production, you'd use advanced NLP models
        sentences = self._split_sentences(content)
        
        # Extract key phrases and concepts
        key_phrases = self._extract_key_phrases(content, config)
        key_concepts = self._extract_key_concepts(content, config)
        
        # Create new sentences based on key information
        summary_parts = []
        
        if key_concepts:
            summary_parts.append(f"The main topics discussed include {', '.join(key_concepts[:3])}.")
        
        if key_phrases:
            summary_parts.append(f"Key points mentioned are {', '.join(key_phrases[:3])}.")
        
        # Add statistical information if needed
        if config.include_statistics:
            word_count = len(content.split())
            sentence_count = len(sentences)
            summary_parts.append(f"The content contains {word_count} words across {sentence_count} sentences.")
        
        return ' '.join(summary_parts) if summary_parts else self._extractive_summary(content, config)
    
    def _bullet_point_summary(self, content: str, config: SummaryConfig) -> str:
        """Create bullet point summary"""
        sentences = self._split_sentences(content)
        sentence_scores = self._score_sentences(sentences, content, config)
        
        target_points = min(self._get_target_sentence_count(sentences, config), 10)
        top_sentences = heapq.nlargest(target_points, sentence_scores.items(), key=lambda x: x[1])
        
        bullet_points = []
        for sentence, score in top_sentences:
            # Simplify sentence for bullet point
            simplified = self._simplify_sentence(sentence)
            bullet_points.append(f"• {simplified}")
        
        return '\n'.join(bullet_points)
    
    def _keyword_summary(self, content: str, config: SummaryConfig) -> str:
        """Create keyword-based summary"""
        keywords = self._extract_keywords(content, config)
        key_phrases = self._extract_key_phrases(content, config)
        
        summary_parts = []
        
        if keywords:
            summary_parts.append(f"Keywords: {', '.join(keywords[:10])}")
        
        if key_phrases:
            summary_parts.append(f"Key Phrases: {', '.join(key_phrases[:5])}")
        
        # Add context sentences for top keywords
        if config.focus_keywords:
            focus_sentences = []
            sentences = self._split_sentences(content)
            
            for sentence in sentences:
                if any(keyword.lower() in sentence.lower() for keyword in config.focus_keywords):
                    focus_sentences.append(sentence)
                    if len(focus_sentences) >= 3:
                        break
            
            if focus_sentences:
                summary_parts.append(f"Related content: {' '.join(focus_sentences)}")
        
        return '\n'.join(summary_parts)
    
    def _statistical_summary(self, content: str, config: SummaryConfig) -> str:
        """Create statistical summary of content"""
        words = content.split()
        sentences = self._split_sentences(content)
        paragraphs = content.split('\n\n')
        
        # Calculate statistics
        stats = {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'paragraph_count': len([p for p in paragraphs if p.strip()]),
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
            'unique_words': len(set(word.lower() for word in words if word.isalpha())),
        }
        
        # Most common words (excluding stop words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        filtered_words = [word.lower() for word in words if word.isalpha() and word.lower() not in stop_words]
        word_freq = Counter(filtered_words)
        
        summary_parts = [
            f"Content Statistics:",
            f"• {stats['word_count']} words, {stats['sentence_count']} sentences, {stats['paragraph_count']} paragraphs",
            f"• Average sentence length: {stats['avg_sentence_length']:.1f} words",
            f"• Vocabulary diversity: {stats['unique_words']} unique words",
        ]
        
        if word_freq:
            top_words = word_freq.most_common(5)
            summary_parts.append(f"• Most frequent words: {', '.join([f'{word} ({count})' for word, count in top_words])}")
        
        return '\n'.join(summary_parts)
    
    def _entity_focused_summary(self, content: str, config: SummaryConfig) -> str:
        """Create entity-focused summary"""
        # Simple named entity extraction
        entities = self._extract_entities(content)
        
        summary_parts = []
        
        if entities:
            by_type = {}
            for entity in entities:
                entity_type = entity.get('type', 'UNKNOWN')
                if entity_type not in by_type:
                    by_type[entity_type] = []
                by_type[entity_type].append(entity['text'])
            
            for entity_type, entity_list in by_type.items():
                unique_entities = list(set(entity_list))[:5]  # Top 5 unique entities per type
                summary_parts.append(f"{entity_type}: {', '.join(unique_entities)}")
        
        # Add context for entities
        sentences = self._split_sentences(content)
        entity_sentences = []
        
        for sentence in sentences:
            if entities and any(entity['text'].lower() in sentence.lower() for entity in entities):
                entity_sentences.append(sentence)
                if len(entity_sentences) >= 3:
                    break
        
        if entity_sentences:
            summary_parts.append(f"Context: {' '.join(entity_sentences)}")
        
        return '\n'.join(summary_parts) if summary_parts else "No significant entities found."
    
    def _timeline_summary(self, content: str, config: SummaryConfig) -> str:
        """Create timeline-based summary"""
        # Extract temporal references
        temporal_patterns = [
            r'\b(19|20)\d{2}\b',  # Years
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+(19|20)?\d{2}\b',  # Dates
            r'\b(first|then|next|later|finally|after|before|during)\b',  # Temporal indicators
            r'\b(yesterday|today|tomorrow|now|currently)\b',  # Relative time
        ]
        
        temporal_events = []
        sentences = self._split_sentences(content)
        
        for sentence in sentences:
            for pattern in temporal_patterns:
                matches = re.findall(pattern, sentence, re.IGNORECASE)
                if matches:
                    temporal_events.append({
                        'sentence': sentence,
                        'temporal_markers': matches
                    })
                    break
        
        if temporal_events:
            timeline_summary = "Timeline of Events:\n"
            for i, event in enumerate(temporal_events[:5]):  # Limit to 5 events
                timeline_summary += f"{i+1}. {event['sentence']}\n"
            return timeline_summary.strip()
        
        return "No clear temporal structure found in the content."
    
    def _comparative_summary(self, content: str, config: SummaryConfig) -> str:
        """Create comparative summary highlighting contrasts"""
        # Look for comparative language
        comparative_patterns = [
            r'(however|but|although|whereas|while|in contrast|on the other hand|conversely)',
            r'(better|worse|more|less|higher|lower|greater|smaller)',
            r'(versus|vs\.|compared to|in comparison|relative to)',
        ]
        
        comparative_sentences = []
        sentences = self._split_sentences(content)
        
        for sentence in sentences:
            if any(re.search(pattern, sentence, re.IGNORECASE) for pattern in comparative_patterns):
                comparative_sentences.append(sentence)
        
        if comparative_sentences:
            return f"Comparative Analysis:\n" + '\n'.join(f"• {sentence}" for sentence in comparative_sentences[:5])
        
        return "No significant comparative content found."
    
    # Helper methods
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _score_sentences(self, sentences: List[str], full_text: str, config: SummaryConfig) -> Dict[str, float]:
        """Score sentences based on importance"""
        scores = {}
        
        # Word frequency analysis
        words = re.findall(r'\b\w+\b', full_text.lower())
        word_freq = Counter(words)
        
        # Remove stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        
        for sentence in sentences:
            sentence_words = re.findall(r'\b\w+\b', sentence.lower())
            
            # Base score from word frequency
            score = sum(word_freq.get(word, 0) for word in sentence_words if word not in stop_words)
            
            # Position bonus (first and last sentences often important)
            position = sentences.index(sentence)
            if position == 0 or position == len(sentences) - 1:
                score *= 1.2
            
            # Length penalty for very short or very long sentences
            length = len(sentence_words)
            if length < 5:
                score *= 0.5
            elif length > 30:
                score *= 0.8
            
            # Focus keyword bonus
            if config.focus_keywords:
                keyword_matches = sum(1 for keyword in config.focus_keywords if keyword.lower() in sentence.lower())
                score *= (1 + keyword_matches * 0.5)
            
            # Custom weights
            if config.custom_weights:
                for term, weight in config.custom_weights.items():
                    if term.lower() in sentence.lower():
                        score *= weight
            
            scores[sentence] = score
        
        return scores
    
    def _get_target_sentence_count(self, sentences: List[str], config: SummaryConfig) -> int:
        """Determine target number of sentences for summary"""
        if config.max_sentences:
            return min(config.max_sentences, len(sentences))
        
        if config.length == SummaryLength.BRIEF:
            return min(2, len(sentences))
        elif config.length == SummaryLength.SHORT:
            return min(5, len(sentences))
        elif config.length == SummaryLength.MEDIUM:
            return min(len(sentences) // 3, 10)
        elif config.length == SummaryLength.LONG:
            return min(len(sentences) // 2, 15)
        else:  # CUSTOM or default
            return min(len(sentences) // 4, 8)
    
    def _extract_key_phrases(self, content: str, config: SummaryConfig) -> List[str]:
        """Extract key phrases from content"""
        # Simple n-gram extraction
        words = re.findall(r'\b\w+\b', content.lower())
        
        # Extract 2-grams and 3-grams
        phrases = []
        
        # 2-grams
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            phrases.append(phrase)
        
        # 3-grams
        for i in range(len(words) - 2):
            phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
            phrases.append(phrase)
        
        # Count and filter phrases
        phrase_freq = Counter(phrases)
        
        # Filter out common phrases
        stop_phrases = {'of the', 'in the', 'to the', 'and the', 'for the', 'is a', 'are a', 'was a', 'were a'}
        
        key_phrases = [phrase for phrase, freq in phrase_freq.most_common(20) if phrase not in stop_phrases and freq > 1]
        
        return key_phrases[:10]
    
    def _extract_key_concepts(self, content: str, config: SummaryConfig) -> List[str]:
        """Extract key concepts from content"""
        # Simple concept extraction based on word frequency and patterns
        words = re.findall(r'\b[A-Z][a-z]+\b', content)  # Capitalized words
        
        # Filter common words
        concepts = [word for word in words if len(word) > 3]
        concept_freq = Counter(concepts)
        
        return [concept for concept, freq in concept_freq.most_common(10) if freq > 1]
    
    def _extract_keywords(self, content: str, config: SummaryConfig) -> List[str]:
        """Extract keywords from content"""
        words = re.findall(r'\b\w+\b', content.lower())
        
        # Filter stop words and short words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
        word_freq = Counter(filtered_words)
        
        return [word for word, freq in word_freq.most_common(20) if freq > 1]
    
    def _extract_entities(self, content: str) -> List[Dict[str, str]]:
        """Simple entity extraction"""
        entities = []
        
        # Simple patterns for different entity types
        patterns = {
            'PERSON': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            'ORGANIZATION': r'\b[A-Z][a-zA-Z\s&.,]+(?:Inc|LLC|Corp|Ltd|Company)\b',
            'LOCATION': r'\b[A-Z][a-z]+(?:,\s[A-Z]{2})?\b',
            'DATE': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            'MONEY': r'\$\d+(?:,\d{3})*(?:\.\d{2})?\b',
        }
        
        for entity_type, pattern in patterns.items():
            matches = re.findall(pattern, content)
            for match in matches:
                entities.append({'text': match, 'type': entity_type})
        
        return entities
    
    def _simplify_sentence(self, sentence: str) -> str:
        """Simplify sentence for bullet points"""
        # Remove unnecessary words and phrases
        simplified = sentence
        
        # Remove introductory phrases
        simplified = re.sub(r'^(It is|There is|There are|This is|That is)\s+', '', simplified)
        
        # Remove filler words
        filler_words = ['very', 'really', 'quite', 'rather', 'extremely']
        for filler in filler_words:
            simplified = re.sub(rf'\b{filler}\s+', '', simplified)
        
        return simplified.strip()
    
    def _format_summary(self, summary: str, config: SummaryConfig) -> str:
        """Format summary according to configuration"""
        if config.max_words:
            words = summary.split()
            if len(words) > config.max_words:
                summary = ' '.join(words[:config.max_words]) + '...'
        
        return summary.strip()
    
    def _generate_metadata(self, original_content: Union[str, List, Dict], summary: str, config: SummaryConfig) -> Dict[str, Any]:
        """Generate metadata about the summarization"""
        original_text = self._preprocess_content(original_content)
        
        original_words = len(original_text.split())
        summary_words = len(summary.split()) if isinstance(summary, str) else 0
        
        compression_ratio = summary_words / original_words if original_words > 0 else 0
        
        return {
            'original_word_count': original_words,
            'summary_word_count': summary_words,
            'compression_ratio': compression_ratio,
            'compression_percentage': (1 - compression_ratio) * 100,
            'original_sentence_count': len(self._split_sentences(original_text)),
            'summary_sentence_count': len(self._split_sentences(summary)) if isinstance(summary, str) else 0,
        }
    
    def _apply_user_preferences(self, config: SummaryConfig, user_id: str) -> SummaryConfig:
        """Apply user preferences to configuration"""
        preferences = self.user_preferences[user_id]
        
        # Update config based on preferences
        if 'preferred_length' in preferences:
            config.length = SummaryLength(preferences['preferred_length'])
        
        if 'preferred_type' in preferences:
            config.summary_type = SummaryType(preferences['preferred_type'])
        
        if 'focus_keywords' in preferences:
            config.focus_keywords = preferences['focus_keywords']
        
        return config
    
    def _update_user_preferences(self, user_id: str, config: SummaryConfig, result: Dict[str, Any]):
        """Update user preferences based on usage"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {'usage_count': 0}
        
        prefs = self.user_preferences[user_id]
        prefs['usage_count'] += 1
        prefs['last_used_type'] = config.summary_type.value
        prefs['last_used_length'] = config.length.value
        
        # Simple preference learning (could be enhanced with ML)
        if 'preferred_type' not in prefs:
            prefs['preferred_type'] = config.summary_type.value
        
        if 'preferred_length' not in prefs:
            prefs['preferred_length'] = config.length.value
    
    def _config_to_dict(self, config: SummaryConfig) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            'summary_type': config.summary_type.value,
            'length': config.length.value,
            'max_sentences': config.max_sentences,
            'max_words': config.max_words,
            'focus_keywords': config.focus_keywords,
            'preserve_order': config.preserve_order,
            'include_statistics': config.include_statistics,
            'custom_weights': config.custom_weights,
            'language': config.language
        }
    
    def _merge_config(self, kwargs: Dict[str, Any]) -> SummaryConfig:
        """Merge kwargs with default config"""
        config_dict = {
            'summary_type': kwargs.get('summary_type', self.config.summary_type),
            'length': kwargs.get('length', self.config.length),
            'max_sentences': kwargs.get('max_sentences', self.config.max_sentences),
            'max_words': kwargs.get('max_words', self.config.max_words),
            'focus_keywords': kwargs.get('focus_keywords', self.config.focus_keywords),
            'preserve_order': kwargs.get('preserve_order', self.config.preserve_order),
            'include_statistics': kwargs.get('include_statistics', self.config.include_statistics),
            'custom_weights': kwargs.get('custom_weights', self.config.custom_weights),
            'language': kwargs.get('language', self.config.language)
        }
        return SummaryConfig(**config_dict)
    
    def create_custom_template(self, name: str, template_config: Dict[str, Any]) -> str:
        """Create a custom summary template"""
        # This would allow users to create reusable summary configurations
        template_id = f"template_{name}_{int(datetime.now().timestamp())}"
        
        # Store template (in production, this would be persisted)
        # For now, just return the template ID
        
        self.logger.info(f"Created summary template: {name}")
        return template_id
    
    def get_summary_recommendations(self, content: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get recommendations for best summary type and configuration"""
        content_analysis = {
            'word_count': len(content.split()),
            'sentence_count': len(self._split_sentences(content)),
            'has_temporal_elements': bool(re.search(r'\b(19|20)\d{2}\b', content)),
            'has_entities': bool(re.search(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', content)),
            'has_comparisons': bool(re.search(r'(however|but|versus|compared)', content, re.IGNORECASE)),
            'has_statistics': bool(re.search(r'\d+%|\d+,\d+|\$\d+', content)),
        }
        
        recommendations = {
            'suggested_type': SummaryType.EXTRACTIVE,
            'suggested_length': SummaryLength.MEDIUM,
            'reasoning': [],
            'alternatives': []
        }
        
        # Logic for recommendations based on content analysis
        if content_analysis['has_temporal_elements']:
            recommendations['suggested_type'] = SummaryType.TIMELINE
            recommendations['reasoning'].append("Content contains temporal elements")
            recommendations['alternatives'].append(SummaryType.EXTRACTIVE)
        
        if content_analysis['has_entities']:
            if recommendations['suggested_type'] == SummaryType.EXTRACTIVE:
                recommendations['suggested_type'] = SummaryType.ENTITY_FOCUSED
                recommendations['reasoning'].append("Content is rich in named entities")
        
        if content_analysis['has_comparisons']:
            recommendations['alternatives'].append(SummaryType.COMPARATIVE)
        
        if content_analysis['has_statistics']:
            recommendations['alternatives'].append(SummaryType.STATISTICAL)
        
        # Length recommendations
        if content_analysis['word_count'] < 100:
            recommendations['suggested_length'] = SummaryLength.BRIEF
        elif content_analysis['word_count'] > 1000:
            recommendations['suggested_length'] = SummaryLength.LONG
        
        # User preference consideration
        if user_id and user_id in self.user_preferences:
            prefs = self.user_preferences[user_id]
            recommendations['user_preference'] = {
                'type': prefs.get('preferred_type'),
                'length': prefs.get('preferred_length')
            }
        
        return recommendations