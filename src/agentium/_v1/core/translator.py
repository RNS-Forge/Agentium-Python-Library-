"""
Translator Module - Multi-language translation with tone adaptation

This module provides translation capabilities with tone and context awareness
for multi-language communication.
"""

import re
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from ..utils.logger_utils import LoggerUtils


class TranslationType(Enum):
    """Types of translation services"""
    BASIC = "basic"
    CONTEXTUAL = "contextual"
    TONE_AWARE = "tone_aware"
    TECHNICAL = "technical"


class ToneType(Enum):
    """Tone types for translation"""
    FORMAL = "formal"
    INFORMAL = "informal"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    TECHNICAL = "technical"
    MARKETING = "marketing"
    ACADEMIC = "academic"


@dataclass
class TranslationConfig:
    """Configuration for translation operations"""
    source_language: str = "auto"
    target_language: str = "en"
    translation_type: TranslationType = TranslationType.CONTEXTUAL
    tone: ToneType = ToneType.PROFESSIONAL
    preserve_formatting: bool = True
    include_confidence: bool = True
    batch_size: int = 100


# Alias for consistent naming
TranslatorConfig = TranslationConfig


class Translator:
    """
    Advanced multi-language translator with tone adaptation.
    
    Features:
    - Multi-language support
    - Tone adaptation
    - Context preservation
    - Technical term handling
    - Batch translation
    - Confidence scoring
    - Format preservation
    """
    
    def __init__(self, config: Optional[TranslationConfig] = None):
        self.config = config or TranslationConfig()
        self.logger = LoggerUtils.get_logger(__name__)
        self._setup_language_mappings()
        self._setup_tone_adjustments()
    
    def _setup_language_mappings(self):
        """Setup language code mappings"""
        self.language_codes = {
            'english': 'en', 'spanish': 'es', 'french': 'fr', 'german': 'de',
            'italian': 'it', 'portuguese': 'pt', 'russian': 'ru', 'chinese': 'zh',
            'japanese': 'ja', 'korean': 'ko', 'arabic': 'ar', 'hindi': 'hi',
            'dutch': 'nl', 'swedish': 'sv', 'norwegian': 'no', 'danish': 'da',
            'finnish': 'fi', 'polish': 'pl', 'czech': 'cs', 'hungarian': 'hu'
        }
        
        self.language_families = {
            'romance': ['es', 'fr', 'it', 'pt', 'ro'],
            'germanic': ['en', 'de', 'nl', 'sv', 'no', 'da'],
            'slavic': ['ru', 'pl', 'cs', 'sk', 'bg'],
            'sino_tibetan': ['zh', 'my'],
            'semitic': ['ar', 'he']
        }
    
    def _setup_tone_adjustments(self):
        """Setup tone adjustment patterns"""
        self.tone_patterns = {
            ToneType.FORMAL: {
                'replacements': {
                    "can't": "cannot",
                    "won't": "will not",
                    "don't": "do not",
                    "isn't": "is not",
                    "aren't": "are not"
                },
                'prefixes': ["Please note that", "It should be mentioned that"],
                'suffixes': ["Thank you for your attention", "We appreciate your understanding"]
            },
            ToneType.INFORMAL: {
                'replacements': {
                    "cannot": "can't",
                    "will not": "won't",
                    "do not": "don't"
                },
                'prefixes': ["Hey", "So", "By the way"],
                'suffixes': ["Hope this helps!", "Let me know!"]
            },
            ToneType.PROFESSIONAL: {
                'replacements': {
                    "very good": "excellent",
                    "bad": "suboptimal",
                    "problem": "challenge"
                },
                'prefixes': ["I would like to inform you that", "Please be advised that"],
                'suffixes': ["Best regards", "Thank you for your time"]
            },
            ToneType.FRIENDLY: {
                'replacements': {
                    "error": "oops",
                    "failure": "hiccup",
                    "problem": "little issue"
                },
                'prefixes': ["Hope you're doing well!", "Just wanted to let you know"],
                'suffixes': ["Have a great day!", "Talk soon!"]
            }
        }
    
    @LoggerUtils.log_operation("translate_text")
    def translate(self, text: str, target_language: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Translate text with tone adaptation
        
        Args:
            text: Text to translate
            target_language: Target language code
            **kwargs: Additional translation parameters
            
        Returns:
            Translation result with metadata
        """
        config = self._merge_config(kwargs)
        target_lang = target_language or config.target_language
        
        self.logger.info(f"Translating text to {target_lang}")
        
        # Detect source language if auto
        source_lang = config.source_language
        if source_lang == "auto":
            source_lang = self._detect_language(text)
        
        # Skip translation if source and target are the same
        if source_lang == target_lang:
            result = {
                'original_text': text,
                'translated_text': text,
                'source_language': source_lang,
                'target_language': target_lang,
                'confidence': 1.0,
                'translation_type': config.translation_type.value,
                'tone_applied': config.tone.value,
                'skipped': True,
                'reason': 'Same source and target language'
            }
            return result
        
        # Perform translation
        if config.translation_type == TranslationType.BASIC:
            translated = self._basic_translate(text, source_lang, target_lang)
        elif config.translation_type == TranslationType.CONTEXTUAL:
            translated = self._contextual_translate(text, source_lang, target_lang, config)
        elif config.translation_type == TranslationType.TONE_AWARE:
            translated = self._tone_aware_translate(text, source_lang, target_lang, config)
        elif config.translation_type == TranslationType.TECHNICAL:
            translated = self._technical_translate(text, source_lang, target_lang, config)
        else:
            translated = self._basic_translate(text, source_lang, target_lang)
        
        # Apply tone adjustments
        if config.tone != ToneType.PROFESSIONAL:  # Professional is default
            translated['translated_text'] = self._apply_tone(translated['translated_text'], config.tone, target_lang)
        
        # Preserve formatting if requested
        if config.preserve_formatting:
            translated['translated_text'] = self._preserve_formatting(text, translated['translated_text'])
        
        result = {
            'original_text': text,
            'translated_text': translated['translated_text'],
            'source_language': source_lang,
            'target_language': target_lang,
            'confidence': translated.get('confidence', 0.8),
            'translation_type': config.translation_type.value,
            'tone_applied': config.tone.value,
            'word_count': len(text.split()),
            'character_count': len(text),
            'skipped': False
        }
        
        return result
    
    def _detect_language(self, text: str) -> str:
        """Detect language of text (simplified implementation)"""
        # This is a very basic language detection
        # In production, you'd use a proper language detection library
        
        # Common words in different languages
        language_indicators = {
            'en': ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with'],
            'es': ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no'],
            'fr': ['le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir'],
            'de': ['der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich'],
            'it': ['il', 'di', 'che', 'e', 'la', 'per', 'in', 'un', 'è', 'le'],
            'pt': ['o', 'de', 'e', 'que', 'do', 'da', 'em', 'um', 'para', 'é'],
            'ru': ['в', 'и', 'не', 'на', 'я', 'быть', 'он', 'с', 'как', 'а'],
        }
        
        text_lower = text.lower()
        scores = {}
        
        for lang, indicators in language_indicators.items():
            score = sum(text_lower.count(indicator) for indicator in indicators)
            scores[lang] = score
        
        # Return language with highest score, default to English
        detected_lang = max(scores, key=scores.get) if scores else 'en'
        return detected_lang if scores[detected_lang] > 0 else 'en'
    
    def _basic_translate(self, text: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
        """Basic translation using dictionary approach (placeholder)"""
        # This is a placeholder for actual translation service integration
        # In production, you'd integrate with Google Translate, Azure Translator, etc.
        
        self.logger.warning("Using placeholder translation - integrate with actual translation service")
        
        # Simple word-by-word translation for demonstration
        basic_dictionary = {
            ('es', 'en'): {
                'hola': 'hello',
                'mundo': 'world',
                'gracias': 'thank you',
                'por favor': 'please',
                'sí': 'yes',
                'no': 'no'
            },
            ('fr', 'en'): {
                'bonjour': 'hello',
                'monde': 'world',
                'merci': 'thank you',
                's\'il vous plaît': 'please',
                'oui': 'yes',
                'non': 'no'
            }
        }
        
        dictionary = basic_dictionary.get((source_lang, target_lang), {})
        
        # Simple word replacement
        translated = text
        for source_word, target_word in dictionary.items():
            translated = re.sub(r'\b' + re.escape(source_word) + r'\b', target_word, translated, flags=re.IGNORECASE)
        
        return {
            'translated_text': translated,
            'confidence': 0.6,  # Low confidence for basic translation
            'method': 'dictionary'
        }
    
    def _contextual_translate(self, text: str, source_lang: str, target_lang: str, config: TranslationConfig) -> Dict[str, Any]:
        """Contextual translation with better understanding"""
        # Placeholder for contextual translation
        # This would use AI/ML models for better context understanding
        
        basic_result = self._basic_translate(text, source_lang, target_lang)
        
        # Apply some contextual improvements
        translated = basic_result['translated_text']
        
        # Improve sentence structure
        translated = self._improve_sentence_structure(translated, target_lang)
        
        # Handle idioms and expressions
        translated = self._handle_idioms(translated, source_lang, target_lang)
        
        return {
            'translated_text': translated,
            'confidence': 0.75,
            'method': 'contextual'
        }
    
    def _tone_aware_translate(self, text: str, source_lang: str, target_lang: str, config: TranslationConfig) -> Dict[str, Any]:
        """Translation with tone awareness"""
        contextual_result = self._contextual_translate(text, source_lang, target_lang, config)
        
        # Apply tone-specific adjustments
        translated = contextual_result['translated_text']
        translated = self._apply_tone(translated, config.tone, target_lang)
        
        return {
            'translated_text': translated,
            'confidence': 0.8,
            'method': 'tone_aware'
        }
    
    def _technical_translate(self, text: str, source_lang: str, target_lang: str, config: TranslationConfig) -> Dict[str, Any]:
        """Technical translation with domain-specific handling"""
        contextual_result = self._contextual_translate(text, source_lang, target_lang, config)
        
        translated = contextual_result['translated_text']
        
        # Preserve technical terms
        translated = self._preserve_technical_terms(text, translated)
        
        # Apply technical tone
        translated = self._apply_tone(translated, ToneType.TECHNICAL, target_lang)
        
        return {
            'translated_text': translated,
            'confidence': 0.85,
            'method': 'technical'
        }
    
    def _apply_tone(self, text: str, tone: ToneType, language: str) -> str:
        """Apply tone adjustments to translated text"""
        if tone not in self.tone_patterns:
            return text
        
        tone_config = self.tone_patterns[tone]
        adjusted_text = text
        
        # Apply word replacements
        for old_word, new_word in tone_config.get('replacements', {}).items():
            adjusted_text = re.sub(r'\b' + re.escape(old_word) + r'\b', new_word, adjusted_text, flags=re.IGNORECASE)
        
        return adjusted_text
    
    def _preserve_formatting(self, original: str, translated: str) -> str:
        """Preserve original formatting in translation"""
        # Preserve line breaks
        if '\n' in original and '\n' not in translated:
            # Try to maintain paragraph structure
            original_lines = original.split('\n')
            if len(original_lines) > 1:
                # Split translated text proportionally
                words = translated.split()
                words_per_line = len(words) // len(original_lines)
                
                formatted_lines = []
                start_idx = 0
                for i, orig_line in enumerate(original_lines):
                    if i == len(original_lines) - 1:
                        # Last line gets remaining words
                        line_words = words[start_idx:]
                    else:
                        line_words = words[start_idx:start_idx + words_per_line]
                    
                    formatted_lines.append(' '.join(line_words))
                    start_idx += words_per_line
                
                translated = '\n'.join(formatted_lines)
        
        # Preserve leading/trailing whitespace
        if original.startswith(' '):
            translated = ' ' + translated.lstrip()
        if original.endswith(' '):
            translated = translated.rstrip() + ' '
        
        return translated
    
    def _improve_sentence_structure(self, text: str, target_lang: str) -> str:
        """Improve sentence structure for target language"""
        # Language-specific sentence structure improvements
        if target_lang == 'en':
            # English improvements
            text = re.sub(r'\s+', ' ', text)  # Normalize spaces
            text = text.strip()
        elif target_lang in ['es', 'fr', 'it', 'pt']:
            # Romance language improvements
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
        
        return text
    
    def _handle_idioms(self, text: str, source_lang: str, target_lang: str) -> str:
        """Handle idioms and expressions"""
        idiom_mappings = {
            ('es', 'en'): {
                'llueve a cántaros': 'it\'s raining cats and dogs',
                'costar un ojo de la cara': 'cost an arm and a leg'
            },
            ('fr', 'en'): {
                'il pleut des cordes': 'it\'s raining cats and dogs',
                'coûter les yeux de la tête': 'cost an arm and a leg'
            }
        }
        
        mappings = idiom_mappings.get((source_lang, target_lang), {})
        
        for idiom, translation in mappings.items():
            text = re.sub(re.escape(idiom), translation, text, flags=re.IGNORECASE)
        
        return text
    
    def _preserve_technical_terms(self, original: str, translated: str) -> str:
        """Preserve technical terms that shouldn't be translated"""
        # Common technical terms to preserve
        technical_terms = [
            'API', 'HTTP', 'JSON', 'XML', 'SQL', 'HTML', 'CSS', 'JavaScript',
            'Python', 'Java', 'C++', 'GitHub', 'Docker', 'Kubernetes',
            'URL', 'URI', 'UUID', 'TCP', 'UDP', 'IP', 'DNS', 'SSL', 'TLS'
        ]
        
        for term in technical_terms:
            if term in original:
                # Ensure the term appears in the translated text
                if term not in translated:
                    # Simple approach: add at the end if missing
                    translated += f" ({term})"
        
        return translated
    
    def translate_batch(self, texts: List[str], target_language: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """Translate multiple texts in batch"""
        results = []
        
        batch_size = kwargs.get('batch_size', self.config.batch_size)
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            batch_results = []
            for text in batch:
                try:
                    result = self.translate(text, target_language, **kwargs)
                    batch_results.append(result)
                except Exception as e:
                    batch_results.append({
                        'original_text': text,
                        'error': str(e),
                        'success': False
                    })
            
            results.extend(batch_results)
            
            self.logger.info(f"Processed batch {i // batch_size + 1}, {len(batch)} texts")
        
        return results
    
    def get_supported_languages(self) -> Dict[str, List[str]]:
        """Get supported languages"""
        return {
            'codes': list(self.language_codes.values()),
            'names': list(self.language_codes.keys()),
            'families': self.language_families
        }
    
    def detect_tone(self, text: str) -> ToneType:
        """Detect tone of text"""
        text_lower = text.lower()
        
        # Simple tone detection based on keywords
        formal_indicators = ['please', 'kindly', 'would you', 'could you', 'thank you', 'sincerely']
        informal_indicators = ['hey', 'hi', 'cool', 'awesome', 'yeah', 'ok', 'bye']
        technical_indicators = ['algorithm', 'implementation', 'function', 'variable', 'data', 'system']
        
        formal_score = sum(1 for indicator in formal_indicators if indicator in text_lower)
        informal_score = sum(1 for indicator in informal_indicators if indicator in text_lower)
        technical_score = sum(1 for indicator in technical_indicators if indicator in text_lower)
        
        if technical_score > max(formal_score, informal_score):
            return ToneType.TECHNICAL
        elif formal_score > informal_score:
            return ToneType.FORMAL
        elif informal_score > formal_score:
            return ToneType.INFORMAL
        else:
            return ToneType.PROFESSIONAL
    
    def _merge_config(self, kwargs: Dict[str, Any]) -> TranslationConfig:
        """Merge kwargs with default config"""
        config_dict = {
            'source_language': kwargs.get('source_language', self.config.source_language),
            'target_language': kwargs.get('target_language', self.config.target_language),
            'translation_type': kwargs.get('translation_type', self.config.translation_type),
            'tone': kwargs.get('tone', self.config.tone),
            'preserve_formatting': kwargs.get('preserve_formatting', self.config.preserve_formatting),
            'include_confidence': kwargs.get('include_confidence', self.config.include_confidence),
            'batch_size': kwargs.get('batch_size', self.config.batch_size)
        }
        return TranslationConfig(**config_dict)
    
    def get_translation_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get translation statistics"""
        if not results:
            return {'total_translations': 0}
        
        successful = [r for r in results if not r.get('skipped', False) and 'error' not in r]
        skipped = [r for r in results if r.get('skipped', False)]
        failed = [r for r in results if 'error' in r]
        
        language_pairs = {}
        avg_confidence = 0
        total_chars = 0
        
        for result in successful:
            pair = f"{result.get('source_language', 'unknown')}->{result.get('target_language', 'unknown')}"
            language_pairs[pair] = language_pairs.get(pair, 0) + 1
            avg_confidence += result.get('confidence', 0)
            total_chars += result.get('character_count', 0)
        
        return {
            'total_translations': len(results),
            'successful': len(successful),
            'skipped': len(skipped),
            'failed': len(failed),
            'success_rate': (len(successful) / len(results)) * 100 if results else 0,
            'language_pairs': language_pairs,
            'average_confidence': (avg_confidence / len(successful)) if successful else 0,
            'total_characters_translated': total_chars
        }