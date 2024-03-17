class KnownDevice:
    def __init__(self, device_name: str, slave_address: int):
        self.device_name = device_name
        self.slave_address = slave_address


known_devices = [
    KnownDevice("Excellent400", 0x7c),
    KnownDevice("Excellent300", 0x3c),
    KnownDevice("Sky300", 0x3c),
]