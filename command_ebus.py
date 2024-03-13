import re
import glob

import params
import dev

class CommandEBus:
    def __init__(self, cmd: str, pbsb: str, len: str, id: str, write_len: str, read_len: str):
        self.cmd = cmd
        self.pbsb = pbsb
        self.len = len
        self.id = id
        self.write_len = write_len
        self.read_len = read_len
    
    def __str__(self):
        return str([vars(self)[key] for key in sorted(vars(self).keys())])
    def __eq__(self, other):
        return str(self) == str(other)
    def __hash__(self):
        return hash(str(self))
    def __repr__(self):
        return str(self)

def get_commands_dict_for_file(name: str) -> tuple[dict[str, CommandEBus], dict[str, CommandEBus]]:
    cmd_dict: dict[str, CommandEBus] = {}
    cmd_bytes_dict: dict[str, CommandEBus] = {}
    with open(f'./BCSServiceTool/BusinessLogic/Commands/{name}EBusCommands.cs') as f:
        datafile = f.readlines()
        for line in datafile:
            #     public static CommandEBus CmdReadActualSoftwareVersion = new CommandEBus("40220100", (ushort) 0, 15U);
            match = re.search('public static CommandEBus (?P<cmd>.*) = new CommandEBus."(?P<pbsb>....)(?P<len>..)(?P<id>.*)", .* (?P<write_len>.*), (?P<read_len>.*)U.;', line)
            if match:
                cmd = CommandEBus(match.group('cmd'),match.group('pbsb'),match.group('len'),match.group('id'),match.group('write_len'),match.group('read_len'))
                command_bytes = cmd.pbsb + cmd.len + cmd.id
                
                assert cmd.cmd not in cmd_dict
                assert command_bytes not in cmd_bytes_dict

                cmd_dict[cmd.cmd] = cmd
                cmd_bytes_dict[command_bytes] = cmd

    return cmd_dict, cmd_bytes_dict