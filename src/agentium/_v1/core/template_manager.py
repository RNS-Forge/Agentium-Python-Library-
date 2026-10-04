"""
Template Manager Module - Standardize outputs

This module provides template management capabilities for standardizing
and formatting outputs across different contexts and formats.
"""

import re
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import jinja2
from pathlib import Path

from ..utils.logger_utils import LoggerUtils


class TemplateType(Enum):
    """Types of templates"""
    TEXT = "text"
    EMAIL = "email"
    REPORT = "report"
    JSON = "json"
    XML = "xml"
    HTML = "html"
    MARKDOWN = "markdown"
    CSV = "csv"


@dataclass
class TemplateConfig:
    """Configuration for template management"""
    template_directory: Optional[str] = None
    auto_escape: bool = True
    strict_undefined: bool = False
    cache_templates: bool = True
    default_encoding: str = "utf-8"


class TemplateManager:
    """
    Advanced template management system for standardized outputs.
    
    Features:
    - Multiple template formats
    - Jinja2 template engine
    - Template inheritance
    - Custom filters and functions
    - Template validation
    - Output formatting
    - Template versioning
    """
    
    def __init__(self, config: Optional[TemplateConfig] = None):
        self.config = config or TemplateConfig()
        self.logger = LoggerUtils.get_logger(__name__)
        self.templates: Dict[str, Dict] = {}
        self._setup_jinja_env()
    
    def _setup_jinja_env(self):
        """Setup Jinja2 environment"""
        if self.config.template_directory:
            loader = jinja2.FileSystemLoader(self.config.template_directory)
        else:
            loader = jinja2.DictLoader({})
        
        self.jinja_env = jinja2.Environment(
            loader=loader,
            autoescape=self.config.auto_escape,
            undefined=jinja2.StrictUndefined if self.config.strict_undefined else jinja2.Undefined,
            cache_size=100 if self.config.cache_templates else 0
        )
        
        # Add custom filters
        self.jinja_env.filters['dateformat'] = self._date_format
        self.jinja_env.filters['currency'] = self._currency_format
        self.jinja_env.filters['percentage'] = self._percentage_format
        self.jinja_env.filters['truncate_smart'] = self._smart_truncate
        
        # Add custom functions
        self.jinja_env.globals['now'] = datetime.now
        self.jinja_env.globals['format_list'] = self._format_list
    
    @LoggerUtils.log_operation("create_template")
    def create_template(self, name: str, content: str, template_type: TemplateType = TemplateType.TEXT, **kwargs) -> str:
        """
        Create a new template
        
        Args:
            name: Template name
            content: Template content
            template_type: Type of template
            **kwargs: Additional template metadata
            
        Returns:
            Template ID
        """
        template_id = f"{name}_{template_type.value}_{int(datetime.now().timestamp())}"
        
        template = {
            'id': template_id,
            'name': name,
            'content': content,
            'type': template_type,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'version': 1,
            'metadata': kwargs,
            'usage_count': 0
        }
        
        # Validate template
        self._validate_template(template)
        
        self.templates[template_id] = template
        
        # Add to Jinja environment if it's a text-based template
        if template_type in [TemplateType.TEXT, TemplateType.EMAIL, TemplateType.HTML, TemplateType.MARKDOWN]:
            self.jinja_env.loader.mapping[template_id] = content
        
        self.logger.info(f"Created template '{name}' of type {template_type.value}")
        return template_id
    
    @LoggerUtils.log_operation("render_template")
    def render(self, template_id: str, data: Dict[str, Any], **kwargs) -> str:
        """
        Render a template with data
        
        Args:
            template_id: ID of template to render
            data: Data to render template with
            **kwargs: Additional rendering options
            
        Returns:
            Rendered template content
        """
        if template_id not in self.templates:
            raise ValueError(f"Template {template_id} not found")
        
        template_info = self.templates[template_id]
        template_info['usage_count'] += 1
        
        self.logger.info(f"Rendering template: {template_info['name']}")
        
        try:
            if template_info['type'] == TemplateType.JSON:
                return self._render_json_template(template_info, data, **kwargs)
            elif template_info['type'] == TemplateType.XML:
                return self._render_xml_template(template_info, data, **kwargs)
            elif template_info['type'] == TemplateType.CSV:
                return self._render_csv_template(template_info, data, **kwargs)
            else:
                # Use Jinja2 for text-based templates
                template = self.jinja_env.get_template(template_id)
                return template.render(data, **kwargs)
                
        except Exception as e:
            self.logger.error(f"Template rendering failed: {str(e)}")
            raise
    
    def _render_json_template(self, template_info: Dict, data: Dict[str, Any], **kwargs) -> str:
        """Render JSON template"""
        template_content = template_info['content']
        
        # Simple variable substitution for JSON
        rendered = template_content
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, json.dumps(value))
        
        # Validate JSON
        try:
            json.loads(rendered)
        except json.JSONDecodeError as e:
            raise ValueError(f"Rendered JSON template is invalid: {str(e)}")
        
        return rendered
    
    def _render_xml_template(self, template_info: Dict, data: Dict[str, Any], **kwargs) -> str:
        """Render XML template"""
        template_content = template_info['content']
        
        # Simple variable substitution for XML
        rendered = template_content
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            # Escape XML special characters
            escaped_value = str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            rendered = rendered.replace(placeholder, escaped_value)
        
        return rendered
    
    def _render_csv_template(self, template_info: Dict, data: Dict[str, Any], **kwargs) -> str:
        """Render CSV template"""
        import csv
        import io
        
        template_content = template_info['content']
        
        # Parse CSV template structure
        lines = template_content.strip().split('\n')
        header = lines[0] if lines else ""
        row_template = lines[1] if len(lines) > 1 else ""
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        if header:
            header_fields = [field.strip() for field in header.split(',')]
            writer.writerow(header_fields)
        
        # Write data rows
        if 'rows' in data and isinstance(data['rows'], list):
            for row_data in data['rows']:
                # Render row template with row data
                rendered_row = row_template
                for key, value in row_data.items():
                    placeholder = f"{{{{{key}}}}}"
                    rendered_row = rendered_row.replace(placeholder, str(value))
                
                # Parse and write row
                row_fields = [field.strip() for field in rendered_row.split(',')]
                writer.writerow(row_fields)
        
        return output.getvalue()
    
    def create_from_file(self, file_path: str, name: Optional[str] = None, template_type: Optional[TemplateType] = None, **kwargs) -> str:
        """Create template from file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Template file not found: {file_path}")
        
        content = file_path.read_text(encoding=self.config.default_encoding)
        
        # Auto-detect template type from extension
        if template_type is None:
            extension_map = {
                '.json': TemplateType.JSON,
                '.xml': TemplateType.XML,
                '.html': TemplateType.HTML,
                '.md': TemplateType.MARKDOWN,
                '.csv': TemplateType.CSV,
                '.txt': TemplateType.TEXT
            }
            template_type = extension_map.get(file_path.suffix.lower(), TemplateType.TEXT)
        
        template_name = name or file_path.stem
        
        return self.create_template(template_name, content, template_type, **kwargs)
    
    def update_template(self, template_id: str, content: Optional[str] = None, **kwargs):
        """Update existing template"""
        if template_id not in self.templates:
            raise ValueError(f"Template {template_id} not found")
        
        template = self.templates[template_id]
        
        if content is not None:
            template['content'] = content
            template['version'] += 1
            
            # Update in Jinja environment
            if template['type'] in [TemplateType.TEXT, TemplateType.EMAIL, TemplateType.HTML, TemplateType.MARKDOWN]:
                self.jinja_env.loader.mapping[template_id] = content
        
        template['updated_at'] = datetime.now()
        template['metadata'].update(kwargs)
        
        # Validate updated template
        self._validate_template(template)
        
        self.logger.info(f"Updated template: {template['name']}")
    
    def delete_template(self, template_id: str):
        """Delete template"""
        if template_id not in self.templates:
            raise ValueError(f"Template {template_id} not found")
        
        template = self.templates[template_id]
        
        # Remove from Jinja environment
        if template_id in self.jinja_env.loader.mapping:
            del self.jinja_env.loader.mapping[template_id]
        
        del self.templates[template_id]
        self.logger.info(f"Deleted template: {template['name']}")
    
    def list_templates(self, template_type: Optional[TemplateType] = None) -> List[Dict[str, Any]]:
        """List available templates"""
        templates = list(self.templates.values())
        
        if template_type:
            templates = [t for t in templates if t['type'] == template_type]
        
        return [{
            'id': t['id'],
            'name': t['name'],
            'type': t['type'].value,
            'created_at': t['created_at'].isoformat(),
            'updated_at': t['updated_at'].isoformat(),
            'version': t['version'],
            'usage_count': t['usage_count']
        } for t in templates]
    
    def get_template_info(self, template_id: str) -> Dict[str, Any]:
        """Get template information"""
        if template_id not in self.templates:
            raise ValueError(f"Template {template_id} not found")
        
        template = self.templates[template_id]
        
        return {
            'id': template['id'],
            'name': template['name'],
            'type': template['type'].value,
            'created_at': template['created_at'].isoformat(),
            'updated_at': template['updated_at'].isoformat(),
            'version': template['version'],
            'usage_count': template['usage_count'],
            'metadata': template['metadata'],
            'content_preview': template['content'][:200] + '...' if len(template['content']) > 200 else template['content']
        }
    
    def create_email_template(self, name: str, subject: str, body: str, **kwargs) -> str:
        """Create email-specific template"""
        email_template = f"""Subject: {subject}

{body}"""
        
        return self.create_template(name, email_template, TemplateType.EMAIL, **kwargs)
    
    def create_report_template(self, name: str, title: str, sections: List[str], **kwargs) -> str:
        """Create report template"""
        report_content = """# """ + title + """

Generated on: {{ now().strftime('%Y-%m-%d %H:%M:%S') }}

{% for section in sections %}
## {{ section.title }}
{{ section.content }}

{% endfor %}

---
Report generated by Agentium Template Manager
"""
        
        return self.create_template(name, report_content, TemplateType.REPORT, **kwargs)
    
    def render_with_fallback(self, template_id: str, data: Dict[str, Any], fallback_template: Optional[str] = None, **kwargs) -> str:
        """Render template with fallback option"""
        try:
            return self.render(template_id, data, **kwargs)
        except Exception as e:
            self.logger.warning(f"Primary template failed, using fallback: {str(e)}")
            
            if fallback_template:
                return self.render(fallback_template, data, **kwargs)
            else:
                # Create simple fallback
                fallback_content = json.dumps(data, indent=2, default=str)
                return f"Template rendering failed. Raw data:\n{fallback_content}"
    
    def _validate_template(self, template: Dict):
        """Validate template content"""
        content = template['content']
        template_type = template['type']
        
        try:
            if template_type == TemplateType.JSON:
                # Check if it's valid JSON structure (with placeholders)
                test_content = re.sub(r'\{\{[^}]+\}\}', '"placeholder"', content)
                json.loads(test_content)
            
            elif template_type in [TemplateType.TEXT, TemplateType.EMAIL, TemplateType.HTML, TemplateType.MARKDOWN]:
                # Validate Jinja2 syntax
                self.jinja_env.parse(content)
                
        except Exception as e:
            raise ValueError(f"Template validation failed: {str(e)}")
    
    # Custom Jinja2 filters and functions
    def _date_format(self, date_value, format_string='%Y-%m-%d'):
        """Format date filter"""
        if isinstance(date_value, str):
            try:
                date_value = datetime.fromisoformat(date_value)
            except ValueError:
                return date_value
        
        if hasattr(date_value, 'strftime'):
            return date_value.strftime(format_string)
        
        return str(date_value)
    
    def _currency_format(self, value, currency='$'):
        """Format currency filter"""
        try:
            num_value = float(value)
            return f"{currency}{num_value:,.2f}"
        except (ValueError, TypeError):
            return str(value)
    
    def _percentage_format(self, value, decimals=1):
        """Format percentage filter"""
        try:
            num_value = float(value)
            return f"{num_value:.{decimals}f}%"
        except (ValueError, TypeError):
            return str(value)
    
    def _smart_truncate(self, text, length=100, suffix='...'):
        """Smart truncation filter"""
        if len(text) <= length:
            return text
        
        # Try to truncate at word boundary
        truncated = text[:length - len(suffix)]
        last_space = truncated.rfind(' ')
        
        if last_space > length * 0.8:  # If we can truncate at a reasonable word boundary
            return truncated[:last_space] + suffix
        else:
            return truncated + suffix
    
    def _format_list(self, items, separator=', ', conjunction='and'):
        """Format list with proper conjunction"""
        if not items:
            return ''
        
        if len(items) == 1:
            return str(items[0])
        
        if len(items) == 2:
            return f"{items[0]} {conjunction} {items[1]}"
        
        return f"{separator.join(str(item) for item in items[:-1])}{separator}{conjunction} {items[-1]}"
    
    def export_templates(self, file_path: str, template_ids: Optional[List[str]] = None):
        """Export templates to file"""
        templates_to_export = {}
        
        if template_ids:
            for template_id in template_ids:
                if template_id in self.templates:
                    templates_to_export[template_id] = self.templates[template_id]
        else:
            templates_to_export = self.templates.copy()
        
        # Convert datetime objects to strings for JSON serialization
        export_data = {}
        for template_id, template in templates_to_export.items():
            export_template = template.copy()
            export_template['created_at'] = template['created_at'].isoformat()
            export_template['updated_at'] = template['updated_at'].isoformat()
            export_template['type'] = template['type'].value
            export_data[template_id] = export_template
        
        with open(file_path, 'w', encoding=self.config.default_encoding) as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Exported {len(export_data)} templates to {file_path}")
    
    def import_templates(self, file_path: str, overwrite: bool = False):
        """Import templates from file"""
        with open(file_path, 'r', encoding=self.config.default_encoding) as f:
            import_data = json.load(f)
        
        imported_count = 0
        for template_id, template_data in import_data.items():
            if template_id in self.templates and not overwrite:
                self.logger.warning(f"Template {template_id} already exists, skipping")
                continue
            
            # Convert back from JSON format
            template_data['created_at'] = datetime.fromisoformat(template_data['created_at'])
            template_data['updated_at'] = datetime.fromisoformat(template_data['updated_at'])
            template_data['type'] = TemplateType(template_data['type'])
            
            self.templates[template_id] = template_data
            
            # Add to Jinja environment if applicable
            if template_data['type'] in [TemplateType.TEXT, TemplateType.EMAIL, TemplateType.HTML, TemplateType.MARKDOWN]:
                self.jinja_env.loader.mapping[template_id] = template_data['content']
            
            imported_count += 1
        
        self.logger.info(f"Imported {imported_count} templates from {file_path}")
    
    def get_template_stats(self) -> Dict[str, Any]:
        """Get template usage statistics"""
        total_templates = len(self.templates)
        by_type = {}
        total_usage = 0
        
        for template in self.templates.values():
            template_type = template['type'].value
            by_type[template_type] = by_type.get(template_type, 0) + 1
            total_usage += template['usage_count']
        
        most_used = max(self.templates.values(), key=lambda t: t['usage_count']) if self.templates else None
        
        return {
            'total_templates': total_templates,
            'by_type': by_type,
            'total_usage': total_usage,
            'average_usage': total_usage / total_templates if total_templates > 0 else 0,
            'most_used_template': {
                'name': most_used['name'],
                'usage_count': most_used['usage_count']
            } if most_used else None
        }