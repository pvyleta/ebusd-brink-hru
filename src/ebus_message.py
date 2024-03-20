MSG_TYPE_WRITE = 'w'
MSG_TYPE_READ = 'r'


def multiplier_to_divider(multiplier: float) -> str:
    if multiplier < 1.0:
        return str(int(1 / multiplier))
    elif multiplier > 1.0:
        return str(-int(multiplier))
    else:
        return ""

class Field:
    def __init__(self, name: str, datatype: str, length: int, multiplier: float, values: str, unit: str):
        self.name: str = name
        self.datatype: str = datatype
        self.length: int = length
        self.multiplier: float = multiplier
        self.values: str = values
        self.unit: str = unit

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

class EbusMessage:
    def __init__(self, name: str, pbsb: int, id: int|None, type: str, fields: list[Field]):
        self.name: str = name
        self.pbsb: int = pbsb
        self.id: int|None = id
        self.type: str = type
        self.fields: list[Field] = fields

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
    
    def dump(self, circuit: str = '', slave_address: str = '') -> str:
        # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
        id_str = f'{self.id:02x}' if self.id else ''
        result = f'{self.type},{circuit},{self.name},,,{slave_address},{self.pbsb:04x},{id_str}'
        for field in self.fields:
            values_str = multiplier_to_divider(field.multiplier) if field.values == '' else field.values 
            result += f',{field.name},,{field.datatype},{values_str},{field.unit},'
        return result + '\n'


class BrinkConfigEbusMessage(EbusMessage):
    def __init__(self, name: str, id: int, type: str, is_signed: bool, multiplier: float, values: str, unit: str):
        field_names = ['', 'Min', 'Max', 'Step', 'Default']
        self.name = name
        self.id = id
        self.type = type
        
        if is_signed:
            datatype = 'SIR'
        else:
            datatype = 'UIR'

        self.fields = []
        if type == MSG_TYPE_WRITE:
            self.pbsb = 0x4080
            self.fields.append(Field('', datatype, 2, multiplier, values, unit))
        else:
            self.pbsb = 0x4050
            if values == '':
                for field_name in field_names:
                    self.fields.append(Field(field_name, datatype, 2, multiplier, values, unit))
            else:
                self.fields.append(Field('', datatype, 2, multiplier, values, unit))
                self.fields.append(Field('', 'IGN:6', 6, 1.0, '', ''))
                self.fields.append(Field('Default', datatype, 2, multiplier, values, unit))

## TODO what if ru message has the same name? then this could work...
## Filter and error reset is split to two messages - one for writing and one for reading. I am unaware how to otherwise specify this so that MQTT would understand this Command-Response type of message ##
## Reset notification logic and response codes is base on HandleResetNotificationsResponse function from BCSServiceTool
#ru,,ResetErrors,409103FFFFFF,,,4091,3c0001,,,UIR,0=ResetNotRequested;1=ResetSuccessful;2=ResetRelayed;3=NoErrorsFound;4=ResetFailed;5=BlockingErrors,,,,,IGN:2,,,
#ru,,ResetFilter,409103FFFFFF,,,4091,3c0100,,,IGN:1,,,,,,UIR,0=ResetNotRequested;1=ResetSuccessful;2=ResetRelayed;3=FilterWarningWasNotSet;4=ResetFailed,,,,,IGN:1,,,
#w,,ResetNotifications,409103FFFFFF,,,4091,3c,,,UIR,0x0001=Errors;0x0100=Filter,,

# TODO Check if the fields are writable - especially the filter threshhold
brink_wtw_commands_list: list[EbusMessage] = [
    EbusMessage('ResetNotifications', 0x4091, 0x00, 'w', [Field('', 'UIR', 2, 1.0, '0x0001=Errors;0x0100=Filter', '')]),
    EbusMessage('RequestErrorList', 0x4090, 0x00, 'r', [Field('', 'HEX:18', 18, 1.0, '', '')]),
    EbusMessage('FanMode', 0x40a1, None, 'w', [Field('', 'ULR', 4, 1.0, '0x0=Min;0x00010001=Low;0x00020002=Medium;0x00030003=High', '')]),
    # The following message simply does not work. The last IGN bytes clearly can be zeroes only sometimes, in general they need to be filed with some value that I was nto able to decode the meaning.
    # EbusMessage('FanMode', 0x40a3, 0x01, 'w', [Field('', 'UCH', 1, 1.0, '0=Min;1=Low;2=Medium;3=High', ''), Field('', 'IGN:2', 2, 1.0, '', '')]),
    # This one look like not present on Sky300
    # BrinkConfigEbusMessage('DeviceType', 0x00, 'r', False, 1.0, '', ''),
    BrinkConfigEbusMessage('FilterNotificationFlow', 0x1c, 'r', False, 1000, '', 'm³'),
    BrinkConfigEbusMessage('TotalFilterDays', 0x22, 'r', False, 1.0, '', 'Days'),
    BrinkConfigEbusMessage('TotalFilterFlow', 0x23, 'r', False, 1000,'',  'm³'),

    # Based on https://github.com/dstrigl/ebusd-config-brink-renovent-excellent-300 and my obervation, the multiplier mathches; Contrary to what WTWCommands.cs says, the ID is mixed up between OperatingHours and TotalFlow
    BrinkConfigEbusMessage('TotalOperatingHours', 0x24, 'r', False, 5,'',  'Hours'),

    # Based on https://github.com/dstrigl/ebusd-config-brink-renovent-excellent-300 and my obervation, the multiplier mathches; Contrary to what WTWCommands.cs says, the ID is mixed up between OperatingHours and TotalFlow
    BrinkConfigEbusMessage('TotalFlow', 0x25, 'r', False, 1000, '', 'm³'), 
]
        

raw_ebusd_config = '''
# type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment,field2,part (m/s),datatypes/templates ,divider/values,unit,comment,field3,part (m/s),datatypes/templates,divider/values,unit,comment,field4,part (m/s),datatypes/templates,divider/values,unit,comment,field5,part (m/s),datatypes/templates,divider/values,unit,comment
## Read commands from WTWCommands.cs, search '.*CmdRead(.*) = "(....)01(..).*', replace 'r,,$1,$1,,,$2,$3,,,SIR,,,'
## Write commands from WTWCommands.cs, search '.*CmdWrite(.*) = "(....)03(..)FFFF.*', replace 'w,,$1,$1,,,$2,$3,,,SIR,,,'
## Test commands from WTWCommands.cs, search '.*CmdTestCommand(.*) = "(....)03(..).*', replace 'w,,TestCommand$1,TestCommand$1,,,$2,$3,,,HEX:2,,,'

## These commands are based on contents of WTWCommands.cs. There is more commands in that file, but the following subset looks useful and implemented by Renovent units. Flair units and/or other devices might differ.

*r,sky300,,,,3c,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
# Request Error - ID taken from capture of what air control sends
r,,RequestErrorList,RequestErrorList,,,4090,00,,,HEX:18,,,

r,,ParameterFilterNotificationFlow,ParameterFilterNotificationFlow,,,4050,1C,,,UIR,-1000,m³,
r,,ParameterActualFilterDays,ParameterActualFilterDays,,,4050,22,,,UIR,,,,min,,UIR,,,,max,,UIR,,,,step,,UIR,,,,default,,UIR,,
r,,ParameterActualFilterFlow,ParameterActualFilterFlow,,,4050,23,,,UIR,-1000,m³,,min,,UIR,-1000,m³,,max,,UIR,-1000,m³,,step,,UIR,-1000,m³,,default,,UIR,-1000,m³,

# Based on https://github.com/dstrigl/ebusd-config-brink-renovent-excellent-300 and my obervation, the multiplier mathches; Contrary to what WTWCommands.cs says, the ID is mixed up between OperatingHours and TotalFlow
r,,ParameterOperatingHours,ParameterOperatingHours,,,4050,24,,,UIR,-5,h,,min,,UIR,-5,h,,max,,UIR,-5,h,,step,,UIR,-5,h,,default,,UIR,-5,h,

# Based on https://github.com/dstrigl/ebusd-config-brink-renovent-excellent-300 and my obervation, the multiplier mathches; Contrary to what WTWCommands.cs says, the ID is mixed up between OperatingHours and TotalFlow
r,,ParameterTotalFlow,ParameterTotalFlow,,,4050,25,,,UIR,-1000,m³,,min,,UIR,-1000,m³,,max,,UIR,-1000,m³,,step,,UIR,-1000,m³,,default,,UIR,-1000,m³,

#### CHANGE FAN MODE ####
w,,FanMode,,,,40a1,,,,ULR,0x0=Min;0x00010001=Low;0x00020002=Medium;0x00030003=High,,,,,IGN:2
w,,FanMode,,,,40a3,01,,,UCH,0=Min;1=Low;2=Medium;3=High,,,,,IGN:2

## Filter and error reset is split to two messages - one for writing and one for reading. I am unaware how to otherwise specify this so that MQTT would understand this Command-Response type of message ##
## TODO Check and explain this from code
## TODO what if ru message has the same name? then this could work...
ru,,ResetErrors,409103FFFFFF,,,4091,3c0001,,,UIR,0=ResetNotRequested;1=ResetSuccessful;2=ResetRelayed;3=NoErrorsFound;4=ResetFailed;5=BlockingErrors,,,,,IGN:2,,,
ru,,ResetFilter,409103FFFFFF,,,4091,3c0100,,,IGN:1,,,,,,UIR,0=ResetNotRequested;1=ResetSuccessful;2=ResetRelayed;3=FilterWarningWasNotSet;4=ResetFailed,,,,,IGN:1,,,
w,,ResetNotifications,409103FFFFFF,,,4091,3c,,,UIR,0x0001=Errors;0x0100=Filter,,
'''

