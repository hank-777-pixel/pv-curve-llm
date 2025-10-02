from agent.output.sinks import MemorySink


class WebUICapture:
    def __init__(self):
        self._mem = MemorySink()
    
    def info(self, text: str):
        from agent.output.router import info as _info
        _info(text)
    
    def answer(self, text: str):
        from agent.output.router import answer as _answer
        _answer(text)
    
    def spinner(self, text: str):
        from agent.output.router import spinner as _spinner
        return _spinner(text)
    
    def get_progress_messages(self):
        return self._mem.get_events()
    
    def clear(self):
        self._mem.clear()

