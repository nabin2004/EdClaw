import asyncio

class Orchestrator:
    """
    Controls concurrency per session (very simplified version)
    """

    def __init__(self):
        self.locks = {}

    async def acquire(self, session_id):
        if session_id not in self.locks:
            self.locks[session_id] = asyncio.Lock()

        await self.locks[session_id].acquire()

    def release(self, session_id):
        self.locks[session_id].release()