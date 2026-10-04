# Content Processing Pipeline

A comprehensive demonstration of Agentium's content processing capabilities with AI enhancement.

## Features Demonstrated

- [PASS] **Data Extraction** - Emails, URLs, phones, numbers
- [PASS] **Text Condensation** - AI-powered content reduction
- [PASS] **Content Optimization** - Readability and structure improvement
- [PASS] **Insight Generation** - Business insights from content
- [PASS] **Custom Summarization** - Executive summaries
- [PASS] **Memory Management** - Context storage and retrieval
- [PASS] **Template Processing** - Report generation
- [PASS] **Gemini API Integration** - AI enhancement

## Setup

1. **Install dependencies:**
   ```bash
   pip install agentium google-generativeai
   ```

2. **Set up Gemini API:**
   ```bash
   export GEMINI_API_KEY="your_gemini_api_key"
   # or
   export GOOGLE_API_KEY="your_google_api_key"
   ```

3. **Run the demo:**
   ```bash
   python content_pipeline.py
   ```

## How It Works

### 1. Content Loading
Loads sample business content about AI/ML in business operations.

### 2. Processing Pipeline
1. **Data Extraction** - Finds structured data (emails, URLs, etc.)
2. **Condensation** - Reduces content while preserving key information
3. **Optimization** - Improves readability and structure
4. **Insight Generation** - Extracts business insights
5. **Summarization** - Creates executive summary

### 3. Report Generation
Creates comprehensive Markdown report with:
- Executive summary
- Key insights
- Extracted data
- Processing steps

### 4. Memory Demonstration
Shows context storage and retrieval capabilities.

## Sample Output

The pipeline processes business content and generates:

- **JSON Results** - Complete processing data
- **Markdown Report** - Human-readable summary
- **Console Output** - Real-time processing status

## Configuration

Customize processing by modifying:

```python
# Change Gemini model
pipeline = ContentProcessingPipeline(gemini_model="gemini-1.5-pro")

# Adjust condensation ratio
condensed_result = agentium.condenser.condense(content, compression_ratio=0.3)

# Change optimization focus
optimized_result = gemini.enhance_optimizer(text, optimization_type='professional')
```

## Expected Results

- Original content: ~2000 characters
- Condensed content: ~800 characters
- 5-8 business insights
- Structured data extraction
- Professional report generation

## Error Handling

The pipeline gracefully handles:
- Missing Gemini API key (falls back to local processing)
- Network connectivity issues
- Invalid content formats
- Memory storage errors

## Files Generated

- `content_processing_results_YYYYMMDD_HHMMSS.json`
- `report_content_processing_results_YYYYMMDD_HHMMSS.md`