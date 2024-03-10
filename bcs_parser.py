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
    def __init__(self, id, name, name_current, unit, update_rate):
        self.id = id
        self.name = name
        self.name_current = name_current
        self.unit = unit
        self.update_rate = update_rate
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
                # TODO dome flair units are reading one ID multiple times for different values in UI, e.g. CurrentSoftwareVersionUIFModule
            match = re.search('this._current(?P<name_current>.*) = new ParameterData."parameterDescription(?P<name>.*)", "(?P<unit>.*)", .* (?P<update_rate>.*), "(?P<pbsb>....)..(?P<id>..)".;', line)
            if match:
                assert match.group('pbsb') == "4022"
                sensors.append(Sensor(match.group('id'),match.group('name'),"Current"+match.group('name_current'),value_type_dict[match.group('unit')],match.group('update_rate')))
                continue

            # We need to check separately for flair units that have different definition

            # strip pottential "actual" from the front to improve matching
            # this._currentSoftwareVersion = new ParameterData("parameterDescriptionSoftwareVersion", "", (ushort) 60, FlairEBusCommands.CmdReadActualSoftwareVersion.Cmd);
            match = re.search('this._current(?P<name_current>.*) = new ParameterData."parameterDescription(?P<name>.*)", "(?P<unit>.*)", .* (?P<update_rate>.*), FlairEBusCommands\\.(?P<cmd>.*)\\.Cmd.;', line)
            if match:
                sensors.append(Sensor(flair_cmd_dict[match.group('cmd')].id,match.group('name'),"Current"+match.group('name_current'),value_type_dict[match.group('unit')],match.group('update_rate')))
                continue

        # This skips the Flair base class
        if "name" not in device_dict:
            print("sensor: skipping file " + file)
            continue

        device_dict["sensors"] = sensors
        device = DeviceSensor(**device_dict)
        dict_devices_sensor[device.name.lower()] = device

# Get converters
device_to_name_param_to_converter = converters.find_converters2()
device_to_name_param_to_converter_unused = copy.deepcopy(device_to_name_param_to_converter)
device_to_name_current_to_name_param_dict = converters.device_to_name_current_to_name_param2()

# TODO status and value is switched - figure out reason, fix it:
    #   this.paramCO2Sensor1Status.ParameterName = this.FindResource((object) this._viewModel.ModelFlairParameterData.CurrentCO2Sensor1Value.Description).ToString();
    #   this.paramCO2Sensor1Value.ParameterName = string.Empty;

# For some parameters, there is no valid conversion in code, manually pick the best backups
manual_current_to_param_conversion = {
    "CurrentCO2Sensor1Status" : "paramCO2Sensor1Value", # conversion missing for all units for no apparent reason
    "CurrentCO2Sensor2Status" : "paramCO2Sensor2Value", # conversion missing for all units for no apparent reason
    "CurrentCO2Sensor3Status" : "paramCO2Sensor3Value", # conversion missing for all units for no apparent reason
    "CurrentCO2Sensor4Status" : "paramCO2Sensor4Value", # conversion missing for all units for no apparent reason
    "CurrentSoftwareVersionUIFModule" : "paramBaseSoftwareVersion", # Vitovent300WH32SC325 speciality
    "CurrentHardwareVersionUIFModule" : "paramBaseHardwareVersion", # Vitovent300WH32SC325 speciality
}

# Some parameters seem not to be present in UI at all - we fabricate the converters on other knowledge
manual_current_to_converter = {
    "CurrentDipswitchValue" : "UInt16ToUNumberConverter", # paramDipswitch; conversion missing for Flair units and few others for no apparent reason
    "CurrentEBusAddressing" : "unknown", # 
    "CurrenteBusPowerStatus": "UInt16ToEBusPowerStateConverter", # paramEBusPowerState; Assumed from decentralair70actualstateview_01.xaml
    "CurrentEBusSyncGenErrorCount" : "UInt16ToUNumberConverter", # paramSyncGenErrorCount; conversion missing for Flair units and few others for no apparent reason
    "CurrentExhaustFanPWMValue" : "UInt16ToUNumberConverter",  # paramFanPWMSetpoint; Assumed from decentralair70actualstateview_01.xaml
    "CurrentHardwareVersionExtensionModule" : "unknown", # Vitovent300WH32SC325 speciality
    "CurrentInletFanPWMValue" : "UInt16ToUNumberConverter",  # paramFanPWMSetpoint; Assumed from decentralair70actualstateview_01.xaml
    "CurrentPerilexPosition" : "UInt16ToFanSwitchConverter", # paramPerilexPosition; Mising for Sky units
    "CurrentSoftwareVersion" : "default", # Missing for many units, but present for some
    "CurrentSoftwareVersionExtensionModule" : "unknown", # Vitovent300WH32SC325 speciality

    # Some flar specific stuff
    "CurrentDeviceID" : "unknown", 
    "CurrentDeviceType" : "unknown",
    "CurrentImageVersionUIFModule" : "unknown", # Not easy to figure out, DynamicResource, parameterDescriptionUIFImageVersion
    "CurrentLanguageVersionUIFModule" : "unknown", # Not easy to figure out, DynamicResource, parameterDescriptionUIFLanguageVersion
    "CurrentLocalUIFSwitchPosition" : "unknown",
    "CurrentUIFButtonsStatus" : "unknown",

    # Some random fields that seems almost forgotten for some units, as they exist for the rest, taken from other places almost at random
    "CurrentBypassCurrent" : "UInt16ToUNumberConverter", 
    "CurrentBypassStatus" : "UInt16ToBypassStatusConverter", 
    "CurrentContact1Position" : "UInt16ToOnOffConverter", 
    "CurrentContact2Position" : "UInt16ToOnOffConverter", 
    "CurrentEWTStatus" : "UInt16ToEWTStatusConverter", 
    "CurrentExhaustFlow" : "UInt16ToUNumberConverter", 
    "CurrentHumidityBoostState" : "UInt16ToHumidityBoostStateConverter", 
    "CurrentInletFlow" : "UInt16ToUNumberConverter", 
    "CurrentInsideTemperature" : "Int16ToTemperatureConverterFact10", 
    "CurrentMRCConfigurationStatus" : "unknown", 
    "CurrentOptionTemperature" : "Int16ToTemperatureConverterFact10", 
    "CurrentPostheaterPower" : "UInt16ToUNumberConverter", 
    "CurrentPostheaterStatus" : "UInt16ToHeaterStatusConverter", 
    "CurrentPressureExhaust" : "UInt16ToPressureConverter", 
    "CurrentPressureInlet" : "UInt16ToPressureConverter", 
    "CurrentRelativeHumidity" : "Int16ToPercentageFact10Converter", 
}
    
# assign converters to each sensor in each device
for device_name_lower, device in dict_devices_sensor.items():

    # flair units have a shared converter under the name 'flair'
    if "flair" in device_name_lower:
        device_name_lower = "flair"
    # This Particular Vitovent comes in too many flavors but only one converter
    elif "vitovent300wh32s" in device_name_lower:
        device_name_lower = "vitovent300wh32s"

    device_converters = device_to_name_param_to_converter[device_name_lower]
    device_converters_unused = device_to_name_param_to_converter_unused[device_name_lower]

    for sensor in device.sensors:
        # First, Try to match the converter through following the path in code from ebus to UI
        name_param = device_to_name_current_to_name_param_dict[device_name_lower].get(sensor.name_current, None)
        if converter := device_converters.get(name_param, None):
            sensor.converter = converter
            device_converters_unused.pop(name_param, None)
            continue
        
        # Try the 'base' flair converter as a backup for vitovent units
        if "vitovent" in device_name_lower:
            if converter := device_to_name_param_to_converter["flair"].get(name_param, None):
                sensor.converter = converter
                device_to_name_param_to_converter_unused["flair"].pop(name_param, None)
                continue
        
        # For some parameters the convertors are listed, but the conversion path is broken, so we manually connect the dots
        name_param_manual = manual_current_to_param_conversion.get(sensor.name_current, None)
        if converter := device_converters.get(name_param_manual, None):
            sensor.converter = converter
            device_converters_unused.pop(name_param_manual, None)
            continue

        # If everything else fails, we have manually searched for the most suitable converter from otehr units
        # TODO Mark these sensors somehow, since there may have been a reason the parameter was hidden for certain units
        # TODO the device type is likely viessmann/brink, so we might figure that out from code
        if converter := manual_current_to_converter.get(sensor.name_current, None):
            sensor.converter = converter
            device_converters_unused.pop(name_param_manual, None)
            continue
        
        print(f"Error: Sensor not found: device: {device.name} lower: {device_name_lower} name: {sensor.name} name_current: {sensor.name_current} name_param: {name_param}")
            
# Now we have added all known converters to all known fields - but there are potential missed matches -> we calculate their count for debugging purposses
sensors_without_converters_set = set()        
for device_name_lower,  device in dict_devices_sensor.items():
    for sensor in device.sensors:
        if sensor.converter == "":
            sensors_without_converters_set.add(sensor.name + "_" + device_name_lower)
            
print("sensors_without_converters_set: " + str(len(sensors_without_converters_set)) )

converter_sensor_unused_set = set()  
for device_name_lower, device in device_to_name_param_to_converter_unused.items():
    for sensor_name in device:       
        converter_sensor_unused_set.add(sensor_name + "_" + device_name_lower)

print("converter_fields_without_sensor_set: "+ str(len(converter_sensor_unused_set)) )

out.write_files(dict_devices_sensor, devices_param)
