#!/usr/bin/env python3
"""
Multi-Language News Analyzer - Sample Project 2

This project demonstrates news analysis with translation capabilities,
sentiment analysis, and multi-language processing using Agentium.

Features demonstrated:
- Multi-language translation
- News content analysis  
- Sentiment insights
- Content summarization
- Workflow orchestration
- Communication system
- Gemini AI integration

Required API Keys:
- GEMINI_API_KEY: Your Google Gemini API key for AI enhancement
  Get your key at: https://makersuite.google.com/app/apikey

Setup Instructions:
1. Get your Gemini API key from Google AI Studio
2. Set environment variable: GEMINI_API_KEY=your_api_key_here
3. Install dependencies: pip install agentium google-generativeai requests beautifulsoup4
4. Run: python news_analyzer.py

Example using environment variable:
Windows: set GEMINI_API_KEY=your_api_key_here
Linux/Mac: export GEMINI_API_KEY=your_api_key_here
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import json
from datetime import datetime
import requests

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from agentium import (
        Agentium, 
        GeminiIntegration, 
        GeminiConfig, 
        GeminiModel,
        LoggerUtils
    )
except ImportError:
    print("Agentium not found. Install with: pip install agentium")
    sys.exit(1)


class NewsAnalyzer:
    """
    Multi-language news analyzer with AI enhancement
    """
    
    def __init__(self, gemini_model: str = "gemini-pro"):
        """Initialize the news analyzer"""
        # Initialize Agentium
        self.agentium = Agentium()
        
        # Setup Gemini integration
        gemini_config = GeminiConfig(
            model=GeminiModel(gemini_model),
            temperature=0.3,  # Lower temperature for factual analysis
            max_output_tokens=1024
        )
        self.gemini = GeminiIntegration(gemini_config)
        
        # Setup logging
        self.logger = LoggerUtils.get_logger(__name__)
        
        # Create memory for news analysis
        self.memory = self.agentium.memory_helper.create_context("news_analyzer")
        
        # Supported languages for analysis
        self.supported_languages = [
            'english', 'spanish', 'french', 'german', 'italian', 
            'portuguese', 'russian', 'japanese', 'chinese', 'arabic'
        ]
        
        print(f" Multi-Language News Analyzer initialized")
        print(f"Gemini integration: {'Available' if self.gemini.is_available() else 'Not available'}")
        print(f" Supported languages: {len(self.supported_languages)}")
        
    def load_sample_news(self) -> List[Dict[str, str]]:
        """Load sample news articles in different languages"""
        sample_news = [
            {
                'title': 'AI Revolution in Healthcare',
                'content': '''
                Artificial intelligence is transforming healthcare delivery worldwide. 
                Hospitals are implementing AI-powered diagnostic tools that can detect 
                diseases earlier and more accurately than traditional methods. Machine 
                learning algorithms analyze medical images, predict patient outcomes, 
                and optimize treatment plans. The technology has shown remarkable 
                success in radiology, pathology, and drug discovery. However, concerns 
                remain about data privacy, algorithmic bias, and the need for human 
                oversight in medical decisions.
                ''',
                'language': 'english',
                'source': 'TechHealth News',
                'category': 'Technology'
            },
            {
                'title': 'Revolución de la IA en la Atención Médica',
                'content': '''
                La inteligencia artificial está transformando la prestación de atención 
                médica en todo el mundo. Los hospitales están implementando herramientas 
                de diagnóstico impulsadas por IA que pueden detectar enfermedades más 
                temprano y con mayor precisión que los métodos tradicionales. Los 
                algoritmos de aprendizaje automático analizan imágenes médicas, predicen 
                resultados de pacientes y optimizan planes de tratamiento.
                ''',
                'language': 'spanish',
                'source': 'Noticias TechSalud',
                'category': 'Tecnología'
            },
            {
                'title': 'Climate Change Impact on Global Economy',
                'content': '''
                A new report from the International Monetary Fund reveals that climate 
                change could reduce global GDP by 15% by 2050. The analysis shows that 
                extreme weather events, rising sea levels, and temperature changes are 
                already affecting productivity across industries. Financial institutions 
                are now incorporating climate risks into their investment strategies, 
                while governments worldwide are implementing carbon pricing mechanisms 
                to incentivize green technologies.
                ''',
                'language': 'english',
                'source': 'Economic Times',
                'category': 'Economics'
            }
        ]
        
        return sample_news
    
    def analyze_news_article(self, article: Dict[str, str]) -> Dict[str, Any]:
        """Analyze a single news article"""
        print(f"\nAnalyzing: {article['title']}")
        
        analysis_result = {
            'original_article': article,
            'analysis': {},
            'translations': {},
            'insights': [],
            'summary': '',
            'metadata': {
                'analyzed_at': datetime.now().isoformat(),
                'analyzer_model': self.gemini.config.model.value if self.gemini.is_available() else 'local'
            }
        }
        
        content = article['content'].strip()
        
        # Step 1: Content Analysis and Optimization
        print("  Analyzing content structure...")
        if self.gemini.is_available():
            optimized_result = self.gemini.enhance_optimizer(content, optimization_type='readability')
            optimized_content = optimized_result.get('text', content)
        else:
            optimized_result = self.agentium.optimizer.optimize(content, optimization_type='text')
            optimized_content = optimized_result.get('text', content)
        
        analysis_result['analysis']['optimized_content'] = optimized_content
        
        # Step 2: Extract Key Information
        print("  Extracting key information...")
        extracted_data = self.extract_news_data(content)
        analysis_result['analysis']['extracted_data'] = extracted_data
        
        # Step 3: Generate Insights
        print("  Generating insights...")
        if self.gemini.is_available():
            insights_result = self.gemini.enhance_insights(content, focus_area='trends')
            insights = insights_result.get('insights', [])
        else:
            insights_result = self.agentium.insight_generator.generate_insights(content)
            insights = insights_result.get('insights', [])
        
        analysis_result['insights'] = insights
        
        # Step 4: Create Summary
        print("  Creating summary...")
        if self.gemini.is_available():
            summary_result = self.gemini.enhance_summarizer(content, summary_type='bullet')
            summary = summary_result.get('summary', content[:200] + '...')
        else:
            summary_result = self.agentium.summarizer.summarize(content, strategy='extractive')
            summary = summary_result.get('summary', content[:200] + '...')
        
        analysis_result['summary'] = summary
        
        # Step 5: Translation (if not English)
        if article['language'].lower() != 'english':
            print("   Translating to English...")
            if self.gemini.is_available():
                translation_result = self.gemini.enhance_translation(
                    content, 
                    target_language='English',
                    source_language=article['language']
                )
                english_translation = translation_result.get('translated_text', content)
            else:
                translation_result = self.agentium.translator.translate(
                    content,
                    target_language='en',
                    source_language=article['language'][:2]
                )
                english_translation = translation_result.get('translated_text', content)
            
            analysis_result['translations']['english'] = english_translation
        
        # Store in memory
        article_key = f"article_{datetime.now().strftime('%H%M%S')}"
        self.memory.store(article_key, analysis_result)
        
        return analysis_result
    
    def extract_news_data(self, content: str) -> Dict[str, Any]:
        """Extract structured data from news content"""
        extracted = {}
        
        # Extract organizations/companies
        # Simple keyword-based extraction for demo
        organizations = []
        org_keywords = ['Company', 'Corporation', 'Inc', 'Ltd', 'Organization', 'Institute', 'Fund']
        words = content.split()
        for i, word in enumerate(words):
            if any(keyword in word for keyword in org_keywords):
                if i > 0:
                    organizations.append(f"{words[i-1]} {word}")
        
        extracted['organizations'] = list(set(organizations))
        
        # Extract URLs and emails
        url_result = self.agentium.extractor.extract(content, extraction_type='urls')
        extracted['urls'] = url_result.get('extracted_data', [])
        
        email_result = self.agentium.extractor.extract(content, extraction_type='emails')
        extracted['emails'] = email_result.get('extracted_data', [])
        
        # Extract numbers (could be statistics)
        number_result = self.agentium.extractor.extract(content, extraction_type='numbers')
        extracted['statistics'] = number_result.get('extracted_data', [])
        
        return extracted
    
    def analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """Analyze sentiment of content using AI"""
        if not self.gemini.is_available():
            return {'sentiment': 'neutral', 'confidence': 0.5, 'explanation': 'Gemini not available'}
        
        prompt = f"""
        Analyze the sentiment of the following news content. 
        Classify it as positive, negative, or neutral and provide a confidence score (0-1).
        Also provide a brief explanation.
        
        Content: {content}
        
        Response format:
        Sentiment: [positive/negative/neutral]
        Confidence: [0.0-1.0]
        Explanation: [brief explanation]
        """
        
        result = self.gemini.generate_text(prompt)
        if result['success']:
            response = result['text']
            # Simple parsing of response
            sentiment_info = {
                'sentiment': 'neutral',
                'confidence': 0.5,
                'explanation': response
            }
            
            # Extract sentiment
            if 'positive' in response.lower():
                sentiment_info['sentiment'] = 'positive'
            elif 'negative' in response.lower():
                sentiment_info['sentiment'] = 'negative'
            
            return sentiment_info
        
        return {'sentiment': 'neutral', 'confidence': 0.5, 'explanation': 'Analysis failed'}
    
    def generate_news_report(self, analyses: List[Dict[str, Any]]) -> str:
        """Generate comprehensive news analysis report"""
        print("\nGenerating comprehensive news report...")
        
        # Aggregate insights
        all_insights = []
        for analysis in analyses:
            all_insights.extend(analysis.get('insights', []))
        
        # Count languages
        languages = set()
        for analysis in analyses:
            languages.add(analysis['original_article']['language'])
        
        # Create report template
        template_content = """
# Multi-Language News Analysis Report

**Generated:** {{ timestamp }}
**Articles Analyzed:** {{ total_articles }}
**Languages Processed:** {{ languages | join(', ') }}
**AI Model:** {{ model_used }}

## Executive Summary

This report analyzes {{ total_articles }} news articles across {{ language_count }} languages, 
providing insights, translations, and structured data extraction.

## Article Summaries

{% for analysis in analyses %}
### {{ analysis.original_article.title }}
**Source:** {{ analysis.original_article.source }}  
**Language:** {{ analysis.original_article.language }}  
**Category:** {{ analysis.original_article.category }}

**Summary:** {{ analysis.summary }}

**Key Insights:**
{% for insight in analysis.insights[:3] %}
- {{ insight }}
{% endfor %}

{% if analysis.translations.english %}
**English Translation Available** 
{% endif %}

---
{% endfor %}

## Aggregated Insights

{% for insight in all_insights[:10] %}
{{ loop.index }}. {{ insight }}
{% endfor %}

## Statistics

- **Total Articles:** {{ total_articles }}
- **Languages:** {{ language_count }}
- **Total Insights:** {{ total_insights }}
- **Translations Generated:** {{ translation_count }}

---
*Report generated by Agentium Multi-Language News Analyzer*
        """
        
        # Prepare template data
        template_data = {
            'timestamp': datetime.now().isoformat(),
            'total_articles': len(analyses),
            'languages': sorted(languages),
            'language_count': len(languages),
            'model_used': self.gemini.config.model.value if self.gemini.is_available() else 'local',
            'analyses': analyses,
            'all_insights': all_insights,
            'total_insights': len(all_insights),
            'translation_count': sum(1 for a in analyses if a.get('translations'))
        }
        
        # Render report
        report_result = self.agentium.template_manager.process_template(
            template_content,
            template_data,
            template_type='markdown'
        )
        
        return report_result.get('rendered_content', 'Report generation failed')
    
    def send_analysis_notification(self, summary_stats: Dict[str, Any]):
        """Send analysis completion notification"""
        print("\nSending analysis notification...")
        
        message = f"""
         News Analysis Complete!
        
        Analysis Summary:
        • Articles processed: {summary_stats.get('total_articles', 0)}
        • Languages analyzed: {summary_stats.get('languages', 0)}
        • Insights generated: {summary_stats.get('total_insights', 0)}
        • Translations created: {summary_stats.get('translations', 0)}
        
        AI Model: {summary_stats.get('model_used', 'Local')}
         Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # Send console notification
        notification_result = self.agentium.communicator.send_notification(
            message=message,
            channel='console',
            title='News Analysis Complete'
        )
        
        return notification_result
    
    def save_analysis_results(self, analyses: List[Dict[str, Any]], report: str):
        """Save all analysis results"""
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save analyses JSON
        json_file = output_dir / f"news_analysis_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(analyses, f, indent=2, ensure_ascii=False)
        
        # Save report
        report_file = output_dir / f"news_report_{timestamp}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f" Analysis saved to: {json_file}")
        print(f"Report saved to: {report_file}")
        
        return json_file, report_file


def main():
    """Main demonstration function"""
    print(" Agentium Multi-Language News Analyzer Demo")
    print("=" * 60)
    
    # Initialize analyzer
    try:
        analyzer = NewsAnalyzer(gemini_model="gemini-pro")
    except Exception as e:
        print(f"Using fallback configuration: {e}")
        analyzer = NewsAnalyzer()
    
    # Load sample news articles
    news_articles = analyzer.load_sample_news()
    print(f"Loaded {len(news_articles)} news articles")
    
    # Analyze each article
    analyses = []
    for article in news_articles:
        analysis = analyzer.analyze_news_article(article)
        analyses.append(analysis)
    
    # Generate comprehensive report
    report = analyzer.generate_news_report(analyses)
    
    # Calculate summary statistics
    summary_stats = {
        'total_articles': len(analyses),
        'languages': len(set(a['original_article']['language'] for a in analyses)),
        'total_insights': sum(len(a.get('insights', [])) for a in analyses),
        'translations': sum(1 for a in analyses if a.get('translations')),
        'model_used': analyzer.gemini.config.model.value if analyzer.gemini.is_available() else 'Local'
    }
    
    # Send notification
    analyzer.send_analysis_notification(summary_stats)
    
    # Save results
    json_file, report_file = analyzer.save_analysis_results(analyses, report)
    
    # Display final summary
    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Articles analyzed: {summary_stats['total_articles']}")
    print(f" Languages processed: {summary_stats['languages']}")
    print(f"Insights generated: {summary_stats['total_insights']}")
    print(f" Translations created: {summary_stats['translations']}")
    print(f"AI Model used: {summary_stats['model_used']}")
    print(f" Files saved: 2")
    
    # Show sample insights
    print("\nSAMPLE INSIGHTS:")
    insight_count = 0
    for analysis in analyses:
        for insight in analysis.get('insights', []):
            if insight_count < 5:
                print(f"  • {insight}")
                insight_count += 1
    
    print("\nMulti-language news analysis completed successfully!")
    
    # Demonstrate memory retrieval
    print("\nMemory demonstration:")
    all_keys = analyzer.memory.list_keys()
    print(f"Stored {len(all_keys)} analysis results in memory")


if __name__ == "__main__":
    # Check for API key and provide setup instructions
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("WARNING: No Gemini API key found!")
        print("To enable AI enhancement, please set your API key:")
        print("\nWindows Command Prompt:")
        print("  set GEMINI_API_KEY=your_api_key_here")
        print("\nWindows PowerShell:")
        print("  $env:GEMINI_API_KEY=\"your_api_key_here\"")
        print("\nLinux/Mac:")
        print("  export GEMINI_API_KEY=your_api_key_here")
        print("\nGet your API key at: https://makersuite.google.com/app/apikey")
        print("\nContinuing with standard processing...\n")
    
    main()