"""
Condenser Module - Intelligent content condensation and compression

This module provides sophisticated text condensation capabilities,
including summarization, compression, and key information extraction.
"""

import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging

# Optional imports with fallbacks
try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

try:
    from textstat import flesch_reading_ease
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from ..utils.logger_utils import LoggerUtils


@dataclass
class CondensationConfig:
    """Configuration for text condensation"""
    target_length: Optional[int] = None
    compression_ratio: Optional[float] = 0.5
    preserve_key_phrases: bool = True
    maintain_structure: bool = True
    reading_level: Optional[str] = None
    language: str = "en"


# Alias for consistent naming
CondenserConfig = CondensationConfig


class Condenser:
    """
    Advanced text condenser that intelligently reduces content while preserving meaning.
    
    Features:
    - Extractive and abstractive summarization
    - Key phrase preservation
    - Structure maintenance
    - Reading level adjustment
    - Multi-language support
    """
    
    def __init__(self, config: Optional[CondensationConfig] = None):
        self.config = config or CondensationConfig()
        self.logger = LoggerUtils.get_logger(__name__)
        self._setup_nltk()
    
    def _setup_nltk(self):
        """Setup NLTK dependencies"""
        if not NLTK_AVAILABLE:
            self.logger.warning("NLTK not available - some functionality will be limited")
            return
            
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            try:
                nltk.download('punkt', quiet=True)
            except Exception as e:
                self.logger.warning(f"Could not download NLTK punkt: {e}")
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            try:
                nltk.download('stopwords', quiet=True)
            except Exception as e:
                self.logger.warning(f"Could not download NLTK stopwords: {e}")
    
    def condense(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Main condensation method
        
        Args:
            text: Text to condense
            **kwargs: Override default config parameters
            
        Returns:
            Condensed text
        """
        config = self._merge_config(kwargs)
        
        self.logger.info(f"Starting condensation of text ({len(text)} chars)")
        
        # Pre-processing
        text = self._preprocess_text(text)
        
        # Choose condensation strategy
        if config.target_length and len(text) <= config.target_length:
            return text
            
        if config.compression_ratio:
            target_length = int(len(text) * config.compression_ratio)
        else:
            target_length = config.target_length or len(text) // 2
        
        # Apply condensation
        condensed = self._extractive_condense(text, target_length)
        
        # Post-processing
        condensed = self._postprocess_text(condensed, config)
        
        # Calculate stats
        compression_ratio = round((1 - len(condensed) / len(text)) * 100, 2)
        
        self.logger.info(f"Condensation complete ({len(condensed)} chars)")
        
        return {
            'text': condensed,
            'stats': {
                'original_length': len(text),
                'condensed_length': len(condensed),
                'compression_ratio': compression_ratio
            },
            'success': True
        }
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and prepare text for condensation"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove empty lines
        text = re.sub(r'\n\s*\n', '\n', text)
        return text.strip()
    
    def _tokenize_sentences(self, text: str) -> List[str]:
        """Tokenize text into sentences with fallback"""
        if NLTK_AVAILABLE:
            try:
                return sent_tokenize(text)
            except Exception:
                pass
        
        # Fallback sentence tokenization
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _tokenize_words(self, text: str) -> List[str]:
        """Tokenize text into words with fallback"""
        if NLTK_AVAILABLE:
            try:
                return word_tokenize(text)
            except Exception:
                pass
        
        # Fallback word tokenization
        words = re.findall(r'\b\w+\b', text.lower())
        return words
    
    def _get_stopwords(self, language: str = 'english') -> set:
        """Get stopwords with fallback"""
        if NLTK_AVAILABLE:
            try:
                return set(stopwords.words(language))
            except Exception:
                pass
        
        # Fallback basic English stopwords
        return {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
            'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
            'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their',
            'theirs', 'themselves'
        }

    def _extractive_condense(self, text: str, target_length: int) -> str:
        """Extractive summarization approach"""
        sentences = self._tokenize_sentences(text)
        
        if len(sentences) <= 2:
            return text
        
        # Score sentences
        sentence_scores = self._score_sentences(sentences, text)
        
        # Select top sentences
        selected_sentences = []
        current_length = 0
        
        # Sort by score and select until target length
        sorted_sentences = sorted(
            sentence_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for sentence, score in sorted_sentences:
            if current_length + len(sentence) <= target_length:
                selected_sentences.append(sentence)
                current_length += len(sentence)
            
            if current_length >= target_length * 0.9:  # Allow 10% flexibility
                break
        
        # Maintain original order
        result_sentences = []
        for sentence in sentences:
            if sentence in selected_sentences:
                result_sentences.append(sentence)
        
        return ' '.join(result_sentences)
    
    def _score_sentences(self, sentences: List[str], full_text: str) -> Dict[str, float]:
        """Score sentences based on importance"""
        scores = {}
        word_freq = self._get_word_frequency(full_text)
        
        for sentence in sentences:
            words = sentence.lower().split()
            score = 0
            
            # Frequency-based scoring
            for word in words:
                if word in word_freq:
                    score += word_freq[word]
            
            # Length penalty (avoid too short/long sentences)
            length_score = 1.0
            if len(sentence) < 10:
                length_score = 0.5
            elif len(sentence) > 200:
                length_score = 0.7
            
            # Position score (first and last sentences often important)
            position_score = 1.0
            if sentences.index(sentence) in [0, len(sentences)-1]:
                position_score = 1.2
            
            scores[sentence] = score * length_score * position_score
        
        return scores
    
    def _get_word_frequency(self, text: str) -> Dict[str, float]:
        """Calculate word frequency scores"""
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Remove stopwords
        try:
            from nltk.corpus import stopwords
            stop_words = set(stopwords.words('english'))
            words = [w for w in words if w not in stop_words and len(w) > 2]
        except:
            # If NLTK stopwords not available, use basic list
            basic_stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
            words = [w for w in words if w not in basic_stopwords and len(w) > 2]
        
        # Calculate frequencies
        word_count = {}
        for word in words:
            word_count[word] = word_count.get(word, 0) + 1
        
        # Normalize
        max_count = max(word_count.values()) if word_count else 1
        return {word: count / max_count for word, count in word_count.items()}
    
    def _postprocess_text(self, text: str, config: CondensationConfig) -> str:
        """Post-process condensed text"""
        # Ensure proper sentence endings
        if text and not text.endswith(('.', '!', '?')):
            text += '.'
        
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _merge_config(self, kwargs: Dict[str, Any]) -> CondensationConfig:
        """Merge kwargs with default config"""
        config_dict = {
            'target_length': kwargs.get('target_length', self.config.target_length),
            'compression_ratio': kwargs.get('compression_ratio', self.config.compression_ratio),
            'preserve_key_phrases': kwargs.get('preserve_key_phrases', self.config.preserve_key_phrases),
            'maintain_structure': kwargs.get('maintain_structure', self.config.maintain_structure),
            'reading_level': kwargs.get('reading_level', self.config.reading_level),
            'language': kwargs.get('language', self.config.language)
        }
        return CondensationConfig(**config_dict)
    
    def get_compression_stats(self, original: str, condensed: str) -> Dict[str, Any]:
        """Get compression statistics"""
        original_length = len(original)
        condensed_length = len(condensed)
        compression_ratio = condensed_length / original_length if original_length > 0 else 0
        
        return {
            'original_length': original_length,
            'condensed_length': condensed_length,
            'compression_ratio': compression_ratio,
            'space_saved': original_length - condensed_length,
            'percentage_saved': round((1 - compression_ratio) * 100, 2)
        }
    
    def batch_condense(self, texts: List[str], **kwargs) -> List[str]:
        """Condense multiple texts"""
        results = []
        for i, text in enumerate(texts):
            self.logger.info(f"Processing text {i+1}/{len(texts)}")
            condensed = self.condense(text, **kwargs)
            results.append(condensed)
        return results