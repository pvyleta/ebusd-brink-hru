import re
import glob
import params
import dev


class CurrentParam:
    def __init__(self, name_current: str, datatype: str):
        self.name_current = name_current
        self.datatype = datatype

    def __str__(self):
        return str([vars(self)[key] for key in sorted(vars(self).keys())])

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return str(self)


def get_device_to_current_param() -> dict[dev.Device, dict[str, CurrentParam]]:
    device_to_current_param: dict[dev.Device, dict[str, CurrentParam]] = {}
    files_view_model = glob.glob('./BCSServiceTool/ViewModel/Devices/**/*ActualState*ViewModel_*.cs', recursive=True)
    for file in files_view_model:
        with open(file) as f:
            file_str = f.read()

            match1 = re.search(r'public (partial )?class (?P<name>\w+)ActualState(Sub\d)?ViewModel_\d(?P<view_no>\d) :', file_str)
            match2 = re.search(r'public const uint VALID_FIRST_VERSION = (?P<first_version>\d*);', file_str)
            match3 = re.search(r'public const uint VALID_LAST_VERSION = (?P<last_version>\d*);', file_str)
            assert match1 and match2 and match3

            device = dev.Device(match1.group('name'), match1.group('view_no'), match2.group('first_version'), match3.group('last_version'))
            device_to_current_param.setdefault(device, {})
            matches = re.finditer(r'public (?P<datatype_out>\w*) (?P<name_actual>\w*)\n *\{\n *get => this\.\w*\.(?P<name_current>\w*)\.(?P<datatype_in>\w*)Value;', file_str)
            for m in matches:
                current_param = CurrentParam(m.group('name_current'), m.group('datatype_out'))
                assert not (current_param_in_dict := device_to_current_param[device].get(m.group('name_current'))) or current_param_in_dict == current_param
                device_to_current_param[device][m.group('name_current')] = current_param

    return device_to_current_param
