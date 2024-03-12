import re
import glob
import params


# TODO ActualStateViewModel_ has conversion between the type handler and 'Current' name -> can be likely more useful than 'actual' parsing through converters
def get_device_to_actual_param_to_datatype():
    device_to_actual_param_to_datatype = {}
    files_view_model = glob.glob('./BCSServiceTool/ViewModel/Devices/**/*ActualState*ViewModel_*.cs', recursive=True)
    for file in files_view_model:
        
        match = re.search(f'BCSServiceTool/ViewModel/Devices.*\\\\(?P<name>\\w+)ActualState.*ViewModel_...cs$', file)
        if match:
            device_name_lower = match.group('name').lower()
            device_to_actual_param_to_datatype.setdefault(device_name_lower, {})

        with open(file) as f:
            datafile = f.readlines()
            for line in datafile:
                #     this.ActualFanState = itemResponseType.WordValue;
                match = re.search('this.(?P<actual_name>\\w*) = itemResponseType.(?P<datatype>\\w*);', line)
                if match:
                    device_to_actual_param_to_datatype[device_name_lower][match.group('actual_name')] = match.group('datatype')

    return device_to_actual_param_to_datatype

value_type_dict = {
    '': "",
    'rpm': "rpm",
    'm3/h': "m³/h",
    'm3': "m³",
    'Pa': "Pa",
    'Â°C': "°C",
    '°C': "°C",
    'PPM': "ppm",
    'Hour': "Hour",
    'Steps': "Steps",
    'PWM': "PWM",
    'V': "V",
    '%': "%"
}

class Sensor:
    def __init__(self, device_lowercase, id, name, name_current, unit, update_rate, cmd=None, datatype=None):
        self.device_lowercase = device_lowercase
        self.id = id
        self.name = name
        self.name_current = name_current
        self.unit = unit
        self.update_rate = update_rate
        self.cmd = cmd
        self.datatype = datatype
        
        self.converter = None
        self.converter_match = ""

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

class CommandEBus:
    def __init__(self, cmd, pbsb, len, id, write_len, read_len):
        self.cmd = cmd
        self.pbsb = pbsb
        self.len = len
        self.id = id
        self.write_len = write_len
        self.read_len = read_len
    
    def __eq__(self, other):
        return vars(self) == vars(other)

# TODO must be done per-device
def get_commands_dict():
    cmd_dict = {}
    cmd_bytes_dict = {}
    cmd_dict_conflict_counter = 0
    cmd_bytes_dict_conflict_counter = 0
    files_commands = glob.glob('./BCSServiceTool/BusinessLogic/Commands/*Commands.cs', recursive=True)
    for file in files_commands:
        with open(file) as f:
            datafile = f.readlines()
            for line in datafile:
                #     public static CommandEBus CmdReadActualSoftwareVersion = new CommandEBus("40220100", (ushort) 0, 15U);
                match = re.search('public static CommandEBus (?P<cmd>.*) = new CommandEBus."(?P<pbsb>....)(?P<len>..)(?P<id>.*)", .* (?P<write_len>.*), (?P<read_len>.*)U.;', line)
                if match:
                    cmd = CommandEBus(match.group('cmd'),match.group('pbsb'),match.group('len'),match.group('id'),match.group('write_len'),match.group('read_len'))
                    command_bytes = cmd.pbsb + cmd.len + cmd.id
                    
                    # Sanity checks - if command is present more than once, it must the an identical command, otherwise throw an error
                    if cmd.cmd in cmd_dict:
                        if cmd != cmd_dict[cmd.cmd]:
                            cmd_dict_conflict_counter += 1
                            if params.DEBUG:
                                print("Warning: Duplicate: cmd_dict: " + str(vars(cmd)))
                                print("Warning: Duplicate: cmd_dict: " + str(vars(cmd_dict[cmd.cmd])))
                    if command_bytes in cmd_bytes_dict:
                        if cmd != cmd_bytes_dict[command_bytes]:
                            cmd_bytes_dict_conflict_counter += 1
                            if params.DEBUG:
                                print("Warning: Duplicate: cmd_bytes_dict: " + str(vars(cmd)))
                                print("Warning: Duplicate: cmd_bytes_dict: " + str(vars(cmd_bytes_dict[command_bytes])))
                    
                    cmd_dict[cmd.cmd] = cmd
                    cmd_bytes_dict[command_bytes] = cmd

    print("cmd_dict_conflict_counter: " + str(cmd_dict_conflict_counter))
    print("cmd_bytes_dict_conflict_counter: " + str(cmd_bytes_dict_conflict_counter))

    return cmd_dict, cmd_bytes_dict

def get_dict_devices_sensor(cmd_dict, cmd_bytes_dict):
    dict_devices_sensor = {}
    missing_commands_set = set()
    
    files_sensor = glob.glob('./BCSServiceTool/Model/Devices/**/*DataModel_*.cs', recursive=True)
    for file in files_sensor:
        # This skips the Flair base class, which contains no sensor definitions
        if "FlairBase" in file:
            print("sensor: skipping file " + file)
            continue

        # TODO get device name from filename
        
        with open(file) as f:
            device_dict = {}
            sensors = []
            datafile = f.readlines()

            for line in datafile:
                
                # The files first contain some constants that are useful
                for property, regex in search_list_sensor:
                    match = re.search(regex, line)
                    if match:
                        device_dict[property] = match.group('match')
                
                # Then there is a line with sensor definition
                # this._currentSettingExhaustFlow = new ParameterData("parameterDescriptionExhaustFlowSetting", "%", (ushort) 10, "4022010A");
                # TODO some flair units are reading one ID multiple times for different values in UI, e.g. CurrentSoftwareVersionUIFModule
                match = re.search('this._current(?P<name_current>.*) = new ParameterData."parameterDescription(?P<name>.*)", "(?P<unit>.*)", .* (?P<update_rate>.*), "(?P<pbsb>....)(?P<len>..)(?P<id>..)".;', line)
                if match:
                    # Sanity checks
                    assert match.group('pbsb') == "4022"
                    assert match.group('len') == "01"

                    # Unfortunately, not all Commands are defined - at least track those that are missing
                    command_bytes = match.group('pbsb') + match.group('len') + match.group('id')
                    if command_bytes not in cmd_bytes_dict:
                        missing_commands_set.add(command_bytes)
                        
                    sensors.append(Sensor(device_dict['name'].lower(), match.group('id'),match.group('name'),"Current"+match.group('name_current'),value_type_dict[match.group('unit')],match.group('update_rate'), cmd_bytes_dict.get(command_bytes, None)))
                    continue

                # We need to check separately for flair units that have different definition
                # this._currentSoftwareVersion = new ParameterData("parameterDescriptionSoftwareVersion", "", (ushort) 60, FlairEBusCommands.CmdReadActualSoftwareVersion.Cmd);
                match = re.search('this._current(?P<name_current>.*) = new ParameterData."parameterDescription(?P<name>.*)", "(?P<unit>.*)", .* (?P<update_rate>.*), FlairEBusCommands\\.(?P<cmd>.*)\\.Cmd.;', line)
                if match:
                    sensors.append(Sensor(device_dict['name'].lower(), cmd_dict[match.group('cmd')].id,match.group('name'),"Current"+match.group('name_current'),value_type_dict[match.group('unit')],match.group('update_rate'), cmd_bytes_dict.get(command_bytes, None)))
                    continue

            device_dict["sensors"] = sensors
            device = DeviceSensor(**device_dict)
            dict_devices_sensor[device.name.lower()] = device

    print("Info: missing commands definition: " + str(missing_commands_set))

    return dict_devices_sensor