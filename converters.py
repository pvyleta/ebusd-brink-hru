import glob
import re
import copy

# TODO Add note to converters that were filled manually

# All converters from BCSServiceTool/Converters
list_converters = [
    "BooleanToColorConverter",
    "BooleanToVisibilityConverter",
    "ByteArrayToStringConverter",
    "EnumMatchToBooleanConverter",    
    "Int16ToPercentageFact10Converter",
    "Int16ToTemperatureConverterFact10",
    "Int16ToTemperatureFact100Converter",
    "Int16ToVoltageConverterFact10",
    "Int16vStringConverter",
    "Int32vStringConverter",
    "ResetErrorListResultConverter",
    "ResetFilterResultConverter",
    "UInt16ToAir70FanStatusConverter",
    "UInt16ToAir70SystemStatus_02Converter",
    "UInt16ToAir70VentilationMode_02Converter",
    "UInt16ToAllureBlockingStatusConverter",
    "UInt16ToAllureHeatDemandStatusConverter",
    "UInt16ToBypassStatusConverter",
    "UInt16ToCO2SensorStatusConverter",
    "UInt16ToContactConverter",
    "UInt16ToEBusPowerStateConverter",
    "UInt16ToElanFanStatusConverter",
    "UInt16ToElanFrostStatusConverter",
    "UInt16ToElanStatusConverter",
    "UInt16ToEWTStatusConverter",
    "UInt16ToFanCtrlTypeOldFlairConverter",
    "UInt16ToFanModeConverter",
    "UInt16ToFanStatusConverter",
    "UInt16ToFanSwitchConverter",
    "UInt16ToFilterStateConverter",
    "UInt16ToFlairFrostStatusConverter",
    "UInt16ToFrostStatusConverter",
    "UInt16ToHeaterStatusConverter",
    "UInt16ToHeaterStatusOldFlairConverter",
    "UInt16ToHumidityBoostStateConverter",
    "UInt16ToModbusFanStatusConverter",
    "UInt16ToMRCDeviceStatusConverter",
    "UInt16ToMRCStatusConverter",
    "UInt16ToOnOffConverter",
    "UInt16ToPercentageConverter",
    "UInt16ToPresenceConverter",
    "UInt16ToPressureConverter",
    "UInt16ToPressureBarFact256Converter",
    "UInt16ToRotateDirectionConverter",
    "UInt16ToSystemStatusConverter",
    "UInt16ToTemperatureConverter",
    "UInt16ToTemperatureFact10Converter",
    "UInt16ToTemperatureFact16Converter",
    "UInt16ToUNumberConverter",
    "UInt16ToValveStatusConverter",
    "UInt16ToVentilationModeConverter",
    "UInt16ToWTWFunctionConverter",
    "UInt32ToUNumberConverter",
    "UInt32vStringConverter",
    "UnitTypeToStringConverter",
]


class Converter:
    def __init__(self, type, multiplier, length, values, name_actual=None):
        self.name = None
        self.type = type
        self.multiplier = multiplier
        self.length = length
        self.values = values
        self.name_actual = None

    def set_match_type(self, match_type):
        self.match_type = match_type
    
    def set_name_actual(self, name_actual):
        self.name_actual = name_actual

    def __eq__(self, other):
        return vars(self) == vars(other)
    
    def __str__(self):
        return str(vars(self))
    
    def __hash__(self):
        return hash(str(self))


# Based on the converters from BCServiceTool/Converters; formated for ebusd
        # TODO the convertion between '[]Converter' and 'Converter[]' is not 1:1 and should be done per-file - especially for the elan and flair units e.g. frost is different.
        #     "UInt16ToMRCDeviceStatusConverter": Converter("UIR", 1, "0=NotInConfig;1=NotFound;2=Error;3=OK"),

        # TODO filter state converter is largely unused which is a shame
        #     "UInt16ToFilterStateConverter": Converter("UIR", 1, "0=Clean;1=Dirty"),
converters_map = {
    "Int16ToPercentageFact10Converter": Converter("SIR", 10, 2, ""),
    "Int16ToTemperatureConverterFact10": Converter("SIR", 10, 2, ""),
    "Int16ToVoltageConverterFact10": Converter("SIR", 10, 2, ""),
    "UInt16ToBypassStatusConverter": Converter("UIR", 1, 2, "0=Initializing;1=Opening;2=Closing;3=Open;4=Closed;5=Error,6=Calibrating;255=Error"),
    "UInt16ToCO2SensorStatusConverter": Converter("UIR", 1, 2, "0=Error;1=NotInitialized;2=Idle;3=WarmingUp;4=Running;5=Calibrating;6=SelfTest"),
    "UInt16ToContactConverter": Converter("UIR", 1, 2, "0=Open;1=Closed"),
    "UInt16ToEBusPowerStateConverter": Converter("UIR", 1, 2, "0=PowerUp;1=Initialize;2=PowerOff;3=PowerOn;4=WaitForPowerOff;5=SlavePowerOff;255=Error"),
    "UInt16ToEWTStatusConverter": Converter("UIR", 1, 2, "0=OpenLow;1=Closed;2=OpenHigh"),
    "UInt16ToFanModeConverter": Converter("UIR", 1, 2, "0=Holiday;1=Reduced;2=Normal;3=High;4=Auto"),
    "UInt16ToFanStatusConverter": Converter("UIR", 1, 2, "0=Initializing;1=ConstantFlow;2=ConstantPWM;3=Off;4=Error;5=MassBalance;6=Standby;7=ConstantRPM"),
    "UInt16ToFanSwitchConverter": Converter("UIR", 1, 2, "0=Position_0;1=Position_1;2=Position_2;3=Position_3;"),
    "UInt16ToFrostStatusConverter": Converter("UIR", 1, 2, "0=Initializing;1=NoFrost;17=NoFrost;2=DefrostWait;3=Preheater;18=Preheater;255=Error;5=VeluHeater;6=VeluFanCtrl;7=TableFanCtrl;19=TableFanCtrl;8=Sky150Heater;9=FanCtrlFanOff;10=FanCtrlFanRestart;11=FanCtrlCurve1;12=FanCtrlCurve2;13=FanCtrlCurve3;14=FanCtrlCurve4;15=HeaterCoolDown;16=Blocked"),
    "UInt16ToHeaterStatusConverter": Converter("UIR", 1, 2, "0=Initializing;1=Off;2=On"),
    "UInt16ToHumidityBoostStateConverter": Converter("UIR", 1, 2, "0=Error;1=NotInitialized;2=SensorNotActive;3=PowerUpDelay;4=NormalRH;5=BoostRising;6=BoostStable;7=BoostDecending;8=BoostRHLowLevelStable"),
    "UInt16ToMRCStatusConverter": Converter("UIR", 1, 2, "0=Error;1=NotInitialized;2=Idle;3=PowerUp;4=Running"),
    "UInt16ToModbusFanStatusConverter": Converter("UIR", 1, 2, "0=NotInitialized;2=NoCommunication;3=Idle;4=Running;5=Blocked;6=Error"),
    "UInt16ToOnOffConverter": Converter("UIR", 1, 2, "0=Off;1=On"),
    "UInt16ToPercentageConverter": Converter("UIR", 1, 2, ""),
    "UInt16ToPressureConverter": Converter("UIR", 1, 2, ""),
    "UInt16ToRotateDirectionConverter": Converter("UIR", 1, 2, "0=CW;1=CCW"),
    "UInt16ToUNumberConverter": Converter("UIR", 1, 2, ""),
    "UInt16ToValveStatusConverter": Converter("UIR", 1, 2, "0=Error;1=NotInitialized;2=NotCalibrated;3=Traveling;4=InPosition;5=Calibrating"),
    "UInt16ToWTWFunctionConverter": Converter("UIR", 1, 2, "0=Standby;1=Bootloader;2=NonBlockingError;3=BlockingError;4=MAnual;5=Holiday;6=NightVentilation;7=Party;8=BypassBoost;9=NormalBoost;10=AutoCO2;11=AutoEBus;12=AutoModbus;13=AutoLanWLanPortal;14=AutoLanWLanLocal"),
    "UInt32ToUNumberConverter": Converter("ULR", 1, 4, ""),
    
    "default": Converter("HEX:*", 1, 0, ""),
    "unknown": Converter("SIR", 1, 2, ""),

    # TODO figure out if these converters are used
    "UInt16ToSystemStatusConverter": Converter("", -1, -1, ""),
    "UInt16ToVentilationModeConverter": Converter("", -1, -1, ""),
    "UInt16ToAir70FanStatusConverter": Converter("", -1, -1, ""),
    "UInt16ToElanStatusConverter": Converter("", -1, -1, ""),
    "UInt16ToElanFanStatusConverter": Converter("", -1, -1, ""),
    "UInt16ToFilterStateConverter": Converter("", -1, -1, ""),
    "UInt16ToElanFrostStatusConverter": Converter("", -1, -1, ""),
    "UInt16ToMRCDeviceStatusConverter": Converter("", -1, -1, ""),
}

def find_converters():
    files_converters = glob.glob('./BCSServiceTool/View/Devices/**/*Actual*.xaml', recursive=True)
    device_to_name_param_to_converter = {}
    converters_str = "|".join(list_converters)

    # filter out only the device-specific files and retrieve the device name
    for file in files_converters:
        match = re.search(f'BCSServiceTool/View/Devices.*\\\\(?P<name>\\w+)actual.*view_...xaml$', file)
        if match:
            device_name_lower = match.group('name').lower()
            device_to_name_param_to_converter.setdefault(device_name_lower, {})
        else:
            print("converter: skipping file " + file)
            continue

        with open(file) as f:
            file_str = f.read().replace('\n', ' ')

            # <my:ParameterField Name="paramDipswitch" Height="28" Grid.Column="1" Grid.ColumnSpan="3" Grid.Row="6"
            #                    HorizontalAlignment="Left" VerticalAlignment="Top" ColumnWidthName="160" ColumnWidthValue="100"
            #                    ColumnWidthUnit="5"
            #                    FieldValue="{Binding Path=ActualDipSwitch, Converter={StaticResource UInt16ToUNumberConverter}}"
            #                    FieldStatus="{Binding Path=ActualDipSwitchStatus}"/>

            matches = re.finditer(f'<my:ParameterField Name="(?P<name_param>\\w*)"([^<>]*)FieldValue="{{Binding Path=(?P<name_actual>\\w*), Converter={{StaticResource (?P<converter>{converters_str})}}', file_str)
            for m in matches:
                if m:
                    name_param = m.group('name_param')
                    converter = copy.deepcopy(converters_map[m.group('converter')])
                    converter.set_name_actual(m.group('name_actual'))

                    device_to_name_param_to_converter[device_name_lower][name_param] = converter

            matches = re.finditer(f'<my:ParameterField Name="(?P<name_param>\\w*)"([^<>]*)FieldValue="{{Binding Path=(?P<name_actual>\\w*)}}', file_str)
            for m in matches:
                if m:
                    name_param = m.group('name_param')
                    converter = copy.deepcopy(converters_map["default"])
                    converter.set_name_actual(m.group('name_actual'))
                    
                    device_to_name_param_to_converter[device_name_lower][name_param] = converter
    
    return device_to_name_param_to_converter

def device_to_name_current_to_name_param():
    device_to_name_current_to_name_param_dict = {}
    files = glob.glob('./BCSServiceTool/View/Devices/**/*Actual*.xaml.cs', recursive=True)
    for file in files:
        # Matches the name - name can be identified as the repeated string in the file name
        match = re.search(r'(\w{3,}?)\1+(.*)', file)
        if not match:
            print("converter: skipping file " + file)
            continue

        name = match.group(1).lower()

        # Special case of Nather300 being in Nather dir breaking pattern for any other HRU
        if name == "nather":
            name += "300"
        
        device_to_name_current_to_name_param_dict.setdefault(name, {})

        with open(file) as f:
            datafile = f.readlines()
            for line in datafile:
                # this.paramExtContact1.ParameterName = this.FindResource((object) this._viewModel.ModelFlairParameterData.CurrentExtContact1Position.Description).ToString();
                match = re.search(r'this\.(?P<name_param>.*)\.ParameterName = this.FindResource..object. this._viewModel\..*\.(?P<name_current>.*)\.Description', line)
                if match:
                    device_to_name_current_to_name_param_dict[name][match.group('name_current')] = match.group('name_param')
                                
    return device_to_name_current_to_name_param_dict