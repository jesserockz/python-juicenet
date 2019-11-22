"""Access data from the Juicenet API"""
import uuid
import json
import time
import requests

class Api:
    # URL from the official API documentation:
    BASE_URL = "https://jbv1-api.emotorwerks.com"

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
        if not response_json.get("success"):
            raise ValueError(response_json.get("error_message"))

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

    def get_info(self, charger):
        data = {
            "device_id": self.uuid,
            "cmd": "get_info",
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

    def set_override(self, charger, override_time, energy_at_plugin, energy_to_add):
        data = {
            "device_id": self.uuid,
            "cmd": "set_override",
            "token": charger.token(),
            "account_token": self.api_token,
            "override_time": override_time,
            "energy_at_plugin": energy_at_plugin,
            "energy_to_add": energy_to_add
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

    def update_state(self, force=False):
        """ Update state with latest info from API. """
        if not force and time.time() - self.last_updated_at < 30:
            return True
        self.last_updated_at = time.time()
        json_state = self.api.get_device_state(self)
        self.json_state = json_state
        return json_state["success"]

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

    def getOverrideTime(self):
        return self.json_state.get("override_time")

    def setOverride(self, charge_now):
        override_time = 0
        energy_at_plugin = 0
        energy_to_add = 0

        if charge_now:
            # To enter the "Charge Now" state, override_time should be set to a time in the past.
            # Otherwise, it simply sets the target time the vehicle should be charged by.
            # Through experiment, it appears that override_time expects the timestamp
            # in the timezone of the unit, so we will simply set override_time to the
            # last known unit_time from the json_state.

            # First, (re)load state in case it's empty or stale
            self.update_state(True)
            override_time = self.json_state["unit_time"]
            # energy_to_add actually comes from your vehicle configuration.  Since we don't
            # know the charge state of the vehicle, this is normally the complete
            # battery capacity of the vehicle.
            energy_to_add = self.json_state["charging"]["wh_energy_to_add"]

        override_state = self.api.set_override(self, override_time, energy_at_plugin, energy_to_add)

        # Update state again to show current override status
        self.update_state(True)

        return override_state["success"]
