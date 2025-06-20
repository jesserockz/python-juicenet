# Archived 

The juicenet API has been shut down.

There are multiple open source projects available to receive data and control charging directly via UDP.

- https://github.com/JuiceRescue/juicepassproxy


# Python Juicenet

Access to the Juicenet EVSE charger API


## Example

```python
import aiohttp
import asyncio
import pyjuicenet

async def main():
  async with aiohttp.ClientSession() as session:
    api = pyjuicenet.Api('ACCESS_TOKEN', session)
    devices = await api.get_devices()
    charger = devices[0]
    await charger.update_state()
    print(charger.voltage) # 240
    await charger.set_override(True) # Charge the car now ignoring the schedule

asyncio.run(main())
```
