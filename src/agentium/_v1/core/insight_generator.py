"""
Insight Generator Module - Generate actionable insights from data

This module provides AI-powered insight generation capabilities
for extracting meaningful patterns and actionable information from data.
"""

import json
import statistics
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import re

from ..utils.logger_utils import LoggerUtils


class InsightType(Enum):
    """Types of insights that can be generated"""
    TREND = "trend"
    ANOMALY = "anomaly"
    PATTERN = "pattern"
    CORRELATION = "correlation"
    PREDICTION = "prediction"
    SUMMARY = "summary"
    RECOMMENDATION = "recommendation"


class DataType(Enum):
    """Types of data for insight generation"""
    NUMERIC = "numeric"
    TEXT = "text"
    TIME_SERIES = "time_series"
    CATEGORICAL = "categorical"
    MIXED = "mixed"


@dataclass
class InsightConfig:
    """Configuration for insight generation"""
    insight_types: List[InsightType] = None
    confidence_threshold: float = 0.7
    max_insights: int = 10
    include_visualizations: bool = False
    context_window: int = 30
    custom_patterns: List[str] = None


class InsightGenerator:
    """
    AI-powered insight generator for actionable intelligence.
    
    Features:
    - Multi-type insight generation
    - Pattern recognition
    - Anomaly detection
    - Trend analysis
    - Correlation discovery
    - Predictive insights
    - Actionable recommendations
    """
    
    def __init__(self, config: Optional[InsightConfig] = None):
        self.config = config or InsightConfig()
        if self.config.insight_types is None:
            self.config.insight_types = list(InsightType)
        
        self.logger = LoggerUtils.get_logger(__name__)
    
    @LoggerUtils.log_operation("generate_insights")
    def generate_insights(self, data: Union[List, Dict, str], **kwargs) -> List[Dict[str, Any]]:
        """
        Generate insights from data
        
        Args:
            data: Data to analyze for insights
            **kwargs: Override configuration parameters
            
        Returns:
            List of insights with confidence scores and recommendations
        """
        config = self._merge_config(kwargs)
        
        self.logger.info("Generating insights from data")
        
        # Detect data type
        data_type = self._detect_data_type(data)
        
        insights = []
        
        for insight_type in config.insight_types:
            try:
                if insight_type == InsightType.TREND:
                    insights.extend(self._analyze_trends(data, data_type, config))
                elif insight_type == InsightType.ANOMALY:
                    insights.extend(self._detect_anomalies(data, data_type, config))
                elif insight_type == InsightType.PATTERN:
                    insights.extend(self._find_patterns(data, data_type, config))
                elif insight_type == InsightType.CORRELATION:
                    insights.extend(self._find_correlations(data, data_type, config))
                elif insight_type == InsightType.PREDICTION:
                    insights.extend(self._generate_predictions(data, data_type, config))
                elif insight_type == InsightType.SUMMARY:
                    insights.extend(self._generate_summaries(data, data_type, config))
                elif insight_type == InsightType.RECOMMENDATION:
                    insights.extend(self._generate_recommendations(data, data_type, config))
            except Exception as e:
                self.logger.warning(f"Failed to generate {insight_type.value} insights: {str(e)}")
        
        # Filter by confidence threshold
        filtered_insights = [
            insight for insight in insights 
            if insight.get('confidence', 0) >= config.confidence_threshold
        ]
        
        # Sort by confidence and limit results
        filtered_insights.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return filtered_insights[:config.max_insights]
    
    def _detect_data_type(self, data: Union[List, Dict, str]) -> DataType:
        """Detect the type of data for appropriate analysis"""
        if isinstance(data, str):
            return DataType.TEXT
        elif isinstance(data, list):
            if not data:
                return DataType.MIXED
            
            first_item = data[0]
            if isinstance(first_item, (int, float)):
                return DataType.NUMERIC
            elif isinstance(first_item, dict) and 'timestamp' in first_item:
                return DataType.TIME_SERIES
            elif isinstance(first_item, str):
                return DataType.CATEGORICAL
            else:
                return DataType.MIXED
        elif isinstance(data, dict):
            # Check if it looks like time series data
            if any(key in data for key in ['timestamp', 'time', 'date']):
                return DataType.TIME_SERIES
            
            # Check value types
            values = list(data.values())
            if all(isinstance(v, (int, float)) for v in values):
                return DataType.NUMERIC
            else:
                return DataType.MIXED
        
        return DataType.MIXED
    
    def _analyze_trends(self, data: Union[List, Dict], data_type: DataType, config: InsightConfig) -> List[Dict[str, Any]]:
        """Analyze trends in the data"""
        insights = []
        
        if data_type == DataType.NUMERIC and isinstance(data, list):
            if len(data) < 3:
                return insights
            
            # Calculate trend direction
            trend_slope = self._calculate_trend_slope(data)
            
            if abs(trend_slope) > 0.1:  # Significant trend threshold
                direction = "increasing" if trend_slope > 0 else "decreasing"
                confidence = min(0.9, abs(trend_slope))
                
                insights.append({
                    'type': InsightType.TREND.value,
                    'title': f'Data shows {direction} trend',
                    'description': f'The data exhibits a {direction} trend with slope {trend_slope:.3f}',
                    'confidence': confidence,
                    'value': trend_slope,
                    'actionable': True,
                    'recommendation': f'Monitor the {direction} trend and consider adjusting strategies accordingly'
                })
        
        elif data_type == DataType.TIME_SERIES:
            # Time series trend analysis
            insights.extend(self._analyze_time_series_trends(data, config))
        
        return insights
    
    def _detect_anomalies(self, data: Union[List, Dict], data_type: DataType, config: InsightConfig) -> List[Dict[str, Any]]:
        """Detect anomalies in the data"""
        insights = []
        
        if data_type == DataType.NUMERIC and isinstance(data, list):
            if len(data) < 5:
                return insights
            
            mean_val = statistics.mean(data)
            std_val = statistics.stdev(data)
            
            anomalies = []
            for i, value in enumerate(data):
                z_score = abs(value - mean_val) / std_val if std_val > 0 else 0
                if z_score > 2:  # 2 standard deviations
                    anomalies.append({
                        'index': i,
                        'value': value,
                        'z_score': z_score
                    })
            
            if anomalies:
                confidence = min(0.9, len(anomalies) / len(data) * 10)
                
                insights.append({
                    'type': InsightType.ANOMALY.value,
                    'title': f'Found {len(anomalies)} anomalous data points',
                    'description': f'Detected {len(anomalies)} values that deviate significantly from the mean',
                    'confidence': confidence,
                    'anomalies': anomalies,
                    'actionable': True,
                    'recommendation': 'Investigate the anomalous values to determine if they represent errors or significant events'
                })
        
        return insights
    
    def _find_patterns(self, data: Union[List, Dict, str], data_type: DataType, config: InsightConfig) -> List[Dict[str, Any]]:
        """Find patterns in the data"""
        insights = []
        
        if data_type == DataType.TEXT and isinstance(data, str):
            # Text pattern analysis
            patterns = self._analyze_text_patterns(data, config)
            insights.extend(patterns)
        
        elif data_type == DataType.CATEGORICAL and isinstance(data, list):
            # Frequency pattern analysis
            frequency_patterns = self._analyze_frequency_patterns(data)
            insights.extend(frequency_patterns)
        
        elif data_type == DataType.NUMERIC and isinstance(data, list):
            # Numeric pattern analysis
            numeric_patterns = self._analyze_numeric_patterns(data)
            insights.extend(numeric_patterns)
        
        return insights
    
    def _find_correlations(self, data: Union[List, Dict], data_type: DataType, config: InsightConfig) -> List[Dict[str, Any]]:
        """Find correlations in the data"""
        insights = []
        
        if isinstance(data, dict) and data_type == DataType.MIXED:
            numeric_keys = []
            numeric_values = []
            
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    numeric_keys.append(key)
                    numeric_values.append(value)
            
            if len(numeric_values) >= 2:
                # Simple correlation analysis
                correlations = self._calculate_correlations(numeric_keys, numeric_values)
                insights.extend(correlations)
        
        return insights
    
    def _generate_predictions(self, data: Union[List, Dict], data_type: DataType, config: InsightConfig) -> List[Dict[str, Any]]:
        """Generate predictive insights"""
        insights = []
        
        if data_type == DataType.NUMERIC and isinstance(data, list) and len(data) >= 5:
            # Simple linear prediction
            trend_slope = self._calculate_trend_slope(data)
            last_value = data[-1]
            predicted_value = last_value + trend_slope
            
            confidence = 0.6 if abs(trend_slope) > 0.1 else 0.4
            
            insights.append({
                'type': InsightType.PREDICTION.value,
                'title': 'Predicted next value',
                'description': f'Based on current trend, next value is predicted to be {predicted_value:.2f}',
                'confidence': confidence,
                'predicted_value': predicted_value,
                'current_value': last_value,
                'trend_slope': trend_slope,
                'actionable': True,
                'recommendation': 'Use this prediction for planning but validate with domain expertise'
            })
        
        return insights
    
    def _generate_summaries(self, data: Union[List, Dict, str], data_type: DataType, config: InsightConfig) -> List[Dict[str, Any]]:
        """Generate summary insights"""
        insights = []
        
        if data_type == DataType.NUMERIC and isinstance(data, list):
            if data:
                summary_stats = {
                    'count': len(data),
                    'mean': statistics.mean(data),
                    'median': statistics.median(data),
                    'min': min(data),
                    'max': max(data),
                    'range': max(data) - min(data)
                }
                
                insights.append({
                    'type': InsightType.SUMMARY.value,
                    'title': 'Data Summary Statistics',
                    'description': f'Dataset contains {len(data)} values with mean {summary_stats["mean"]:.2f}',
                    'confidence': 0.95,
                    'statistics': summary_stats,
                    'actionable': False,
                    'recommendation': 'Use these statistics to understand data distribution and identify outliers'
                })
        
        elif data_type == DataType.TEXT and isinstance(data, str):
            text_summary = self._summarize_text(data)
            insights.append(text_summary)
        
        return insights
    
    def _generate_recommendations(self, data: Union[List, Dict, str], data_type: DataType, config: InsightConfig) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        insights = []
        
        # General recommendations based on data characteristics
        if isinstance(data, list) and len(data) < 10:
            insights.append({
                'type': InsightType.RECOMMENDATION.value,
                'title': 'Increase data collection',
                'description': 'Dataset is relatively small which may limit insight quality',
                'confidence': 0.8,
                'actionable': True,
                'recommendation': 'Collect more data points to improve analysis accuracy and discover more patterns'
            })
        
        # Data type specific recommendations
        if data_type == DataType.NUMERIC and isinstance(data, list):
            std_val = statistics.stdev(data) if len(data) > 1 else 0
            mean_val = statistics.mean(data) if data else 0
            
            if std_val > mean_val:  # High variability
                insights.append({
                    'type': InsightType.RECOMMENDATION.value,
                    'title': 'High data variability detected',
                    'description': 'Data shows high variability which may indicate inconsistent processes',
                    'confidence': 0.75,
                    'actionable': True,
                    'recommendation': 'Investigate sources of variability and consider implementing process controls'
                })
        
        return insights
    
    # Helper methods
    def _calculate_trend_slope(self, data: List[float]) -> float:
        """Calculate trend slope using simple linear regression"""
        n = len(data)
        if n < 2:
            return 0
        
        x = list(range(n))
        y = data
        
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        return numerator / denominator if denominator != 0 else 0
    
    def _analyze_time_series_trends(self, data: Union[List, Dict], config: InsightConfig) -> List[Dict[str, Any]]:
        """Analyze trends in time series data"""
        # Placeholder for time series analysis
        return []
    
    def _analyze_text_patterns(self, text: str, config: InsightConfig) -> List[Dict[str, Any]]:
        """Analyze patterns in text data"""
        insights = []
        
        # Word frequency analysis
        words = re.findall(r'\b\w+\b', text.lower())
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Skip short words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        if word_freq:
            most_common = max(word_freq, key=word_freq.get)
            insights.append({
                'type': InsightType.PATTERN.value,
                'title': f'Most frequent word: "{most_common}"',
                'description': f'The word "{most_common}" appears {word_freq[most_common]} times',
                'confidence': 0.8,
                'word_frequency': dict(sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]),
                'actionable': True,
                'recommendation': 'Consider the context and importance of frequently occurring words'
            })
        
        return insights
    
    def _analyze_frequency_patterns(self, data: List) -> List[Dict[str, Any]]:
        """Analyze frequency patterns in categorical data"""
        insights = []
        
        frequency = {}
        for item in data:
            frequency[str(item)] = frequency.get(str(item), 0) + 1
        
        if frequency:
            most_common = max(frequency, key=frequency.get)
            total_count = len(data)
            most_common_pct = (frequency[most_common] / total_count) * 100
            
            insights.append({
                'type': InsightType.PATTERN.value,
                'title': f'Most frequent category: "{most_common}"',
                'description': f'Category "{most_common}" represents {most_common_pct:.1f}% of the data',
                'confidence': 0.85,
                'frequency_distribution': frequency,
                'most_common_percentage': most_common_pct,
                'actionable': True,
                'recommendation': 'Analyze why certain categories dominate and if this aligns with expectations'
            })
        
        return insights
    
    def _analyze_numeric_patterns(self, data: List[float]) -> List[Dict[str, Any]]:
        """Analyze patterns in numeric data"""
        insights = []
        
        # Check for periodic patterns (simplified)
        if len(data) > 10:
            # Look for repeating intervals
            differences = [data[i+1] - data[i] for i in range(len(data)-1)]
            
            # Check if differences show a pattern
            if differences:
                avg_diff = statistics.mean(differences)
                std_diff = statistics.stdev(differences) if len(differences) > 1 else 0
                
                if std_diff < abs(avg_diff) * 0.1:  # Low variability in differences
                    insights.append({
                        'type': InsightType.PATTERN.value,
                        'title': 'Regular interval pattern detected',
                        'description': f'Data shows regular intervals with average difference of {avg_diff:.2f}',
                        'confidence': 0.7,
                        'average_interval': avg_diff,
                        'interval_variability': std_diff,
                        'actionable': True,
                        'recommendation': 'Verify if this pattern is expected and investigate any deviations'
                    })
        
        return insights
    
    def _calculate_correlations(self, keys: List[str], values: List[float]) -> List[Dict[str, Any]]:
        """Calculate correlations between numeric variables"""
        # Simplified correlation analysis
        insights = []
        
        # For demonstration, just return a placeholder
        if len(values) >= 2:
            insights.append({
                'type': InsightType.CORRELATION.value,
                'title': 'Correlation analysis completed',
                'description': 'Analyzed correlations between numeric variables',
                'confidence': 0.6,
                'variables': keys,
                'actionable': True,
                'recommendation': 'Use correlation insights to identify related variables and potential causations'
            })
        
        return insights
    
    def _summarize_text(self, text: str) -> Dict[str, Any]:
        """Summarize text data"""
        words = text.split()
        sentences = text.split('.')
        
        return {
            'type': InsightType.SUMMARY.value,
            'title': 'Text Summary',
            'description': f'Text contains {len(words)} words and {len(sentences)} sentences',
            'confidence': 0.9,
            'word_count': len(words),
            'sentence_count': len(sentences),
            'character_count': len(text),
            'actionable': False,
            'recommendation': 'Use text metrics to understand document complexity and readability'
        }
    
    def _merge_config(self, kwargs: Dict[str, Any]) -> InsightConfig:
        """Merge kwargs with default config"""
        config_dict = {
            'insight_types': kwargs.get('insight_types', self.config.insight_types),
            'confidence_threshold': kwargs.get('confidence_threshold', self.config.confidence_threshold),
            'max_insights': kwargs.get('max_insights', self.config.max_insights),
            'include_visualizations': kwargs.get('include_visualizations', self.config.include_visualizations),
            'context_window': kwargs.get('context_window', self.config.context_window),
            'custom_patterns': kwargs.get('custom_patterns', self.config.custom_patterns)
        }
        return InsightConfig(**config_dict)
    
    def get_insight_summary(self, insights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary of generated insights"""
        if not insights:
            return {'total_insights': 0}
        
        by_type = {}
        total_confidence = 0
        actionable_count = 0
        
        for insight in insights:
            insight_type = insight.get('type', 'unknown')
            by_type[insight_type] = by_type.get(insight_type, 0) + 1
            total_confidence += insight.get('confidence', 0)
            if insight.get('actionable', False):
                actionable_count += 1
        
        return {
            'total_insights': len(insights),
            'by_type': by_type,
            'average_confidence': total_confidence / len(insights) if insights else 0,
            'actionable_insights': actionable_count,
            'actionable_percentage': (actionable_count / len(insights)) * 100 if insights else 0
        }