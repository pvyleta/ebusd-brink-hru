import re
import glob
import copy

import dev
import command_ebus
import converters
import params

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
    "CurrentDipswitchValue" : "ConverterUInt16ToUNumber", # paramDipswitch; conversion missing for Flair units and few others for no apparent reason
    "CurrentEBusAddressing" : "ConverterUInt32ToEBusAddressing", # unknown; we create out own empty converter
    "CurrenteBusPowerStatus": "ConverterUInt16ToEBusPowerState", # paramEBusPowerState; Assumed from decentralair70actualstateview_01.xaml
    "CurrentEBusSyncGenErrorCount" : "ConverterUInt16ToUNumber", # paramSyncGenErrorCount; conversion missing for Flair units and few others for no apparent reason
    "CurrentExhaustFanPWMValue" : "ConverterUInt16ToUNumber",  # paramFanPWMSetpoint; Assumed from decentralair70actualstateview_01.xaml
    "CurrentInletFanPWMValue" : "ConverterUInt16ToUNumber",  # paramFanPWMSetpoint; Assumed from decentralair70actualstateview_01.xaml
    "CurrentPerilexPosition" : "ConverterUInt16ToFanSwitch", # paramPerilexPosition; Mising for Sky units
    "CurrentSoftwareVersion" : "ConverterByteArrayToSoftwareVersion", # Missing for many units, but present for some
    "CurrentDeviceType" : "ConverterUInt16ToDeviceType",
    "CurrentUIFButtonsStatus" : "ConverterUInt16ToUIFButtonsStatus", # Missing for flair units
    "CurrentDeviceID" : "ConverterUInt32ToDeviceID", # Missing for flair units

    # DecentralAir70 missing these params in UI meaning we must add converters manually
    "CurrentUIFButtons" : "ConverterUInt16ToUIFButtonsStatus", 
    "CurrentFilterUsedIn1000M3" : "ConverterUInt16ToVolumeFact1000", 
    "CurrentTotalFlowIn1000M3" : "ConverterUInt16ToVolumeFact1000", 
    "CurrentSerialNumber" : "ConverterByteArrayToSerialNumber",

    # Some random fields that seems almost forgotten for some units, as they exist for the rest, taken from other places almost at random
    "CurrentBypassCurrent" : "ConverterUInt16ToUNumber", 
    "CurrentBypassStatus" : "ConverterUInt16ToBypassStatus", 
    "CurrentContact1Position" : "ConverterUInt16ToOnOff", 
    "CurrentContact2Position" : "ConverterUInt16ToOnOff", 
    "CurrentEWTStatus" : "ConverterUInt16ToEWTStatus", 
    "CurrentExhaustFlow" : "ConverterUInt16ToUNumber", 
    "CurrentHumidityBoostState" : "ConverterUInt16ToHumidityBoostState", 
    "CurrentInletFlow" : "ConverterUInt16ToUNumber", 
    "CurrentInsideTemperature" : "ConverterInt16ToTemperatureFact10", 
    "CurrentMRCConfigurationStatus" : "ConverterByteArrayToMRCConfigurationStatus", 
    "CurrentOptionTemperature" : "ConverterInt16ToTemperatureFact10", 
    "CurrentPostheaterPower" : "ConverterUInt16ToUNumber", 
    "CurrentPostheaterStatus" : "ConverterUInt16ToHeaterStatus", # Note: This would not work on 'old flair'; however, I don't see any way to find out if it is correct for the given device programatically, and it seems that for devices this is used, they should not use the 'old flair' version
    "CurrentPressureExhaust" : "ConverterUInt16ToPressure", 
    "CurrentPressureInlet" : "ConverterUInt16ToPressure", 
    "CurrentRelativeHumidity" : "ConverterInt16ToPercentageFact10", 
}

manual_current_to_converter_unused = copy.deepcopy(manual_current_to_converter)

class Sensor:
    def __init__(self, device_name: str, id: str, name_description: str, name_current: str, name_param: str, unit: str, update_rate: str, cmd, datatype=None):
        self.device_name = device_name
        self.id = id
        self.name_description = name_description
        self.name_current = name_current
        self.name_param = name_param
        self.unit = unit
        self.update_rate = update_rate
        self.cmd = cmd
        self.datatype = datatype
        
        self.converter = None
        self.converter_match = ""

    def __eq__(self, other):
        return str(self) == str(other)
    def __str__(self):
        return str([vars(self)[key] for key in sorted(vars(self).keys())])
    def __hash__(self):
        return hash(str(self))
    def __repr__(self):
        return str(self)

search_list_sensor = [
    ("first_version", "public (new )?const uint VALID_FIRST_VERSION = (?P<match>.*);"),
    ("last_version", "public (new )?const uint VALID_LAST_VERSION = (?P<match>.*);"),
]

def get_dict_devices_sensor() -> dict[str, list[Sensor]]:

    device_to_name_current_to_name_param_dict = converters.device_to_name_current_to_name_param()
    cmd_dict, cmd_bytes_dict = command_ebus.get_commands_dict()

    dict_devices_sensor: dict[str, list[Sensor]] = {}
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

            device = dev.Device(match1.group('name'), match1.group('view_no'), match2.group('first_version'), match3.group('last_version'))
            sensors: list[Sensor] = []
                
            # Then there is a line with sensor definition
            # this._currentSettingExhaustFlow = new ParameterData("parameterDescriptionExhaustFlowSetting", "%", (ushort) 10, "4022010A");
            matches = re.finditer(r'this._current(?P<name_current>\w*) = new ParameterData\("parameterDescription(?P<name>\w*)", "(?P<unit>[^"]*)", \(\w*\) (?P<update_rate>\d*), "(?P<pbsb>....)(?P<len>..)(?P<id>..)"\);', file_str)
            for m in matches:

                # Sanity checks
                assert m.group('pbsb') == "4022"
                assert m.group('len') == "01"

                # Try finding the commands in the right category - else use the "Common" commands
                command_bytes = m.group('pbsb') + m.group('len') + m.group('id')
                if command_bytes in cmd_bytes_dict:
                    command = cmd_bytes_dict[command_bytes]
                else:
                    # Unfortunately, not all Commands are defined - at least track those that are missing
                    command = None
                    missing_commands_set.add(command_bytes)

                name_current = "Current" + m.group('name_current')
                name_param = device_to_name_current_to_name_param_dict[device].get(name_current)
                if not name_param:
                    missing_params_count += 1
                    if params.DEBUG:
                        print(f'Missing param for {device.name.lower()} sensor {name_current}')
                    
                sensors.append(Sensor(device.name, m.group('id'),m.group('name'),name_current,name_param,value_type_dict[m.group('unit')],m.group('update_rate'), command))

            # We need to check separately for flair/elan/decentral/vitovent units that have different definition
            # this._currentBypassSenseLevel = new ParameterData("parameterDescriptionBypassSenseLevel", "m3/h", (ushort) 2, FlairEBusCommands.CmdReadActualBypassSenseLevel.Cmd);
            matches = re.finditer(r'this._current(?P<name_current>\w*) = new ParameterData\("parameterDescription(?P<name>\w*)", "(?P<unit>[^"]*)", \(\w*\) (?P<update_rate>\d*), (?P<cmd>\w*\.\w*)\.Cmd\);', file_str)
            for m in matches:

                # Try finding the commands in the right (=flair) category - else use the "Common" commands
                cmd_name = m.group('cmd')
                if cmd_name in cmd_dict:
                    command = cmd_dict[cmd_name]
                else:
                    # Unfortunately, not all Commands are defined - at least track those that are missing
                    command = None
                    missing_commands_set.add(cmd_name)
                
                name_current = "Current" + m.group('name_current')
                name_param = None

                device_copy = copy.deepcopy(device) # Make copy so that we can manipulate the data
 
                # This Particular Vitovent comes in too many flavors but only one converter
                if "Vitovent300WH32S" in device_copy.name:
                    device_copy.name = "Vitovent300WH32S"
                    name_param = device_to_name_current_to_name_param_dict[device_copy].get(name_current)
                elif "Flair" not in device.name:
                    name_param = device_to_name_current_to_name_param_dict[device_copy].get(name_current)
                
                # Vitovent units have some params definition for themselves, and for some they use the Flair base, so we first try with their name, and only then go to the flair base
                if not name_param and "Vitovent" in device.name or "Flair" in device.name:
                    # Flair units share common params definition:
                    device_copy.name = "Flair"
                    name_param = device_to_name_current_to_name_param_dict[device_copy].get(name_current)

                if not name_param:
                    missing_params_count += 1
                    if params.DEBUG:
                        print(f'Missing named param for {device.name} sensor {name_current}')

                sensors.append(Sensor(device.name, command.id, m.group('name'),name_current,name_param,value_type_dict[m.group('unit')],m.group('update_rate'), command))

            dict_devices_sensor[device] = sensors

    print("Info: missing_commands_set: " + str(missing_commands_set))

    device_to_name_param_to_converter = converters.find_converters()
    device_to_name_param_to_converter_unused = copy.deepcopy(device_to_name_param_to_converter)

    # assign converters to each sensor in each device
    for d, sensors in dict_devices_sensor.items():
        d_copy = dev.DeviceView(d.name, d.view_no)

        # flair units have a shared converter under the name 'flair'
        if "Flair" in d_copy.name:
            d_copy.name = "Flair"
        # This Particular Vitovent comes in too many flavors but only one converter
        elif "Vitovent300WH32S" in d_copy.name:
            d_copy.name = "Vitovent300WH32S"

        for sensor in sensors:
            # First, Try to match the converter through following the path in code from ebus to UI
            if converter := device_to_name_param_to_converter[d_copy].get(sensor.name_param):
                sensor.converter = converter
                sensor.converter_match = "from_code"
                device_to_name_param_to_converter_unused[d_copy].pop(sensor.name_param, None)
                continue
            
            # Try the 'base' flair converter as a backup for vitovent units
            if "Vitovent" in d_copy.name:
                d_flair = dev.DeviceView("Flair", "1")
                if converter := device_to_name_param_to_converter[d_flair].get(sensor.name_param):
                    sensor.converter = converter
                    sensor.converter_match = "from_code_flair"
                    device_to_name_param_to_converter_unused[d_flair].pop(sensor.name_param, None)
                    continue
            
            # TODO add sanity check that converter length matches the CMD read
            # If everything else fails, we manually search for the most suitable converter from other units
            if converter := manual_current_to_converter.get(sensor.name_current):
                sensor.converter = converters.converters_map[converter]
                sensor.converter_match = "manual_full"
                manual_current_to_converter_unused.pop(sensor.name_current, None)
                continue
            
            print(f"Error: Sensor without convertor: device: {d} name_current: {sensor.name_current} name_param: {sensor.name_param} cmd: {sensor.cmd}")

    converter_param_unused_set = set()  
    for dev_view, params_to_converter in device_to_name_param_to_converter_unused.items():
        for param in params_to_converter:       
            converter_param_unused_set.add(dev_view.name + "_" + param)

    print("missing_params_count: " + str(missing_params_count))
    print("manual_current_to_converter_unused: " + str(manual_current_to_converter_unused))
    print("converter_param_unused_set: "+ str(len(converter_param_unused_set)) )
    if params.DEBUG:
        for param_unused in sorted(converter_param_unused_set):
            print("Unused Converter for param: " + param_unused)

    return dict_devices_sensor