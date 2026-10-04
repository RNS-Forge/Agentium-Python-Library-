# Multi-Language News Analyzer

Advanced news analysis system with multi-language support and AI-powered insights.

## Features Demonstrated

- [PASS] **Multi-Language Processing** - English, Spanish, French, German, etc.
- [PASS] **Content Translation** - Automatic language translation
- [PASS] **News Analysis** - Structure and content optimization
- [PASS] **Sentiment Analysis** - AI-powered sentiment detection
- [PASS] **Data Extraction** - Organizations, statistics, URLs
- [PASS] **Insight Generation** - Trend analysis and key takeaways
- [PASS] **Report Generation** - Comprehensive analysis reports
- [PASS] **Notification System** - Analysis completion alerts
- [PASS] **Memory Management** - Store and retrieve analyses

## Setup

1. **Install dependencies:**
   ```bash
   pip install agentium google-generativeai requests
   ```

2. **Set up Gemini API:**
   ```bash
   export GEMINI_API_KEY="your_gemini_api_key"
   ```

3. **Run the analyzer:**
   ```bash
   python news_analyzer.py
   ```

## How It Works

### 1. News Loading
Loads sample news articles in multiple languages (English, Spanish, etc.).

### 2. Article Analysis Pipeline
For each article:
1. **Content Optimization** - Improves readability and structure
2. **Data Extraction** - Finds organizations, statistics, URLs
3. **Insight Generation** - Extracts key insights and trends
4. **Summarization** - Creates bullet-point summaries
5. **Translation** - Translates non-English content to English
6. **Sentiment Analysis** - Determines article sentiment

### 3. Report Generation
Creates comprehensive Markdown report with:
- Executive summary
- Individual article analysis
- Aggregated insights
- Translation status
- Processing statistics

### 4. Notification System
Sends completion notifications via:
- Console output
- Email (if configured)
- Slack (if webhook provided)

## Sample News Articles

The demo includes articles about:
- AI Revolution in Healthcare (English)
- AI in Healthcare (Spanish)
- Climate Change Economics (English)

## Configuration Options

### Language Support
```python
supported_languages = [
    'english', 'spanish', 'french', 'german', 'italian', 
    'portuguese', 'russian', 'japanese', 'chinese', 'arabic'
]
```

### Gemini Model Selection
```python
# Use different Gemini models
analyzer = NewsAnalyzer(gemini_model="gemini-1.5-pro")    # More capable
analyzer = NewsAnalyzer(gemini_model="gemini-1.5-flash")  # Faster
```

### Analysis Customization
```python
# Focus on different aspects
insights_result = gemini.enhance_insights(content, focus_area='business')
insights_result = gemini.enhance_insights(content, focus_area='technical')
insights_result = gemini.enhance_insights(content, focus_area='risks')
```

## Expected Output

### Analysis Results
- **Content Optimization**: Improved readability
- **Data Extraction**: Organizations, URLs, statistics
- **Insights**: 3-5 key insights per article
- **Summaries**: Bullet-point summaries
- **Translations**: English translations for non-English content

### Reports Generated
- `news_analysis_YYYYMMDD_HHMMSS.json` - Detailed analysis data
- `news_report_YYYYMMDD_HHMMSS.md` - Human-readable report

### Console Output
```
 Multi-Language News Analyzer Demo
 Analyzing: AI Revolution in Healthcare
   Analyzing content structure...
   Extracting key information...
   Generating insights...
   Creating summary...
   Translating to English...
```

## Advanced Features

### Memory System
Stores analysis results for later retrieval:
```python
# Store analysis
analyzer.memory.store('article_123', analysis_result)

# Retrieve later
stored_analysis = analyzer.memory.get('article_123')
```

### Sentiment Analysis
AI-powered sentiment detection:
- Positive/Negative/Neutral classification
- Confidence scores
- Detailed explanations

### Multi-Channel Notifications
Send results to various channels:
- Console output
- Email notifications
- Slack webhooks
- File exports

## Error Handling

Graceful handling of:
- Missing Gemini API key
- Network connectivity issues
- Unsupported languages
- Invalid content formats
- Translation failures

## Performance Tips

- Use `gemini-1.5-flash` for faster processing
- Process articles in batches
- Cache translation results
- Store frequently accessed data in memory

## Real-World Applications

This analyzer can be extended for:
- **News Monitoring** - Track industry developments
- **Social Media Analysis** - Analyze multilingual posts
- **Market Intelligence** - Extract business insights
- **Content Localization** - Prepare content for global markets
- **Trend Analysis** - Identify emerging patterns