from fastapi import Request
import ipaddress
from typing import Optional

# Define the ZingHttpService class
class ZingHttpService:
    def __init__(self, request: Request):
        self.request = request

    def get_client_ip(self) -> str:
        ip_address: Optional[str] = None
        try:
            # Access the X-Forwarded-For header
            x_forwarded_for = self.request.headers.get("X-Forwarded-For")
            if x_forwarded_for:
                # If multiple IPs are present (comma-separated), take the first one
                if "," in x_forwarded_for:
                    ip_address = x_forwarded_for.split(",")[0].strip()
                else:
                    ip_address = x_forwarded_for
            else:
                # Fallback to the client's direct IP
                ip_address = self.request.client.host

            # Handle IPv4-mapped IPv6 addresses
            if ip_address:
                try:
                    ip = ipaddress.ip_address(ip_address)
                    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
                        ip_address = str(ip.ipv4_mapped)
                except ValueError:
                    pass  # If IP parsing fails, proceed with raw value

        except Exception:
            # Silently handle exceptions
            pass

        # Return the IP, stripping ports if present, or an empty string if None
        return ip_address.split(":")[0] if ip_address else ""
