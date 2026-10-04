"""
Agentium - Comprehensive Python Library for AI Agent Development

A production-ready library providing essential tools and utilities for 
building intelligent AI agents, compatible with LangChain, LangGraph, and CrewAI.

Core Features:
- Content condensation and optimization
- Data extraction and processing  
- Multi-channel communication
- Translation and localization
- Insight generation and analysis
- Workflow orchestration
- Template management
- Memory and context storage
- Custom summarization
- Advanced logging and monitoring

Framework Integrations:
- LangChain: Tools, memory, parsers, callbacks
- LangGraph: Workflow nodes, state management
- CrewAI: Enhanced agents, tasks, crews
"""

__version__ = "1.0.0"
__author__ = "Agentium Development Team"
__license__ = "MIT"

# Core components
from .core.condenser import Condenser, CondenserConfig
from .core.optimizer import Optimizer, OptimizerConfig  
from .core.rearranger import Rearranger, RearrangerConfig
from .core.extractor import Extractor, ExtractorConfig
from .core.communicator import Communicator, CommunicatorConfig
from .core.translator import Translator, TranslatorConfig
from .core.insight_generator import InsightGenerator, InsightConfig
from .core.workflow_helper import WorkflowHelper, WorkflowConfig
from .core.template_manager import TemplateManager, TemplateConfig
from .core.memory_helper import MemoryHelper, MemoryConfig
from .core.summarize_custom import CustomSummarizer, SummaryConfig

# Utilities
from .utils.logger_utils import LoggerUtils, LoggerConfig

# Integrations (with optional imports)
try:
    from .integrations.langchain import (
        get_agentium_langchain_integration,
        AgentiumLangChainIntegration,
        AgentiumMemory,
        AgentiumOutputParser,
        AgentiumCallbackHandler
    )
    LANGCHAIN_INTEGRATION_AVAILABLE = True
except Exception:
    LANGCHAIN_INTEGRATION_AVAILABLE = False

try:
    from .integrations.langgraph import (
        get_agentium_langgraph_integration,
        AgentiumLangGraphIntegration,
        AgentiumLangGraphBuilder,
        AgentiumLangGraphWorkflow
    )
    LANGGRAPH_INTEGRATION_AVAILABLE = True
except Exception:
    LANGGRAPH_INTEGRATION_AVAILABLE = False

try:
    from .integrations.gemini import (
        GeminiIntegration,
        GeminiConfig,
        GeminiModel,
        get_gemini_integration
    )
    GEMINI_INTEGRATION_AVAILABLE = True
except Exception:
    GEMINI_INTEGRATION_AVAILABLE = False

# Main exports
__all__ = [
    # Version and metadata
    '__version__',
    '__author__',
    '__license__',
    
    # Core components
    'Condenser',
    'CondenserConfig',
    'Optimizer', 
    'OptimizerConfig',
    'Rearranger',
    'RearrangerConfig',
    'Extractor',
    'ExtractorConfig',
    'Communicator',
    'CommunicatorConfig',
    'Translator',
    'TranslatorConfig',
    'InsightGenerator',
    'InsightConfig',
    'WorkflowHelper',
    'WorkflowConfig',
    'TemplateManager',
    'TemplateConfig',
    'MemoryHelper',
    'MemoryConfig',
    'CustomSummarizer',
    'SummaryConfig',
    
    # Utilities
    'LoggerUtils',
    'LoggerConfig',
    
    # Integration flags
    'LANGCHAIN_INTEGRATION_AVAILABLE',
    'LANGGRAPH_INTEGRATION_AVAILABLE', 
    'GEMINI_INTEGRATION_AVAILABLE',
]

# Add integration exports if available
if LANGCHAIN_INTEGRATION_AVAILABLE:
    __all__.extend([
        'get_agentium_langchain_integration',
        'AgentiumLangChainIntegration',
        'AgentiumMemory',
        'AgentiumOutputParser',
        'AgentiumCallbackHandler'
    ])

if LANGGRAPH_INTEGRATION_AVAILABLE:
    __all__.extend([
        'get_agentium_langgraph_integration',
        'AgentiumLangGraphIntegration',
        'AgentiumLangGraphBuilder',
        'AgentiumLangGraphWorkflow'
    ])

if GEMINI_INTEGRATION_AVAILABLE:
    __all__.extend([
        'GeminiIntegration',
        'GeminiConfig',
        'GeminiModel',
        'get_gemini_integration'
    ])

from typing import Optional, Dict, Any


class Agentium:
    """
    Main Agentium class providing unified access to all components.
    
    This class serves as a convenient entry point for accessing all
    Agentium functionality in a single interface.
    """
    
    def __init__(self, logger_config: Optional[LoggerConfig] = None):
        """Initialize Agentium with optional logging configuration"""
        self.logger = LoggerUtils.get_logger(__name__)
        
        if logger_config:
            LoggerUtils.configure(logger_config)
        
        # Initialize core components
        self.condenser = Condenser()
        self.optimizer = Optimizer()
        self.rearranger = Rearranger()
        self.extractor = Extractor()
        self.communicator = Communicator()
        self.translator = Translator()
        self.insight_generator = InsightGenerator()
        self.workflow_helper = WorkflowHelper()
        self.template_manager = TemplateManager()
        self.memory_helper = MemoryHelper()
        self.summarizer = CustomSummarizer()
        
        # Initialize integrations
        self._init_integrations()
        
        self.logger.info("Agentium initialized with all core components")
    
    def _init_integrations(self):
        """Initialize framework integrations"""
        self.langchain_integration = None
        self.langgraph_integration = None
        self.gemini_integration = None
        
        if LANGCHAIN_INTEGRATION_AVAILABLE:
            try:
                self.langchain_integration = get_agentium_langchain_integration()
                self.logger.info("LangChain integration initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize LangChain integration: {e}")
        
        if LANGGRAPH_INTEGRATION_AVAILABLE:
            try:
                self.langgraph_integration = get_agentium_langgraph_integration()
                self.logger.info("LangGraph integration initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize LangGraph integration: {e}")
        
        if GEMINI_INTEGRATION_AVAILABLE:
            try:
                self.gemini_integration = get_gemini_integration()
                self.logger.info("Gemini integration initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Gemini integration: {e}")
    
    def get_integration_status(self) -> Dict[str, bool]:
        """Get the status of all integrations"""
        return {
            'langchain': LANGCHAIN_INTEGRATION_AVAILABLE and self.langchain_integration is not None,
            'langgraph': LANGGRAPH_INTEGRATION_AVAILABLE and self.langgraph_integration is not None,
            'gemini': GEMINI_INTEGRATION_AVAILABLE and self.gemini_integration is not None,
        }
    
    def process_content(self, content: str, workflow: str = "basic") -> Dict[str, Any]:
        """
        Process content through a predefined workflow
        
        Available workflows:
        - basic: condense -> optimize -> summarize
        - analysis: extract -> insights -> summarize  
        - translation: translate -> optimize -> summarize
        """
        
        results = {'workflow': workflow, 'steps': []}
        
        try:
            if workflow == "basic":
                # Condense -> Optimize -> Summarize
                condensed_result = self.condenser.condense(content)
                condensed_text = condensed_result.get('text') if isinstance(condensed_result, dict) else condensed_result
                results['steps'].append({'step': 'condense', 'result': condensed_result})
                
                optimized_result = self.optimizer.optimize(condensed_text)
                optimized_text = optimized_result.get('text') if isinstance(optimized_result, dict) else optimized_result
                results['steps'].append({'step': 'optimize', 'result': optimized_result})
                
                summarized_result = self.summarizer.summarize(optimized_text)
                summarized = summarized_result if isinstance(summarized_result, dict) else {'summary': summarized_result}
                results['steps'].append({'step': 'summarize', 'result': summarized})
                
                results['final_output'] = summarized.get('summary', str(summarized))
                
            elif workflow == "analysis":
                # Extract -> Insights -> Summarize
                extracted_result = self.extractor.extract(content)
                extracted = extracted_result if isinstance(extracted_result, dict) else {'extracted_data': extracted_result}
                results['steps'].append({'step': 'extract', 'result': extracted})
                
                insights_result = self.insight_generator.generate_insights(str(extracted['extracted_data']))
                insights = insights_result if isinstance(insights_result, dict) else {'insights': insights_result}
                results['steps'].append({'step': 'insights', 'result': insights})
                
                data_str = str(extracted['extracted_data'])
                insights_str = str(insights.get('insights', insights))
                summarized_result = self.summarizer.summarize(f"Data: {data_str} Insights: {insights_str}")
                summarized = summarized_result if isinstance(summarized_result, dict) else {'summary': summarized_result}
                results['steps'].append({'step': 'summarize', 'result': summarized})
                
                results['final_output'] = summarized.get('summary', str(summarized))
                
            elif workflow == "translation":
                # Translate -> Optimize -> Summarize  
                translated_result = self.translator.translate(content)
                translated = translated_result if isinstance(translated_result, dict) else {'translated_text': translated_result}
                results['steps'].append({'step': 'translate', 'result': translated})
                
                optimized_result = self.optimizer.optimize(translated['translated_text'])
                optimized = optimized_result if isinstance(optimized_result, dict) else {'optimized_content': optimized_result}
                results['steps'].append({'step': 'optimize', 'result': optimized})
                
                summarized_result = self.summarizer.summarize(optimized['optimized_content'])
                summarized = summarized_result if isinstance(summarized_result, dict) else {'summary': summarized_result}
                results['steps'].append({'step': 'summarize', 'result': summarized})
                
                results['final_output'] = summarized.get('summary', str(summarized))
                
            else:
                raise ValueError(f"Unknown workflow: {workflow}")
                
            results['success'] = True
            
        except Exception as e:
            results['success'] = False
            results['error'] = str(e)
            self.logger.error(f"Workflow {workflow} failed: {e}")
        
        return results


# Add to main exports
__all__.extend(['Agentium'])