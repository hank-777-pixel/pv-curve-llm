# AI Agent

Utilizing LLMs to contextualize, create, and analyze Power-Voltage Curves for Power System Voltage Stability analysis.

## Current Agentic Workflow

![Agentic Workflow Diagram](workflow.png)

## TODO

- [X] `/pv_curve`
- [X] Improve `Modelfile`
- [ ] Improve documentation
- [X] Improve prompting `prompts.py` and classification model
- [X] Create visual map of nodes
- [ ] Multiple DBs/RAG sources depending on usage (Explanation, Analysis, etc.)
- [X] Add Error handling/analysis node
- [X] Make inputs less involved and use more natural language, where the AI can determine the parameter values based on RAG context
- [X] Review copyright information and add vector DB to git
- [X] Could split question node to classify type of question. Could be related to what an input means, could be general about curves, etc.
- [ ] Add web crawling node to agent for more advanced questions
- [ ] Update `workflow.png` to reflect changes to nodes/structure
- [ ] For Parameter questions, add context of what will happen to curve based on changes in parameters
- [ ] Have LLM understand context to modify inputs in certain way. i.e. generate a system that has a certain looking curve, or something that will replicate a certain environment, etc.
- [ ] Lower quality models (particularly DeepSeek) hallucinate about Photovoltaic Systems

## Installation & Run

Run Agent locally:

```bash
cd /agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
