import asyncio
import json
from typing import AsyncGenerator, Any

class EventBroadcaster:
    def __init__(self):
        self._queues: dict[str, list[asyncio.Queue]] = {}

    def subscribe(self, run_id: str) -> asyncio.Queue:
        if run_id not in self._queues:
            self._queues[run_id] = []
        q = asyncio.Queue()
        self._queues[run_id].append(q)
        return q

    def unsubscribe(self, run_id: str, q: asyncio.Queue):
        if run_id in self._queues:
            if q in self._queues[run_id]:
                self._queues[run_id].remove(q)
            if not self._queues[run_id]:
                del self._queues[run_id]

    async def broadcast(self, run_id: str, event_type: str, payload: dict[str, Any]):
        data = {"type": event_type, "payload": payload}
        if run_id in self._queues:
            for q in list(self._queues[run_id]):
                await q.put(data)

broadcaster = EventBroadcaster()

async def event_generator(run_id: str) -> AsyncGenerator[str, None]:
    q = broadcaster.subscribe(run_id)
    try:
        while True:
            item = await q.get()
            event_type = item["type"]
            payload = item["payload"]
            yield f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"
            if event_type in ("final", "error"):
                break
    finally:
        broadcaster.unsubscribe(run_id, q)