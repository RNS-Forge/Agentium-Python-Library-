"""
Optimizer Module - Refine text, code, workflows

This module provides optimization capabilities for text, code,
and workflow refinement to improve performance and quality.
"""

import re
import ast
import json
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import time

from ..utils.logger_utils import LoggerUtils


class OptimizationType(Enum):
    """Types of optimization available"""
    TEXT = "text"
    CODE = "code"
    WORKFLOW = "workflow"
    JSON = "json"
    QUERY = "query"


@dataclass
class OptimizationConfig:
    """Configuration for optimization operations"""
    optimization_type: OptimizationType = OptimizationType.TEXT
    target_metric: str = "readability"  # readability, performance, conciseness
    preserve_meaning: bool = True
    aggressive_mode: bool = False
    language: str = "en"
    custom_rules: List[Dict[str, Any]] = None


# Alias for consistent naming
OptimizerConfig = OptimizationConfig


class Optimizer:
    """
    Advanced optimizer for text, code, and workflows.
    
    Features:
    - Text optimization for readability and conciseness
    - Code optimization for performance and style
    - Workflow optimization for efficiency
    - JSON structure optimization
    - Query optimization for databases and APIs
    """
    
    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or OptimizationConfig()
        self.logger = LoggerUtils.get_logger(__name__)
        self._setup_optimizers()
    
    def _setup_optimizers(self):
        """Initialize optimization strategies"""
        self.text_rules = self._load_text_rules()
        self.code_rules = self._load_code_rules()
        self.workflow_rules = self._load_workflow_rules()
    
    def optimize(self, content: str, optimization_type: Optional[OptimizationType] = None, **kwargs) -> Dict[str, Any]:
        """
        Main optimization method
        
        Args:
            content: Content to optimize
            optimization_type: Type of optimization to apply
            **kwargs: Additional optimization parameters
            
        Returns:
            Optimized content
        """
        opt_type = optimization_type or self.config.optimization_type
        
        self.logger.info(f"Starting {opt_type.value} optimization")
        
        with LoggerUtils.create_operation_context(f"optimize_{opt_type.value}") as ctx:
            if opt_type == OptimizationType.TEXT:
                result = self.optimize_text(content, **kwargs)
            elif opt_type == OptimizationType.CODE:
                result = self.optimize_code(content, **kwargs)
            elif opt_type == OptimizationType.WORKFLOW:
                result = self.optimize_workflow(content, **kwargs)
            elif opt_type == OptimizationType.JSON:
                result = self.optimize_json(content, **kwargs)
            elif opt_type == OptimizationType.QUERY:
                result = self.optimize_query(content, **kwargs)
            else:
                raise ValueError(f"Unsupported optimization type: {opt_type}")
            
            # Track improvements made
            improvements = []
            if len(result) != len(content):
                improvements.append(f"Length changed from {len(content)} to {len(result)}")
            if result != content:
                improvements.append(f"{opt_type.value} optimization applied")
            
            ctx.log(f"Optimization completed", extra={
                'original_length': len(content),
                'optimized_length': len(result),
                'compression_ratio': len(result) / len(content) if content else 0
            })
        
        return {
            'text': result,
            'improvements': improvements,
            'stats': {
                'original_length': len(content),
                'optimized_length': len(result),
                'optimization_type': opt_type.value
            },
            'success': True
        }
    
    def optimize_text(self, text: str, **kwargs) -> str:
        """Optimize text for readability and conciseness"""
        target_metric = kwargs.get('target_metric', self.config.target_metric)
        
        # Apply text optimization rules
        optimized = text
        
        if target_metric == "readability":
            optimized = self._optimize_for_readability(optimized)
        elif target_metric == "conciseness":
            optimized = self._optimize_for_conciseness(optimized)
        elif target_metric == "performance":
            optimized = self._optimize_for_performance(optimized)
        
        # Apply general text rules
        optimized = self._apply_text_rules(optimized)
        
        return optimized
    
    def _optimize_for_readability(self, text: str) -> str:
        """Optimize text for better readability"""
        # Break long sentences
        text = self._break_long_sentences(text)
        
        # Simplify complex words
        text = self._simplify_vocabulary(text)
        
        # Improve paragraph structure
        text = self._improve_paragraphs(text)
        
        # Fix grammar issues
        text = self._fix_grammar(text)
        
        return text
    
    def _optimize_for_conciseness(self, text: str) -> str:
        """Optimize text for conciseness"""
        # Remove redundant words
        text = self._remove_redundancy(text)
        
        # Combine similar sentences
        text = self._combine_sentences(text)
        
        # Replace verbose phrases
        text = self._replace_verbose_phrases(text)
        
        return text
    
    def _optimize_for_performance(self, text: str) -> str:
        """Optimize text for processing performance"""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove unnecessary punctuation
        text = re.sub(r'[.]{2,}', '...', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        return text.strip()
    
    def optimize_code(self, code: str, language: str = "python", **kwargs) -> str:
        """Optimize code for performance and style"""
        if language.lower() == "python":
            return self._optimize_python_code(code, **kwargs)
        elif language.lower() == "javascript":
            return self._optimize_javascript_code(code, **kwargs)
        elif language.lower() == "sql":
            return self._optimize_sql_code(code, **kwargs)
        else:
            return self._optimize_generic_code(code, **kwargs)
    
    def _optimize_python_code(self, code: str, **kwargs) -> str:
        """Optimize Python code"""
        try:
            tree = ast.parse(code)
            optimizer = PythonCodeOptimizer()
            optimized_tree = optimizer.visit(tree)
            return ast.unparse(optimized_tree)
        except SyntaxError:
            self.logger.warning("Invalid Python syntax, applying basic optimizations")
            return self._apply_basic_code_optimizations(code)
    
    def _optimize_javascript_code(self, code: str, **kwargs) -> str:
        """Optimize JavaScript code"""
        # Basic JavaScript optimizations
        optimizations = [
            # Remove console.log statements in production
            (r'console\.log\([^)]*\);?\s*', ''),
            # Simplify boolean comparisons
            (r'== true', ''),
            (r'== false', ' === false'),
            # Remove extra semicolons
            (r';;+', ';'),
        ]
        
        optimized = code
        for pattern, replacement in optimizations:
            optimized = re.sub(pattern, replacement, optimized)
        
        return optimized
    
    def _optimize_sql_code(self, code: str, **kwargs) -> str:
        """Optimize SQL queries"""
        # Basic SQL optimizations
        optimized = code.upper()
        
        # Add proper formatting
        keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'GROUP BY', 'ORDER BY', 'HAVING']
        for keyword in keywords:
            optimized = re.sub(f'\\b{keyword}\\b', f'\n{keyword}', optimized)
        
        # Remove extra whitespace
        optimized = re.sub(r'\s+', ' ', optimized)
        
        return optimized.strip()
    
    def optimize_workflow(self, workflow_data: Union[str, Dict[str, Any]], **kwargs) -> Union[str, Dict[str, Any]]:
        """Optimize workflow definitions"""
        if isinstance(workflow_data, str):
            try:
                workflow = json.loads(workflow_data)
                optimized = self._optimize_workflow_dict(workflow, **kwargs)
                return json.dumps(optimized, indent=2)
            except json.JSONDecodeError:
                return workflow_data
        else:
            return self._optimize_workflow_dict(workflow_data, **kwargs)
    
    def _optimize_workflow_dict(self, workflow: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Optimize workflow dictionary"""
        optimized = workflow.copy()
        
        # Remove redundant steps
        optimized = self._remove_redundant_steps(optimized)
        
        # Optimize step ordering
        optimized = self._optimize_step_order(optimized)
        
        # Merge compatible steps
        optimized = self._merge_compatible_steps(optimized)
        
        # Add error handling
        optimized = self._add_error_handling(optimized)
        
        return optimized
    
    def optimize_json(self, json_data: Union[str, Dict[str, Any]], **kwargs) -> Union[str, Dict[str, Any]]:
        """Optimize JSON structure"""
        if isinstance(json_data, str):
            try:
                data = json.loads(json_data)
                optimized = self._optimize_json_dict(data, **kwargs)
                return json.dumps(optimized, separators=(',', ':'))
            except json.JSONDecodeError:
                return json_data
        else:
            return self._optimize_json_dict(json_data, **kwargs)
    
    def _optimize_json_dict(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Optimize JSON dictionary structure"""
        # Remove null/empty values if specified
        if kwargs.get('remove_empty', True):
            data = self._remove_empty_values(data)
        
        # Flatten nested structures if possible
        if kwargs.get('flatten', False):
            data = self._flatten_json(data)
        
        # Sort keys for consistency
        if kwargs.get('sort_keys', True):
            data = dict(sorted(data.items()))
        
        return data
    
    def optimize_query(self, query: str, query_type: str = "search", **kwargs) -> str:
        """Optimize queries for better performance"""
        if query_type == "search":
            return self._optimize_search_query(query, **kwargs)
        elif query_type == "database":
            return self._optimize_sql_code(query, **kwargs)
        elif query_type == "api":
            return self._optimize_api_query(query, **kwargs)
        else:
            return query
    
    def _optimize_search_query(self, query: str, **kwargs) -> str:
        """Optimize search queries"""
        # Remove stop words if specified
        if kwargs.get('remove_stopwords', True):
            query = self._remove_stopwords(query)
        
        # Add quotes for exact phrases
        if kwargs.get('exact_phrases', False):
            query = self._add_phrase_quotes(query)
        
        # Clean up the query
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query
    
    # Helper methods for optimization rules
    def _load_text_rules(self) -> List[Dict[str, Any]]:
        """Load text optimization rules"""
        return [
            {'pattern': r'\b(very|really|quite|rather|extremely)\s+', 'replacement': '', 'description': 'Remove weak intensifiers'},
            {'pattern': r'\bin order to\b', 'replacement': 'to', 'description': 'Simplify phrases'},
            {'pattern': r'\bdue to the fact that\b', 'replacement': 'because', 'description': 'Simplify phrases'},
            {'pattern': r'\s{2,}', 'replacement': ' ', 'description': 'Normalize whitespace'},
        ]
    
    def _load_code_rules(self) -> List[Dict[str, Any]]:
        """Load code optimization rules"""
        return [
            {'pattern': r'if\s+(.+)\s*==\s*True:', 'replacement': r'if \1:', 'description': 'Simplify boolean checks'},
            {'pattern': r'len\((.+)\)\s*==\s*0', 'replacement': r'not \1', 'description': 'Simplify empty checks'},
        ]
    
    def _load_workflow_rules(self) -> List[Dict[str, Any]]:
        """Load workflow optimization rules"""
        return []
    
    def _apply_text_rules(self, text: str) -> str:
        """Apply text optimization rules"""
        optimized = text
        for rule in self.text_rules:
            optimized = re.sub(rule['pattern'], rule['replacement'], optimized)
        return optimized
    
    def _apply_basic_code_optimizations(self, code: str) -> str:
        """Apply basic code optimizations"""
        optimized = code
        for rule in self.code_rules:
            optimized = re.sub(rule['pattern'], rule['replacement'], optimized)
        return optimized
    
    # Additional helper methods would be implemented here
    def _break_long_sentences(self, text: str) -> str:
        """Break long sentences into shorter ones"""
        # Implementation for breaking long sentences
        return text
    
    def _simplify_vocabulary(self, text: str) -> str:
        """Replace complex words with simpler alternatives"""
        # Implementation for vocabulary simplification
        return text
    
    def _improve_paragraphs(self, text: str) -> str:
        """Improve paragraph structure"""
        # Implementation for paragraph improvement
        return text
    
    def _fix_grammar(self, text: str) -> str:
        """Fix basic grammar issues"""
        # Implementation for grammar fixes
        return text
    
    def _remove_redundancy(self, text: str) -> str:
        """Remove redundant words and phrases"""
        # Implementation for redundancy removal
        return text
    
    def _combine_sentences(self, text: str) -> str:
        """Combine similar sentences"""
        # Implementation for sentence combination
        return text
    
    def _replace_verbose_phrases(self, text: str) -> str:
        """Replace verbose phrases with concise alternatives"""
        verbose_replacements = {
            'in order to': 'to',
            'due to the fact that': 'because',
            'at this point in time': 'now',
            'in the event that': 'if',
            'for the reason that': 'because',
        }
        
        text_lower = text.lower()
        for verbose, concise in verbose_replacements.items():
            text = re.sub(re.escape(verbose), concise, text, flags=re.IGNORECASE)
        
        return text
    
    def _remove_redundant_steps(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Remove redundant steps from workflow"""
        # Implementation for removing redundant workflow steps
        return workflow
    
    def _optimize_step_order(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize the order of workflow steps"""
        # Implementation for optimizing step order
        return workflow
    
    def _merge_compatible_steps(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Merge compatible workflow steps"""
        # Implementation for merging compatible steps
        return workflow
    
    def _add_error_handling(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Add error handling to workflow"""
        # Implementation for adding error handling
        return workflow
    
    def _remove_empty_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove null and empty values from dictionary"""
        cleaned = {}
        for key, value in data.items():
            if value is not None and value != "" and value != []:
                if isinstance(value, dict):
                    cleaned_value = self._remove_empty_values(value)
                    if cleaned_value:
                        cleaned[key] = cleaned_value
                else:
                    cleaned[key] = value
        return cleaned
    
    def _flatten_json(self, data: Dict[str, Any], separator: str = "_") -> Dict[str, Any]:
        """Flatten nested JSON structure"""
        def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = "_") -> Dict[str, Any]:
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
            return dict(items)
        
        return flatten_dict(data, separator=separator)
    
    def _remove_stopwords(self, query: str) -> str:
        """Remove common stopwords from query"""
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        words = query.split()
        filtered_words = [word for word in words if word.lower() not in stopwords]
        return ' '.join(filtered_words)
    
    def _add_phrase_quotes(self, query: str) -> str:
        """Add quotes around phrases in query"""
        # Simple implementation - can be enhanced
        if ' ' in query and not ('"' in query or "'" in query):
            return f'"{query}"'
        return query
    
    def _optimize_api_query(self, query: str, **kwargs) -> str:
        """Optimize API queries"""
        # Remove unnecessary parameters, encode properly, etc.
        return query
    
    def get_optimization_stats(self, original: str, optimized: str) -> Dict[str, Any]:
        """Get optimization statistics"""
        return {
            'original_length': len(original),
            'optimized_length': len(optimized),
            'reduction_ratio': (len(original) - len(optimized)) / len(original) if original else 0,
            'characters_saved': len(original) - len(optimized),
            'lines_original': original.count('\n') + 1,
            'lines_optimized': optimized.count('\n') + 1,
        }


class PythonCodeOptimizer(ast.NodeTransformer):
    """AST-based Python code optimizer"""
    
    def visit_Compare(self, node):
        """Optimize comparison operations"""
        # Optimize == True comparisons
        if (len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq) and
            len(node.comparators) == 1 and
            isinstance(node.comparators[0], ast.Constant) and
            node.comparators[0].value is True):
            return node.left
        
        return self.generic_visit(node)
    
    def visit_Call(self, node):
        """Optimize function calls"""
        # Optimize len(x) == 0 to not x
        if (isinstance(node.func, ast.Name) and node.func.id == 'len' and
            len(node.args) == 1):
            # This would be part of a larger comparison optimization
            pass
        
        return self.generic_visit(node)