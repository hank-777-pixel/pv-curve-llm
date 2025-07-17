# AI Agent

AI Agent which creates PV curves or answers Voltage Stability related requests using LLMs and RAG.

## Current Agentic Workflow

![Agentic Workflow Diagram](workflow.png)

### Potential improvements:

- Separate RAG agents to different nodes with smaller vector databases (i.e. analysis database, general voltage stability question database, questions about agent/repo database, etc.)
- Add Error node, determining the cause of failure and responding to the user with feedback instead of breaking flow.

## TODO

- [ ] `/pv_curve`
- [X] Improve `Modelfile`
- [ ] Improve documentation
- [X] Improve prompting `prompts.py` and classification model
- [X] Create visual map of nodes
- [ ] Consider instead of just answering questions about PV-curves generally to fetch guidelines, explain parameters, etc. (Add more nodes to LangGraph)
- [ ] Multiple DBs/RAG sources depending on usage (Explanation, Analysis, etc.)
- [ ] Add Error handling/analysis node
- [X] Make inputs less involved and use more natural language, where the AI can determine the parameter values based on RAG context
- [ ] Review copyright information and add vector DB to git
- [X] Could split question node to classify type of question. Could be related to what an input means, could be general about curves, etc.
- [ ] Add web crawling node to agent for more advanced questions
- [ ] Update `workflow.png` to reflect changes to nodes/structure

## Installation & Run

Run Agent locally:

```bash
cd /agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
