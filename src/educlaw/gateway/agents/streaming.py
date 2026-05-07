
class Streamer:
    def __init__(self, ws):
        self.ws = ws 

    async def token(self, token: str):
        await self.ws.send_json({
            "type": "assistant.delta",
            "token": token 
        })

    async def event(self, event_type: str, data):
        await self.ws.send_json({
            "type": event_type, 
            "data": data 
        })
        