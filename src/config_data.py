import glob
import re

from dev import Device
from params import UINT16, INT16


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


class ParamEnum:
    def __init__(self, min: int, max: int, values: str):
        self.min = min
        self.max = max
        self.values = values

    def __str__(self):
        return str([vars(self)[key] for key in sorted(vars(self).keys())])

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return str(self)


# Manually retrieved values from various sources other than decompiling
known_values_params = {
    "CVWTWMode": ParamEnum(0, 1, "0=off;1=on"),  # CVWTWMode
    "UnbalanceMode": ParamEnum(0, 1, "0=Not Permitted;1=Permitted"),  # UnbalanceMode
    "Input1Mode": ParamEnum(0, 4, "0=Normally Closed;1=0-10V input;2=Normally Open;3=12V Bypass Open/0V Bypass Closed;4=0V Bypass Open/12V Bypass Closed"),  # Input1Mode
    "CN1Coupling": ParamEnum(0, 4, "0=off;1=on;2=on if bypass open condition satisfied;3=bypass control;4=Bedroom valve"),  # CN1Coupling
    "CN1Inlet": ParamEnum(0, 7, "0=FanOff;1=Minimal flow 50m³/h;2=FanMode1;3=FanMode2;4=FanMode3;5=ManualSwitch;6=MaximalFlow;7=FanNotActive"),  # CN1Inlet
    "CN1Exhaust": ParamEnum(0, 7, "0=FanOff;1=Minimal flow 50m³/h;2=FanMode1;3=FanMode2;4=FanMode3;5=ManualSwitch;6=MaximalFlow;7=FanNotActive"),  # CN1Exhaust
    "Input2Mode": ParamEnum(0, 4, "0=Normally Closed;1=0-10V input;2=Normally Open;3=12V Bypass Open/0V Bypass Closed;4=0V Bypass Open/12V Bypass Closed"),  # Input2Mode
    "CN2Coupling": ParamEnum(0, 4, "0=off;1=on;2=on if bypass open condition satisfied;3=bypass control;4=Bedroom valve"),  # CN2Coupling
    "CN2Inlet": ParamEnum(0, 7, "0=FanOff;1=Minimal flow 50m³/h;2=FanMode1;3=FanMode2;4=FanMode3;5=ManualSwitch;6=MaximalFlow;7=FanNotActive"),  # CN2Inlet
    "CN2Exhaust": ParamEnum(0, 7, "0=FanOff;1=Minimal flow 50m³/h;2=FanMode1;3=FanMode2;4=FanMode3;5=ManualSwitch;6=MaximalFlow;7=FanNotActive"),  # CN2Exhaust
    "EWTMode": ParamEnum(0, 1, "0=off;1=on"),  # EWTMode
    "BypassMode": ParamEnum(0, 2, "0=Auto;1=Closed;2=Open"),  # BypassMode
    "PreheaterPresent": ParamEnum(0, 1, "0=no;1=yes"),  # PreheaterPresent
    "RHSensorPresent": ParamEnum(0, 1, "0=no;1=yes"),  # RHSensorPresent
    "CO2SensorsActivated": ParamEnum(0, 1, "0=no;1=yes"),  # CO2SensorsActivated
    "SwitchDefaultPos": ParamEnum(0, 1, "0=off;1=on"),  # SwitchDefaultPos
    "ModbusInterface": ParamEnum(0, 2, "0=Modbus internal;1=Modbus external connect;2=External customer"),  # ModbusInterface
    "ModbusSpeed": ParamEnum(0, 7, "0=1200 Baud;1=2400 Baud;2=4800 Baud;3=9600 Baud;4=19k2 Baud;5=38k4 Baud;6=56k Baud;7=115k Baud"),  # ModbusSpeed
    "ModbusParity": ParamEnum(0, 3, "0=No Parity;1=Even Parity;2=Odd Parity;3=Unknown"),  # ModbusParity
}

class Fields:
    def __init__(self, current: int, min: int, max: int, step: int, default: int):
        self.current = current
        self.min = min
        self.max = max
        self.step = step
        self.default = default

    def __str__(self):
        return str([vars(self)[key] for key in sorted(vars(self).keys())])

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return str(self)


class Parameter:
    def __init__(self, device_name: str, first_version: int, last_version: int, is_plus_only: bool, id: int, name: str, unit: str, multiplier: float, datatype: str, is_read_only: bool, fields: Fields):
        self.device_name = device_name
        self.first_version = first_version
        self.last_version = last_version
        self.is_plus_only = is_plus_only
        self.id = id
        self.name = name
        self.unit = unit
        self.multiplier = multiplier
        self.datatype = datatype
        self.is_read_only = is_read_only
        self.field_current = fields.current
        self.field_min = fields.min
        self.field_max = fields.max
        self.field_step = fields.step
        self.field_default = fields.default

        self.values = self.__get_enum_values()

    # Check as many conditions as possible to make sure that the enum fields are used only on applicable places.
    # This is necessary, since we only have the values from handful of units. We may assume those to be applicable on other units,
    # But in fact other units may have different values.
    def __get_enum_values(self):
        if param_enum := known_values_params.get(self.name):
            if param_enum.min != self.field_min:
                return None
            elif param_enum.max != self.field_max:
                return None
            elif self.datatype != UINT16:
                return None
            elif self.field_step != 1:
                return None
            elif self.unit != "":
                return None
            else:
                return param_enum.values
        else:
            return None

    def __str__(self):
        return str([vars(self)[key] for key in sorted(vars(self).keys())])

    def __eq__(self, other):
        return str(self) == str(other)
    
    def __lt__(self, other):
        return self.device_name + self.name + str(self.first_version) + str(self.last_version) < other.device_name + other.name + str(other.first_version) + str(other.last_version) 

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return str(self)


class DeviceParameters(Device):
    def __init__(self, name: str, view_no: int, params_basic: int, params_plus: int, first_version: int, last_version: int, controller_code: int):
        super().__init__(name, view_no, first_version, last_version)
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
            
            name = match.group('name')
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
            
            device = DeviceParameters(name, view_no, params_basic, params_plus, first_version, last_version, controller_code)

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
                param = Parameter(name, first_version, last_version, is_plus_only, int(m.group('id')), m.group('name'), value_type_dict_config[m.group('unit')], float(m.group('multiplier')), datatype, is_read_only, fields)
                params.append(param)

            device_parameters[device] = params

    return device_parameters
