import glob
import re

from model import Parameter, UINT16, INT16, DeviceVersion, Fields, VersionRange


value_type_dict_config = {
    'NoUnit': "",
    'DegrCelcius': "°C",
    'Minutes': "Minutes",
    'Voltage': "V",
    'Degrees': "°",
    'M3PerHour': "m³/h",
    'Day': "Day",
    'PPM': "ppm",
    'Percentage': "%",
}


class DeviceParameters(DeviceVersion):
    def __init__(self, device_name: str, version_range: VersionRange, params_basic: int, params_plus: int, controller_code: int):
        super().__init__(device_name, version_range)
        self.params_basic = params_basic
        self.params_plus = params_plus
        self.controller_code = controller_code

files_params = glob.glob('./BCSServiceTool/Model/Devices/**/*ParameterSet_*.cs', recursive=True)
def get_device_parameters() -> dict[DeviceParameters, list[Parameter]]:
    device_parameters: dict[DeviceParameters, list[Parameter]] = {}
    for file in files_params:
        with open(file) as f:
            params: list[Parameter] = []
            file_str = f.read()

            match = re.search(r'public class (?P<name>\w*)ParameterSet_\d(?P<view_no>\d) : (?P<device_type>FlairBaseParameterSet_01|FlairBaseParameterSet_02|WTWParameterFileHeader)', file_str)
            assert match
            
            device_name = match.group('name')
            view_no = int(match.group('view_no'))
            device_type = match.group('device_type')

            # Flair units have two different base classes, we manually overwrite the relevant base class values
            if device_type == 'FlairBaseParameterSet_01':
                params_basic = params_plus = 57
            elif device_type == 'FlairBaseParameterSet_02':
                params_basic = params_plus = 60
            else:
                match = re.search(
                    r'public const int PARAMETER_COUNT_(BASIC|AUTO) = (?P<params_basic>\d*);[\s\S]*'
                    r'public const int PARAMETER_COUNT_(PLUS|MANUAL) = (?P<params_plus>\d*);', file_str)
                assert match
                params_basic = int(match.group('params_basic'))
                params_plus = int(match.group('params_plus'))

            match = re.search(
                r'public (new )?const (uint|byte) CONTROLLER_CODE = (?P<controller_code>\d*);[\s\S]*'
                r'public (new )?const uint VALID_FIRST_VERSION = (?P<first_version>\d*);[\s\S]*'
                r'public (new )?const uint VALID_LAST_VERSION = (?P<last_version>\d*);', file_str)
            assert match

            first_version = int(match.group('first_version'))
            last_version = int(match.group('last_version'))
            controller_code = int(match.group('controller_code'))
            
            version_range = VersionRange(view_no, first_version, last_version)
            device = DeviceParameters(device_name, version_range, params_basic, params_plus, controller_code)

            params_basic_int = int(params_basic)
            
            matches = re.finditer(r'WTWParameterDefinition (?P<param_def>\w*) = new WTWParameterDefinition[^ ]* (?P<id>\d*), "parameter(SetDescription)?(?P<name>\w*)", (?P<is_read_only>\w*), WTWParameterDefinition\.UnitType\.(?P<unit>\w*), (?P<multiplier>[^ ]*), (?P<is_signed>\w*)\);'
                                  r'[\s\S]*((?P=param_def))\.SetApplianceData[^ ]* (?P<current>-?\d*), [^ ]* (?P<min>-?\d*), [^ ]* (?P<max>-?\d*), [^ ]* (?P<step>-?\d*), [^ ]* (?P<default>-?\d*)\);', file_str)
            for m in matches:
                # First 'params_basic' count of parameters are present in basic and plus variants of device, the subsequent ones are only in plus version
                is_plus_only = params_basic_int < 1
                params_basic_int -= 1
                fields = Fields(int(m.group('current')), int(m.group('min')), int(m.group('max')), int(m.group('step')), int(m.group('default')))
                datatype = INT16 if m.group('is_signed') == 'true' else UINT16
                is_read_only = bool(m.group('is_read_only') == 'true')
                param = Parameter(device_name, first_version, last_version, is_plus_only, int(m.group('id')), m.group('name'), value_type_dict_config[m.group('unit')], float(m.group('multiplier')), datatype, is_read_only, fields)
                params.append(param)

            device_parameters[device] = params

    return device_parameters
