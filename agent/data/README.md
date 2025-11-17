# RAG Training Data

The data in this directory serves to train the RAG agent. Due to copyright, this raw data is not included in the repository. However, the embedded vector database is included.

## Custom Data

To embed custom data in the vector database, format your data as specified below and run `/agent/train.py`

## Required Data Format

Each `.md` document must be grouped by headers (e.g. beginning with #, ##, ###, etc.)

Example text document format:
```
## Chunk 1
This is one chunk of data.

I can write as much as I want with newlines between it.

### Chunk 2 Header
This is another chunk of data.
```

This is automatically embedded into the vector database based on this format.
Run `agent/train.py` from the project root to retrain the RAG agent.

## TODO

- [ ] Properly cite training resources under a citations header

# Citations
