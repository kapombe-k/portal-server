import os
from routeros_api import RouterOsApiPool
from datetime import timedelta

class RouterManager:
    def __init__(self):
        self.host = os.environ.get('MIKROTIK_HOST')
        self.username = os.environ.get('MIKROTIK_USERNAME')
        self.password = os.environ.get('MIKROTIK_PASSWORD')
        self.api_pool = None

    def connect(self):
        """Initializes the connection pool."""
        try:
            self.api_pool = RouterOsApiPool(
                host=self.host,
                username=self.username,
                password=self.password,
                port=int(os.environ.get('MIKROTIK_API_PORT', 8728)),
                use_ssl=False
            )
            return True
        except Exception as e:
            print(f"Router connection failed: {e}")
            return False

    def get_api(self):
        """Gets an API object from the pool."""
        if not self.api_pool:
            self.connect()
        return self.api_pool.get_api()

    def authorize_mac(self, mac_address, ip_address, comment=""):
        """Bypasses a device in the hotspot using its MAC address."""
        api = self.get_api()
        try:
            ip_bindings = api.get_resource('/ip/hotspot/ip-binding')
            ip_bindings.add(
                mac_address=mac_address,
                address=ip_address,
                to_address=ip_address,
                type='bypassed',
                comment=comment
            )
            print(f"Successfully authorized MAC: {mac_address}")
            return True
        except Exception as e:
            print(f"Failed to authorize MAC {mac_address}: {e}")
            return False

    def remove_authorization(self, mac_address):
        """Removes a bypassed device to terminate its session."""
        api = self.get_api()
        try:
            ip_bindings = api.get_resource('/ip/hotspot/ip-binding')
            binding = ip_bindings.get(mac_address=mac_address)
            if binding:
                ip_bindings.remove(id=binding[0]['id'])
                print(f"Successfully removed authorization for MAC: {mac_address}")
            return True
        except Exception as e:
            print(f"Failed to remove authorization for MAC {mac_address}: {e}")
            return False

    def disconnect(self):
        """Disconnects the pool."""
        if self.api_pool:
            self.api_pool.disconnect()