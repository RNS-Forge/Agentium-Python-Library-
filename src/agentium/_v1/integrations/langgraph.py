"""
LangGraph Integration Module

This module provides seamless integration with LangGraph framework,
allowing Agentium features to be used within LangGraph workflows.
"""

from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass
import json

try:
    from langgraph.graph import Graph, StateGraph
    from langgraph.checkpoint import BaseCheckpointSaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    # Create minimal base classes for type hints
    class Graph:
        pass
    class StateGraph:
        pass
    class BaseCheckpointSaver:
        pass

from ..core.condenser import Condenser
from ..core.optimizer import Optimizer
from ..core.extractor import Extractor
from ..core.communicator import Communicator
from ..core.translator import Translator
from ..core.insight_generator import InsightGenerator
from ..core.workflow_helper import WorkflowHelper
from ..core.summarize_custom import CustomSummarizer
from ..core.memory_helper import MemoryHelper
from ..utils.logger_utils import LoggerUtils


class AgentiumLangGraphNode:
    """Base class for Agentium LangGraph nodes"""
    
    def __init__(self, agentium_component, name: str):
        self.agentium_component = agentium_component
        self.name = name
        self.logger = LoggerUtils.get_logger(__name__)
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the node"""
        return self.process(state)
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the state - to be implemented by subclasses"""
        raise NotImplementedError


class CondenserNode(AgentiumLangGraphNode):
    """LangGraph node for text condensing"""
    
    def __init__(self, condenser: Optional[Condenser] = None):
        super().__init__(condenser or Condenser(), "condenser")
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process content condensing"""
        content = state.get('content', '')
        ratio = state.get('condense_ratio', 0.5)
        
        try:
            result = self.agentium_component.condense(content, target_ratio=ratio)
            
            return {
                **state,
                'condensed_content': result.get('condensed_text', content),
                'condensing_stats': result.get('stats', {}),
                'step_completed': 'condensing'
            }
        except Exception as e:
            self.logger.error(f"Condenser node error: {e}")
            return {
                **state,
                'error': f"Condensing failed: {str(e)}",
                'step_completed': 'condensing_failed'
            }


class OptimizerNode(AgentiumLangGraphNode):
    """LangGraph node for content optimization"""
    
    def __init__(self, optimizer: Optional[Optimizer] = None):
        super().__init__(optimizer or Optimizer(), "optimizer")
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process content optimization"""
        content = state.get('content', '')
        content_type = state.get('content_type', 'text')
        
        try:
            result = self.agentium_component.optimize(content, content_type=content_type)
            
            return {
                **state,
                'optimized_content': result.get('optimized_content', content),
                'optimization_stats': result.get('stats', {}),
                'step_completed': 'optimization'
            }
        except Exception as e:
            self.logger.error(f"Optimizer node error: {e}")
            return {
                **state,
                'error': f"Optimization failed: {str(e)}",
                'step_completed': 'optimization_failed'
            }


class ExtractorNode(AgentiumLangGraphNode):
    """LangGraph node for data extraction"""
    
    def __init__(self, extractor: Optional[Extractor] = None):
        super().__init__(extractor or Extractor(), "extractor")
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process data extraction"""
        source = state.get('source', '')
        extraction_type = state.get('extraction_type', 'auto')
        
        try:
            result = self.agentium_component.extract(source, extraction_type=extraction_type)
            
            return {
                **state,
                'extracted_data': result.get('extracted_data', {}),
                'extraction_stats': result.get('stats', {}),
                'step_completed': 'extraction'
            }
        except Exception as e:
            self.logger.error(f"Extractor node error: {e}")
            return {
                **state,
                'error': f"Extraction failed: {str(e)}",
                'step_completed': 'extraction_failed'
            }


class TranslatorNode(AgentiumLangGraphNode):
    """LangGraph node for translation"""
    
    def __init__(self, translator: Optional[Translator] = None):
        super().__init__(translator or Translator(), "translator")
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process translation"""
        text = state.get('text', '')
        target_language = state.get('target_language', 'en')
        
        try:
            result = self.agentium_component.translate(text, target_language=target_language)
            
            return {
                **state,
                'translated_text': result.get('translated_text', text),
                'translation_stats': result.get('stats', {}),
                'step_completed': 'translation'
            }
        except Exception as e:
            self.logger.error(f"Translator node error: {e}")
            return {
                **state,
                'error': f"Translation failed: {str(e)}",
                'step_completed': 'translation_failed'
            }


class InsightGeneratorNode(AgentiumLangGraphNode):
    """LangGraph node for insight generation"""
    
    def __init__(self, insight_generator: Optional[InsightGenerator] = None):
        super().__init__(insight_generator or InsightGenerator(), "insight_generator")
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process insight generation"""
        data = state.get('data', '')
        insight_type = state.get('insight_type', 'general')
        
        try:
            result = self.agentium_component.generate_insights(data, insight_type=insight_type)
            
            return {
                **state,
                'insights': result.get('insights', []),
                'insight_stats': result.get('stats', {}),
                'step_completed': 'insight_generation'
            }
        except Exception as e:
            self.logger.error(f"Insight generator node error: {e}")
            return {
                **state,
                'error': f"Insight generation failed: {str(e)}",
                'step_completed': 'insight_generation_failed'
            }


class SummarizerNode(AgentiumLangGraphNode):
    """LangGraph node for summarization"""
    
    def __init__(self, summarizer: Optional[CustomSummarizer] = None):
        super().__init__(summarizer or CustomSummarizer(), "summarizer")
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process summarization"""
        content = state.get('content', '')
        summary_type = state.get('summary_type', 'extractive')
        
        try:
            result = self.agentium_component.summarize(content, summary_type=summary_type)
            
            return {
                **state,
                'summary': result.get('summary', ''),
                'summary_stats': result.get('metadata', {}),
                'step_completed': 'summarization'
            }
        except Exception as e:
            self.logger.error(f"Summarizer node error: {e}")
            return {
                **state,
                'error': f"Summarization failed: {str(e)}",
                'step_completed': 'summarization_failed'
            }


class CommunicatorNode(AgentiumLangGraphNode):
    """LangGraph node for communication"""
    
    def __init__(self, communicator: Optional[Communicator] = None):
        super().__init__(communicator or Communicator(), "communicator")
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process communication"""
        message = state.get('message', '')
        channel = state.get('channel', 'email')
        
        try:
            result = self.agentium_component.send_message(message, channel=channel)
            
            return {
                **state,
                'message_sent': True,
                'message_id': result.get('message_id', ''),
                'communication_stats': result.get('stats', {}),
                'step_completed': 'communication'
            }
        except Exception as e:
            self.logger.error(f"Communicator node error: {e}")
            return {
                **state,
                'message_sent': False,
                'error': f"Communication failed: {str(e)}",
                'step_completed': 'communication_failed'
            }


class AgentiumCheckpointSaver(BaseCheckpointSaver):
    """Checkpoint saver using Agentium MemoryHelper"""
    
    def __init__(self, memory_helper: Optional[MemoryHelper] = None, context: str = "langgraph"):
        self.memory_helper = memory_helper or MemoryHelper()
        self.context = context
        self.logger = LoggerUtils.get_logger(__name__)
        
        # Initialize context
        self.memory_context = self.memory_helper.create_context(context)
    
    def put(self, config: Dict[str, Any], checkpoint: Dict[str, Any]) -> None:
        """Save checkpoint"""
        try:
            checkpoint_id = config.get('checkpoint_id', 'default')
            
            checkpoint_data = {
                'config': config,
                'checkpoint': checkpoint,
                'timestamp': LoggerUtils.get_timestamp()
            }
            
            self.memory_context.store(f"checkpoint_{checkpoint_id}", checkpoint_data)
            self.logger.info(f"Saved checkpoint: {checkpoint_id}")
            
        except Exception as e:
            self.logger.error(f"Error saving checkpoint: {e}")
    
    def get(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Load checkpoint"""
        try:
            checkpoint_id = config.get('checkpoint_id', 'default')
            
            checkpoint_data = self.memory_context.get(f"checkpoint_{checkpoint_id}")
            
            if checkpoint_data:
                return checkpoint_data.get('checkpoint')
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error loading checkpoint: {e}")
            return None
    
    def list(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List checkpoints"""
        try:
            # This is a simplified implementation
            # In a full implementation, you'd query for all checkpoint keys
            checkpoint_id = config.get('checkpoint_id', 'default')
            checkpoint_data = self.memory_context.get(f"checkpoint_{checkpoint_id}")
            
            if checkpoint_data:
                return [checkpoint_data]
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error listing checkpoints: {e}")
            return []


class AgentiumLangGraphBuilder:
    """Builder class for creating LangGraph workflows with Agentium nodes"""
    
    def __init__(self):
        self.logger = LoggerUtils.get_logger(__name__)
        self.nodes = {}
        self.edges = []
        self.conditional_edges = []
        self.entry_point = None
        self.finish_points = []
    
    def add_condenser_node(self, name: str = "condenser", condenser: Optional[Condenser] = None) -> 'AgentiumLangGraphBuilder':
        """Add a condenser node"""
        self.nodes[name] = CondenserNode(condenser)
        return self
    
    def add_optimizer_node(self, name: str = "optimizer", optimizer: Optional[Optimizer] = None) -> 'AgentiumLangGraphBuilder':
        """Add an optimizer node"""
        self.nodes[name] = OptimizerNode(optimizer)
        return self
    
    def add_extractor_node(self, name: str = "extractor", extractor: Optional[Extractor] = None) -> 'AgentiumLangGraphBuilder':
        """Add an extractor node"""
        self.nodes[name] = ExtractorNode(extractor)
        return self
    
    def add_translator_node(self, name: str = "translator", translator: Optional[Translator] = None) -> 'AgentiumLangGraphBuilder':
        """Add a translator node"""
        self.nodes[name] = TranslatorNode(translator)
        return self
    
    def add_insight_generator_node(self, name: str = "insight_generator", insight_generator: Optional[InsightGenerator] = None) -> 'AgentiumLangGraphBuilder':
        """Add an insight generator node"""
        self.nodes[name] = InsightGeneratorNode(insight_generator)
        return self
    
    def add_summarizer_node(self, name: str = "summarizer", summarizer: Optional[CustomSummarizer] = None) -> 'AgentiumLangGraphBuilder':
        """Add a summarizer node"""
        self.nodes[name] = SummarizerNode(summarizer)
        return self
    
    def add_communicator_node(self, name: str = "communicator", communicator: Optional[Communicator] = None) -> 'AgentiumLangGraphBuilder':
        """Add a communicator node"""
        self.nodes[name] = CommunicatorNode(communicator)
        return self
    
    def add_custom_node(self, name: str, node_function: Callable) -> 'AgentiumLangGraphBuilder':
        """Add a custom node function"""
        self.nodes[name] = node_function
        return self
    
    def add_edge(self, from_node: str, to_node: str) -> 'AgentiumLangGraphBuilder':
        """Add an edge between nodes"""
        self.edges.append((from_node, to_node))
        return self
    
    def add_conditional_edge(self, from_node: str, condition_function: Callable, edge_map: Dict[str, str]) -> 'AgentiumLangGraphBuilder':
        """Add a conditional edge"""
        self.conditional_edges.append((from_node, condition_function, edge_map))
        return self
    
    def set_entry_point(self, node_name: str) -> 'AgentiumLangGraphBuilder':
        """Set the entry point for the graph"""
        self.entry_point = node_name
        return self
    
    def add_finish_point(self, node_name: str) -> 'AgentiumLangGraphBuilder':
        """Add a finish point"""
        self.finish_points.append(node_name)
        return self
    
    def build(self) -> Optional[StateGraph]:
        """Build the LangGraph"""
        if not LANGGRAPH_AVAILABLE:
            self.logger.error("LangGraph not available")
            return None
        
        try:
            # Create the state graph
            graph = StateGraph(Dict[str, Any])
            
            # Add nodes
            for name, node in self.nodes.items():
                graph.add_node(name, node)
            
            # Add edges
            for from_node, to_node in self.edges:
                graph.add_edge(from_node, to_node)
            
            # Add conditional edges
            for from_node, condition_func, edge_map in self.conditional_edges:
                graph.add_conditional_edges(from_node, condition_func, edge_map)
            
            # Set entry point
            if self.entry_point:
                graph.set_entry_point(self.entry_point)
            
            # Set finish points
            for finish_point in self.finish_points:
                graph.set_finish_point(finish_point)
            
            self.logger.info(f"Built LangGraph with {len(self.nodes)} nodes")
            return graph.compile()
            
        except Exception as e:
            self.logger.error(f"Error building LangGraph: {e}")
            return None


class AgentiumLangGraphWorkflow:
    """High-level workflow builder for common Agentium patterns"""
    
    def __init__(self):
        self.logger = LoggerUtils.get_logger(__name__)
    
    def create_content_processing_workflow(self) -> Optional[StateGraph]:
        """Create a workflow for content processing (condense -> optimize -> summarize)"""
        builder = AgentiumLangGraphBuilder()
        
        # Add nodes
        builder.add_condenser_node("condenser")
        builder.add_optimizer_node("optimizer") 
        builder.add_summarizer_node("summarizer")
        
        # Create flow: condenser -> optimizer -> summarizer
        builder.add_edge("condenser", "optimizer")
        builder.add_edge("optimizer", "summarizer")
        
        # Set entry and finish points
        builder.set_entry_point("condenser")
        builder.add_finish_point("summarizer")
        
        return builder.build()
    
    def create_data_analysis_workflow(self) -> Optional[StateGraph]:
        """Create a workflow for data analysis (extract -> insights -> communicate)"""
        builder = AgentiumLangGraphBuilder()
        
        # Add nodes
        builder.add_extractor_node("extractor")
        builder.add_insight_generator_node("insight_generator")
        builder.add_communicator_node("communicator")
        
        # Create flow
        builder.add_edge("extractor", "insight_generator")
        builder.add_edge("insight_generator", "communicator")
        
        # Set entry and finish points
        builder.set_entry_point("extractor")
        builder.add_finish_point("communicator")
        
        return builder.build()
    
    def create_multilingual_workflow(self) -> Optional[StateGraph]:
        """Create a workflow for multilingual content processing"""
        builder = AgentiumLangGraphBuilder()
        
        # Add nodes
        builder.add_translator_node("translator")
        builder.add_summarizer_node("summarizer")
        builder.add_communicator_node("communicator")
        
        # Create flow
        builder.add_edge("translator", "summarizer")
        builder.add_edge("summarizer", "communicator")
        
        # Set entry and finish points
        builder.set_entry_point("translator")
        builder.add_finish_point("communicator")
        
        return builder.build()
    
    def create_adaptive_workflow(self) -> Optional[StateGraph]:
        """Create an adaptive workflow with conditional routing"""
        builder = AgentiumLangGraphBuilder()
        
        # Add nodes
        builder.add_extractor_node("extractor")
        builder.add_condenser_node("condenser")
        builder.add_optimizer_node("optimizer")
        builder.add_summarizer_node("summarizer")
        builder.add_insight_generator_node("insight_generator")
        
        # Conditional logic function
        def route_content(state: Dict[str, Any]) -> str:
            content_length = len(state.get('content', ''))
            
            if content_length > 1000:
                return "condenser"
            elif 'code' in state.get('content_type', ''):
                return "optimizer"
            else:
                return "summarizer"
        
        # Add conditional routing
        builder.add_conditional_edge(
            "extractor",
            route_content,
            {
                "condenser": "condenser",
                "optimizer": "optimizer", 
                "summarizer": "summarizer"
            }
        )
        
        # Connect to insights
        builder.add_edge("condenser", "insight_generator")
        builder.add_edge("optimizer", "insight_generator")
        builder.add_edge("summarizer", "insight_generator")
        
        # Set entry and finish points
        builder.set_entry_point("extractor")
        builder.add_finish_point("insight_generator")
        
        return builder.build()


class AgentiumLangGraphIntegration:
    """Main integration class for LangGraph"""
    
    def __init__(self):
        self.logger = LoggerUtils.get_logger(__name__)
        self.builder = AgentiumLangGraphBuilder()
        self.workflow = AgentiumLangGraphWorkflow()
    
    def get_builder(self) -> AgentiumLangGraphBuilder:
        """Get the workflow builder"""
        return AgentiumLangGraphBuilder()
    
    def get_workflow(self) -> AgentiumLangGraphWorkflow:
        """Get the workflow helper"""
        return self.workflow
    
    def create_checkpoint_saver(self, context: str = "default") -> AgentiumCheckpointSaver:
        """Create an Agentium-powered checkpoint saver"""
        return AgentiumCheckpointSaver(context=context)
    
    def is_available(self) -> bool:
        """Check if LangGraph integration is available"""
        return LANGGRAPH_AVAILABLE


# Convenience function for easy integration
def get_agentium_langgraph_integration() -> AgentiumLangGraphIntegration:
    """Get the main LangGraph integration object"""
    return AgentiumLangGraphIntegration()


# Example usage functions
def create_simple_content_workflow():
    """Example function showing how to create a simple content processing workflow"""
    if not LANGGRAPH_AVAILABLE:
        raise ImportError("LangGraph is required for this functionality")
    
    integration = get_agentium_langgraph_integration()
    workflow = integration.get_workflow()
    
    return workflow.create_content_processing_workflow()


def create_custom_workflow_example():
    """Example function showing how to create a custom workflow"""
    if not LANGGRAPH_AVAILABLE:
        raise ImportError("LangGraph is required for this functionality")
    
    integration = get_agentium_langgraph_integration()
    builder = integration.get_builder()
    
    # Build custom workflow
    graph = (builder
             .add_extractor_node("extract")
             .add_condenser_node("condense")
             .add_summarizer_node("summarize")
             .add_edge("extract", "condense")
             .add_edge("condense", "summarize")
             .set_entry_point("extract")
             .add_finish_point("summarize")
             .build())
    
    return graph