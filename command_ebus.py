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

def get_commands_dict() -> tuple[dict[str, CommandEBus], dict[str, CommandEBus]]:
    cmd_dict: dict[str, CommandEBus] = {}
    cmd_bytes_dict: dict[str, CommandEBus] = {}
    
    files = glob.glob(f'./BCSServiceTool/BusinessLogic/Commands/*EBusCommands.cs', recursive=True)
    for file in files:
        with open(file) as f:
            file_str = f.read()

            # public static class ElanEBusCommands
            match = re.search(r'public static class (?P<class_name>\w*)', file_str)
            class_name = match.group('class_name')
            
            #     public static CommandEBus CmdReadActualSoftwareVersion = new CommandEBus("40220100", (ushort) 0, 15U);
            matches = re.finditer(r'public static CommandEBus (?P<cmd>\w*) = new CommandEBus\("(?P<pbsb>....)(?P<len>..)(?P<id>[\w]*)", [^ ]* (?P<write_len>\d*), (?P<read_len>\d*)U\);', file_str)
            for m in matches:
                cmd_name = class_name + "." + m.group('cmd')
                cmd = CommandEBus(cmd_name,m.group('pbsb'),m.group('len'),m.group('id'),m.group('write_len'),m.group('read_len'))
                
                assert cmd_name not in cmd_dict
                cmd_dict[cmd_name] = cmd

                # For common commands, we also store them by raw 'bytes' value
                if "Common" in cmd_name:
                    command_bytes = cmd.pbsb + cmd.len + cmd.id
                    assert command_bytes not in cmd_bytes_dict
                    cmd_bytes_dict[command_bytes] = cmd

    return cmd_dict, cmd_bytes_dict