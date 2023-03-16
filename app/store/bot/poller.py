# import asyncio
# from asyncio import Task
# from typing import Optional
#
# from app.store import Store
#
#
# g_i = 0
#
#
# class Poller:
#     def __init__(self, store: Store):
#         self.store = store
#         self.is_running = False
#         self.poll_task: Optional[Task] = None
#
#     async def start(self):
#         self.is_running = True
#         self.poll_task = asyncio.create_task(self.poll())
#
#     async def stop(self):
#         # TODO: gracefully завершить Poller
#         self.is_running = False
#         if self.poll_task:
#             await asyncio.wait([self.poll_task], timeout=31)
#         self.poll_task.cancel()
#
#     async def poll(self):
#         global g_i
#         while self.is_running:
#             print("Poller poll ", g_i)
#             await self.store.vk_api.poll()
#             g_i += 1
