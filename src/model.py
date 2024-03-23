DEBUG = False

INT8 = "Int8"
UINT8 = "UInt8"
INT16 = "Int16"
UINT16 = "UInt16"
INT32 = "Int16"
UINT32 = "Int16"
STRING = "String"

class BaseObject:
    def __eq__(self, other):
        return str(self) == str(other)

    def __str__(self):
        return str([vars(self)[key] for key in sorted(vars(self).keys())])

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return str(self)
    
class CommandEBus(BaseObject):
    def __init__(self, cmd: str, pbsb: str, len: str, id: str, write_len: int, read_len_code: int):
        self.cmd = cmd
        self.pbsb = pbsb
        self.len = len
        self.id = id
        self.write_len = write_len
        self.read_len = read_len_code - 2 # BCServiceTool includes two additional bytes in the resp length (likely length and CRC), but we onyl care for the payload length

class Converter(BaseObject):
    def __init__(self, name: str, type: str, multiplier: float, length: int, values: str):
        self.name: str = name
        self.type: str = type
        self.multiplier: float = multiplier
        self.length: int = length
        self.values: str = values

        self.name_actual: str = ""
        self.converter_str: str = ""

class VersionRange(BaseObject):
    def __init__(self, view_no: int, first_version: int, last_version: int):
        self.view_no = view_no
        self.first_version = first_version
        self.last_version = last_version

    def __lt__(self, other):
        return self.view_no < other.view_no


class DeviceVersion(BaseObject):
    def __init__(self, device_name: str, version: VersionRange):
        self.device_name = device_name
        self.version = version


class DeviceModel(BaseObject):
    def __init__(self, name: str):
        self.name = name
        self.sensors: dict[VersionRange, list[Sensor]] = {}
        self.converters: dict[VersionRange, list[Converter]] = {}
        self.parameters: dict[VersionRange, list[Parameter]] = {}


# .xaml files do not have verson information, so we must rely on the view 'index' for matching
class DeviceView(BaseObject):
    def __init__(self, name: str, view_no: int):
        self.name = name
        self.view_no = view_no

class Sensor(BaseObject):
    def __init__(self, id: int, name_description: str, name_current: str, name_param: str|None, unit: str, update_rate: int, cmd: CommandEBus|None, datatype=None):
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


class ParamEnum(BaseObject):
    def __init__(self, min: int, max: int, values: str):
        self.min = min
        self.max = max
        self.values = values


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

class Fields(BaseObject):
    def __init__(self, current: int, min: int, max: int, step: int, default: int):
        self.current = current
        self.min = min
        self.max = max
        self.step = step
        self.default = default

class Parameter(BaseObject):
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
    
    def __lt__(self, other):
        return self.device_name + self.name + str(self.first_version) + str(self.last_version) < other.device_name + other.name + str(other.first_version) + str(other.last_version) 
