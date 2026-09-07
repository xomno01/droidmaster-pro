# -*- coding: utf-8 -*-
"""
DroidMaster Pro - Smart Device Profiles & Route Resolver
Provides persistent device management, custom hardware configs,
and intelligent fallback connection routing (USB -> LAN -> Tailscale).
"""

import json
import os
import re
import socket
import time
from typing import Dict, List, Optional, Tuple, Any

# Dynamic path resolution
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_FILE = os.path.join(CURRENT_DIR, "profiles.json")


def is_socket_reachable(host: str, port: int = 5555, timeout: float = 1.0) -> bool:
    """Ultra-fast TCP socket check to test if device ADB daemon is reachable
    without incurring subprocess spawn overhead.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


class DeviceProfile:
    """Data model representing a managed Android device."""

    def __init__(
        self,
        id: str,
        name: str,
        model: str = "",
        usb_serial: str = "",
        lan_endpoint: str = "",
        tailscale_endpoint: str = "",
        preferred_route: str = "auto",  # 'auto', 'tailscale', 'lan', 'usb'
        extra_scrcpy_flags: Optional[List[str]] = None,
        auto_reconnect: bool = True,
        max_reconnect_attempts: int = 3,
        notes: str = "",
        last_connected_at: float = 0.0,
    ):
        self.id = id
        self.name = name
        self.model = model
        self.usb_serial = usb_serial
        self.lan_endpoint = lan_endpoint
        self.tailscale_endpoint = tailscale_endpoint
        self.preferred_route = preferred_route
        self.extra_scrcpy_flags = extra_scrcpy_flags or []
        self.auto_reconnect = auto_reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        self.notes = notes
        self.last_connected_at = last_connected_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "model": self.model,
            "usb_serial": self.usb_serial,
            "lan_endpoint": self.lan_endpoint,
            "tailscale_endpoint": self.tailscale_endpoint,
            "preferred_route": self.preferred_route,
            "extra_scrcpy_flags": self.extra_scrcpy_flags,
            "auto_reconnect": self.auto_reconnect,
            "max_reconnect_attempts": self.max_reconnect_attempts,
            "notes": self.notes,
            "last_connected_at": self.last_connected_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceProfile":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Thiết bị không tên"),
            model=data.get("model", ""),
            usb_serial=data.get("usb_serial", ""),
            lan_endpoint=data.get("lan_endpoint", ""),
            tailscale_endpoint=data.get("tailscale_endpoint", ""),
            preferred_route=data.get("preferred_route", "auto"),
            extra_scrcpy_flags=data.get("extra_scrcpy_flags", []),
            auto_reconnect=data.get("auto_reconnect", True),
            max_reconnect_attempts=data.get("max_reconnect_attempts", 3),
            notes=data.get("notes", ""),
            last_connected_at=data.get("last_connected_at", 0.0),
        )

    def get_best_endpoint(self) -> str:
        """Get the primary active network endpoint."""
        if self.preferred_route == "tailscale" and self.tailscale_endpoint:
            return self.tailscale_endpoint
        if self.preferred_route == "lan" and self.lan_endpoint:
            return self.lan_endpoint
        return self.tailscale_endpoint or self.lan_endpoint or self.usb_serial


class DeviceManager:
    """Manages persistent collection of DeviceProfile objects."""

    def __init__(self, storage_path: str = PROFILES_FILE):
        self.storage_path = storage_path
        self._profiles: Dict[str, DeviceProfile] = {}
        self.load_profiles()

    def _create_default_profile(self) -> DeviceProfile:
        """Create initial pre-configured profile for the user's POCO F1."""
        return DeviceProfile(
            id="poco_f1_home",
            name="📱 POCO F1 (Tailscale Remote)",
            model="POCOPHONE F1",
            tailscale_endpoint="100.83.144.79:5555",
            preferred_route="tailscale",
            extra_scrcpy_flags=["--no-audio"],
            auto_reconnect=True,
            max_reconnect_attempts=3,
            notes="Thiết bị chính điều khiển từ xa qua mạng Tailscale VPN.",
        )

    def load_profiles(self) -> List[DeviceProfile]:
        """Load profiles from disk or initialize defaults."""
        self._profiles.clear()
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("profiles", []):
                        prof = DeviceProfile.from_dict(item)
                        if prof.id:
                            self._profiles[prof.id] = prof
            except Exception:
                pass

        if not self._profiles:
            default_prof = self._create_default_profile()
            self._profiles[default_prof.id] = default_prof
            self.save_profiles()

        return list(self._profiles.values())

    def save_profiles(self) -> bool:
        """Persist current profiles dictionary to disk."""
        try:
            data = {
                "version": "1.0",
                "updated_at": time.time(),
                "profiles": [p.to_dict() for p in self._profiles.values()],
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def get_profiles(self) -> List[DeviceProfile]:
        return list(self._profiles.values())

    def get_profile(self, profile_id: str) -> Optional[DeviceProfile]:
        return self._profiles.get(profile_id)

    def save_profile(self, profile: DeviceProfile) -> DeviceProfile:
        if not profile.id:
            profile.id = re.sub(r"[^a-zA-Z0-9_]", "_", profile.name.lower()) + f"_{int(time.time())}"
        self._profiles[profile.id] = profile
        self.save_profiles()
        return profile

    def delete_profile(self, profile_id: str) -> bool:
        if profile_id in self._profiles:
            del self._profiles[profile_id]
            self.save_profiles()
            return True
        return False

    def resolve_best_route(
        self, profile: DeviceProfile, connected_serials: Optional[List[str]] = None
    ) -> Tuple[str, str]:
        """Intelligently resolve the most viable connection route and endpoint.
        Returns (route_name, target_endpoint_or_serial).
        Routes evaluated:
          1. USB if plugged in and present in connected_serials
          2. Tailscale if preferred or reachable
          3. LAN if preferred or reachable
        """
        connected = connected_serials or []

        # 1. Check explicit preferred routes
        if profile.preferred_route == "usb" and profile.usb_serial:
            return "USB", profile.usb_serial

        if profile.preferred_route == "tailscale" and profile.tailscale_endpoint:
            return "Tailscale", profile.tailscale_endpoint

        if profile.preferred_route == "lan" and profile.lan_endpoint:
            return "LAN", profile.lan_endpoint

        # 2. Auto Fallback logic:
        # Priority A: Check if USB serial is directly connected
        if profile.usb_serial and profile.usb_serial in connected:
            return "USB", profile.usb_serial

        # Priority B: Check if device is ALREADY connected via an active endpoint in ADB
        if profile.lan_endpoint and profile.lan_endpoint in connected:
            return "Wi-Fi LAN", profile.lan_endpoint

        if profile.tailscale_endpoint and profile.tailscale_endpoint in connected:
            return "Tailscale", profile.tailscale_endpoint

        # Priority C: Check mDNS auto-discovery (Android 11+ Wireless Debugging with dynamic port)
        if profile.usb_serial:
            try:
                import adb_core
                services = adb_core.discover_mdns_services()
                for s in services:
                    if s.get("serial") == profile.usb_serial:
                        endpoint = s.get("endpoint")
                        if endpoint:
                            profile.lan_endpoint = endpoint
                            self.save_profile(profile)
                            return "Wi-Fi mDNS", endpoint
            except Exception:
                pass

        # Priority D: Check if LAN endpoint is online and responsive
        if profile.lan_endpoint:
            host = profile.lan_endpoint.split(":")[0]
            port = int(profile.lan_endpoint.split(":")[1]) if ":" in profile.lan_endpoint else 5555
            if is_socket_reachable(host, port, timeout=0.8):
                return "LAN", profile.lan_endpoint

        # Priority E: Check Tailscale endpoint
        if profile.tailscale_endpoint:
            return "Tailscale", profile.tailscale_endpoint

        # Fallback to whatever endpoint is defined
        fallback = profile.lan_endpoint or profile.usb_serial or profile.tailscale_endpoint
        return "Auto", fallback


# Global singleton instance
device_manager = DeviceManager()
