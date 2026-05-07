"""
key-stroke level DELTA streaming (correct version)

Future improvements:
1. Proper diff (Myers algorithm)
2. Cursor tracking per user
3. Operation IDs (ordering)
4. CRDT version (real collaboration)
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json

app = FastAPI()


# -----------------------------
# Connection Manager
# -----------------------------
class ConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []
        self.last_state: dict[WebSocket, str] = {}

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)
        self.last_state[ws] = ""

    def disconnect(self, ws: WebSocket):
        self.connections.remove(ws)
        self.last_state.pop(ws, None)

    async def broadcast(self, message: dict, sender: WebSocket):
        for connection in self.connections:
            if connection != sender:
                await connection.send_json(message)


manager = ConnectionManager()


# -----------------------------
# Simple diff engine
# (1-step diff only for demo)
# -----------------------------
def compute_delta(old: str, new: str):
    """
    Returns minimal insert/delete ops.
    This is NOT full diff algorithm, just first-change detection.
    """

    # find first mismatch
    i = 0
    while i < len(old) and i < len(new) and old[i] == new[i]:
        i += 1

    # INSERT
    if len(new) > len(old):
        return {
            "type": "insert",
            "pos": i,
            "char": new[i]
        }

    # DELETE
    if len(new) < len(old):
        return {
            "type": "delete",
            "pos": i
        }

    return None


# -----------------------------
# WebSocket endpoint
# -----------------------------
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)

    print("Client Connected!")

    try:
        while True:
            new_text = await ws.receive_text()

            old_text = manager.last_state[ws]

            delta = compute_delta(old_text, new_text)

            # update stored state
            manager.last_state[ws] = new_text

            print("Received full text:", new_text)
            print("Computed delta:", delta)

            # broadcast ONLY delta
            if delta:
                await manager.broadcast(delta, ws)

    except WebSocketDisconnect:
        manager.disconnect(ws)
        print("Client disconnected")