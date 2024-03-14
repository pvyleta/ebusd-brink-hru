import glob
import re

files_params = glob.glob('./BCSServiceTool/Model/Devices/**/*ParameterSet_*.cs', recursive=True)

value_type_dict_config = {
    'WTWParameterDefinition.UnitType.NoUnit': "", 
    'WTWParameterDefinition.UnitType.DegrCelcius': "°C", 
    'WTWParameterDefinition.UnitType.Minutes': "Minutes", 
    'WTWParameterDefinition.UnitType.Voltage': "V", 
    'WTWParameterDefinition.UnitType.Degrees': "°", 
    'WTWParameterDefinition.UnitType.M3PerHour': "m³/h", 
    'WTWParameterDefinition.UnitType.Day': "Day", 
    'WTWParameterDefinition.UnitType.PPM': "ppm", 
    'WTWParameterDefinition.UnitType.Percentage': "%",
}

class Parameter:
    def __init__(self, device_name: str, id: str, name: str, unit: str, multiplier: str, is_signed: str, is_read_only: str):
        self.device_name = device_name
        self.id = id
        self.name = name
        self.unit = unit
        self.multiplier = multiplier
        self.is_signed = is_signed
        self.is_read_only = is_read_only

    def values(self, curent: str, min: str, max: str, step: str, default: str):
        self.curent = curent
        self.min = min
        self.max = max
        self.step = step
        self.default = default

class DeviceParameters:
    def __init__(self, name: str, params_basic: str, params_plus: str, first_version: str, last_version: str, params: list[Parameter], controller_code: str):
        self.name = name
        self.params_basic = params_basic
        self.params_plus = params_plus
        self.first_version = first_version
        self.last_version = last_version
        self.params = params
        self.controller_code = controller_code

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

def get_device_parameters() -> dict[str, DeviceParameters]:
    device_parameters: list[DeviceParameters] = []
    for file in files_params:
        with open(file) as f:
            device_dict: dict[str, str] = {}
            params: list[Parameter] = []
            datafile = f.readlines()

            # The files first contain some constants that are useful
            for line in datafile:
                for property, regex in search_list_params:
                    match = re.search(regex, line)
                    if match:
                        device_dict[property] = match.group('match')
                        break
                
            # Flair units have two different base classes, we manually overwrite the relevant base class values
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

            # The files first contain some constants that are useful
            for line in datafile:
                # Then there is a line with parameter definition...
                match = re.search('new WTWParameterDefinition.* (?P<id>[0-9]*), "parameter(SetDescription)?(?P<name>.*)", (?P<is_read_only>.*), (?P<unit>.*), (?P<multiplier>.*), (?P<is_signed>.*).;', line)
                if match:
                    params.append(Parameter(device_dict['name'],match.group('id'),match.group('name'),value_type_dict_config[match.group('unit')],match.group('multiplier'),match.group('is_signed'),match.group('is_read_only')))
    
                # And then it follows with line defining the values of the last added parameter
                match = re.search('SetApplianceData.* (-?[0-9]*), .* (-?[0-9]*), .* (-?[0-9]*), .* (-?[0-9]*), .* (-?[0-9]*).;', line)
                if match:
                    params[-1].values(match.group(1),match.group(2),match.group(3),match.group(4),match.group(5))

            device_dict["params"] = params
            device = DeviceParameters(**device_dict)

            device_parameters.append(device)
    
    return device_parameters