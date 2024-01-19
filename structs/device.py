from dataclasses import dataclass


@dataclass
class AirplayDevice:
    address: str = None
    name: str = None
    device_id: str = None
    model: str = None
    mac_addr: str = None
    active: bool = False
    play_session: bool = False

    def parse_line(self, line):
        consumed = False
        if 'has disconnected from this player.' in line:
            print(f'{self.name} disconnected')
            self.active = False
            self.play_session = False
            self.name = None
            self.address = None
            self.mac_addr = None
            self.device_id = None
            self.model = None
            consumed = True
            print(f'Name = {self.name}')
        elif line.startswith('The AirPlay client at ') or\
                line.startswith('The address used by this player for this play session'):
            self.address = line.split('"')[1]
            consumed = True
            print(f'Address = {self.address}')
        elif line.startswith('The name of the AirPlay client'):
            self.name = line.split('"')[1]
            print(f'Name = {self.name}')
            consumed = True
        elif line.startswith('The AirPlay client\'s Device ID is'):
            self.device_id = line.split('"')[1]
            print(f'Device ID = {self.device_id}')
            consumed = True
        elif line.startswith('The model of the AirPlay client is'):
            self.model = line.split('"')[1]
            print(f'Model = {self.model}')
            consumed = True
        elif line.startswith('The AirPlay client\'s MAC address is'):
            self.mac_addr = line.split('"')[1]
            print(f'MAC = {self.mac_addr}')
            consumed = True

        return consumed
