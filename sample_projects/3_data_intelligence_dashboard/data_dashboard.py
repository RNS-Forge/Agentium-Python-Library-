#!/usr/bin/env python3
"""
Data Intelligence Dashboard - Sample Project 3

This project demonstrates comprehensive data intelligence capabilities
using Agentium for data extraction, analysis, and insight generation.

Features demonstrated:
- Multi-source data extraction
- Data pattern recognition
- Automated insights generation
- Workflow orchestration
- Real-time processing
- Dashboard visualization
- Gemini AI enhancement
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from datetime import datetime, timedelta
import random
import csv

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


class DataIntelligenceDashboard:
    """
    Advanced data intelligence system with multi-source analysis
    """
    
    def __init__(self, gemini_model: str = "gemini-1.5-flash"):
        """Initialize the data intelligence dashboard"""
        # Initialize Agentium
        self.agentium = Agentium()
        
        # Setup Gemini integration with fast model for data processing
        gemini_config = GeminiConfig(
            model=GeminiModel(gemini_model),
            temperature=0.1,  # Low temperature for analytical accuracy
            max_output_tokens=1536
        )
        self.gemini = GeminiIntegration(gemini_config)
        
        # Setup logging
        self.logger = LoggerUtils.get_logger(__name__)
        
        # Create memory context for dashboard data
        self.memory = self.agentium.memory_helper.create_context("data_dashboard")
        
        # Data sources and processing results
        self.data_sources = {}
        self.processed_data = {}
        self.insights = {}
        
        print(f"Data Intelligence Dashboard initialized")
        print(f"Gemini integration: {'Available' if self.gemini.is_available() else 'Not available'}")
        
    def generate_sample_data(self) -> Dict[str, Any]:
        """Generate comprehensive sample datasets"""
        print("Generating sample data sources...")
        
        data_sources = {}
        
        # 1. Sales Data
        sales_data = []
        products = ['Product A', 'Product B', 'Product C', 'Product D', 'Product E']
        regions = ['North', 'South', 'East', 'West', 'Central']
        
        for day in range(30):
            date = (datetime.now() - timedelta(days=30-day)).strftime('%Y-%m-%d')
            for product in products:
                for region in regions:
                    sales_data.append({
                        'date': date,
                        'product': product,
                        'region': region,
                        'sales': random.randint(100, 1000),
                        'units': random.randint(10, 100),
                        'revenue': random.randint(1000, 10000)
                    })
        
        data_sources['sales'] = {
            'type': 'csv',
            'description': 'Daily sales data by product and region',
            'data': sales_data,
            'size': len(sales_data)
        }
        
        # 2. Customer Feedback Data
        feedback_data = [
            {
                'id': 1,
                'customer': 'Customer A',
                'rating': 4.5,
                'comment': 'Great product quality and fast delivery. Highly recommended for anyone looking for reliable service.',
                'category': 'Product Quality',
                'sentiment': 'positive'
            },
            {
                'id': 2,
                'customer': 'Customer B', 
                'rating': 2.0,
                'comment': 'Poor customer service experience. Long wait times and unhelpful representatives. Needs improvement.',
                'category': 'Customer Service',
                'sentiment': 'negative'
            },
            {
                'id': 3,
                'customer': 'Customer C',
                'rating': 5.0,
                'comment': 'Excellent experience from start to finish. The product exceeded my expectations and arrived on time.',
                'category': 'Overall Experience',
                'sentiment': 'positive'
            },
            {
                'id': 4,
                'customer': 'Customer D',
                'rating': 3.0,
                'comment': 'Average product but reasonable price. Could be better but meets basic requirements. Would consider again.',
                'category': 'Value',
                'sentiment': 'neutral'
            },
            {
                'id': 5,
                'customer': 'Customer E',
                'rating': 4.0,
                'comment': 'Good quality product with minor packaging issues. Overall satisfied with the purchase and performance.',
                'category': 'Product Quality',
                'sentiment': 'positive'
            }
        ]
        
        data_sources['feedback'] = {
            'type': 'json',
            'description': 'Customer feedback and ratings',
            'data': feedback_data,
            'size': len(feedback_data)
        }
        
        # 3. Web Analytics Data
        analytics_content = """
        Website Traffic Analysis Report
        
        Monthly Performance Summary:
        - Total Visitors: 45,678 (+12% from last month)
        - Page Views: 123,456 (+8% from last month)
        - Average Session Duration: 3:24 minutes
        - Bounce Rate: 34% (-5% from last month)
        - Conversion Rate: 2.8% (+0.3% from last month)
        
        Top Performing Pages:
        1. /products/ai-solutions - 12,345 views
        2. /about-us - 8,901 views  
        3. /blog/ai-trends - 6,789 views
        4. /contact - 5,432 views
        5. /pricing - 4,321 views
        
        Traffic Sources:
        - Organic Search: 45%
        - Direct Traffic: 25%
        - Social Media: 15%
        - Referral Sites: 10%
        - Paid Advertising: 5%
        
        Geographic Distribution:
        - United States: 40%
        - United Kingdom: 15%
        - Canada: 12%
        - Germany: 8%
        - Other: 25%
        
        Device Breakdown:
        - Desktop: 55%
        - Mobile: 35%
        - Tablet: 10%
        
        Contact Information:
        For questions about this report, email analytics@company.com
        or call +1-555-DATA-INTEL (555-328-2468).
        Visit our dashboard at https://analytics.company.com
        """
        
        data_sources['analytics'] = {
            'type': 'text',
            'description': 'Web analytics and traffic data',
            'data': analytics_content,
            'size': len(analytics_content)
        }
        
        # 4. Financial Data
        financial_data = {
            'quarterly_revenue': [2500000, 2750000, 3100000, 3400000],
            'expenses': [1800000, 1950000, 2200000, 2400000],
            'profit_margins': [28.0, 29.1, 29.0, 29.4],
            'growth_rate': [15.2, 10.0, 12.7, 9.7],
            'key_metrics': {
                'current_ratio': 2.1,
                'debt_to_equity': 0.45,
                'return_on_investment': 15.8,
                'customer_acquisition_cost': 125,
                'lifetime_value': 2400
            }
        }
        
        data_sources['financial'] = {
            'type': 'structured',
            'description': 'Financial performance metrics',
            'data': financial_data,
            'size': len(str(financial_data))
        }
        
        self.data_sources = data_sources
        print(f"Generated {len(data_sources)} data sources")
        return data_sources
    
    def extract_data_insights(self, source_name: str, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights from a specific data source"""
        print(f"  Analyzing {source_name} data...")
        
        data = source_data['data']
        data_type = source_data['type']
        
        insights = {
            'source': source_name,
            'type': data_type,
            'analysis': {},
            'key_insights': [],
            'recommendations': [],
            'extracted_entities': {}
        }
        
        if data_type == 'csv' and source_name == 'sales':
            # Analyze sales data
            total_revenue = sum(item['revenue'] for item in data)
            total_units = sum(item['units'] for item in data)
            avg_price = total_revenue / total_units if total_units > 0 else 0
            
            # Product performance
            product_revenue = {}
            for item in data:
                product = item['product']
                product_revenue[product] = product_revenue.get(product, 0) + item['revenue']
            
            best_product = max(product_revenue, key=product_revenue.get)
            
            insights['analysis'] = {
                'total_revenue': total_revenue,
                'total_units': total_units,
                'average_price': round(avg_price, 2),
                'product_performance': product_revenue,
                'best_performing_product': best_product
            }
            
            insights['key_insights'] = [
                f"Total revenue generated: ${total_revenue:,}",
                f"Best performing product: {best_product}",
                f"Average unit price: ${avg_price:.2f}",
                f"Total units sold: {total_units:,}"
            ]
            
        elif data_type == 'json' and source_name == 'feedback':
            # Analyze feedback data
            avg_rating = sum(item['rating'] for item in data) / len(data)
            sentiment_counts = {}
            category_ratings = {}
            
            for item in data:
                sentiment = item['sentiment']
                category = item['category']
                
                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
                if category not in category_ratings:
                    category_ratings[category] = []
                category_ratings[category].append(item['rating'])
            
            # Calculate average rating by category
            category_avg = {cat: sum(ratings)/len(ratings) for cat, ratings in category_ratings.items()}
            
            insights['analysis'] = {
                'average_rating': round(avg_rating, 2),
                'sentiment_distribution': sentiment_counts,
                'category_ratings': category_avg,
                'total_feedback': len(data)
            }
            
            insights['key_insights'] = [
                f"Average customer rating: {avg_rating:.1f}/5.0",
                f"Positive feedback: {sentiment_counts.get('positive', 0)} responses",
                f"Areas needing attention: {min(category_avg, key=category_avg.get)}",
                f"Total feedback collected: {len(data)}"
            ]
            
        elif data_type == 'text' and source_name == 'analytics':
            # Extract structured data from analytics text
            extracted_entities = self.agentium.extractor.extract(data, extraction_type='numbers')
            emails = self.agentium.extractor.extract(data, extraction_type='emails')
            urls = self.agentium.extractor.extract(data, extraction_type='urls')
            phones = self.agentium.extractor.extract(data, extraction_type='phones')
            
            insights['extracted_entities'] = {
                'numbers': extracted_entities.get('extracted_data', []),
                'emails': emails.get('extracted_data', []),
                'urls': urls.get('extracted_data', []),
                'phones': phones.get('extracted_data', [])
            }
            
            # Use AI to analyze the content
            if self.gemini.is_available():
                ai_analysis = self.gemini.enhance_insights(data, focus_area='business')
                insights['key_insights'] = ai_analysis.get('insights', [])
            else:
                insights['key_insights'] = [
                    "Website traffic showing positive growth trends",
                    "Mobile traffic represents significant user segment", 
                    "Organic search is primary traffic driver",
                    "Conversion rates are improving month-over-month"
                ]
        
        elif data_type == 'structured' and source_name == 'financial':
            # Analyze financial data
            quarterly_revenue = data['quarterly_revenue']
            expenses = data['expenses']
            profits = [rev - exp for rev, exp in zip(quarterly_revenue, expenses)]
            
            insights['analysis'] = {
                'quarterly_profits': profits,
                'total_annual_revenue': sum(quarterly_revenue),
                'total_annual_expenses': sum(expenses),
                'annual_profit': sum(profits),
                'profit_margin': round((sum(profits) / sum(quarterly_revenue)) * 100, 2)
            }
            
            insights['key_insights'] = [
                f"Annual profit margin: {insights['analysis']['profit_margin']}%",
                f"Total annual profit: ${sum(profits):,}",
                f"Revenue growth trend: {'Positive' if quarterly_revenue[-1] > quarterly_revenue[0] else 'Negative'}",
                f"Strong financial ratios indicate healthy business"
            ]
        
        # Generate AI-powered recommendations if available
        if self.gemini.is_available():
            recommendations_prompt = f"""
            Based on this data analysis for {source_name}:
            {json.dumps(insights['analysis'], indent=2)}
            
            Provide 3-5 actionable business recommendations.
            """
            
            rec_result = self.gemini.generate_text(recommendations_prompt)
            if rec_result['success']:
                # Parse recommendations
                recommendations_text = rec_result['text']
                recommendations = [line.strip() for line in recommendations_text.split('\n') if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith('-'))]
                insights['recommendations'] = recommendations[:5]
        
        return insights
    
    def create_comprehensive_dashboard(self) -> Dict[str, Any]:
        """Create comprehensive dashboard with all data sources"""
        print("\nCreating comprehensive data intelligence dashboard...")
        
        dashboard = {
            'title': 'Data Intelligence Dashboard',
            'generated_at': datetime.now().isoformat(),
            'data_sources': len(self.data_sources),
            'source_analysis': {},
            'cross_source_insights': [],
            'recommendations': [],
            'summary_stats': {},
            'ai_model': self.gemini.config.model.value if self.gemini.is_available() else 'local'
        }
        
        # Analyze each data source
        all_insights = []
        for source_name, source_data in self.data_sources.items():
            source_insights = self.extract_data_insights(source_name, source_data)
            dashboard['source_analysis'][source_name] = source_insights
            all_insights.extend(source_insights['key_insights'])
            
            # Store in memory
            self.memory.store(f"{source_name}_insights", source_insights)
        
        # Generate cross-source insights using AI
        if self.gemini.is_available() and len(all_insights) > 0:
            cross_analysis_prompt = f"""
            Analyze these business insights from multiple data sources and identify patterns, 
            correlations, and high-level strategic insights:
            
            Sales Insights: {dashboard['source_analysis'].get('sales', {}).get('key_insights', [])}
            Customer Feedback: {dashboard['source_analysis'].get('feedback', {}).get('key_insights', [])}
            Analytics Data: {dashboard['source_analysis'].get('analytics', {}).get('key_insights', [])}
            Financial Data: {dashboard['source_analysis'].get('financial', {}).get('key_insights', [])}
            
            Provide 5 cross-source strategic insights.
            """
            
            cross_result = self.gemini.generate_text(cross_analysis_prompt)
            if cross_result['success']:
                cross_insights = [line.strip() for line in cross_result['text'].split('\n') if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith('-'))]
                dashboard['cross_source_insights'] = cross_insights[:5]
        
        # Calculate summary statistics
        dashboard['summary_stats'] = {
            'total_data_points': sum(source['size'] for source in self.data_sources.values()),
            'insights_generated': len(all_insights),
            'data_types_processed': len(set(source['type'] for source in self.data_sources.values())),
            'recommendations_count': sum(len(analysis.get('recommendations', [])) for analysis in dashboard['source_analysis'].values())
        }
        
        return dashboard
    
    def generate_dashboard_report(self, dashboard: Dict[str, Any]) -> str:
        """Generate comprehensive dashboard report"""
        print("Generating dashboard report...")
        
        template_content = """
# Data Intelligence Dashboard Report

**Generated:** {{ generated_at }}
**Data Sources:** {{ data_sources }}
**AI Model:** {{ ai_model }}

## Executive Summary

This comprehensive analysis covers {{ data_sources }} data sources, generating 
{{ summary_stats.insights_generated }} insights and {{ summary_stats.recommendations_count }} 
actionable recommendations across {{ summary_stats.data_types_processed }} different data types.

## Data Source Analysis

{% for source_name, analysis in source_analysis.items() %}
### {{ source_name | title }} Analysis

**Data Type:** {{ analysis.type }}  
**Key Insights:**
{% for insight in analysis.key_insights %}
- {{ insight }}
{% endfor %}

{% if analysis.recommendations %}
**Recommendations:**
{% for rec in analysis.recommendations %}
- {{ rec }}
{% endfor %}
{% endif %}

---
{% endfor %}

## Cross-Source Strategic Insights

{% for insight in cross_source_insights %}
{{ loop.index }}. {{ insight }}
{% endfor %}

## Performance Metrics

- **Total Data Points Processed:** {{ summary_stats.total_data_points }}
- **Insights Generated:** {{ summary_stats.insights_generated }}
- **Data Types:** {{ summary_stats.data_types_processed }}
- **Recommendations:** {{ summary_stats.recommendations_count }}

## Data Quality Summary

{% for source_name, source_data in data_sources.items() %}
- **{{ source_name | title }}:** {{ source_data.size }} data points ({{ source_data.type }})
{% endfor %}

---
*Dashboard generated by Agentium Data Intelligence System*
        """
        
        # Combine dashboard data with source data for template
        template_data = {**dashboard, 'data_sources_detail': self.data_sources}
        
        # Render report
        report_result = self.agentium.template_manager.process_template(
            template_content,
            template_data,
            template_type='markdown'
        )
        
        return report_result.get('rendered_content', 'Dashboard report generation failed')
    
    def export_dashboard_data(self, dashboard: Dict[str, Any]):
        """Export dashboard data to multiple formats"""
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export JSON
        json_file = output_dir / f"dashboard_data_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(dashboard, f, indent=2, ensure_ascii=False)
        
        # Export CSV (sales data)
        if 'sales' in self.data_sources:
            csv_file = output_dir / f"sales_data_{timestamp}.csv"
            sales_data = self.data_sources['sales']['data']
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                if sales_data:
                    writer = csv.DictWriter(f, fieldnames=sales_data[0].keys())
                    writer.writeheader()
                    writer.writerows(sales_data)
        
        print(f"Dashboard data exported to: {json_file}")
        if 'sales' in self.data_sources:
            print(f"Sales data exported to: {csv_file}")
        
        return json_file


def main():
    """Main demonstration function"""
    print("Agentium Data Intelligence Dashboard Demo")
    print("=" * 60)
    
    # Initialize dashboard
    try:
        dashboard = DataIntelligenceDashboard(gemini_model="gemini-1.5-flash")
    except Exception as e:
        print(f"Using fallback configuration: {e}")
        dashboard = DataIntelligenceDashboard()
    
    # Generate sample data
    data_sources = dashboard.generate_sample_data()
    
    # Create comprehensive dashboard
    dashboard_results = dashboard.create_comprehensive_dashboard()
    
    # Generate report
    report = dashboard.generate_dashboard_report(dashboard_results)
    
    # Export data
    json_file = dashboard.export_dashboard_data(dashboard_results)
    
    # Save report
    report_file = json_file.parent / f"dashboard_report_{json_file.stem.split('_')[-1]}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Dashboard report saved to: {report_file}")
    
    # Send completion notification
    summary_message = f"""
    Data Intelligence Dashboard Complete!
    
    Analysis Summary:
    • Data sources processed: {dashboard_results['data_sources']}
    • Insights generated: {dashboard_results['summary_stats']['insights_generated']}
    • Recommendations created: {dashboard_results['summary_stats']['recommendations_count']}
    • Data points analyzed: {dashboard_results['summary_stats']['total_data_points']:,}
    
    AI Model: {dashboard_results['ai_model']}
     Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    dashboard.agentium.communicator.send_notification(
        message=summary_message,
        channel='console',
        title='Dashboard Analysis Complete'
    )
    
    # Display final summary
    print("\n" + "=" * 60)
    print("DASHBOARD SUMMARY")
    print("=" * 60)
    print(f"Data sources: {dashboard_results['data_sources']}")
    print(f"Insights generated: {dashboard_results['summary_stats']['insights_generated']}")
    print(f"Recommendations: {dashboard_results['summary_stats']['recommendations_count']}")
    print(f"Data points: {dashboard_results['summary_stats']['total_data_points']:,}")
    print(f"AI model: {dashboard_results['ai_model']}")
    print(f" Files generated: 3")
    
    # Show sample cross-source insights
    print("\nCROSS-SOURCE INSIGHTS:")
    for i, insight in enumerate(dashboard_results.get('cross_source_insights', [])[:3], 1):
        print(f"{i}. {insight}")
    
    print("\nMemory demonstration:")
    all_keys = dashboard.memory.list_keys()
    print(f"Stored {len(all_keys)} analysis results in memory")
    
    print("\nData Intelligence Dashboard completed successfully!")


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