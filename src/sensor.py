from __future__ import annotations

import re
import glob
import copy

from converters import find_converters, converters_map
from model import DeviceView, Sensor, Converter, DeviceVersion, VersionRange, DEBUG
from sensor_datatype import get_sensor_datatypes
from command_ebus import CommandEBus
from dipswitch import dipswitch_dict


def maybe_substitute_flair_name(device_version: DeviceVersion) -> DeviceVersion:
    device_copy = copy.deepcopy(device_version)  # Make copy so that we can manipulate the data

    # Vitovent300WH32S comes in too many flavors but only one converter
    if "Vitovent300WH32S" in device_copy.device_name:
        device_copy.device_name = "Vitovent300WH32S"
    # Flair units share common params definition:
    elif "Flair" in device_version.device_name:
        device_copy.device_name = "Flair"

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

# Ensures that the CMD read length matches the converters. Turns out, we found few bugs in our and Brink code as well this way.
def check_converter(sensor: Sensor, device_name: str):
    assert sensor.converter
    if sensor.cmd and sensor.cmd.read_len != sensor.converter.length:
        if sensor.name_current == 'CurrentVirtualDipswitch':
            # NOTE it seems VirtualDipswitch is listed in sensors (4022 cmds) but it is in fact a config param (4050 cmds) and it likely even is writable. No way to confirm this though, and likely not worth investigating further...
            pass
        elif re.search('Elan|MultiRoomCtrl|Valve', device_name) and sensor.converter.length == 2 and sensor.cmd.read_len == 1:
            # seems that enum values are only one byte long for Elan/Valve/MultiRoomCtrl units based on CMDs. This would be a problem for ebusd, so we overide the converter types and lengths here
            sensor.converter.length = 1
            sensor.converter.type = "UCH"
            sensor.converter_match = "patched"
        else:
            print(f'Length Mismatch: device: {device_name} sensor: {sensor.name_current} converter: {sensor.converter.length} {sensor.converter.name}, cmd: {sensor.cmd.read_len} {sensor.cmd.cmd}')
    
    # Filter state converter is largely unused in favor of UInt16ToOnOffConverter which is a shame - replace it where reasonable
    if "CurrentFilterStatus" == sensor.name_current and sensor.converter.name == "ConverterUInt16ToOnOff":
        # NOTE this incorrectly reports ConverterUInt16ToFilterState as unused. Why?
        sensor.converter = copy.deepcopy(converters_map['ConverterUInt16ToFilterState'])
        sensor.converter_match = "patched"
    # We know the dipswitch setting for certain models. This can be useful to help determine rpogramatically from received message, what is the device model.
    elif "CurrentDipswitchValue" == sensor.name_current and (device_name + "Basic" in dipswitch_dict or device_name + "Plus" in dipswitch_dict):
        sensor.converter = copy.deepcopy(converters_map['ConverterUInt16DipswitchValue'])
        sensor.converter_match = "patched"


def get_dict_devices_sensor(
        device_to_name_param_to_converter: dict[DeviceView, dict[str, Converter]],
        device_to_name_current_to_name_param_dict: dict[DeviceVersion, dict[str, str]],
        cmd_dict: dict[str, CommandEBus],
        cmd_bytes_dict: dict[str, CommandEBus]) -> dict[DeviceVersion, list[Sensor]]:

    dict_devices_sensor: dict[DeviceVersion, list[Sensor]] = {}
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

            device_name = match1.group('name')
            version_range = VersionRange(int(match1.group('view_no')), int(match2.group('first_version')), int(match3.group('last_version')))
            device_version = DeviceVersion(device_name, version_range)
            sensors: list[Sensor] = []

            # Then there is a line with sensor definition
            # this._currentSettingExhaustFlow = new ParameterData("parameterDescriptionExhaustFlowSetting", "%", (ushort) 10, "4022010A");
            matches = re.finditer(r'this._current(?P<name_current>\w*) = new ParameterData\("parameterDescription(?P<name>\w*)", "(?P<unit>[^"]*)", \(\w*\) (?P<update_rate>\d*), "(?P<pbsb>....)(?P<len>..)(?P<id>..)"\);', file_str)
            for m in matches:

                # Sanity checks
                assert m.group('pbsb') == "4022"
                assert m.group('len') == "01"

                name_current = "Current" + m.group('name_current')
                name_param = device_to_name_current_to_name_param_dict[device_version].get(name_current)

                # Not all params exist in UI -> we manually assign the most suitable converter later
                if not name_param:
                    missing_params_count += 1
                    if DEBUG:
                        print(f'Missing param for {device_version.device_name} sensor {name_current}')

                # Try finding the commands based on the command_bytes
                command_bytes = m.group('pbsb') + m.group('len') + m.group('id')
                if command_bytes in cmd_bytes_dict:
                    command = cmd_bytes_dict[command_bytes]
                else:
                    # Unfortunately, not all Commands are defined - track those that are missing
                    command = None
                    missing_commands_set.add(command_bytes)
                
                # Sanity check
                if command and command.pbsb != '4022':
                    print(f'Command {command.cmd} pbsb {command.pbsb} - skipping')
                    continue

                sensors.append(Sensor(int(m.group('id'), 16), m.group('name'), name_current, name_param, value_type_dict[m.group('unit')], int(m.group('update_rate')), command))

            # We need to check separately for flair/elan/decentral/vitovent units that have different definition
            # this._currentBypassSenseLevel = new ParameterData("parameterDescriptionBypassSenseLevel", "m3/h", (ushort) 2, FlairEBusCommands.CmdReadActualBypassSenseLevel.Cmd);
            matches = re.finditer(r'this._current(?P<name_current>\w*) = new ParameterData\("parameterDescription(?P<name>\w*)", "(?P<unit>[^"]*)", \(\w*\) (?P<update_rate>\d*), (?P<cmd>\w*\.\w*)\.Cmd\);', file_str)
            for m in matches:

                device_copy = maybe_substitute_flair_name(device_version)

                name_current = "Current" + m.group('name_current')
                name_param = device_to_name_current_to_name_param_dict[device_copy].get(name_current)

                # Vitovent units have some params definition for themselves, and for some they use the Flair base, so if we failed to find it earlier, try the base now
                if not name_param and "Vitovent" in device_version.device_name:
                    device_copy.device_name = "Flair"
                    name_param = device_to_name_current_to_name_param_dict[device_copy].get(name_current)

                # Not all params exist in UI -> we manually assign the most suitable converter later
                if not name_param:
                    missing_params_count += 1
                    if DEBUG:
                        # NOTE This happens only for FlairEBusCommands.CmdReadParameterDeviceType. figure out a way to include this 'param' here in 'sensors'
                        print(f'Missing named param for {device_version.device_name} sensor {name_current}')
                        continue

                command = cmd_dict[m.group('cmd')]

                # Bugfix - this value is clearly written incorrectly in the BCServiceTool
                if "Decentral" in device_version.device_name and name_current == 'CurrentFlowActualValue' and command and command.cmd == 'DecentralEBusCommands.CmdReadActualSoftwareVersion':
                    command = cmd_dict['DecentralEBusCommands.CmdReadActualFlowValue']

                # Sanity check
                if command and command.pbsb != '4022':
                    print(f'Command {command.cmd} pbsb {command.pbsb} - skipping')
                    continue
                

                sensors.append(Sensor(int(command.id, 16), m.group('name'), name_current, name_param, value_type_dict[m.group('unit')], int(m.group('update_rate')), command))

            dict_devices_sensor[device_version] = sensors

    print("Info: missing_commands_set: " + str(missing_commands_set))

    device_to_name_param_to_converter_unused = copy.deepcopy(device_to_name_param_to_converter)

    device_to_sensor_datatype = get_sensor_datatypes()
    sensors_without_datatypes = 0
    sensor_datatypes_set = set()

    # assign converters to each sensor in each device
    for d, sensors in dict_devices_sensor.items():
        d_copy = maybe_substitute_flair_name(d)

        for sensor in sensors:

            # Get datatype for sensors
            if sensor_datatype := device_to_sensor_datatype[d_copy].get(sensor.name_current):
                sensor.datatype = sensor_datatype.datatype
                sensor_datatypes_set.add(sensor.datatype)
            else:
                sensors_without_datatypes += 1
                if DEBUG:
                    print("Warning: No current_param for device: " + str(d_copy) + " sensor: " + str(sensor.name_current))

            dev_view = DeviceView(d_copy.device_name, d_copy.version.view_no)

            if sensor.name_param:
                # First, Try to match the converter through following the path in code from ebus to UI
                if converter := device_to_name_param_to_converter[dev_view].get(sensor.name_param):
                    sensor.converter = converter
                    sensor.converter_match = "auto"
                    check_converter(sensor, d.device_name)
                    device_to_name_param_to_converter_unused[dev_view].pop(sensor.name_param, None)
                    continue

                # Try the 'base' flair converter as a backup for vitovent units
                if "Vitovent" in dev_view.name:
                    dev_view_flair = DeviceView("Flair", 1)
                    if converter := device_to_name_param_to_converter[dev_view_flair].get(sensor.name_param):
                        sensor.converter = converter
                        sensor.converter_match = "auto_flair_base"
                        check_converter(sensor, d.device_name)
                        device_to_name_param_to_converter_unused[dev_view_flair].pop(sensor.name_param, None)
                        continue

            # If everything else fails, we manually search for the most suitable converter from other units
            if converter_str := manual_current_to_converter.get(sensor.name_current):
                sensor.converter = converters_map[converter_str]
                sensor.converter_match = "manual"
                check_converter(sensor, d.device_name)
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
