import re
import glob

from model import UINT16, INT16, UINT32, STRING, BaseObject, DeviceVersion, VersionRange


class SensorDatatype(BaseObject):
    def __init__(self, name_current: str, datatype: str):
        self.name_current = name_current
        self.datatype = datatype


def __datatype_out_to_datatype(datatype_out: str) -> str:
    if datatype_out == 'ushort':
        return UINT16
    elif datatype_out == 'short':
        return INT16
    elif datatype_out == 'uint':
        return UINT32
    elif datatype_out == 'string':
        return STRING
    else:
        raise RuntimeError(f'unknown datatype {datatype_out}')


def get_sensor_datatypes() -> dict[DeviceVersion, dict[str, SensorDatatype]]:
    device_to_sensor_datatype: dict[DeviceVersion, dict[str, SensorDatatype]] = {}
    files_view_model = glob.glob('./BCSServiceTool/ViewModel/Devices/**/*ActualState*ViewModel_*.cs', recursive=True)
    for file in files_view_model:
        with open(file) as f:
            file_str = f.read()

            match1 = re.search(r'public (partial )?class (?P<name>\w+)ActualState(Sub\d)?ViewModel_\d(?P<view_no>\d) :', file_str)
            match2 = re.search(r'public const uint VALID_FIRST_VERSION = (?P<first_version>\d*);', file_str)
            match3 = re.search(r'public const uint VALID_LAST_VERSION = (?P<last_version>\d*);', file_str)
            assert match1 and match2 and match3

            device_name = match1.group('name')
            version_range = VersionRange(int(match1.group('view_no')), int(match2.group('first_version')), int(match3.group('last_version')))
            device_version = DeviceVersion(device_name, version_range)
            device_to_sensor_datatype.setdefault(device_version, {})
            matches = re.finditer(r'public (?P<datatype_out>\w*) (?P<name_actual>\w*)\n *\{\n *get => this\.\w*\.(?P<name_current>\w*)\.(?P<datatype_in>\w*)Value;', file_str)
            for m in matches:
                datatype = __datatype_out_to_datatype(m.group('datatype_out'))
                sensor_datatype = SensorDatatype(m.group('name_current'), datatype)
                assert not (sensor_datatype_in_dict := device_to_sensor_datatype[device_version].get(m.group('name_current'))) or sensor_datatype_in_dict == sensor_datatype
                device_to_sensor_datatype[device_version][m.group('name_current')] = sensor_datatype

    return device_to_sensor_datatype
