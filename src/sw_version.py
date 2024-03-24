from model import BaseObject

# This class represents the Brink SoftwareVersion string represented as three integers
class SWVersionBrinkEbusd(BaseObject):
    def __init__(self, major: int, minor: int, patch: int):
        self.major = major
        self.minor = minor
        self.patch = patch

def sw_version_int_to_ebusd(sw_version_int: int) -> SWVersionBrinkEbusd:
    sw_version_str = str(sw_version_int)
    sw_version_bytes = bytes(sw_version_str,'UTF-8')
    major = int.from_bytes(sw_version_bytes[0:1], "big")
    minor = int.from_bytes(sw_version_bytes[1:3], "big")
    patch = int.from_bytes(sw_version_bytes[3:5], "big")

    return SWVersionBrinkEbusd(major, minor, patch)