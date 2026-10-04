"""
Logger Utils Module - Track and debug operations

This module provides comprehensive logging utilities for tracking,
debugging, and monitoring Agentium operations.
"""

import logging
import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
import functools
from dataclasses import dataclass, asdict


@dataclass
class LogConfig:
    """Configuration for logging setup"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_console: bool = True
    enable_file: bool = True
    json_format: bool = False


# Alias for consistent naming
LoggerConfig = LogConfig


class LoggerUtils:
    """
    Comprehensive logging utility for Agentium operations.
    
    Features:
    - Multiple output formats (text, JSON)
    - File rotation
    - Console and file logging
    - Performance tracking
    - Operation monitoring
    - Structured logging
    """
    
    _loggers: Dict[str, logging.Logger] = {}
    _config: LogConfig = LogConfig()
    
    @classmethod
    def configure(cls, config: LogConfig):
        """Configure global logging settings"""
        cls._config = config
        cls._setup_root_logger()
    
    @classmethod
    def _setup_root_logger(cls):
        """Setup root logger with current configuration"""
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, cls._config.level.upper()))
        
        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Console handler
        if cls._config.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, cls._config.level.upper()))
            
            if cls._config.json_format:
                console_handler.setFormatter(cls._get_json_formatter())
            else:
                console_handler.setFormatter(logging.Formatter(cls._config.format))
            
            root_logger.addHandler(console_handler)
        
        # File handler
        if cls._config.enable_file and cls._config.file_path:
            from logging.handlers import RotatingFileHandler
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(cls._config.file_path), exist_ok=True)
            
            file_handler = RotatingFileHandler(
                cls._config.file_path,
                maxBytes=cls._config.max_file_size,
                backupCount=cls._config.backup_count
            )
            file_handler.setLevel(getattr(logging, cls._config.level.upper()))
            
            if cls._config.json_format:
                file_handler.setFormatter(cls._get_json_formatter())
            else:
                file_handler.setFormatter(logging.Formatter(cls._config.format))
            
            root_logger.addHandler(file_handler)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get or create a logger instance"""
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger
        return cls._loggers[name]
    
    @classmethod
    def _get_json_formatter(cls):
        """Create JSON formatter"""
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                    'name': record.name,
                    'level': record.levelname,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno
                }
                
                # Add exception info if present
                if record.exc_info:
                    log_entry['exception'] = cls.formatException(record.exc_info)
                
                # Add extra fields
                for key, value in record.__dict__.items():
                    if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                                   'pathname', 'filename', 'module', 'exc_info', 
                                   'exc_text', 'stack_info', 'lineno', 'funcName', 
                                   'created', 'msecs', 'relativeCreated', 'thread', 
                                   'threadName', 'processName', 'process', 'getMessage']:
                        log_entry[key] = value
                
                return json.dumps(log_entry)
        
        return JsonFormatter()
    
    @classmethod
    def log_operation(cls, operation_name: str, **kwargs):
        """Decorator for logging operations"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **func_kwargs):
                logger = cls.get_logger(func.__module__)
                start_time = time.time()
                
                # Log operation start
                logger.info(f"Starting operation: {operation_name}", extra={
                    'operation': operation_name,
                    'status': 'start',
                    'args_count': len(args),
                    'kwargs_count': len(func_kwargs),
                    **kwargs
                })
                
                try:
                    result = func(*args, **func_kwargs)
                    duration = time.time() - start_time
                    
                    # Log successful completion
                    logger.info(f"Operation completed: {operation_name}", extra={
                        'operation': operation_name,
                        'status': 'success',
                        'duration': duration,
                        'result_type': type(result).__name__ if result is not None else 'None'
                    })
                    
                    return result
                
                except Exception as e:
                    duration = time.time() - start_time
                    
                    # Log error
                    logger.error(f"Operation failed: {operation_name}", extra={
                        'operation': operation_name,
                        'status': 'error',
                        'duration': duration,
                        'error_type': type(e).__name__,
                        'error_message': str(e)
                    }, exc_info=True)
                    
                    raise
            
            return wrapper
        return decorator
    
    @classmethod
    def log_performance(cls, func_or_name=None, threshold_seconds: float = 1.0):
        """Decorator for logging performance metrics"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                logger = cls.get_logger(func.__module__)
                start_time = time.time()
                
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log if duration exceeds threshold
                if duration >= threshold_seconds:
                    logger.warning(f"Slow operation detected: {func.__name__}", extra={
                        'function': func.__name__,
                        'duration': duration,
                        'threshold': threshold_seconds,
                        'performance_issue': True
                    })
                else:
                    logger.debug(f"Performance: {func.__name__}", extra={
                        'function': func.__name__,
                        'duration': duration
                    })
                
                return result
            return wrapper
        
        if func_or_name is None:
            return decorator
        elif callable(func_or_name):
            return decorator(func_or_name)
        else:
            # If string passed, use it as operation name
            return decorator
    
    @classmethod
    def log_data_flow(cls, data: Any, stage: str, operation: str = None):
        """Log data flow through operations"""
        logger = cls.get_logger('agentium.data_flow')
        
        data_info = {
            'stage': stage,
            'data_type': type(data).__name__,
            'timestamp': datetime.now().isoformat()
        }
        
        if operation:
            data_info['operation'] = operation
        
        # Add size info for common types
        if hasattr(data, '__len__'):
            data_info['size'] = len(data)
        
        if isinstance(data, (dict, list)):
            data_info['structure'] = cls._analyze_structure(data)
        
        logger.debug(f"Data flow: {stage}", extra=data_info)
    
    @classmethod
    def _analyze_structure(cls, data: Union[dict, list], max_depth: int = 3) -> Dict[str, Any]:
        """Analyze data structure for logging"""
        if max_depth <= 0:
            return {'truncated': True}
        
        if isinstance(data, dict):
            return {
                'type': 'dict',
                'keys': list(data.keys())[:10],  # Limit to first 10 keys
                'key_count': len(data),
                'sample_values': {k: cls._analyze_structure(v, max_depth - 1) 
                                  for k, v in list(data.items())[:3]}
            }
        elif isinstance(data, list):
            return {
                'type': 'list',
                'length': len(data),
                'sample_items': [cls._analyze_structure(item, max_depth - 1) 
                                 for item in data[:3]]
            }
        else:
            return {'type': type(data).__name__, 'value': str(data)[:100]}
    
    @classmethod
    def create_operation_context(cls, operation_id: str, **context):
        """Create a context manager for operation logging"""
        return OperationContext(operation_id, **context)
    
    @classmethod
    def get_logs_summary(cls, log_file: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of logged operations"""
        if log_file is None:
            log_file = cls._config.file_path
        
        if not log_file or not os.path.exists(log_file):
            return {'error': 'Log file not found'}
        
        summary = {
            'total_entries': 0,
            'by_level': {},
            'by_module': {},
            'errors': [],
            'operations': {}
        }
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    if cls._config.json_format:
                        try:
                            entry = json.loads(line)
                            cls._update_summary(summary, entry)
                        except json.JSONDecodeError:
                            continue
                    else:
                        # Basic parsing for non-JSON logs
                        summary['total_entries'] += 1
        
        except Exception as e:
            summary['error'] = str(e)
        
        return summary
    
    @classmethod
    def _update_summary(cls, summary: Dict[str, Any], entry: Dict[str, Any]):
        """Update summary with log entry"""
        summary['total_entries'] += 1
        
        # Count by level
        level = entry.get('level', 'UNKNOWN')
        summary['by_level'][level] = summary['by_level'].get(level, 0) + 1
        
        # Count by module
        module = entry.get('name', 'unknown')
        summary['by_module'][module] = summary['by_module'].get(module, 0) + 1
        
        # Track errors
        if level == 'ERROR':
            summary['errors'].append({
                'timestamp': entry.get('timestamp'),
                'message': entry.get('message'),
                'module': module
            })
        
        # Track operations
        if 'operation' in entry:
            op_name = entry['operation']
            if op_name not in summary['operations']:
                summary['operations'][op_name] = {'count': 0, 'failures': 0}
            
            summary['operations'][op_name]['count'] += 1
            if entry.get('status') == 'error':
                summary['operations'][op_name]['failures'] += 1


class OperationContext:
    """Context manager for operation logging"""
    
    def __init__(self, operation_id: str, **context):
        self.operation_id = operation_id
        self.context = context
        self.logger = LoggerUtils.get_logger('agentium.operations')
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(f"Operation started: {self.operation_id}", extra={
            'operation_id': self.operation_id,
            'status': 'start',
            **self.context
        })
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time if self.start_time else 0
        
        if exc_type is None:
            self.logger.info(f"Operation completed: {self.operation_id}", extra={
                'operation_id': self.operation_id,
                'status': 'success',
                'duration': duration,
                **self.context
            })
        else:
            self.logger.error(f"Operation failed: {self.operation_id}", extra={
                'operation_id': self.operation_id,
                'status': 'error',
                'duration': duration,
                'error_type': exc_type.__name__,
                'error_message': str(exc_val),
                **self.context
            }, exc_info=True)
    
    def log(self, message: str, level: str = 'INFO', **extra):
        """Log message within operation context"""
        log_method = getattr(self.logger, level.lower())
        log_method(message, extra={
            'operation_id': self.operation_id,
            **self.context,
            **extra
        })