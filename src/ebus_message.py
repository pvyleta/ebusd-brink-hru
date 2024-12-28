from parse_xaml import get_name

MSG_TYPE_WRITE = 'w'
MSG_TYPE_READ = 'r'


def multiplier_to_divider(multiplier: float) -> str:
    if multiplier < 1.0:
        return str(int(1 / multiplier))
    elif multiplier > 1.0:
        return str(-int(multiplier))
    else:
        return ""
    
def pad_hex_string_from_number(number: int):
    hex_string = f'{number:x}'
    # Add a leading zero if the length is odd
    if len(hex_string) % 2 != 0:
        hex_string = '0' + hex_string
    return hex_string

class Field:
    def __init__(self, name: str, datatype: str, length: int, multiplier: float, values: str, unit: str, comment: str = ''):
        self.name: str = name
        self.datatype: str = datatype
        self.length: int = length
        self.multiplier: float = multiplier
        self.values: str = values
        self.unit: str = unit
        self.comment: str = comment

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
    def __init__(self, name: str, parameter_name: str, pbsb: int, id: int|None, type: str, fields: list[Field], suffix: str = ''):
        self.name: str = name
        self.pbsb: int = pbsb
        self.id: int|None = id
        self.type: str = type
        self.fields: list[Field] = fields
        self.parameter_name = parameter_name # This one is necessary for correct translation
        self.suffix = suffix

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
    
    def dump(self, language: str, circuit: str = '', slave_address: str = '') -> str:
        # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
        id_str = pad_hex_string_from_number(self.id) if self.id else ''
        result = f'{self.type},{circuit},{get_name(self.parameter_name, language)}{self.suffix},{self.name},,{slave_address},{self.pbsb:04x},{id_str}'
        for field in self.fields:
            values_str = multiplier_to_divider(field.multiplier) if field.values == '' else field.values 
            result += f',{field.name},,{field.datatype},{values_str},{field.unit},{field.comment}'
        return result + '\n'


class BrinkConfigEbusMessage(EbusMessage):
    def __init__(self, name: str, parameter_name: str, id: int, type: str, is_signed: bool, multiplier: float, values: str, unit: str, suffix: str = ''):
        field_names = ['', 'min', 'max', 'step', 'default']
        self.name = name
        self.id = id
        self.type = type
        self.parameter_name = parameter_name # This one is necessary for correct translation
        self.suffix = suffix
        
        if is_signed:
            datatype = 'SIR'
        else:
            datatype = 'UIR'

        self.fields = []
        if type == MSG_TYPE_WRITE:
            self.pbsb = 0x4080
            self.fields.append(Field('', datatype, 2, multiplier, values, unit))
        elif type == MSG_TYPE_READ:
            self.pbsb = 0x4050
            if values == '':
                for field_name in field_names:
                    self.fields.append(Field(field_name, datatype, 2, multiplier, values, unit))
            else:
                self.fields.append(Field('', datatype, 2, multiplier, values, unit))
                self.fields.append(Field('', 'IGN:6', 6, 1.0, '', ''))
                self.fields.append(Field('default', datatype, 2, multiplier, values, unit))
        else:
            raise RuntimeError()


brink_wtw_commands_list: list[EbusMessage] = [
    # Factory reset is a write to address 40FF with no ID and a string "FactoryReset" in ascii -> "40FF0C466163746F72795265736574"
    # EbusMessage('FactoryReset', 0x40ff, None, 'w', [Field('', 'STR:12', 12, 1.0, '0x466163746F72795265736574=FactoryReset', '')]),
    EbusMessage('FactoryReset', 'diagnosticsViewbtnFactoryReset', 0x40ff, 0x466163746F72795265736574, 'w', []),

    # Filter and error reset is split to two messages - one for writing and one for reading. I am unaware how to otherwise specify this so that MQTT would understand this Command-Response type of message
    # ru,,ResetErrors,409103FFFFFF,,,4091,3c0001,,,UIR,0=ResetNotRequested;1=ResetSuccessful;2=ResetRelayed;3=NoErrorsFound;4=ResetFailed;5=BlockingErrors,,,,,IGN:2,,,
    # ru,,ResetFilter,409103FFFFFF,,,4091,3c0100,,,IGN:1,,,,,,UIR,0=ResetNotRequested;1=ResetSuccessful;2=ResetRelayed;3=FilterWarningWasNotSet;4=ResetFailed,,,,,IGN:1,,, 
      
    # Reset notification logic and response codes is based on HandleResetNotificationsResponse function from BCSServiceTool
    EbusMessage('ResetNotifications', 'ResetNotificationDialogTitle', 0x4091, 0x00, 'w', [Field('', 'UIR', 2, 1.0, '0x0100=Errors;0x0001=Filter;0x0101=ErrorsAndFilter;0x0000=NoResetRequested', '', 'NoResetRequested is a dummy message doing nothing. It might be useful for integration in MQTT and HA automation. ErrorsAndFilter seems not working for me - but is specified.')]),
    
    EbusMessage('RequestErrorList', 'errorHistoryViewTableTitle', 0x4090, 0x00, 'r', [Field('', 'HEX:18', 18, 1.0, '', '')]),

    # This one is only temporary and resets after one or two minutes 
    EbusMessage('FanMode', 'parameterDescriptionFanMode', 0x40a1, None, 'w', [Field('', 'ULR', 4, 1.0, '0x0=Holiday;0x00010001=Reduced;0x00020002=Normal;0x00030003=High', '', 'Temporary settings which resets after few minutes')]),
    
    # This one does not reset after one minute, at least in my Sky300 with latest SW; this is the message sent by Brink AirControl wall panel
    EbusMessage('FanModeAlternative', 'parameterDescriptionFanMode', 0x40cb, 0x0101, 'w', [Field('', 'UIR', 1, 1.0, '0=Holiday;1=Reduced;2=Normal;3=High', '', 'Does not reset after one minute with Sky300 with latest SW; this message is sent by Brink AirControl wall panel')], 'Alternative'),
    
    # The following message simply does not work. The last IGN bytes clearly can be zeroes only sometimes, in general they need to be filed with some value that I was not able to decode the meaning.
    # EbusMessage('FanMode', 'parameterDescriptionFanMode',0x40a3, 0x01, 'w', [Field('', 'UCH', 1, 1.0, '0=Holiday;1=Reduced;2=Normal;3=High', ''), Field('', 'IGN:2', 2, 1.0, '', '')]),
    
    # This is readable on Sky300, but it is virtual dpswitch on flair units, and seems to have no use elsewhere - definitely unable to figure out what it could mean...
    # BrinkConfigEbusMessage('DeviceType', 'parameterDescriptionDeviceType', 0x00, 'r', False, 1.0, '', ''),

    # ## Control Commands - No further knowledge of meaning, or list of compatible units
    # w,,ApplianceCascade,ApplianceCascade,,,40A0,,,,HEX:4,,,
    # w,,ApplianceStatus,ApplianceStatus,,,40A1,,,,HEX:6,,,

    # # WTWCommandControlMode_HandleResponse sends 0x03 - can we figure out the meaning?
    # w,,WTWControlMode,WTWControlMode,,,40A2,,,,UCH,,,
    # w,,WTWControlDemandStatus,WTWControlDemandStatus,,,40A3,,,,HEX:4,,,
    
    BrinkConfigEbusMessage('FilterNotificationFlow', 'parameterSetDescriptionFilterMaximumFlow',0x1c, 'r', False, 1000, '', 'm³'),
    BrinkConfigEbusMessage('TotalFilterDays', 'parameterDescriptionFiltersUsedInDays', 0x22, 'r', False, 1.0, '', 'Days'),
    
    # Note: there is also parameterDescriptionFiltersUsedIn1000M3, but that is unnecessary, since we already factored in the 1000 multiplier
    BrinkConfigEbusMessage('TotalFilterFlow', 'parameterDescriptionFiltersUsedInM3', 0x23, 'r', False, 1000,'',  'm³'),

    # Based on https://github.com/dstrigl/ebusd-config-brink-renovent-excellent-300 and my obervation, the multiplier mathches; Contrary to what WTWCommands.cs says, the ID is mixed up between OperatingHours and TotalFlow
    BrinkConfigEbusMessage('TotalOperatingHours', 'parameterDescriptionOperatingTime', 0x24, 'r', False, 5,'',  'Hours'),

    # Based on https://github.com/dstrigl/ebusd-config-brink-renovent-excellent-300 and my obervation, the multiplier mathches; Contrary to what WTWCommands.cs says, the ID is mixed up between OperatingHours and TotalFlow
    # Note: there is also parameterDescriptionTotalFlowIn1000M3, but that is unnecessary, since we already factored in the 1000 multiplier
    BrinkConfigEbusMessage('TotalFlow', 'parameterDescriptionTotalFlowInM3', 0x25, 'r', False, 1000, '', 'm³'), 

    # Note: Following messages were tested, but are not present on SKY300:
    # - ActualEBusAddressing = "40220150";
    # - ActualSerialNumber = "40220151";
    # - ActualDeviceID = "40220180";
    # - ActualOperatingTime = "40220183";
    # - ParameterEBusGroupNumber = "405001D0";
    # - ParameterEBusSlaveNumber = "405001D1";
    # - ParameterHeartBeatTimeout = "405001D2";
]