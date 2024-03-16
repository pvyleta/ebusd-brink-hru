import re
import glob
import copy

from params import DEBUG
from converters import Converter, device_to_name_current_to_name_param, find_converters, converters_map
from dev import Device, DeviceView
from command_ebus import get_commands_dict
from current_param import get_device_to_current_param
from command_ebus import CommandEBus


def substitute_flair_name(device: Device) -> Device:
    device_copy = copy.deepcopy(device)  # Make copy so that we can manipulate the data

    # Vitovent300WH32S comes in too many flavors but only one converter
    if "Vitovent300WH32S" in device_copy.name:
        device_copy.name = "Vitovent300WH32S"
    # Flair units share common params definition:
    elif "Flair" in device.name:
        device_copy.name = "Flair"

    return device_copy

value_type_dict = {
    '': "",
    'rpm': "rpm",
    'm3/h': "m³/h",
    'm3': "m³",
    'Pa': "Pa",
    'Â°C': "°C",
    '°C': "°C",
    'PPM': "ppm",
    'ppm': "ppm",
    'days': "Days",
    'Hour': "Hour",
    'hours': "Hours",
    'Steps': "Steps",
    'PWM': "PWM",
    'V': "V",
    '%': "%"
}

# Some parameters seem not to be present in UI at all - we fabricate the converters on other knowledge
manual_current_to_converter = {
    "CurrentDipswitchValue": "ConverterUInt16ToUNumber",  # paramDipswitch; conversion missing for Flair units and few others for no apparent reason
    "CurrentEBusAddressing": "ConverterUInt32ToEBusAddressing",  # unknown; we create out own empty converter
    "CurrenteBusPowerStatus": "ConverterUInt16ToEBusPowerState",  # paramEBusPowerState; Assumed from decentralair70actualstateview_01.xaml
    "CurrentEBusSyncGenErrorCount": "ConverterUInt16ToUNumber",  # paramSyncGenErrorCount; conversion missing for Flair units and few others for no apparent reason
    "CurrentExhaustFanPWMValue": "ConverterUInt16ToUNumber",  # paramFanPWMSetpoint; Assumed from decentralair70actualstateview_01.xaml
    "CurrentInletFanPWMValue": "ConverterUInt16ToUNumber",  # paramFanPWMSetpoint; Assumed from decentralair70actualstateview_01.xaml
    "CurrentPerilexPosition": "ConverterUInt16ToFanSwitch",  # paramPerilexPosition; Mising for Sky units
    "CurrentSoftwareVersion": "ConverterByteArrayToSoftwareVersion",  # Missing for many units, but present for some
    "CurrentDeviceType": "ConverterUInt16ToDeviceType",
    "CurrentUIFButtonsStatus": "ConverterUInt16ToUIFButtonsStatus",  # Missing for flair units
    "CurrentDeviceID": "ConverterUInt32ToDeviceID",  # Missing for flair units

    # DecentralAir70 missing these params in UI meaning we must add converters manually
    "CurrentUIFButtons": "ConverterUInt16ToUIFButtonsStatus",
    "CurrentFilterUsedIn1000M3": "ConverterUInt16ToVolumeFact1000",
    "CurrentTotalFlowIn1000M3": "ConverterUInt16ToVolumeFact1000",
    "CurrentSerialNumber": "ConverterByteArrayToSerialNumber",

    # Some random fields that seems almost forgotten for some units, as they exist for the rest, taken from other places almost at random
    "CurrentBypassCurrent": "ConverterUInt16ToUNumber",
    "CurrentBypassStatus": "ConverterUInt16ToBypassStatus",
    "CurrentContact1Position": "ConverterUInt16ToOnOff",
    "CurrentContact2Position": "ConverterUInt16ToOnOff",
    "CurrentEWTStatus": "ConverterUInt16ToEWTStatus",
    "CurrentExhaustFlow": "ConverterUInt16ToUNumber",
    "CurrentHumidityBoostState": "ConverterUInt16ToHumidityBoostState",
    "CurrentInletFlow": "ConverterUInt16ToUNumber",
    "CurrentInsideTemperature": "ConverterInt16ToTemperatureFact10",
    "CurrentMRCConfigurationStatus": "ConverterByteArrayToMRCConfigurationStatus",
    "CurrentOptionTemperature": "ConverterInt16ToTemperatureFact10",
    "CurrentPostheaterPower": "ConverterUInt16ToUNumber",
    # Note: This would not work on 'old flair'; however, I don't see any way to find out if it is correct for the given device programatically, and it seems that for devices this is used, they should not use the 'old flair' version
    "CurrentPostheaterStatus": "ConverterUInt16ToHeaterStatus",
    "CurrentPressureExhaust": "ConverterUInt16ToPressure",
    "CurrentPressureInlet": "ConverterUInt16ToPressure",
    "CurrentRelativeHumidity": "ConverterInt16ToPercentageFact10",
}

manual_current_to_converter_unused = copy.deepcopy(manual_current_to_converter)


# TODO rename Sensor to State?
class Sensor:
    def __init__(self, device_name: str, first_version: int, last_version: int, id: str, name_description: str, name_current: str, name_param: str|None, unit: str, update_rate: int, cmd: CommandEBus|None, datatype=None):
        self.device_name = device_name
        self.first_version = first_version
        self.last_version = last_version
        self.id = id
        self.name_description = name_description
        self.name_current = name_current
        self.name_param = name_param
        self.unit = unit
        self.update_rate = update_rate
        self.cmd = cmd
        self.datatype = datatype

        self.converter: Converter|None = None
        self.converter_match = ""

    def __eq__(self, other):
        return str(self) == str(other)
    
    def __lt__(self, other):
        return self.device_name + self.name_current + str(self.first_version) + str(self.last_version) < other.device_name + other.name_current + str(other.first_version) + str(other.last_version)

    def __str__(self):
        return str([vars(self)[key] for key in sorted(vars(self).keys())])

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return str(self)
    
    # Ensures that the CMD read length matches the converters. Turns out, we found few bugs in our and Brink code as well this way.
    def check_converter(self):
        if self.cmd and self.cmd.read_len != self.converter.length:
            if self.name_current == 'CurrentVirtualDipswitch':
                # TODO it seems VirtualDipswitch is listed in sensors (4022 cmds) but it is in fact a config param (4050 cmds) and it likely even is writable. No way to confirm this though, and likely not worth investigating further...
                pass
            elif re.search('Elan|MultiRoomCtrl|Valve', self.device_name) and self.converter.length == 2 and self.cmd.read_len == 1:
                # seems that enum values are only one byte long for Elan/Valve/MultiRoomCtrl units based on CMDs. This would be a problem for ebusd, so we overide the converter types and lengths here
                self.converter.length = 1
                self.converter.type = "UCH"
            else:
                print(f'Length Mismatch: device: {self.device_name} sensor: {self.name_current} converter: {self.converter.length} {self.converter.name}, cmd: {self.cmd.read_len} {self.cmd.cmd}')


search_list_sensor = [
    ("first_version", "public (new )?const uint VALID_FIRST_VERSION = (?P<match>.*);"),
    ("last_version", "public (new )?const uint VALID_LAST_VERSION = (?P<match>.*);"),
]


def get_dict_devices_sensor() -> dict[Device, list[Sensor]]:

    device_to_name_current_to_name_param_dict = device_to_name_current_to_name_param()
    cmd_dict, cmd_bytes_dict = get_commands_dict()

    dict_devices_sensor: dict[Device, list[Sensor]] = {}
    missing_commands_set: set[str] = set()
    missing_params_count = 0

    files_sensor = glob.glob('./BCSServiceTool/Model/Devices/**/*DataModel_*.cs', recursive=True)
    for file in files_sensor:
        # This skips the Flair base class, which contains no sensor definitions
        if "FlairBase" in file:
            print("sensor: skipping file " + file)
            continue

        with open(file) as f:
            file_str = f.read()
            match1 = re.search(r'public (partial )?class (?P<name>\w+)ParameterDataModel_\d(?P<view_no>\d)', file_str)
            match2 = re.search(r'public const uint VALID_FIRST_VERSION = (?P<first_version>\d*);', file_str)
            match3 = re.search(r'public const uint VALID_LAST_VERSION = (?P<last_version>\d*);', file_str)
            assert match1 and match2 and match3

            device = Device(match1.group('name'), int(match1.group('view_no')), int(match2.group('first_version')), int(match3.group('last_version')))
            sensors: list[Sensor] = []

            # Then there is a line with sensor definition
            # this._currentSettingExhaustFlow = new ParameterData("parameterDescriptionExhaustFlowSetting", "%", (ushort) 10, "4022010A");
            matches = re.finditer(r'this._current(?P<name_current>\w*) = new ParameterData\("parameterDescription(?P<name>\w*)", "(?P<unit>[^"]*)", \(\w*\) (?P<update_rate>\d*), "(?P<pbsb>....)(?P<len>..)(?P<id>..)"\);', file_str)
            for m in matches:

                # Sanity checks
                assert m.group('pbsb') == "4022"
                assert m.group('len') == "01"

                name_current = "Current" + m.group('name_current')
                name_param = device_to_name_current_to_name_param_dict[device].get(name_current)

                # Not all params exist in UI -> we manually assign the most suitable converter later
                if not name_param:
                    missing_params_count += 1
                    if DEBUG:
                        print(f'Missing param for {device.name.lower()} sensor {name_current}')

                # Try finding the commands based on the command_bytes
                command_bytes = m.group('pbsb') + m.group('len') + m.group('id')
                if command_bytes in cmd_bytes_dict:
                    command = cmd_bytes_dict[command_bytes]
                else:
                    # Unfortunately, not all Commands are defined - track those that are missing
                    command = None
                    missing_commands_set.add(command_bytes)

                sensors.append(Sensor(device.name, device.first_version, device.last_version, m.group('id'), m.group('name'), name_current, name_param, value_type_dict[m.group('unit')], int(m.group('update_rate')), command))

            # We need to check separately for flair/elan/decentral/vitovent units that have different definition
            # this._currentBypassSenseLevel = new ParameterData("parameterDescriptionBypassSenseLevel", "m3/h", (ushort) 2, FlairEBusCommands.CmdReadActualBypassSenseLevel.Cmd);
            matches = re.finditer(r'this._current(?P<name_current>\w*) = new ParameterData\("parameterDescription(?P<name>\w*)", "(?P<unit>[^"]*)", \(\w*\) (?P<update_rate>\d*), (?P<cmd>\w*\.\w*)\.Cmd\);', file_str)
            for m in matches:

                device_copy = substitute_flair_name(device)

                name_current = "Current" + m.group('name_current')
                name_param = device_to_name_current_to_name_param_dict[device_copy].get(name_current)

                # Vitovent units have some params definition for themselves, and for some they use the Flair base, so if we failed to find it earlier, try the base now
                if not name_param and "Vitovent" in device.name:
                    device_copy.name = "Flair"
                    name_param = device_to_name_current_to_name_param_dict[device_copy].get(name_current)

                # Not all params exist in UI -> we manually assign the most suitable converter later
                if not name_param:
                    missing_params_count += 1
                    if DEBUG:
                        print(f'Missing named param for {device.name} sensor {name_current}')

                command = cmd_dict[m.group('cmd')]

                # Bugfix - this value is clearly written incorrectly in the BCServiceTool
                if "Decentral" in device.name and name_current == 'CurrentFlowActualValue' and command and command.cmd == 'DecentralEBusCommands.CmdReadActualSoftwareVersion':
                    command = cmd_dict['DecentralEBusCommands.CmdReadActualFlowValue']

                sensors.append(Sensor(device.name, device.first_version, device.last_version, command.id, m.group('name'), name_current, name_param, value_type_dict[m.group('unit')], int(m.group('update_rate')), command))

            dict_devices_sensor[device] = sensors

    print("Info: missing_commands_set: " + str(missing_commands_set))

    device_to_name_param_to_converter = find_converters()
    device_to_name_param_to_converter_unused = copy.deepcopy(device_to_name_param_to_converter)

    device_to_current_param = get_device_to_current_param()
    sensors_without_datatypes = 0
    sensor_datatypes_set = set()

    # assign converters to each sensor in each device
    for d, sensors in dict_devices_sensor.items():
        d_copy = substitute_flair_name(d)

        for sensor in sensors:

            # Get datatype for sensors
            if curr_param := device_to_current_param[d_copy].get(sensor.name_current):
                sensor.datatype = curr_param.datatype
                sensor_datatypes_set.add(sensor.datatype)
            else:
                sensors_without_datatypes += 1
                if DEBUG:
                    print("Warning: No current_param for device: " + str(device) + " sensor: " + str(sensor.name_current))

            dev_view = DeviceView(d_copy.name, d_copy.view_no)

            if sensor.name_param:
                # First, Try to match the converter through following the path in code from ebus to UI
                if converter := device_to_name_param_to_converter[dev_view].get(sensor.name_param):
                    sensor.converter = converter
                    sensor.converter_match = "from_code"
                    sensor.check_converter()
                    device_to_name_param_to_converter_unused[dev_view].pop(sensor.name_param, None)
                    continue

                # Try the 'base' flair converter as a backup for vitovent units
                if "Vitovent" in dev_view.name:
                    dev_view_flair = DeviceView("Flair", 1)
                    if converter := device_to_name_param_to_converter[dev_view_flair].get(sensor.name_param):
                        sensor.converter = converter
                        sensor.converter_match = "from_code_flair"
                        sensor.check_converter()
                        device_to_name_param_to_converter_unused[dev_view_flair].pop(sensor.name_param, None)
                        continue

            # If everything else fails, we manually search for the most suitable converter from other units
            if converter_str := manual_current_to_converter.get(sensor.name_current):
                sensor.converter = converters_map[converter_str]
                sensor.converter_match = "manual_full"
                sensor.check_converter()
                manual_current_to_converter_unused.pop(sensor.name_current, None)
                continue

            print(f"Error: Sensor without convertor: device: {d} name_current: {sensor.name_current} name_param: {sensor.name_param} cmd: {sensor.cmd}")

    converter_param_unused_set = set()
    for dev_view, params_to_converter in device_to_name_param_to_converter_unused.items():
        for param in params_to_converter:
            converter_param_unused_set.add(dev_view.name + "_" + param)

    print("missing_params_count: " + str(missing_params_count))
    print("manual_current_to_converter_unused: " + str(manual_current_to_converter_unused))
    print("converter_param_unused_set: " + str(len(converter_param_unused_set)))

    print("sensor_datatypes_set: " + str(sensor_datatypes_set))
    print("sensors_without_datatypes: " + str(sensors_without_datatypes))

    if DEBUG:
        for param_unused in sorted(converter_param_unused_set):
            print("Unused Converter for param: " + param_unused)

    return dict_devices_sensor
