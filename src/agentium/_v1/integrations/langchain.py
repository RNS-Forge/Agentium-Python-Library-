"""
LangChain Integration Module

This module provides seamless integration with LangChain framework,
allowing Agentium features to be used within LangChain pipelines.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

try:
    from langchain.schema import BaseOutputParser
    from langchain.tools import BaseTool
    from langchain.agents import BaseAgent
    from langchain.memory import BaseMemory
    from langchain.callbacks.base import BaseCallbackHandler
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # Create minimal base classes for type hints
    class BaseOutputParser:
        pass
    class BaseTool:
        pass
    class BaseAgent:
        pass
    class BaseMemory:
        pass
    class BaseCallbackHandler:
        pass

from ..core.condenser import Condenser
from ..core.optimizer import Optimizer
from ..core.extractor import Extractor
from ..core.communicator import Communicator
from ..core.translator import Translator
from ..core.insight_generator import InsightGenerator
from ..core.summarize_custom import CustomSummarizer
from ..core.memory_helper import MemoryHelper
from ..utils.logger_utils import LoggerUtils


class AgentiumLangChainTool(BaseTool):
    """Base class for Agentium LangChain tools"""
    
    def __init__(self, agentium_component, name: str, description: str):
        self.agentium_component = agentium_component
        self.name = name
        self.description = description
        self.logger = LoggerUtils.get_logger(__name__)


class CondenserTool(AgentiumLangChainTool):
    """LangChain tool wrapper for Condenser"""
    
    def __init__(self, condenser: Optional[Condenser] = None):
        condenser = condenser or Condenser()
        super().__init__(
            agentium_component=condenser,
            name="condenser",
            description="Condense text content intelligently while preserving key information"
        )
    
    def _run(self, content: str, ratio: float = 0.5, **kwargs) -> str:
        """Run the condenser tool"""
        try:
            result = self.agentium_component.condense(content, target_ratio=ratio, **kwargs)
            return result.get('condensed_text', content)
        except Exception as e:
            self.logger.error(f"Condenser tool error: {e}")
            return f"Error condensing text: {str(e)}"
    
    async def _arun(self, content: str, ratio: float = 0.5, **kwargs) -> str:
        """Async version of the tool"""
        return self._run(content, ratio, **kwargs)


class OptimizerTool(AgentiumLangChainTool):
    """LangChain tool wrapper for Optimizer"""
    
    def __init__(self, optimizer: Optional[Optimizer] = None):
        optimizer = optimizer or Optimizer()
        super().__init__(
            agentium_component=optimizer,
            name="optimizer",
            description="Optimize text, code, or workflow content for better performance and clarity"
        )
    
    def _run(self, content: str, content_type: str = "text", **kwargs) -> str:
        """Run the optimizer tool"""
        try:
            result = self.agentium_component.optimize(content, content_type=content_type, **kwargs)
            return result.get('optimized_content', content)
        except Exception as e:
            self.logger.error(f"Optimizer tool error: {e}")
            return f"Error optimizing content: {str(e)}"
    
    async def _arun(self, content: str, content_type: str = "text", **kwargs) -> str:
        """Async version of the tool"""
        return self._run(content, content_type, **kwargs)


class ExtractorTool(AgentiumLangChainTool):
    """LangChain tool wrapper for Extractor"""
    
    def __init__(self, extractor: Optional[Extractor] = None):
        extractor = extractor or Extractor()
        super().__init__(
            agentium_component=extractor,
            name="extractor",
            description="Extract structured information from various data sources and formats"
        )
    
    def _run(self, source: str, extraction_type: str = "auto", **kwargs) -> str:
        """Run the extractor tool"""
        try:
            result = self.agentium_component.extract(source, extraction_type=extraction_type, **kwargs)
            return str(result.get('extracted_data', {}))
        except Exception as e:
            self.logger.error(f"Extractor tool error: {e}")
            return f"Error extracting data: {str(e)}"
    
    async def _arun(self, source: str, extraction_type: str = "auto", **kwargs) -> str:
        """Async version of the tool"""
        return self._run(source, extraction_type, **kwargs)


class CommunicatorTool(AgentiumLangChainTool):
    """LangChain tool wrapper for Communicator"""
    
    def __init__(self, communicator: Optional[Communicator] = None):
        communicator = communicator or Communicator()
        super().__init__(
            agentium_component=communicator,
            name="communicator",
            description="Send messages and notifications through various channels"
        )
    
    def _run(self, message: str, channel: str = "email", **kwargs) -> str:
        """Run the communicator tool"""
        try:
            result = self.agentium_component.send_message(message, channel=channel, **kwargs)
            return f"Message sent successfully via {channel}: {result.get('message_id', 'N/A')}"
        except Exception as e:
            self.logger.error(f"Communicator tool error: {e}")
            return f"Error sending message: {str(e)}"
    
    async def _arun(self, message: str, channel: str = "email", **kwargs) -> str:
        """Async version of the tool"""
        return self._run(message, channel, **kwargs)


class TranslatorTool(AgentiumLangChainTool):
    """LangChain tool wrapper for Translator"""
    
    def __init__(self, translator: Optional[Translator] = None):
        translator = translator or Translator()
        super().__init__(
            agentium_component=translator,
            name="translator",
            description="Translate text between languages and adapt tone/style"
        )
    
    def _run(self, text: str, target_language: str = "en", **kwargs) -> str:
        """Run the translator tool"""
        try:
            result = self.agentium_component.translate(text, target_language=target_language, **kwargs)
            return result.get('translated_text', text)
        except Exception as e:
            self.logger.error(f"Translator tool error: {e}")
            return f"Error translating text: {str(e)}"
    
    async def _arun(self, text: str, target_language: str = "en", **kwargs) -> str:
        """Async version of the tool"""
        return self._run(text, target_language, **kwargs)


class InsightGeneratorTool(AgentiumLangChainTool):
    """LangChain tool wrapper for InsightGenerator"""
    
    def __init__(self, insight_generator: Optional[InsightGenerator] = None):
        insight_generator = insight_generator or InsightGenerator()
        super().__init__(
            agentium_component=insight_generator,
            name="insight_generator",
            description="Generate actionable insights from data and text"
        )
    
    def _run(self, data: str, insight_type: str = "general", **kwargs) -> str:
        """Run the insight generator tool"""
        try:
            result = self.agentium_component.generate_insights(data, insight_type=insight_type, **kwargs)
            insights = result.get('insights', [])
            return f"Generated {len(insights)} insights: " + "; ".join(insights[:3])
        except Exception as e:
            self.logger.error(f"Insight generator tool error: {e}")
            return f"Error generating insights: {str(e)}"
    
    async def _arun(self, data: str, insight_type: str = "general", **kwargs) -> str:
        """Async version of the tool"""
        return self._run(data, insight_type, **kwargs)


class SummarizerTool(AgentiumLangChainTool):
    """LangChain tool wrapper for CustomSummarizer"""
    
    def __init__(self, summarizer: Optional[CustomSummarizer] = None):
        summarizer = summarizer or CustomSummarizer()
        super().__init__(
            agentium_component=summarizer,
            name="summarizer",
            description="Create custom summaries with various strategies and configurations"
        )
    
    def _run(self, content: str, summary_type: str = "extractive", **kwargs) -> str:
        """Run the summarizer tool"""
        try:
            result = self.agentium_component.summarize(content, summary_type=summary_type, **kwargs)
            return result.get('summary', content)
        except Exception as e:
            self.logger.error(f"Summarizer tool error: {e}")
            return f"Error summarizing content: {str(e)}"
    
    async def _arun(self, content: str, summary_type: str = "extractive", **kwargs) -> str:
        """Async version of the tool"""
        return self._run(content, summary_type, **kwargs)


class AgentiumMemory(BaseMemory):
    """LangChain memory implementation using Agentium MemoryHelper"""
    
    def __init__(self, memory_helper: Optional[MemoryHelper] = None, context: str = "langchain"):
        self.memory_helper = memory_helper or MemoryHelper()
        self.context = context
        self.logger = LoggerUtils.get_logger(__name__)
        
        # LangChain memory properties
        self.memory_key = "history"
        self.input_key = None
        self.output_key = None
        
        # Initialize context
        self.memory_context = self.memory_helper.create_context(context)
    
    @property
    def memory_variables(self) -> List[str]:
        """Return memory variables"""
        return [self.memory_key]
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load memory variables"""
        try:
            # Get conversation history
            history = self.memory_context.get("conversation_history", [])
            
            # Format for LangChain
            formatted_history = self._format_history(history)
            
            return {self.memory_key: formatted_history}
        
        except Exception as e:
            self.logger.error(f"Error loading memory: {e}")
            return {self.memory_key: ""}
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]):
        """Save context to memory"""
        try:
            # Get input and output
            input_key = self.input_key or list(inputs.keys())[0] if inputs else "input"
            output_key = self.output_key or list(outputs.keys())[0] if outputs else "output"
            
            user_input = inputs.get(input_key, "")
            ai_output = outputs.get(output_key, "")
            
            # Store in memory
            conversation_entry = {
                'timestamp': LoggerUtils.get_timestamp(),
                'input': user_input,
                'output': ai_output
            }
            
            # Get existing history
            history = self.memory_context.get("conversation_history", [])
            history.append(conversation_entry)
            
            # Store updated history
            self.memory_context.store("conversation_history", history)
            
        except Exception as e:
            self.logger.error(f"Error saving context: {e}")
    
    def clear(self):
        """Clear memory"""
        try:
            self.memory_context.clear()
        except Exception as e:
            self.logger.error(f"Error clearing memory: {e}")
    
    def _format_history(self, history: List[Dict]) -> str:
        """Format conversation history for LangChain"""
        formatted_lines = []
        
        for entry in history[-10:]:  # Keep last 10 entries
            user_input = entry.get('input', '').strip()
            ai_output = entry.get('output', '').strip()
            
            if user_input:
                formatted_lines.append(f"Human: {user_input}")
            if ai_output:
                formatted_lines.append(f"AI: {ai_output}")
        
        return '\n'.join(formatted_lines)


class AgentiumOutputParser(BaseOutputParser):
    """Output parser that uses Agentium features"""
    
    def __init__(self, use_optimizer: bool = True, use_condenser: bool = False):
        self.use_optimizer = use_optimizer
        self.use_condenser = use_condenser
        
        if use_optimizer:
            self.optimizer = Optimizer()
        if use_condenser:
            self.condenser = Condenser()
        
        self.logger = LoggerUtils.get_logger(__name__)
    
    def parse(self, output: str) -> str:
        """Parse and process output using Agentium features"""
        try:
            processed_output = output
            
            # Optimize output if requested
            if self.use_optimizer:
                result = self.optimizer.optimize(processed_output, content_type="text")
                processed_output = result.get('optimized_content', processed_output)
            
            # Condense output if requested
            if self.use_condenser:
                result = self.condenser.condense(processed_output)
                processed_output = result.get('condensed_text', processed_output)
            
            return processed_output
        
        except Exception as e:
            self.logger.error(f"Error parsing output: {e}")
            return output


class AgentiumCallbackHandler(BaseCallbackHandler):
    """Callback handler for logging LangChain operations"""
    
    def __init__(self):
        self.logger = LoggerUtils.get_logger(__name__)
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """Called when LLM starts"""
        self.logger.info("LLM started", extra={
            'prompts_count': len(prompts),
            'model_info': serialized
        })
    
    def on_llm_end(self, response, **kwargs) -> None:
        """Called when LLM ends"""
        self.logger.info("LLM completed", extra={
            'response_type': type(response).__name__
        })
    
    def on_llm_error(self, error: Exception, **kwargs) -> None:
        """Called when LLM errors"""
        self.logger.error(f"LLM error: {error}")
    
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs) -> None:
        """Called when chain starts"""
        self.logger.info("Chain started", extra={
            'chain_type': serialized.get('_type', 'unknown'),
            'inputs': list(inputs.keys())
        })
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs) -> None:
        """Called when chain ends"""
        self.logger.info("Chain completed", extra={
            'outputs': list(outputs.keys())
        })
    
    def on_chain_error(self, error: Exception, **kwargs) -> None:
        """Called when chain errors"""
        self.logger.error(f"Chain error: {error}")


class AgentiumLangChainIntegration:
    """Main integration class for LangChain"""
    
    def __init__(self):
        self.logger = LoggerUtils.get_logger(__name__)
        self.tools = {}
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize all Agentium tools"""
        if not LANGCHAIN_AVAILABLE:
            self.logger.warning("LangChain not available - integration tools will have limited functionality")
            return
        
        try:
            self.tools = {
                'condenser': CondenserTool(),
                'optimizer': OptimizerTool(),
                'extractor': ExtractorTool(),
                'communicator': CommunicatorTool(),
                'translator': TranslatorTool(),
                'insight_generator': InsightGeneratorTool(),
                'summarizer': SummarizerTool(),
            }
            
            self.logger.info(f"Initialized {len(self.tools)} LangChain tools")
        
        except Exception as e:
            self.logger.error(f"Error initializing tools: {e}")
    
    def get_tool(self, tool_name: str) -> Optional[AgentiumLangChainTool]:
        """Get a specific tool"""
        return self.tools.get(tool_name)
    
    def get_all_tools(self) -> List[AgentiumLangChainTool]:
        """Get all available tools"""
        return list(self.tools.values())
    
    def create_memory(self, context: str = "default") -> AgentiumMemory:
        """Create Agentium-powered memory"""
        return AgentiumMemory(context=context)
    
    def create_output_parser(self, **kwargs) -> AgentiumOutputParser:
        """Create Agentium-powered output parser"""
        return AgentiumOutputParser(**kwargs)
    
    def create_callback_handler(self) -> AgentiumCallbackHandler:
        """Create Agentium callback handler"""
        return AgentiumCallbackHandler()
    
    def is_available(self) -> bool:
        """Check if LangChain integration is available"""
        return LANGCHAIN_AVAILABLE


# Convenience function for easy integration
def get_agentium_langchain_integration() -> AgentiumLangChainIntegration:
    """Get the main LangChain integration object"""
    return AgentiumLangChainIntegration()


# Example usage functions
def create_agent_with_agentium_tools():
    """Example function showing how to create a LangChain agent with Agentium tools"""
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain is required for this functionality")
    
    integration = get_agentium_langchain_integration()
    tools = integration.get_all_tools()
    memory = integration.create_memory()
    callback_handler = integration.create_callback_handler()
    
    return {
        'tools': tools,
        'memory': memory,
        'callback_handler': callback_handler
    }