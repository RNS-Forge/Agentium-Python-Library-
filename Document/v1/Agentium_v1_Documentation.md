# Agentium v1 — Function-by-Function Architecture & Test Documentation

> **Status:** Legacy v1 Documentation (All functions preserved under `src/agentium/_v1/` and exposed via backward compatibility shims in `agentium.*`).  
> **PDF Report:** Available at [Document/Agentium_v1_Documentation.pdf](file:///c:/Temp%20Files/My%20Projects/Agentium-Python-Library-/Document/Agentium_v1_Documentation.pdf).

---

## 1. Tone Adaptation System (`ToneType`)

Agentium v1 features a specialized multi-tone adaptation system defined in `agentium.core.translator.ToneType`. It governs contractions, vocabulary transformation, polite prefixes, and professional sign-offs:

| # | Tone Name | Enum Identifier | Vocabulary & Contraction Rules | Ideal Use Cases / Scenarios |
|:---:|:---|:---|:---|:---|
| 1 | **FORMAL** | `ToneType.FORMAL` (`"formal"`) | Expands contractions (*can't &rarr; cannot*, *won't &rarr; will not*). Adds formal prefixes (*"Please note that"*, *"It should be mentioned that"*). | Legal, regulatory compliance, contracts, executive briefings. |
| 2 | **INFORMAL** | `ToneType.INFORMAL` (`"informal"`) | Introduces conversational contractions (*cannot &rarr; can't*). Adds casual greetings (*"Hey"*, *"By the way"*). | Quick internal messaging, Slack/Discord bots, community channels. |
| 3 | **PROFESSIONAL** | `ToneType.PROFESSIONAL` (`"professional"`) | Upgrades corporate vocabulary (*very good &rarr; excellent*, *problem &rarr; challenge*). Prefixes: *"Please be advised that"*. | Default enterprise tone. B2B emails, customer deliverables, quarterly reports. |
| 4 | **FRIENDLY** | `ToneType.FRIENDLY` (`"friendly"`) | Softens critique (*error &rarr; little issue*). Adds warm prefixes (*"Hope you're doing well!"*). | Customer support chatbots, onboarding tutorials, community helpdesks. |
| 5 | **TECHNICAL** | `ToneType.TECHNICAL` (`"technical"`) | Preserves code symbols, exact parameters, architectural acronyms without colloquial softening. | Developer API docs, engineering specs, DevOps alerts, error traces. |
| 6 | **MARKETING** | `ToneType.MARKETING` (`"marketing"`) | Engaging, benefit-driven phrasing highlighting value propositions and ROI. | Release announcements, marketing campaigns, landing page copy. |
| 7 | **ACADEMIC** | `ToneType.ACADEMIC` (`"academic"`) | Objective, scholarly, passive-voice phrasing prioritizing methodology and empirical analysis. | Whitepapers, scientific literature surveys, statistical reports. |

---

## 2. Core v1 Modules Reference

### 2.1 Rearranger (`Rearranger`)
- **Location:** `agentium.core.rearranger`
- **Class:** `Rearranger(config=RearrangerConfig())`
- **Primary Function:** `rearrange(content, strategy, content_type)`
- **Strategies Supported:** `ALPHABETICAL`, `LENGTH_ASC`, `LENGTH_DESC`, `LOGICAL_FLOW`, `CUSTOM`
- **Use Cases:** Sorting pipeline steps, reordering chaotic text logically, structuring bulleted lists.

### 2.2 Condenser (`Condenser`)
- **Location:** `agentium.core.condenser`
- **Class:** `Condenser(config=CondenserConfig())`
- **Primary Function:** `condense(text, target_ratio=0.5)`
- **Use Cases:** Trimming token counts before sending prompts to LLMs, extracting essential sentences.

### 2.3 Optimizer (`Optimizer`)
- **Location:** `agentium.core.optimizer`
- **Class:** `Optimizer(config=OptimizerConfig())`
- **Primary Function:** `optimize(content, target="speed"|"memory"|"clarity")`
- **Use Cases:** Code refactoring, prompt optimization, removing redundancy from text.

### 2.4 Communicator (`Communicator`)
- **Location:** `agentium.core.communicator`
- **Class:** `Communicator(config=CommunicatorConfig())`
- **Primary Function:** `send(channel, message, recipient)`
- **Use Cases:** Dispatching webhook payloads, sending platform notifications across Slack, Email, and Webhooks.

### 2.5 Extractor (`Extractor`)
- **Location:** `agentium.core.extractor`
- **Class:** `Extractor(config=ExtractorConfig())`
- **Primary Function:** `extract(text, schema=None, entities=None)`
- **Use Cases:** Pulling emails, phone numbers, URLs, dates, and structured JSON schemas from unstructured text.

### 2.6 Translator (`Translator`)
- **Location:** `agentium.core.translator`
- **Class:** `Translator(config=TranslatorConfig())`
- **Primary Functions:**
  - `translate(text, target_language)`
  - `adapt_tone(text, tone: ToneType)`
  - `detect_tone(text) -> ToneType`
- **Use Cases:** Cross-language agent communication and dynamic tone adaptation.

### 2.7 Insight Generator (`InsightGenerator`)
- **Location:** `agentium.core.insight_generator`
- **Class:** `InsightGenerator(config=InsightConfig())`
- **Primary Function:** `generate_insights(data, focus_area=None)`
- **Use Cases:** Deriving trends, anomalies, and key takeaways from tabular or time-series data.

### 2.8 Workflow Helper (`WorkflowHelper`)
- **Location:** `agentium.core.workflow_helper`
- **Class:** `WorkflowHelper(config=WorkflowConfig())`
- **Primary Function:** `execute_workflow(steps, context=None)`
- **Use Cases:** Multi-step pipeline execution, step sequencing, conditional branching.

### 2.9 Template Manager (`TemplateManager`)
- **Location:** `agentium.core.template_manager`
- **Class:** `TemplateManager(config=TemplateConfig())`
- **Primary Function:** `render(template_name, variables)`
- **Use Cases:** Standardizing agent prompts, system messages, and automated email generation.

### 2.10 Memory Helper (`MemoryHelper`)
- **Location:** `agentium.core.memory_helper`
- **Class:** `MemoryHelper(config=MemoryConfig())`
- **Primary Function:** `store(key, value)`, `retrieve(key)`, `query_similar(query)`
- **Use Cases:** Session context storage and short-term memory retrieval.

### 2.11 Custom Summarizer (`CustomSummarizer`)
- **Location:** `agentium.core.summarize_custom`
- **Class:** `CustomSummarizer(config=SummaryConfig())`
- **Primary Function:** `summarize(text, max_length=150)`
- **Use Cases:** Executive briefs, bulleted abstracts, transcript digestion.

### 2.12 Logger Utils (`LoggerUtils`)
- **Location:** `agentium.utils.logger_utils`
- **Class:** `LoggerUtils(config=LoggerConfig())`
- **Primary Function:** `log(message, level="INFO")`, `audit(action, metadata)`
- **Use Cases:** Debugging agent pipelines and auditing operational events.

### 2.13 Gemini Integration (`GeminiIntegration`)
- **Location:** `agentium.integrations.gemini`
- **Class:** `GeminiIntegration(api_key=None, model="gemini-1.5-flash")`
- **Primary Function:** `generate_content(prompt)`, `chat(messages)`
- **Use Cases:** Direct Google Gemini API access for multimodal and generative inference.
