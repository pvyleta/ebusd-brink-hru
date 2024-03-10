import glob
import re
import copy

import converters
import out

# This script expects decompiled BCSServiceTool in its child folder via JetBrains DotPeak

class CommandEBus:
    def __init__(self, cmd, pbsb, len, id, write_len, read_len):
        self.cmd = cmd
        self.pbsb = pbsb
        self.len = len
        self.id = id
        self.write_len = write_len
        self.read_len = read_len

flair_cmd_dict = {}

# Get flair commands
with open("./BCSServiceTool/BusinessLogic/Commands/FlairEBusCommands.cs") as f:
    datafile = f.readlines()
    for line in datafile:
        #     public static CommandEBus CmdReadActualSoftwareVersion = new CommandEBus("40220100", (ushort) 0, 15U);
        match = re.search('public static CommandEBus (?P<cmd>.*) = new CommandEBus."(?P<pbsb>....)(?P<len>..)(?P<id>.*)", .* (?P<write_len>.*), (?P<read_len>.*)U.;', line)
        if match:
            cmd = CommandEBus(match.group('cmd'),match.group('pbsb'),match.group('len'),match.group('id'),match.group('write_len'),match.group('read_len'))
            flair_cmd_dict[cmd.cmd] = cmd

# First we parse the params data

files_params = glob.glob('./BCSServiceTool/Model/Devices/**/*ParameterSet_*.cs', recursive=True)

search_list_params = [
    ("name_flair_1", "public class (?P<match>.*)ParameterSet_.. : FlairBaseParameterSet_01"),
    ("name_flair_2", "public class (?P<match>.*)ParameterSet_.. : FlairBaseParameterSet_02"),
    ("name", "public class (?P<match>.*)ParameterSet_.. : WTWParameterFileHeader"),

    ("params_basic", "public const int PARAMETER_COUNT_(BASIC|AUTO) = (?P<match>.*);"),
    ("params_plus", "public const int PARAMETER_COUNT_(PLUS|MANUAL) = (?P<match>.*);"),
    ("first_version", "public (new )?const uint VALID_FIRST_VERSION = (?P<match>.*);"),
    ("last_version", "public (new )?const uint VALID_LAST_VERSION = (?P<match>.*);"),
    ("controller_code", "public (new )?const (uint|byte) CONTROLLER_CODE = (?P<match>.*);"),
]


value_type_dict = {'WTWParameterDefinition.UnitType.NoUnit': "", 
                   'WTWParameterDefinition.UnitType.DegrCelcius': "°C", 
                   'WTWParameterDefinition.UnitType.Minutes': "Minutes", 
                   'WTWParameterDefinition.UnitType.Voltage': "V", 
                   'WTWParameterDefinition.UnitType.Degrees': "°", 
                   'WTWParameterDefinition.UnitType.M3PerHour': "m³/h", 
                   'WTWParameterDefinition.UnitType.Day': "Day", 
                   'WTWParameterDefinition.UnitType.PPM': "ppm", 
                   'WTWParameterDefinition.UnitType.Percentage': "%",
                   
                   '': "",
                   'rpm': "rpm",
                   'm3/h': "m³/h",
                   'm3': "m³",
                   'Pa': "Pa",
                   'Â°C': "°C",
                   'PPM': "ppm",
                   'Hour': "Hour",
                   'Steps': "Steps",
                   'PWM': "PWM",
                   'V': "V",
                   '%': "%"
                   }

class Parameter:
    def __init__(self, id, name, unit, multiplier, is_signed, is_read_only):
        self.id = id
        self.name = name
        self.unit = unit
        self.multiplier = multiplier
        self.is_signed = is_signed
        self.is_read_only = is_read_only

    def values(self, curent, min, max, step, default):
        self.curent = curent
        self.min = min
        self.max = max
        self.step = step
        self.default = default

class Device:
    def __init__(self, name, params_basic, params_plus, first_version, last_version, params, controller_code):
        self.name = name
        self.params_basic = params_basic
        self.params_plus = params_plus
        self.first_version = first_version
        self.last_version = last_version
        self.params = params
        self.controller_code = controller_code

devices_param = []
for file in files_params:
    with open(file) as f:
        device_dict = {}
        params = []
        datafile = f.readlines()

        # The files first contain some constants that are useful
        for line in datafile:
            for property, regex in search_list_params:
                match = re.search(regex, line)
                if match:
                    device_dict[property] = match.group('match')
                    break
            
            # Then there is a line with parameter definition...
            match = re.search('new WTWParameterDefinition.* (?P<id>[0-9]*), "parameter(SetDescription)?(?P<name>.*)", (?P<is_read_only>.*), (?P<unit>.*), (?P<multiplier>.*), (?P<is_signed>.*).;', line)
            if match:
                params.append(Parameter(match.group('id'),match.group('name'),value_type_dict[match.group('unit')],match.group('multiplier'),match.group('is_signed'),match.group('is_read_only')))
   
            # And then it follows with line defining the values of the last added parameter
            match = re.search('SetApplianceData.* (-?[0-9]*), .* (-?[0-9]*), .* (-?[0-9]*), .* (-?[0-9]*), .* (-?[0-9]*).;', line)
            if match:
                params[-1].values(match.group(1),match.group(2),match.group(3),match.group(4),match.group(5))

        # Flair units have a two different base classes, we manually overwrite the relevant base class values
        if "name_flair_1" in device_dict:
            device_dict["name"] = device_dict["name_flair_1"]
            device_dict["params_basic"] = "57"
            device_dict["params_plus"] = "57"
            del device_dict["name_flair_1"]  
        elif "name_flair_2" in device_dict:
            device_dict["name"] = device_dict["name_flair_2"]
            device_dict["params_basic"] = "60"
            device_dict["params_plus"] = "60"
            del device_dict["name_flair_2"]

        device_dict["params"] = params
        device = Device(**device_dict)
        devices_param.append(device)

# Now let's parse the sensor data

files_sensor = glob.glob('./BCSServiceTool/Model/Devices/**/*DataModel_*.cs', recursive=True)

class Sensor:
    def __init__(self, id, name, name_current, unit, length):
        self.id = id
        self.name = name
        self.name_current = name_current
        self.unit = unit
        self.length = length
        self.converter = ""

class DeviceSensor:
    def __init__(self, name, first_version, last_version, sensors):
        self.name = name
        self.first_version = first_version
        self.last_version = last_version
        self.sensors = sensors

search_list_sensor = [
    ("name", "(private|public) static (?P<match>.*)ParameterDataModel_.. (I|i)nstance;"),
    ("first_version", "public (new )?const uint VALID_FIRST_VERSION = (?P<match>.*);"),
    ("last_version", "public (new )?const uint VALID_LAST_VERSION = (?P<match>.*);"),
]

dict_devices_sensor = {}
for file in files_sensor:
    with open(file) as f:
        device_dict = {}
        sensors = []
        datafile = f.readlines()

        # The files first contain some constants that are useful
        for line in datafile:
            for property, regex in search_list_sensor:
                match = re.search(regex, line)
                if match:
                    device_dict[property] = match.group('match')
                    break
            
            # Then there is a line with sensor definition

            # strip pottential "actual" from the front to improve matching
            # this._currentSettingExhaustFlow = new ParameterData("parameterDescriptionExhaustFlowSetting", "%", (ushort) 10, "4022010A");
            match = re.search('this._current(?P<name_current>.*) = new ParameterData."parameterDescription(Actual)?(?P<name>.*)", "(?P<unit>.*)", .* (?P<len>.*), "(?P<pbsb>....)..(?P<id>..)".;', line)
            if match:
                assert match.group('pbsb') == "4022"
                sensors.append(Sensor(match.group('id'),match.group('name'),match.group('name_current'),value_type_dict[match.group('unit')],match.group('len')))
                continue

            # We need to check separately for flair units that have different definition

            # strip pottential "actual" from the front to improve matching
            # this._currentSoftwareVersion = new ParameterData("parameterDescriptionSoftwareVersion", "", (ushort) 60, FlairEBusCommands.CmdReadActualSoftwareVersion.Cmd);
            match = re.search('this._current(?P<name_current>.*) = new ParameterData."parameterDescription(Actual)?(?P<name>.*)", "(?P<unit>.*)", .* (?P<len>.*), FlairEBusCommands\\.(?P<cmd>.*)\\.Cmd.;', line)
            if match:
                sensors.append(Sensor(flair_cmd_dict[match.group('cmd')].id,match.group('name'),match.group('name_current'),value_type_dict[match.group('unit')],match.group('len')))
                continue

        # This skips the Flair base class
        if "name" not in device_dict:
            print("sensor: skipping file " + file)
            continue

        device_dict["sensors"] = sensors
        device = DeviceSensor(**device_dict)
        dict_devices_sensor[device.name.lower()] = device

# Manually matching mis-matches in names for the same fields
dict_fields_pairs_manual = {
    "BypassSenseLevel" : "BypassSensLevel",
    "ExhaustFanPWMSetpoint" : "FanPWMSetpoint",
    "ExhaustfanSpeed" : "SpeedExhaustFan",
    "ExhaustFlow": "FlowExhaust",
    "ExhaustFlowSetting": "SettingExhaustFlow",
    "ExhaustPressure": "PressureExhaust",
    "FilterNotification" : "FilterState",
    "InletFanPWMSetpoint" : "FanPWMSetpoint",
    "InletfanSpeed" : "SpeedInletFan",
    "InletFlow": "FlowInlet",
    "InletFlowSetting": "SettingInletFlow",
    "InletPressure": "PressureInlet",
    "InsideTemperature" : "TemperatureInside",
    "OperatingTime": "TotalOperatingHours",
    "OptionTemperature" : "TemperatureOption",
    "OutsideTemperature" : "TemperatureOutside",
}

# Get converters
device_to_sensor_to_converter = converters.find_converters()
device_to_sensor_to_converter_unused = copy.deepcopy(device_to_sensor_to_converter)
device_to_name_current_to_name_param_dict = converters.device_to_name_current_to_name_param()

# assign converters to each sensor in each device
for device_name_lower, device in dict_devices_sensor.items():

    # flair units have a shared converter under the name 'flair'
    if "flair" in device_name_lower:
        device_name_lower = "flair"
    # This Particular Vitovent comes in too many flavors but only one converter
    elif "vitovent300wh32s" in device_name_lower:
        device_name_lower = "vitovent300wh32s"

    device_converters = device_to_sensor_to_converter[device_name_lower]
    device_converters_unused = device_to_sensor_to_converter_unused[device_name_lower]

    for sensor in device.sensors:
        name_param = device_to_name_current_to_name_param_dict[device_name_lower].get(sensor.name_current, None)
        if converter := device_converters.get(sensor.name, None):
            sensor.converter = converter
            device_converters_unused.pop(sensor.name, None)
            continue
        elif converter := device_converters.get(dict_fields_pairs_manual.get(sensor.name, None), None):
            sensor.converter = converter
            device_converters_unused.pop(dict_fields_pairs_manual[sensor.name], None)
            continue
        elif converter := device_converters.get(name_param, None):
            sensor.converter = converter
            device_converters_unused.pop(name_param, None)
            continue
        elif sensor.name.endswith("Status"):
            # Some (but *maybe* not all) Status fields are named "state" in the binding, so try that as a backup
            sensor_name_state = sensor.name.removesuffix("Status") + "State"
            if converter := device_converters.get(sensor_name_state, None):
                sensor.converter = converter
                device_converters_unused.pop(sensor_name_state, None)
                continue
            elif converter := device_converters.get(dict_fields_pairs_manual.get(sensor_name_state, None), None):
                sensor.converter = converter
                device_converters_unused.pop(dict_fields_pairs_manual[sensor_name_state], None)
                continue
        elif "vitovent" in device_name_lower:
            # Try the 'base' flair converter as a backup for vitovent units
            device_name_lower = "flair"
            if converter := device_converters.get(sensor.name, None):
                sensor.converter = converter
                device_converters_unused.pop(sensor.name, None)
                continue
            elif converter := device_converters.get(dict_fields_pairs_manual.get(sensor.name, None), None):
                sensor.converter = converter
                device_converters_unused.pop(dict_fields_pairs_manual[sensor.name], None)
                continue
            elif converter := device_converters.get(name_param, None):
                sensor.converter = converter
                device_converters_unused.pop(name_param, None)
                continue

        # If we are here, all other tries failed. Let's use some manual map of failed attempts:
        last_resort_device_converters = {
            "BypassCurrent" : "UInt16ToUNumberConverter",
            "BypassStatus" : "UInt16ToBypassStatusConverter",
            "BypassStepPosition" : "UInt32ToUNumberConverter",
            "Contact1Position" : "UInt16ToOnOffConverter",
            "Contact2Position" : "UInt16ToOnOffConverter",
            "DeviceID" : "UInt16ToUNumberConverter",
            "DeviceType" : "unknown",
            "DipswitchValue" : "unknown",
            "DispSwitchPosition" : "UInt16ToFanSwitchConverter",
            "EBusAddressing" : "unknown",
            "eBusPowerStatus" : "UInt16ToOnOffConverter", # paramEBusPowerState
            "EBusSyncGenErrors" : "unknown",
            "EWTStatus" : "UInt16ToEWTStatusConverter",
            "ExhaustFanPWMSetpoint" : "UInt16ToUNumberConverter",
            "ExhaustFlow" : "UInt16ToUNumberConverter",
            "ExhaustPressure" : "UInt16ToPressureConverter",
            "FanMode" : "UInt16ToFanModeConverter",
            "FanStatus" : "UInt16ToFanStatusConverter",
            "HumidityBoostState" : "UInt16ToHumidityBoostStateConverter",
            "InletFanPWMSetpoint" : "UInt16ToUNumberConverter",
            "InletFlow" : "UInt16ToUNumberConverter",
            "InletPressure" : "UInt16ToPressureConverter",
            "InsideTemperature" : "Int16ToTemperatureConverterFact10",
            "MRCConfigurationStatus" : "unknown",
            "OptionTemperature" : "Int16ToTemperatureFact100Converter",
            "PerilexPosition" : "UInt16ToFanSwitchConverter",
            "PostheaterPower" : "UInt16ToUNumberConverter",
            "PostheaterStatus" : "UInt16ToHeaterStatusConverter",
            "RelativeHumidity" : "Int16ToPercentageFact10Converter",
            "SoftwareVersion" : "default",
            "SwitchPosition" : "UInt16ToFanSwitchConverter",
            "UIFButtonsStatus" : "UInt16ToUNumberConverter",
        }
        if converter := last_resort_device_converters.get(sensor.name, None):
            sensor.converter = converter
            continue
        
        print(f"Error: Sensor not found: device: {device.name} name: {sensor.name} name_current: {sensor.name_current} name_param: {name_param}")
            
# Now we have added all known converters to all known fields - but there are potential missed matches -> we list those for debugging purposses
                                    
# set of sensor names, that have unfilled converter
sensors_without_converters_set = set()        
for device_name_lower,  device in dict_devices_sensor.items():
    for sensor in device.sensors:
        if sensor.converter == "":
            sensors_without_converters_set.add(sensor.name + "_" + device_name_lower)

converter_sensor_unused_set = set()  
for device_name_lower, device in device_to_sensor_to_converter_unused.items():
    print(device_name_lower + ":")            
    for sensor_name in device:
        print("    "+ sensor_name)          
        converter_sensor_unused_set.add(sensor_name + "_" + device_name_lower)

if False:
    print(sensors_without_converters_set)            
    print("------")            
print(converter_sensor_unused_set)      
print("------")            
print("sensors_without_converters_set: " + str(len(sensors_without_converters_set)) )
print("converter_fields_without_sensor_set: "+ str(len(converter_sensor_unused_set)) )

out.write_files(dict_devices_sensor, devices_param)
