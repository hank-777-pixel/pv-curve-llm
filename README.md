# PV Curve LLM (Work in Progress)

<img src="https://github.com/CURENT/andes/raw/master/docs/source/images/sponsors/CURENT_Logo_NameOnTrans.png" alt="CURENT ERC Logo" width="300" height="auto">

Using LLMs to contextualize, create, and analyze Power-Voltage Curves (Nose Curves) for Power System Voltage Stability analysis. This project experiments with AI agents and to accomplish specific tasks with natural language.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/CURENT/pv-curve-llm/blob/master/LICENSE)
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![GitHub last commit (master)](https://img.shields.io/github/last-commit/CURENT/pv-curve-llm/master?label=last%20commit%20to%20master)](https://github.com/CURENT/pv-curve-llm/commits/master/)
[![Visitors](https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Fgithub.com%2FCURENT%2Fpv-curve-llm&countColor=%2337d67a&style=plastic)](https://visitorbadge.io/status?path=https%3A%2F%2Fgithub.com%2FCURENT%2Fpv-curve-llm)

# Installation & Run

### Prerequisites

- Python 3.8+
- Ollama installed and running: https://www.ollama.com/download

### Quick Start

```bash
# Run terminal as administrator
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
ollama pull deepseek-r1:7b
ollama create pv-curve -f agent\Modelfile
python main.py
```

To leave the virtual environment, enter `deactivate`.

# Custom vector database

To setup a custom vector database, see `agent/data/README.md`

# Agent Workflow

![Agentic Workflow Diagram](agent/workflow.png)

# License

This repository is licensed under the [MIT License](./LICENSE), unless specified otherwise in subdirectories.
