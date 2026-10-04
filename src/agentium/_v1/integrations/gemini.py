"""
Gemini Integration Module - Google Gemini API Integration

This module provides integration with Google's Gemini API for enhanced
AI capabilities across all Agentium components.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from ..utils.logger_utils import LoggerUtils


class GeminiModel(Enum):
    """Available Gemini models"""
    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_1_5_PRO = "gemini-1.5-pro"


@dataclass
class GeminiConfig:
    """Configuration for Gemini API integration"""
    api_key: Optional[str] = None
    model: GeminiModel = GeminiModel.GEMINI_PRO
    temperature: float = 0.7
    top_p: float = 0.8
    top_k: int = 40
    max_output_tokens: int = 2048
    safety_settings: Dict[str, Any] = None
    

class GeminiIntegration:
    """
    Google Gemini API integration for Agentium components.
    
    Features:
    - Multiple Gemini model support
    - Configurable generation parameters
    - Safety settings management
    - Error handling and fallbacks
    - Token usage tracking
    """
    
    def __init__(self, config: Optional[GeminiConfig] = None):
        self.config = config or GeminiConfig()
        self.logger = LoggerUtils.get_logger(__name__)
        self._setup_gemini()
        
    def _setup_gemini(self):
        """Setup Gemini API client"""
        if not GEMINI_AVAILABLE:
            self.logger.warning("Google GenerativeAI not available - install with: pip install google-generativeai")
            self.client = None
            return
            
        # Get API key from config or environment
        api_key = self.config.api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        
        if not api_key:
            self.logger.warning("Gemini API key not found. Set GEMINI_API_KEY environment variable.")
            self.client = None
            return
            
        try:
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(self.config.model.value)
            self.logger.info(f"Gemini API initialized with model: {self.config.model.value}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini API: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Gemini integration is available"""
        return GEMINI_AVAILABLE and self.client is not None
    
    def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate text using Gemini API
        
        Args:
            prompt: Text prompt for generation
            **kwargs: Override generation parameters
            
        Returns:
            Generated text response
        """
        if not self.is_available():
            return {
                'text': '',
                'error': 'Gemini API not available',
                'success': False
            }
            
        try:
            # Merge config with kwargs
            generation_config = {
                'temperature': kwargs.get('temperature', self.config.temperature),
                'top_p': kwargs.get('top_p', self.config.top_p),
                'top_k': kwargs.get('top_k', self.config.top_k),
                'max_output_tokens': kwargs.get('max_output_tokens', self.config.max_output_tokens)
            }
            
            # Configure safety settings
            safety_settings = kwargs.get('safety_settings', self.config.safety_settings)
            
            # Generate response
            response = self.client.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            if response.text:
                return {
                    'text': response.text,
                    'model': self.config.model.value,
                    'prompt_tokens': len(prompt.split()),  # Approximate
                    'completion_tokens': len(response.text.split()),  # Approximate
                    'success': True
                }
            else:
                return {
                    'text': '',
                    'error': 'No text generated - possibly blocked by safety filters',
                    'success': False
                }
                
        except Exception as e:
            self.logger.error(f"Gemini generation failed: {e}")
            return {
                'text': '',
                'error': str(e),
                'success': False
            }
    
    def generate_with_context(self, system_prompt: str, user_prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate text with system context
        
        Args:
            system_prompt: System/context prompt
            user_prompt: User input prompt
            **kwargs: Generation parameters
            
        Returns:
            Generated response
        """
        full_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"
        return self.generate_text(full_prompt, **kwargs)
    
    def enhance_condenser(self, text: str, target_length: int = None, **kwargs) -> Dict[str, Any]:
        """Enhance text condensation using Gemini"""
        if not self.is_available():
            return {'text': text, 'success': False, 'error': 'Gemini not available'}
            
        length_instruction = f" to approximately {target_length} characters" if target_length else ""
        
        prompt = f"""Please condense the following text{length_instruction} while preserving the key information and main ideas:

Text to condense:
{text}

Condensed version:"""
        
        result = self.generate_text(prompt, **kwargs)
        if result['success']:
            return {
                'text': result['text'].strip(),
                'original_length': len(text),
                'condensed_length': len(result['text']),
                'compression_ratio': round((1 - len(result['text']) / len(text)) * 100, 2),
                'model': result['model'],
                'success': True
            }
        return result
    
    def enhance_optimizer(self, text: str, optimization_type: str = "readability", **kwargs) -> Dict[str, Any]:
        """Enhance text optimization using Gemini"""
        if not self.is_available():
            return {'text': text, 'success': False, 'error': 'Gemini not available'}
        
        optimization_prompts = {
            'readability': "Improve the readability and clarity of this text while maintaining its meaning:",
            'grammar': "Fix grammar, spelling, and punctuation errors in this text:",
            'style': "Improve the writing style and flow of this text:",
            'conciseness': "Make this text more concise and to the point:",
            'professional': "Rewrite this text in a more professional tone:"
        }
        
        base_prompt = optimization_prompts.get(optimization_type, optimization_prompts['readability'])
        
        prompt = f"""{base_prompt}

Original text:
{text}

Optimized version:"""
        
        result = self.generate_text(prompt, **kwargs)
        if result['success']:
            return {
                'text': result['text'].strip(),
                'optimization_type': optimization_type,
                'improvements': ['AI-enhanced optimization applied'],
                'model': result['model'],
                'success': True
            }
        return result
    
    def enhance_summarizer(self, text: str, summary_type: str = "extractive", **kwargs) -> Dict[str, Any]:
        """Enhance summarization using Gemini"""
        if not self.is_available():
            return {'summary': text, 'success': False, 'error': 'Gemini not available'}
        
        summary_prompts = {
            'extractive': "Create a summary by extracting the key sentences and main points from this text:",
            'abstractive': "Create an abstractive summary that captures the essence and main ideas of this text:",
            'bullet': "Create a bullet-point summary of the main points in this text:",
            'executive': "Create an executive summary highlighting the key findings and recommendations:",
            'technical': "Create a technical summary focusing on the methodology and results:"
        }
        
        base_prompt = summary_prompts.get(summary_type, summary_prompts['extractive'])
        
        prompt = f"""{base_prompt}

Text to summarize:
{text}

Summary:"""
        
        result = self.generate_text(prompt, **kwargs)
        if result['success']:
            return {
                'summary': result['text'].strip(),
                'summary_type': summary_type,
                'original_length': len(text),
                'summary_length': len(result['text']),
                'model': result['model'],
                'success': True
            }
        return result
    
    def enhance_insights(self, data: str, focus_area: str = "general", **kwargs) -> Dict[str, Any]:
        """Generate insights using Gemini"""
        if not self.is_available():
            return {'insights': [], 'success': False, 'error': 'Gemini not available'}
        
        focus_prompts = {
            'general': "Analyze this data and provide key insights and patterns:",
            'business': "Analyze this data from a business perspective and provide actionable insights:",
            'technical': "Provide technical insights and recommendations based on this data:",
            'trends': "Identify trends, patterns, and potential future developments from this data:",
            'risks': "Identify potential risks, challenges, and mitigation strategies from this data:"
        }
        
        base_prompt = focus_prompts.get(focus_area, focus_prompts['general'])
        
        prompt = f"""{base_prompt}

Data to analyze:
{data}

Key insights:
1."""
        
        result = self.generate_text(prompt, **kwargs)
        if result['success']:
            # Parse insights into list
            insights_text = result['text'].strip()
            insights = []
            
            # Try to extract numbered insights
            lines = insights_text.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # Clean up the line
                    cleaned = line.lstrip('0123456789.-• ').strip()
                    if cleaned:
                        insights.append(cleaned)
            
            if not insights:
                # Fallback: split by sentences
                insights = [s.strip() for s in insights_text.split('.') if s.strip()]
            
            return {
                'insights': insights,
                'focus_area': focus_area,
                'total_insights': len(insights),
                'model': result['model'],
                'success': True
            }
        return result
    
    def enhance_translation(self, text: str, target_language: str, source_language: str = "auto", **kwargs) -> Dict[str, Any]:
        """Enhance translation using Gemini"""
        if not self.is_available():
            return {'translated_text': text, 'success': False, 'error': 'Gemini not available'}
        
        source_instruction = f"from {source_language} " if source_language != "auto" else ""
        
        prompt = f"""Translate the following text {source_instruction}to {target_language}. Maintain the tone and context:

Text to translate:
{text}

Translation in {target_language}:"""
        
        result = self.generate_text(prompt, **kwargs)
        if result['success']:
            return {
                'translated_text': result['text'].strip(),
                'source_language': source_language,
                'target_language': target_language,
                'model': result['model'],
                'success': True
            }
        return result
    
    def get_available_models(self) -> List[str]:
        """Get list of available Gemini models"""
        return [model.value for model in GeminiModel]
    
    def change_model(self, model: Union[str, GeminiModel]):
        """Change the active model"""
        if isinstance(model, str):
            model = GeminiModel(model)
        
        self.config.model = model
        if self.is_available():
            try:
                self.client = genai.GenerativeModel(model.value)
                self.logger.info(f"Changed to model: {model.value}")
            except Exception as e:
                self.logger.error(f"Failed to change model: {e}")


# Global instance for easy access
_gemini_instance = None

def get_gemini_integration(config: Optional[GeminiConfig] = None) -> GeminiIntegration:
    """Get global Gemini integration instance"""
    global _gemini_instance
    if _gemini_instance is None:
        _gemini_instance = GeminiIntegration(config)
    return _gemini_instance