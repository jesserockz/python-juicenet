"""Access data from the Juicenet API"""
import uuid
import json
import time
import requests

class Api:

    BASE_URL = "http://emwjuicebox.cloudapp.net"

    def __init__(self, api_token):
        self.api_token = api_token
        self.uuid = str(uuid.uuid4())

    def get_devices(self):
        data = {
            "device_id": self.uuid,
            "cmd": "get_account_units",
            "account_token": self.api_token
        }
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post("{}/box_pin".format(self.BASE_URL),
                                 data=json.dumps(data),
                                 headers=headers)
        response_json = response.json()
        units_json = response_json.get("units")
        devices = []
        for unit in units_json:
            device = Charger(unit, self)
            device.update_state()
            devices.append(device)

        return devices

    def get_device_state(self, charger):
        data = {
            "device_id": self.uuid,
            "cmd": "get_state",
            "token": charger.token(),
            "account_token": self.api_token
        }
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post("{}/box_api_secure".format(self.BASE_URL),
                                 data=json.dumps(data),
                                 headers=headers)
        response_json = response.json()
        return response_json


class Charger:
    def __init__(self, json_settings, api):
        self.json_settings = json_settings
        self.json_state = {}
        self.api = api
        self.last_updated_at = 0

    def name(self):
        return self.json_settings.get("name")

    def token(self):
        return self.json_settings.get("token")

    def id(self):
        return self.json_settings.get("unit_id")

    def update_state(self):
        """ Update state with latest info from API. """
        if time.time() - self.last_updated_at < 30:
            return True
        self.last_updated_at = time.time()
        json_state = self.api.get_device_state(self)
        self.json_state = json_state
        return True

    def getVoltage(self):
        return self.json_state.get("charging").get("voltage")

    def getAmps(self):
        return self.json_state.get("charging").get("amps_current")

    def getWatts(self):
        return self.json_state.get("charging").get("watt_power")

    def getStatus(self):
        return self.json_state.get("state")

    def getTemperature(self):
        return self.json_state.get("temperature")

    def getChargeTime(self):
        return self.json_state.get("charging").get("seconds_charging")

    def getEnergyAdded(self):
        return self.json_state.get("charging").get("wh_energy")
