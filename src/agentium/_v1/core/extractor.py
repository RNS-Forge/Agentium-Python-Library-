"""
Extractor Module - Extract structured information from various data sources

This module provides sophisticated data extraction capabilities
for structured information from unstructured data.
"""

import re
import json
import csv
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Union, Pattern
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse, parse_qs
import mimetypes

from ..utils.logger_utils import LoggerUtils


class ExtractionType(Enum):
    """Types of extraction available"""
    TEXT_PATTERNS = "text_patterns"
    STRUCTURED_DATA = "structured_data"
    ENTITIES = "entities"
    METADATA = "metadata"
    URLS = "urls"
    EMAILS = "emails"
    PHONES = "phones"
    DATES = "dates"
    NUMBERS = "numbers"
    JSON_PATHS = "json_paths"
    XML_ELEMENTS = "xml_elements"
    HTML_ELEMENTS = "html_elements"
    TABLE_DATA = "table_data"


@dataclass
class ExtractionConfig:
    """Configuration for extraction operations"""
    extraction_type: ExtractionType = ExtractionType.TEXT_PATTERNS
    patterns: List[str] = None
    case_sensitive: bool = False
    include_context: bool = True
    context_length: int = 50
    output_format: str = "list"  # list, dict, json
    custom_extractors: Dict[str, Any] = None


# Alias for consistent naming
ExtractorConfig = ExtractionConfig


class Extractor:
    """
    Advanced data extractor for structured information.
    
    Features:
    - Pattern-based extraction
    - Entity recognition
    - Structured data parsing
    - Metadata extraction
    - Multi-format support (JSON, XML, HTML, CSV)
    - Custom extraction patterns
    - Context preservation
    """
    
    def __init__(self, config: Optional[ExtractionConfig] = None):
        self.config = config or ExtractionConfig()
        self.logger = LoggerUtils.get_logger(__name__)
        self._setup_patterns()
    
    def _setup_patterns(self):
        """Setup common extraction patterns"""
        self.common_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            'url': r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?',
            'date_iso': r'\d{4}-\d{2}-\d{2}',
            'date_us': r'\d{1,2}/\d{1,2}/\d{4}',
            'date_eu': r'\d{1,2}\.\d{1,2}\.\d{4}',
            'time': r'\d{1,2}:\d{2}(?::\d{2})?(?:\s?[AaPp][Mm])?',
            'number': r'-?\d+(?:\.\d+)?',
            'currency': r'\$\d+(?:,\d{3})*(?:\.\d{2})?',
            'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            'hex_color': r'#[0-9a-fA-F]{6}',
            'uuid': r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            'social_security': r'\d{3}-\d{2}-\d{4}',
            'credit_card': r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}',
            'hash_md5': r'[0-9a-f]{32}',
            'hash_sha1': r'[0-9a-f]{40}',
            'hash_sha256': r'[0-9a-f]{64}',
        }
    
    @LoggerUtils.log_operation("extract_data")
    def extract(self, data: Union[str, Dict, List], **kwargs) -> Dict[str, Any]:
        """
        Main extraction method
        
        Args:
            data: Data to extract from
            **kwargs: Override configuration parameters
            
        Returns:
            Dictionary with extracted data and metadata
        """
        config = self._merge_config(kwargs)
        
        self.logger.info(f"Extracting {config.extraction_type.value} from data")
        
        if config.extraction_type == ExtractionType.TEXT_PATTERNS:
            raw_result = self._extract_patterns(data, config)
        elif config.extraction_type == ExtractionType.STRUCTURED_DATA:
            raw_result = self._extract_structured_data(data, config)
        elif config.extraction_type == ExtractionType.ENTITIES:
            raw_result = self._extract_entities(data, config)
        elif config.extraction_type == ExtractionType.METADATA:
            raw_result = self._extract_metadata(data, config)
        elif config.extraction_type == ExtractionType.URLS:
            raw_result = self._extract_urls(data, config)
        elif config.extraction_type == ExtractionType.EMAILS:
            raw_result = self._extract_emails(data, config)
        elif config.extraction_type == ExtractionType.PHONES:
            raw_result = self._extract_phones(data, config)
        elif config.extraction_type == ExtractionType.DATES:
            raw_result = self._extract_dates(data, config)
        elif config.extraction_type == ExtractionType.NUMBERS:
            raw_result = self._extract_numbers(data, config)
        elif config.extraction_type == ExtractionType.JSON_PATHS:
            raw_result = self._extract_json_paths(data, config)
        elif config.extraction_type == ExtractionType.XML_ELEMENTS:
            raw_result = self._extract_xml_elements(data, config)
        elif config.extraction_type == ExtractionType.HTML_ELEMENTS:
            raw_result = self._extract_html_elements(data, config)
        elif config.extraction_type == ExtractionType.TABLE_DATA:
            raw_result = self._extract_table_data(data, config)
        else:
            raw_result = []
        
        return {
            'extracted_data': raw_result,
            'extraction_type': config.extraction_type.value,
            'items_count': len(raw_result) if isinstance(raw_result, (list, dict)) else 1,
            'success': True
        }
    
    def _extract_patterns(self, data: str, config: ExtractionConfig) -> List[Dict[str, Any]]:
        """Extract using custom patterns"""
        results = []
        patterns = config.patterns or []
        
        flags = 0 if config.case_sensitive else re.IGNORECASE
        
        for pattern in patterns:
            matches = re.finditer(pattern, data, flags)
            for match in matches:
                result = {
                    'match': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'groups': match.groups(),
                }
                
                if config.include_context:
                    context_start = max(0, match.start() - config.context_length)
                    context_end = min(len(data), match.end() + config.context_length)
                    result['context'] = data[context_start:context_end]
                
                results.append(result)
        
        return results
    
    def _extract_structured_data(self, data: Union[str, Dict, List], config: ExtractionConfig) -> Dict[str, Any]:
        """Extract structured data from various formats"""
        if isinstance(data, str):
            # Try to parse as JSON
            try:
                parsed = json.loads(data)
                return self._extract_from_dict(parsed, config)
            except json.JSONDecodeError:
                pass
            
            # Try to parse as XML
            try:
                root = ET.fromstring(data)
                return self._extract_from_xml(root, config)
            except ET.ParseError:
                pass
            
            # Try to parse as CSV
            try:
                return self._extract_from_csv_string(data, config)
            except Exception:
                pass
            
            return {'error': 'Could not parse structured data'}
        
        elif isinstance(data, dict):
            return self._extract_from_dict(data, config)
        
        elif isinstance(data, list):
            return self._extract_from_list(data, config)
        
        return {'error': 'Unsupported data type'}
    
    def _extract_entities(self, text: str, config: ExtractionConfig) -> List[Dict[str, Any]]:
        """Extract named entities (simplified NER)"""
        entities = []
        
        # Simple entity patterns
        entity_patterns = {
            'PERSON': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            'ORGANIZATION': r'\b[A-Z][a-zA-Z\s&.,]+(?:Inc|LLC|Corp|Ltd)\b',
            'LOCATION': r'\b[A-Z][a-z]+(?:,\s[A-Z]{2})?\b',
            'MONEY': r'\$\d+(?:,\d{3})*(?:\.\d{2})?',
            'PERCENT': r'\d+(?:\.\d+)?%',
            'DATE': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            'TIME': r'\b\d{1,2}:\d{2}(?::\d{2})?(?:\s?[AaPp][Mm])?\b',
        }
        
        for entity_type, pattern in entity_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append({
                    'text': match.group(),
                    'type': entity_type,
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.8  # Simplified confidence score
                })
        
        return entities
    
    def _extract_metadata(self, data: Union[str, Dict], config: ExtractionConfig) -> Dict[str, Any]:
        """Extract metadata from data"""
        metadata = {}
        
        if isinstance(data, str):
            metadata.update({
                'length': len(data),
                'word_count': len(data.split()),
                'line_count': data.count('\n') + 1,
                'char_frequency': self._get_char_frequency(data),
                'encoding_hint': self._detect_encoding_hint(data),
                'language_hint': self._detect_language_hint(data),
            })
            
            # Extract file-like metadata if it looks like a file path
            if self._looks_like_filepath(data):
                metadata['file_info'] = self._extract_file_metadata(data)
        
        elif isinstance(data, dict):
            metadata.update({
                'keys_count': len(data.keys()),
                'nested_levels': self._get_nesting_depth(data),
                'data_types': self._get_data_types(data),
                'size_estimate': self._estimate_dict_size(data),
            })
        
        return metadata
    
    def _extract_urls(self, text: str, config: ExtractionConfig) -> List[Dict[str, Any]]:
        """Extract and analyze URLs"""
        urls = []
        pattern = self.common_patterns['url']
        
        matches = re.finditer(pattern, text)
        for match in matches:
            url = match.group()
            parsed = urlparse(url)
            
            url_info = {
                'url': url,
                'scheme': parsed.scheme,
                'domain': parsed.netloc,
                'path': parsed.path,
                'query': dict(parse_qs(parsed.query)) if parsed.query else {},
                'fragment': parsed.fragment,
                'start': match.start(),
                'end': match.end(),
            }
            
            if config.include_context:
                context_start = max(0, match.start() - config.context_length)
                context_end = min(len(text), match.end() + config.context_length)
                url_info['context'] = text[context_start:context_end]
            
            urls.append(url_info)
        
        return urls
    
    def _extract_emails(self, text: str, config: ExtractionConfig) -> List[Dict[str, Any]]:
        """Extract and analyze email addresses"""
        emails = []
        pattern = self.common_patterns['email']
        
        matches = re.finditer(pattern, text)
        for match in matches:
            email = match.group()
            username, domain = email.split('@')
            
            email_info = {
                'email': email,
                'username': username,
                'domain': domain,
                'tld': domain.split('.')[-1] if '.' in domain else '',
                'start': match.start(),
                'end': match.end(),
            }
            
            if config.include_context:
                context_start = max(0, match.start() - config.context_length)
                context_end = min(len(text), match.end() + config.context_length)
                email_info['context'] = text[context_start:context_end]
            
            emails.append(email_info)
        
        return emails
    
    def _extract_phones(self, text: str, config: ExtractionConfig) -> List[Dict[str, Any]]:
        """Extract and analyze phone numbers"""
        phones = []
        pattern = self.common_patterns['phone']
        
        matches = re.finditer(pattern, text)
        for match in matches:
            phone = match.group()
            groups = match.groups()
            
            phone_info = {
                'phone': phone,
                'country_code': groups[0] if groups[0] else '',
                'area_code': groups[1] if len(groups) > 1 else '',
                'exchange': groups[2] if len(groups) > 2 else '',
                'number': groups[3] if len(groups) > 3 else '',
                'formatted': self._format_phone(groups),
                'start': match.start(),
                'end': match.end(),
            }
            
            if config.include_context:
                context_start = max(0, match.start() - config.context_length)
                context_end = min(len(text), match.end() + config.context_length)
                phone_info['context'] = text[context_start:context_end]
            
            phones.append(phone_info)
        
        return phones
    
    def _extract_dates(self, text: str, config: ExtractionConfig) -> List[Dict[str, Any]]:
        """Extract and analyze dates"""
        dates = []
        
        date_patterns = {
            'iso': self.common_patterns['date_iso'],
            'us': self.common_patterns['date_us'],
            'eu': self.common_patterns['date_eu'],
        }
        
        for date_format, pattern in date_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                date_str = match.group()
                
                date_info = {
                    'date': date_str,
                    'format': date_format,
                    'normalized': self._normalize_date(date_str, date_format),
                    'start': match.start(),
                    'end': match.end(),
                }
                
                if config.include_context:
                    context_start = max(0, match.start() - config.context_length)
                    context_end = min(len(text), match.end() + config.context_length)
                    date_info['context'] = text[context_start:context_end]
                
                dates.append(date_info)
        
        return dates
    
    def _extract_numbers(self, text: str, config: ExtractionConfig) -> List[Dict[str, Any]]:
        """Extract and analyze numbers"""
        numbers = []
        
        number_patterns = {
            'integer': r'-?\d+',
            'decimal': r'-?\d+\.\d+',
            'scientific': r'-?\d+(?:\.\d+)?[eE][+-]?\d+',
            'currency': self.common_patterns['currency'],
            'percentage': r'\d+(?:\.\d+)?%',
        }
        
        for number_type, pattern in number_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                number_str = match.group()
                
                number_info = {
                    'number': number_str,
                    'type': number_type,
                    'value': self._parse_number_value(number_str, number_type),
                    'start': match.start(),
                    'end': match.end(),
                }
                
                if config.include_context:
                    context_start = max(0, match.start() - config.context_length)
                    context_end = min(len(text), match.end() + config.context_length)
                    number_info['context'] = text[context_start:context_end]
                
                numbers.append(number_info)
        
        return numbers
    
    def _extract_json_paths(self, data: Union[str, Dict], config: ExtractionConfig) -> Dict[str, Any]:
        """Extract data using JSON paths"""
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return {'error': 'Invalid JSON'}
        
        paths = config.patterns or []
        results = {}
        
        for path in paths:
            value = self._get_json_path_value(data, path)
            results[path] = value
        
        return results
    
    def _extract_xml_elements(self, data: str, config: ExtractionConfig) -> List[Dict[str, Any]]:
        """Extract XML elements"""
        try:
            root = ET.fromstring(data)
            return self._extract_from_xml(root, config)
        except ET.ParseError as e:
            return {'error': f'XML parsing error: {str(e)}'}
    
    def _extract_html_elements(self, data: str, config: ExtractionConfig) -> List[Dict[str, Any]]:
        """Extract HTML elements (simplified)"""
        # This would require a proper HTML parser like BeautifulSoup
        # For now, using regex (not recommended for production)
        elements = []
        
        # Extract common HTML elements
        html_patterns = {
            'links': r'<a\s+[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>',
            'images': r'<img\s+[^>]*src=["\']([^"\']*)["\'][^>]*>',
            'headers': r'<h[1-6][^>]*>(.*?)</h[1-6]>',
            'paragraphs': r'<p[^>]*>(.*?)</p>',
        }
        
        for element_type, pattern in html_patterns.items():
            matches = re.finditer(pattern, data, re.IGNORECASE | re.DOTALL)
            for match in matches:
                element_info = {
                    'type': element_type,
                    'full_match': match.group(),
                    'groups': match.groups(),
                    'start': match.start(),
                    'end': match.end(),
                }
                elements.append(element_info)
        
        return elements
    
    def _extract_table_data(self, data: str, config: ExtractionConfig) -> List[List[str]]:
        """Extract table data from CSV or similar formats"""
        try:
            # Try parsing as CSV
            import io
            csv_reader = csv.reader(io.StringIO(data))
            return [row for row in csv_reader]
        except Exception as e:
            return {'error': f'Table parsing error: {str(e)}'}
    
    # Helper methods
    def _extract_from_dict(self, data: Dict, config: ExtractionConfig) -> Dict[str, Any]:
        """Extract data from dictionary"""
        extracted = {}
        
        # Extract all key-value pairs with metadata
        for key, value in data.items():
            extracted[key] = {
                'value': value,
                'type': type(value).__name__,
                'size': len(str(value)),
            }
            
            if isinstance(value, dict):
                extracted[key]['nested'] = True
                extracted[key]['keys_count'] = len(value)
            elif isinstance(value, list):
                extracted[key]['list'] = True
                extracted[key]['items_count'] = len(value)
        
        return extracted
    
    def _extract_from_xml(self, root: ET.Element, config: ExtractionConfig) -> Dict[str, Any]:
        """Extract data from XML element"""
        def element_to_dict(elem):
            result = {
                'tag': elem.tag,
                'attributes': elem.attrib,
                'text': elem.text.strip() if elem.text else '',
                'children': []
            }
            
            for child in elem:
                result['children'].append(element_to_dict(child))
            
            return result
        
        return element_to_dict(root)
    
    def _extract_from_csv_string(self, data: str, config: ExtractionConfig) -> Dict[str, Any]:
        """Extract structured data from CSV string"""
        import io
        
        csv_data = list(csv.reader(io.StringIO(data)))
        
        if not csv_data:
            return {'error': 'Empty CSV data'}
        
        headers = csv_data[0] if csv_data else []
        rows = csv_data[1:] if len(csv_data) > 1 else []
        
        return {
            'headers': headers,
            'rows': rows,
            'row_count': len(rows),
            'column_count': len(headers),
            'as_dicts': [dict(zip(headers, row)) for row in rows] if headers else []
        }
    
    def _extract_from_list(self, data: List, config: ExtractionConfig) -> Dict[str, Any]:
        """Extract data from list"""
        return {
            'items_count': len(data),
            'data_types': list(set(type(item).__name__ for item in data)),
            'sample_items': data[:5],  # First 5 items as sample
            'has_nested': any(isinstance(item, (dict, list)) for item in data)
        }
    
    def _get_char_frequency(self, text: str) -> Dict[str, int]:
        """Get character frequency distribution"""
        freq = {}
        for char in text:
            freq[char] = freq.get(char, 0) + 1
        
        # Return top 10 most frequent characters
        sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_freq[:10])
    
    def _detect_encoding_hint(self, text: str) -> str:
        """Detect encoding hints from text"""
        # Check for common encoding indicators
        if any(ord(c) > 127 for c in text):
            return 'non_ascii'
        return 'ascii'
    
    def _detect_language_hint(self, text: str) -> str:
        """Detect language hints (very simplified)"""
        # Very basic language detection based on common words
        english_words = ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with']
        spanish_words = ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no']
        
        text_lower = text.lower()
        english_count = sum(text_lower.count(word) for word in english_words)
        spanish_count = sum(text_lower.count(word) for word in spanish_words)
        
        if english_count > spanish_count:
            return 'likely_english'
        elif spanish_count > english_count:
            return 'likely_spanish'
        else:
            return 'unknown'
    
    def _looks_like_filepath(self, text: str) -> bool:
        """Check if text looks like a file path"""
        return ('/' in text or '\\' in text) and '.' in text and len(text.split()) == 1
    
    def _extract_file_metadata(self, filepath: str) -> Dict[str, Any]:
        """Extract metadata from file path"""
        import os
        
        return {
            'basename': os.path.basename(filepath),
            'dirname': os.path.dirname(filepath),
            'extension': os.path.splitext(filepath)[1],
            'mime_type': mimetypes.guess_type(filepath)[0],
        }
    
    def _get_nesting_depth(self, data: Dict, current_depth: int = 0) -> int:
        """Get maximum nesting depth of dictionary"""
        if not isinstance(data, dict):
            return current_depth
        
        if not data:
            return current_depth
        
        return max(
            self._get_nesting_depth(value, current_depth + 1) 
            if isinstance(value, dict) else current_depth + 1
            for value in data.values()
        )
    
    def _get_data_types(self, data: Dict) -> Dict[str, int]:
        """Get distribution of data types in dictionary"""
        type_counts = {}
        
        def count_types(obj):
            if isinstance(obj, dict):
                for value in obj.values():
                    count_types(value)
            elif isinstance(obj, list):
                for item in obj:
                    count_types(item)
            else:
                type_name = type(obj).__name__
                type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        count_types(data)
        return type_counts
    
    def _estimate_dict_size(self, data: Dict) -> int:
        """Estimate size of dictionary in bytes"""
        return len(json.dumps(data, default=str))
    
    def _format_phone(self, groups: tuple) -> str:
        """Format phone number groups"""
        if len(groups) >= 4:
            area = groups[1] or ''
            exchange = groups[2] or ''
            number = groups[3] or ''
            
            if area and exchange and number:
                return f"({area}) {exchange}-{number}"
        
        return ''.join(str(g) for g in groups if g)
    
    def _normalize_date(self, date_str: str, date_format: str) -> str:
        """Normalize date to ISO format"""
        try:
            if date_format == 'iso':
                return date_str
            elif date_format == 'us':
                # MM/DD/YYYY to YYYY-MM-DD
                parts = date_str.split('/')
                if len(parts) == 3:
                    return f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
            elif date_format == 'eu':
                # DD.MM.YYYY to YYYY-MM-DD
                parts = date_str.split('.')
                if len(parts) == 3:
                    return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
        except Exception:
            pass
        
        return date_str
    
    def _parse_number_value(self, number_str: str, number_type: str) -> Union[int, float, str]:
        """Parse number string to appropriate type"""
        try:
            if number_type == 'integer':
                return int(number_str)
            elif number_type == 'decimal':
                return float(number_str)
            elif number_type == 'scientific':
                return float(number_str)
            elif number_type == 'currency':
                # Remove $ and commas
                clean_str = re.sub(r'[$,]', '', number_str)
                return float(clean_str)
            elif number_type == 'percentage':
                # Remove % and convert to decimal
                clean_str = number_str.replace('%', '')
                return float(clean_str) / 100
        except ValueError:
            pass
        
        return number_str
    
    def _get_json_path_value(self, data: Dict, path: str) -> Any:
        """Get value from dictionary using JSON path (simplified)"""
        try:
            keys = path.split('.')
            current = data
            
            for key in keys:
                if isinstance(current, dict):
                    current = current.get(key)
                elif isinstance(current, list) and key.isdigit():
                    current = current[int(key)]
                else:
                    return None
            
            return current
        except (KeyError, IndexError, TypeError):
            return None
    
    def _merge_config(self, kwargs: Dict[str, Any]) -> ExtractionConfig:
        """Merge kwargs with default config"""
        config_dict = {
            'extraction_type': kwargs.get('extraction_type', self.config.extraction_type),
            'patterns': kwargs.get('patterns', self.config.patterns),
            'case_sensitive': kwargs.get('case_sensitive', self.config.case_sensitive),
            'include_context': kwargs.get('include_context', self.config.include_context),
            'context_length': kwargs.get('context_length', self.config.context_length),
            'output_format': kwargs.get('output_format', self.config.output_format),
            'custom_extractors': kwargs.get('custom_extractors', self.config.custom_extractors)
        }
        return ExtractionConfig(**config_dict)
    
    def get_extraction_stats(self, results: Union[List, Dict]) -> Dict[str, Any]:
        """Get statistics about extraction results"""
        if isinstance(results, list):
            return {
                'total_matches': len(results),
                'result_type': 'list',
                'sample_results': results[:3] if results else [],
                'has_context': any('context' in item for item in results if isinstance(item, dict))
            }
        elif isinstance(results, dict):
            return {
                'keys_count': len(results),
                'result_type': 'dict',
                'keys': list(results.keys())[:10],  # First 10 keys
                'has_errors': 'error' in results
            }
        else:
            return {
                'result_type': type(results).__name__,
                'size': len(str(results))
            }