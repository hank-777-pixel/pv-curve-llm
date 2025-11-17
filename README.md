# P-V Curve LLM

<img src="https://github.com/CURENT/andes/raw/master/docs/source/images/sponsors/CURENT_Logo_NameOnTrans.png" alt="CURENT ERC Logo" width="300" height="auto">

Using LLMs to contextualize, create, and analyze Power-Voltage Curves (Nose Curves) for Power System Voltage Stability analysis. This project experiments with AI agents and to accomplish specific tasks with natural language.

The goal of this project is to research how AI frameworks and technology can be applied to power systems, experimenting with ideas and frameworks that will eventually be applied to the CURENT LTB.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/CURENT/pv-curve-llm/blob/master/LICENSE)
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![GitHub last commit (master)](https://img.shields.io/github/last-commit/CURENT/pv-curve-llm/master?label=last%20commit%20to%20master)](https://github.com/CURENT/pv-curve-llm/commits/master/)
[![Visitors](https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Fgithub.com%2FCURENT%2Fpv-curve-llm&countColor=%2337d67a&style=plastic)](https://visitorbadge.io/status?path=https%3A%2F%2Fgithub.com%2FCURENT%2Fpv-curve-llm)

## Installation & Run

### Prerequisites

- Python 3.8+
- Ollama installed: https://www.ollama.com/download

### Quick Start

```bash
# Run terminal as administrator
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
ollama pull mxbai-embed-large  # embedding model for RAG
ollama pull llama3.1:8b
ollama create pv-curve -f agent\Modelfile

python main.py # Run CLI interface
```

To leave the virtual environment, enter `deactivate`.

## Using OpenAI API (Recommended)

When running the application, you will be prompted to use 'openai' or 'ollama'. For improved performance, it is recommended to use OpenAI with an API key.

Create `agent/.env` with `OPENAI_API_KEY=your-key` (get a key at the [OpenAI API keys page](https://platform.openai.com/api-keys)).

## Custom vector database (RAG)

To setup a custom vector database or add to the existing database, see `agent/data/README.md` for instructions.

## File Architecture

**Root Entry Points:**
- `main.py` - Root entry point that launches the CLI interface
- `cli.py` - Rich-based CLI interface with streaming updates and enhanced UI

The `agent/` directory contains the core LangGraph AI agent system with the following architecture:

**LLM Configuration & Prompts:**
- `Modelfile` - Ollama model configuration defining system behavior and example conversations. Only applies to the local model.
- `prompts.py` / `prompts_json.py` - Structured prompt templates for different agent functions. `prompts_json.py` is experimental json formatted prompts.

**Data Layer:**
- `vector_db/` - Chroma vector database storing embedded knowledge for RAG retrieval
- `data/` - Training documents in markdown format covering power system theory and PV curve concepts
- `vector.py` - Interface layer for vector database operations and similarity search
- `train.py` - Script to process training data and build/update the vector database

**Workflow Orchestration:**
- `workflows/` - LangGraph workflow definitions coordinating agent behavior
  - `workflow.py` - Unified workflow handling both simple and complex multi-step tasks with planning, execution, and error handling

**Processing Nodes:**
- `nodes/` - Individual processing units that handle specific agent functions
  - `classify.py` - Message classification and type detection
  - `route.py` - Routing logic to direct messages to appropriate handlers
  - `question_general.py` - General Q&A with RAG retrieval for power system knowledge
  - `question_parameter.py` - Parameter-specific Q&A and explanations
  - `parameter.py` - Parameter modification, validation, and state management
  - `generation.py` - PV curve generation task execution
  - `planner.py` - Multi-step plan creation and decomposition
  - `step_controller.py` - Step execution control for compound tasks
  - `advance_step.py` - Step advancement logic for multi-step workflows
  - `summary.py` - Summary generation for completed tasks
  - `error_handler.py` - Error handling and retry logic

**Data Models:**
- `state/` - State management definitions
  - `app_state.py` - Core State TypedDict defining the agent's state structure
- `schemas/` - Pydantic data structures defining system interfaces
  - `classifier.py` - Classification schema definitions
  - `inputs.py` - Input parameter validation schemas
  - `parameter.py` - Parameter modification schemas
  - `planner.py` - Multi-step plan structures for complex task decomposition
  - `response.py` - Response format schemas
  - `session.py` - Session management schemas
- `session.py` - SessionManager class for managing agent sessions and streaming execution

**Domain Logic:**
- `pv_curve/` - Power system simulation engine using pandapower for IEEE test systems
  - `pv_curve.py` - Core PV curve generation with voltage stability analysis

**Support Utilities:**
- `utils/common_utils.py` - Helper functions for state management and display formatting
- `utils/context.py` - Context management utilities
- `utils/reranker.py` - Reranking utilities for RAG retrieval
- `history_manager.py` - Conversation history management and session persistence
- `core.py` - Core setup functions for LLM, prompts, and graph creation

## License

This repository is licensed under the [MIT License](./LICENSE), unless specified otherwise in subdirectories.
