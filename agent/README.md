# AI Agent
AI Agent which creates PV curves or answers Voltage Stability related requests using LLMs and RAG.

## TODO
- [ ] `/pv_curve`
- [X] `Modelfile`
- [ ] Improve documentation
- [ ] Improve prompting and classification model

## Installation & Run
Run Agent locally:

```bash
cd /agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```