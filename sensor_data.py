import re
import glob

# Now let's parse the sensor data

files_sensor = glob.glob('./BCSServiceTool/Model/Devices/**/*DataModel_*.cs', recursive=True)

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
    def __init__(self, device_lowercase, id, name, name_current, unit, update_rate):
        self.device_lowercase = device_lowercase
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

def get_dict_devices_sensor():
    dict_devices_sensor = {}
    for file in files_sensor:
        # This skips the Flair base class, which contains no sensor definitions
        if "FlairBase" in file:
            print("sensor: skipping file " + file)
            continue
        
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
                match = re.search('this._current(?P<name_current>.*) = new ParameterData."parameterDescription(?P<name>.*)", "(?P<unit>.*)", .* (?P<update_rate>.*), "(?P<pbsb>....)..(?P<id>..)".;', line)
                if match:
                    assert match.group('pbsb') == "4022"
                    sensors.append(Sensor(device_dict['name'].lower(), match.group('id'),match.group('name'),"Current"+match.group('name_current'),value_type_dict[match.group('unit')],match.group('update_rate')))
                    continue

                # We need to check separately for flair units that have different definition
                # this._currentSoftwareVersion = new ParameterData("parameterDescriptionSoftwareVersion", "", (ushort) 60, FlairEBusCommands.CmdReadActualSoftwareVersion.Cmd);
                match = re.search('this._current(?P<name_current>.*) = new ParameterData."parameterDescription(?P<name>.*)", "(?P<unit>.*)", .* (?P<update_rate>.*), FlairEBusCommands\\.(?P<cmd>.*)\\.Cmd.;', line)
                if match:
                    sensors.append(Sensor(device_dict['name'].lower(), flair_cmd_dict[match.group('cmd')].id,match.group('name'),"Current"+match.group('name_current'),value_type_dict[match.group('unit')],match.group('update_rate')))
                    continue

            device_dict["sensors"] = sensors
            device = DeviceSensor(**device_dict)
            dict_devices_sensor[device.name.lower()] = device

    return dict_devices_sensor