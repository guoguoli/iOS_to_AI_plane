import time 
import asyncio 
def sync_workflow():
    start = time.time()
    task1 = time.sleep(2)
    task2 = time.sleep(2)
    task3 = time.sleep(2)
    elapsed = time.time() - start
    return f"Sync workflow took {elapsed:.2f} seconds"
async def async_workflow():
    start = time.time()
    await asyncio.gather(
        asyncio.sleep(2),
        asyncio.sleep(2),
        asyncio.sleep(2)
    )
    elapsed = time.time() - start
    return f"Async workflow took {elapsed:.2f} seconds"
if __name__ == "__main__":
    print(sync_workflow())
    print(asyncio.run(async_workflow()))

    