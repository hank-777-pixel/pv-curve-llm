# AI Agent
AI Agent which creates PV curves or answers Voltage Stability related requests using LLMs and RAG.

## TODO
- [ ] `/pv_curve`
- [X] Improve `Modelfile`
- [ ] Improve documentation
- [ ] Improve prompting `prompts.py` and classification model
- [ ] Create visual map of nodes
- [ ] Consider instead of just answering questions about PV-curves generally to fetch guidelines,
explain parameters, etc. (Add more nodes to LangGraph)

## Installation & Run
Run Agent locally:

```bash
cd /agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```