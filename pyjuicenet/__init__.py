"""Access data from the Juicenet API."""
import asyncio
import logging
import time
import uuid

import aiohttp

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://jbv1-api.emotorwerks.com"


class Charger:
    """Juicenet charger instance."""

    def __init__(self, json_settings, api):
        """Create a Charger."""
        self.json_settings = json_settings
        self.json_state = {}
        self.api = api
        self.last_updated_at = 0

    @property
    def name(self) -> str:
        """Return the name."""
        return self.json_settings.get("name")

    @property
    def token(self) -> str:
        """Return the token."""
        return self.json_settings.get("token")

    @property
    def id(self) -> str:  # pylint: disable=invalid-name
        """Return the id."""
        return self.json_settings.get("unit_id")

    async def update_state(self, force=False) -> bool:
        """Update state with latest info from API."""
        if not force and time.time() - self.last_updated_at < 30:
            return True
        self.last_updated_at = time.time()
        json_state = await self.api.get_device_state(self)
        self.json_state = json_state
        return json_state["success"]

    @property
    def voltage(self) -> int:
        """Get the voltage."""
        return self.json_state.get("charging").get("voltage")

    @property
    def amps(self) -> float:
        """Get the current Amperage."""
        return self.json_state.get("charging").get("amps_current")

    @property
    def watts(self) -> float:
        """Get the current Wattage."""
        return self.json_state.get("charging").get("watt_power")

    @property
    def status(self) -> str:
        """Get the current status."""
        return self.json_state.get("state")

    @property
    def temperature(self) -> int:
        """Get the current temperature."""
        return self.json_state.get("temperature")

    @property
    def charge_time(self) -> int:
        """Get the current session charge time."""
        return self.json_state.get("charging").get("seconds_charging")

    @property
    def energy_added(self) -> int:
        """Get the current session energy."""
        return self.json_state.get("charging").get("wh_energy")

    @property
    def override_time(self) -> int:
        """Get the override time."""
        return self.json_state.get("override_time")

    async def set_override(self, charge_now) -> bool:
        """Set to override schedule or not."""
        override_time = 0
        energy_at_plugin = 0
        energy_to_add = 0

        if charge_now:
            # To enter the "Charge Now" state, override_time
            # should be set to a time in the past. Otherwise, it simply
            # sets the target time the vehicle should be charged by.
            # Through experiment, it appears that override_time expects the
            # timestamp in the timezone of the unit, so we will simply set
            # override_time to the last known unit_time from the json_state.

            # First, (re)load state in case it's empty or stale
            await self.update_state(True)
            override_time = self.json_state["unit_time"]
            # energy_to_add actually comes from your vehicle configuration.
            # Since we don't know the charge state of the vehicle, this is
            # normally the complete battery capacity of the vehicle.
            energy_to_add = self.json_state["charging"]["wh_energy_to_add"]

        override_state = await self.api.set_override(
            self, override_time, energy_at_plugin, energy_to_add
        )

        # Update state again to show current override status
        await self.update_state(True)

        return override_state["success"]


class Api:
    """Api represents the connection to the Juicenet server."""

    def __init__(
            self,
            api_token: str,
            session: aiohttp.ClientSession = None
    ):
        """Create an instance."""
        self.api_token = api_token
        self.uuid = str(uuid.uuid4())
        if not session:
            async def _create_session() -> aiohttp.ClientSession:
                return aiohttp.ClientSession()

            loop = asyncio.get_event_loop()
            if loop.is_running():
                self.session = aiohttp.ClientSession()
            else:
                self.session = loop.run_until_complete(_create_session())
        else:
            self.session = session

    async def close_connection(self):
        """Close the aiohtto session."""
        await self.session.close()

    async def get_devices(self):
        """Fetch the device list."""
        data = {
            "device_id": self.uuid,
            "cmd": "get_account_units",
            "account_token": self.api_token
        }
        response = await self.session.post(
            f"{BASE_URL}/box_pin", json=data,
        )
        response_json = await response.json()

        if not response_json.get("success"):
            raise TokenError(response_json.get("error_message"))

        units_json = response_json.get("units")
        devices = []
        for unit in units_json:
            device = Charger(unit, self)
            await device.update_state()
            devices.append(device)

        return devices

    async def get_device_state(self, charger: Charger):
        """Fetch the full state of a specific charger."""
        data = {
            "device_id": self.uuid,
            "cmd": "get_state",
            "token": charger.token,
            "account_token": self.api_token
        }

        response = await self.session.post(
            f"{BASE_URL}/box_api_secure", json=data,
        )
        return await response.json()

    async def get_info(self, charger: Charger):
        """Fetch more info about the charger."""
        data = {
            "device_id": self.uuid,
            "cmd": "get_info",
            "token": charger.token,
            "account_token": self.api_token
        }

        response = await self.session.post(
            f"{BASE_URL}/box_api_secure", json=data,
        )
        return await response.json()

    async def set_override(
        self,
        charger: Charger,
        override_time: int,
        energy_at_plugin: int,
        energy_to_add: int
    ):
        """Set the override for the charging schedule."""
        data = {
            "device_id": self.uuid,
            "cmd": "set_override",
            "token": charger.token,
            "account_token": self.api_token,
            "override_time": override_time,
            "energy_at_plugin": energy_at_plugin,
            "energy_to_add": energy_to_add
        }

        response = await self.session.post(
            f"{BASE_URL}/box_api_secure", json=data,
        )
        return await response.json()


class TokenError(Exception):
    """Error to indicate token is invalid."""
