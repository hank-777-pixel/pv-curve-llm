# PV Curve Agent: AI-Powered Voltage Stability Analysis

<img src="https://github.com/CURENT/andes/raw/master/docs/source/images/sponsors/CURENT_Logo_NameOnTrans.png" alt="CURENT ERC Logo" width="300" height="auto">

**Conversational agent for power system voltage stability analysis through PV curve generation and AI analysis**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/CURENT/pv-curve-llm/blob/master/LICENSE)
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![GitHub last commit (master)](https://img.shields.io/github/last-commit/CURENT/pv-curve-llm/master?label=last%20commit%20to%20master)](https://github.com/CURENT/pv-curve-llm/commits/master/)
[![Visitors](https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Fgithub.com%2FCURENT%2Fpv-curve-llm&countColor=%2337d67a&style=plastic)](https://visitorbadge.io/status?path=https%3A%2F%2Fgithub.com%2FCURENT%2Fpv-curve-llm)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [LangGraph Workflow](#langgraph-workflow)
- [Node Reference](#node-reference)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Overview

The **PV Curve Agent** is an AI-powered system that brings natural language interaction to power system voltage stability analysis. Built on LangGraph and LangChain, it combines conversational AI with power system simulation to make voltage stability analysis accessible and intelligent.

This project is part of the **CURENT Large-scale Testbed (LTB)** research initiative, exploring how modern AI frameworks and large language models can be integrated into power system analysis workflows. The agent uses a sophisticated multi-agent architecture to understand user intent, manage parameters, generate comprehensive voltage stability analyses through PV (Power-Voltage) curve generation, and provide analysis on the results.

**What it does:**

- Generates PV curves (nose curves) for voltage stability analysis on IEEE test systems
- Provides conversational interface for parameter modification and exploration
- Offers intelligent analysis and explanations using retrieval-augmented generation (RAG)
- Handles complex multi-step workflows with automatic task decomposition

**Why it exists:**

- Research AI integration pathways for CURENT LTB
- Demonstrate practical applications of LLM agents in power systems
- Lower the barrier to entry for voltage stability analysis
- Experiment with agentic workflows for domain-specific engineering tasks

**Technology Stack:**

- **Agent Framework**: LangGraph, LangChain
- **LLMs**: OpenAI (o3-mini), Ollama (local models)
- **Power Simulation**: pandapower
- **Knowledge Base**: Chroma vector database with RAG
- **Validation**: Pydantic models with structured outputs

## Key Features

### 🤖 Intelligent Agent System

- **Multi-Agent Orchestration**: LangGraph-based workflow with 11 specialized nodes
- **Natural Language Interface**: Ask questions, modify parameters, and request analyses conversationally
- **RAG-Enhanced Intelligence**: Vector database storing power systems knowledge for context-aware responses
- **Structured Outputs**: Pydantic schemas ensure reliable, type-safe agent responses

### ⚡ Power System Analysis

- **IEEE Test Systems**: Support for IEEE 14/24/30/39/57/118/300 bus systems from pandapower
- **PV Curve Generation**: Automated voltage stability analysis using pandapower
- **Comprehensive Metrics**: Load margin (MW), nose point voltage, convergence analysis, and more
- **Visual Output**: Matplotlib plots

### 🔄 Advanced Workflow Capabilities

- **Multi-Step Planning**: Automatically decomposes complex queries into executable action sequences
- **Error Recovery**: Intelligent error handling with retry mechanisms and auto-correction
- **Context Awareness**: Maintains conversation history and enables comparative analysis across queries
- **Adaptive Routing**: Conditional workflow paths based on query complexity and state

### 🎯 Flexible Deployment

- **Multiple LLM Providers**: Choose between OpenAI API (recommended) or Ollama local models
- **Session Management**: Persistent conversation storage with JSON-based history
- **Extensible Architecture**: Modular design enables easy addition of new capabilities

## Architecture

### System Overview

The PV Curve Agent uses a graph-based architecture powered by LangGraph, where nodes represent specialized agents and edges define the flow of execution. This enables complex, stateful, multi-agent workflows with dynamic routing and error recovery.

![Workflow Architecture](images/workflow.png)

### Core Components

#### 1. State Management (`agent/state/`)

The system maintains a shared, typed state object that flows through the entire workflow:

```python
State = {
    messages: List[AIMessage | HumanMessage],
    message_type: str | None,
    inputs: Inputs,
    results: dict | None,
    error_info: dict | None,
    plan: MultiStepPlan | None,
    current_step: int,
    step_results: List[dict],
    is_compound: bool,
    retry_count: int,
    failed_node: str | None,
    conversation_context: List[dict]
}
```

- **TypedDict-based**: Ensures type safety across all nodes
- **Pydantic Validation**: Input parameters validated with strict schemas
- **Message Accumulation**: LangGraph reducers automatically manage conversation history

#### 2. Workflow Orchestration (`agent/workflows/`)

LangGraph StateGraph with 11 interconnected nodes:

- **Fixed Edges**: Deterministic paths (e.g., START → Classifier → Router)
- **Conditional Edges**: Dynamic routing based on state (e.g., Router → 5 destinations)
- **Cycles**: Multi-step plans create controlled loops (Step Controller ↔ Advance Step)

#### 3. Processing Nodes (`agent/nodes/`)

Eleven specialized agents handle specific tasks:

- **Routing**: Classifier, Router
- **Planning**: Planner, Step Controller, Advance Step
- **Action**: Question General, Question Parameter, Parameter, Generation
- **Support**: Error Handler, Summary

Each node receives state, performs its function, and returns state updates.

#### 4. Knowledge Base (`agent/vector_db/` & `agent/data/`)

- **Chroma Vector Database**: Embeddings of power system theory documents
- **RAG Pipeline**: Similarity search retrieves relevant context for LLM responses
- **Custom Training**: Add markdown documents to expand knowledge base

#### 5. Domain Engine (`agent/pv_curve/`)

- **pandapower Integration**: IEEE test system power flow simulation
- **PV Curve Algorithm**: Iterative load increase with voltage monitoring
- **Convergence Handling**: Detects and reports stability limits (nose point)
- **Visualization**: Matplotlib-based professional plotting

## Installation

### Prerequisites

- **Python**: 3.8 or higher
- **Ollama**: Required for local models ([Download](https://ollama.com/download))
- **Git**: For cloning repository

### Step-by-Step Setup

1. **Clone the repository**

```bash
git clone https://github.com/CURENT/pv-curve-llm.git
cd pv-curve-llm
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Setup Ollama models** (for local deployment)

```bash
ollama pull mxbai-embed-large  # Embedding model for RAG
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

The `agent/` directory contains the core LangGraph AI agent system with the following architecture:

**Core Entry Points:**
- `main.py` - Primary application entry point for local execution with terminal UI

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
  - `compound_workflow.py` - Complex multi-step task orchestration with planning and execution
  - `simple_workflow.py` - Basic single-step task routing and execution

**Processing Nodes:**
- `nodes/` - Individual processing units that handle specific agent functions
  - `classifier_nodes.py` - Message classification (question/parameter/generation) and routing logic
  - `parameter_nodes.py` - Parameter modification, validation, and state management
  - `execution_nodes.py` - Task execution including Q&A with RAG, parameter explanations, and analysis

**Data Models:**
- `models/` - Pydantic data structures defining system state and interfaces
  - `state_models.py` - Core state management and input parameter validation
  - `plan_models.py` - Multi-step plan structures for complex task decomposition

**Domain Logic:**
- `pv_curve/` - Power system simulation engine using pandapower for IEEE test systems
  - `pv_curve.py` - Core PV curve generation with voltage stability analysis

**Support Utilities:**
- `utils/common_utils.py` - Helper functions for state management and display formatting

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### Third-Party Licenses

- **LangChain/LangGraph**: MIT License
- **pandapower**: BSD 3-Clause License
- **Chroma**: Apache License 2.0

## Acknowledgments

### Organizations

- **[CURENT LTB](https://ltb.curent.org/)**: CURENT Large-scale Testbed (LTB) is a platform for power system development and testing.

### Technologies

- **[LangChain](https://github.com/langchain-ai/langchain)** & **[LangGraph](https://github.com/langchain-ai/langgraph)**: Agent framework and workflow orchestration
- **[pandapower](https://www.pandapower.org/)**: Power system simulation and analysis
- **[OpenAI](https://openai.com/)**: Large language model API
- **[Ollama](https://ollama.com/)**: Local LLM deployment
- **[Chroma](https://www.trychroma.com/)**: Vector database for RAG

### Related CURENT Projects

- **[ANDES](https://github.com/CURENT/andes)**: Power System Transient Stability Simulator
- **[LTB](https://github.com/CURENT/ltb)**: CURENT Large-scale Testbed
- **[AGVis](https://github.com/CURENT/agvis)**: Power Grid Visualization

### Contributors

- [Matt Cannavaro](https://www.github.com/mcnvr)
- [Hank Lin](https://github.com/Hank0857)

---

**Maintained by**: CURENT Research Team
**Contact**: [GitHub Issues](https://github.com/CURENT/pv-curve-llm/issues)

<img src="https://github.com/CURENT/andes/raw/master/docs/source/images/sponsors/CURENT_Logo_NameOnTrans.png" alt="CURENT ERC Logo" width="200" height="auto">
