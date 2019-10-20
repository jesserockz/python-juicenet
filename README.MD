# Python Juicenet

Access to the Juicenet EVSE charger API


## Example

```python
>>> import pyjuicenet
>>> api = pyjuicenet.Api('ACCESS_TOKEN')
>>> devices = api.get_devices()
>>> devices[0].update_state()
>>> devices[0].getVoltage()
240
>>> devices[0].setOverride(True) # Charge the car now ignoring the schedule
True
```
