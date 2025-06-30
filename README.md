# PV Curve LLM (Work in Progress)
<div align="left-center">
  <img src="https://github.com/CURENT/andes/raw/master/docs/source/images/sponsors/CURENT_Logo_NameOnTrans.png" alt="CURENT ERC Logo" style="width: 300px; height: 120px; object-fit: contain; margin: 10px;">
  <img src="ui/public/clemson-logo.png" alt="CLEMSON UNIVERSITY Logo" style="width: 300px; height: 120px; object-fit: contain; margin: 10px;">
</div>

Use natural language to generate PV Curves for Voltage Stability Analysis via an AI agent.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/CURENT/pv-curve-llm/blob/master/LICENSE)
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![GitHub last commit (master)](https://img.shields.io/github/last-commit/CURENT/pv-curve-llm/master?label=last%20commit%20to%20master)](https://github.com/CURENT/pv-curve-llm/commits/master/)
[![Visitors](https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Fgithub.com%2FCURENT%2Fpv-curve-llm&countColor=%2337d67a&style=plastic)](https://visitorbadge.io/status?path=https%3A%2F%2Fgithub.com%2FCURENT%2Fpv-curve-llm)

# TODO
- [ ] Improve `/agent` documentation
- [ ] Improve prompts in `agent/prompts.json`
- [ ] Review and improve PV Curve inputs in `agent/inputs.json`
- [ ] Create function to generate PV Curves using inputs from `agent/inputs.json` (See `agents/pv-curve`)
- [ ] Add documentation/graph for agentic workflow
- [ ] Add LangGraph node to generate PV curve
- [ ] Add LangGraph node to review PV curve and process user feedback
- [ ] Research/review legality of the data stored in `agent/data` in Open-Source repo. More info in `agent/data/README.md` 
- [ ] Add API implementation of `/agent` run on `server/server.py` for UI interaction
- [ ] UI documentation

# Installation & Run
TODO

# License
This repository is licensed under the [MIT License](./LICENSE), unless specified otherwise in subdirectories.