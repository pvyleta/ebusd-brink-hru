import glob
import re
import copy


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

list_converters_files = [
    "ConverterBooleanToColor",
    "ConverterBooleanToVisibility",
    "ConverterByteArrayToString",
    "ConverterEnumMatchToBoolean",
    "ConverterInt16ToPercentageFact10",
    "ConverterInt16ToTemperatureFact10",
    "ConverterInt16ToTemperatureFact100",
    "ConverterInt16ToVoltageFact10",
    "ConverterInt16vString",
    "ConverterInt32vString",
    "ConverterResetErrorListResult",
    "ConverterResetFilterResult",
    "ConverterUInt16ToAir70FanStatus",
    "ConverterUInt16ToAir70SystemStatus_02",
    "ConverterUInt16ToAir70VentilationMode_02",
    "ConverterUInt16ToAllureBlockingStatus",
    "ConverterUInt16ToAllureHeatDemandStatus",
    "ConverterUInt16ToBypassStatus",
    "ConverterUInt16ToCO2SensorStatus",
    "ConverterUInt16ToContact",
    "ConverterUInt16ToEBusPowerState",
    "ConverterUInt16ToElanFanStatus",
    "ConverterUInt16ToElanFrostStatus",
    "ConverterUInt16ToElanStatus",
    "ConverterUInt16ToEWTStatus",
    "ConverterUInt16ToFanCtrlTypeOldFlair",
    "ConverterUInt16ToFanMode",
    "ConverterUInt16ToFanStatus",
    "ConverterUInt16ToFanSwitch",
    "ConverterUInt16ToFilterState",
    "ConverterUInt16ToFlairFrostStatus",
    "ConverterUInt16ToFrostStatus",
    "ConverterUInt16ToHeaterStatus",
    "ConverterUInt16ToHeaterStatusOldFlair",
    "ConverterUInt16ToHumidityBoostState",
    "ConverterUInt16ToModbusFanStatus",
    "ConverterUInt16ToMRCDeviceStatus",
    "ConverterUInt16ToMRCStatus",
    "ConverterUInt16ToOnOff",
    "ConverterUInt16ToPercentage",
    "ConverterUInt16ToPresence",
    "ConverterUInt16ToPressure",
    "ConverterUInt16ToPressureBarFact256",
    "ConverterUInt16ToRotateDirection",
    "ConverterUInt16ToSystemStatus",
    "ConverterUInt16ToTemperature",
    "ConverterUInt16ToTemperatureFact10",
    "ConverterUInt16ToTemperatureFact16",
    "ConverterUInt16ToUNumber",
    "ConverterUInt16ToValveStatus",
    "ConverterUInt16ToVentilationMode",
    "ConverterUInt16ToWTWFunction",
    "ConverterUInt32ToUNumber",
    "ConverterUInt32vStcsring",
    "ConverterUnitTypeToString",
]
class Converter:
    def __init__(self, name, type, multiplier, length, values, name_actual=None):
        self.name = name
        self.type = type
        self.multiplier = multiplier
        self.length = length
        self.values = values
        self.name_actual = None
        self.converter_str = None

    def set_match_type(self, match_type):
        self.match_type = match_type
    
    def set_name_actual(self, name_actual):
        self.name_actual = name_actual

    def set_converter_str(self, converter_str):
        self.converter_str = converter_str

    def __eq__(self, other):
        return vars(self) == vars(other)
    
    def __str__(self):
        return str(vars(self))
    
    def __hash__(self):
        return hash(str(self))

# Based on the converters from BCServiceTool/Converters; formated for ebusd
converters_map = {
    "ConverterInt16ToPercentageFact10": Converter("ConverterInt16ToPercentageFact10","SIR", 10, 2, ""),
    "ConverterInt16ToTemperatureFact10": Converter("ConverterInt16ToTemperatureFact10","SIR", 10, 2, ""),
    "ConverterInt16ToVoltageFact10": Converter("ConverterInt16ToVoltageFact10","SIR", 10, 2, ""),
    "ConverterUInt16ToBypassStatus": Converter("ConverterUInt16ToBypassStatus","UIR", 1, 2, "0=Initializing;1=Opening;2=Closing;3=Open;4=Closed;5=Error,6=Calibrating;255=Error"),
    "ConverterUInt16ToCO2SensorStatus": Converter("ConverterUInt16ToCO2SensorStatus","UIR", 1, 2, "0=Error;1=NotInitialized;2=Idle;3=WarmingUp;4=Running;5=Calibrating;6=SelfTest"),
    "ConverterUInt16ToContact": Converter("ConverterUInt16ToContact","UIR", 1, 2, "0=Open;1=Closed"),
    "ConverterUInt16ToEBusPowerState": Converter("ConverterUInt16ToEBusPowerState","UIR", 1, 2, "0=PowerUp;1=Initialize;2=PowerOff;3=PowerOn;4=WaitForPowerOff;5=SlavePowerOff;255=Error"),
    "ConverterUInt16ToEWTStatus": Converter("ConverterUInt16ToEWTStatus","UIR", 1, 2, "0=OpenLow;1=Closed;2=OpenHigh"),
    "ConverterUInt16ToFanMode": Converter("ConverterUInt16ToFanMode","UIR", 1, 2, "0=Holiday;1=Reduced;2=Normal;3=High;4=Auto"),
    "ConverterUInt16ToFanStatus": Converter("ConverterUInt16ToFanStatus","UIR", 1, 2, "0=Initializing;1=ConstantFlow;2=ConstantPWM;3=Off;4=Error;5=MassBalance;6=Standby;7=ConstantRPM"),
    "ConverterUInt16ToFanSwitch": Converter("ConverterUInt16ToFanSwitch","UIR", 1, 2, "0=Position_0;1=Position_1;2=Position_2;3=Position_3;"),
    "ConverterUInt16ToFrostStatus": Converter("ConverterUInt16ToFrostStatus","UIR", 1, 2, "0=Initializing;1=NoFrost;17=NoFrost;2=DefrostWait;3=Preheater;18=Preheater;255=Error;5=VeluHeater;6=VeluFanCtrl;7=TableFanCtrl;19=TableFanCtrl;8=Sky150Heater;9=FanCtrlFanOff;10=FanCtrlFanRestart;11=FanCtrlCurve1;12=FanCtrlCurve2;13=FanCtrlCurve3;14=FanCtrlCurve4;15=HeaterCoolDown;16=Blocked"),
    "ConverterUInt16ToHeaterStatus": Converter("ConverterUInt16ToHeaterStatus","UIR", 1, 2, "0=Initializing;1=Off;2=On"),
    "ConverterUInt16ToHumidityBoostState": Converter("ConverterUInt16ToHumidityBoostState","UIR", 1, 2, "0=Error;1=NotInitialized;2=SensorNotActive;3=PowerUpDelay;4=NormalRH;5=BoostRising;6=BoostStable;7=BoostDecending;8=BoostRHLowLevelStable"),
    "ConverterUInt16ToMRCStatus": Converter("ConverterUInt16ToMRCStatus","UIR", 1, 2, "0=Error;1=NotInitialized;2=Idle;3=PowerUp;4=Running"),
    "ConverterUInt16ToModbusFanStatus": Converter("ConverterUInt16ToModbusFanStatus","UIR", 1, 2, "0=NotInitialized;2=NoCommunication;3=Idle;4=Running;5=Blocked;6=Error"),
    "ConverterUInt16ToOnOff": Converter("ConverterUInt16ToOnOff","UIR", 1, 2, "0=Off;1=On"),
    "ConverterUInt16ToPercentage": Converter("ConverterUInt16ToPercentage","UIR", 1, 2, ""),
    "ConverterUInt16ToPressure": Converter("ConverterUInt16ToPressure","UIR", 1, 2, ""),
    "ConverterUInt16ToRotateDirection": Converter("ConverterUInt16ToRotateDirection","UIR", 1, 2, "0=CW;1=CCW"),
    "ConverterUInt16ToUNumber": Converter("ConverterUInt16ToUNumber","UIR", 1, 2, ""),
    "ConverterUInt16ToValveStatus": Converter("ConverterUInt16ToValveStatus","UIR", 1, 2, "0=Error;1=NotInitialized;2=NotCalibrated;3=Traveling;4=InPosition;5=Calibrating"),
    "ConverterUInt16ToWTWFunction": Converter("ConverterUInt16ToWTWFunction","UIR", 1, 2, "0=Standby;1=Bootloader;2=NonBlockingError;3=BlockingError;4=MAnual;5=Holiday;6=NightVentilation;7=Party;8=BypassBoost;9=NormalBoost;10=AutoCO2;11=AutoEBus;12=AutoModbus;13=AutoLanWLanPortal;14=AutoLanWLanLocal"),
    "ConverterUInt32ToUNumber": Converter("ConverterUInt32ToUNumber","ULR", 1, 4, ""),
    
    "default": Converter("default","HEX:*", 1, 0, ""),
    "unknown": Converter("unknown","SIR", 1, 2, ""),

    # TODO figure out if these converters are used - and if not, why?
    "ConverterUInt16ToAir70FanStatus": Converter("ConverterUInt16ToAir70FanStatus","UIR", 1, 2, ""),
    "ConverterUInt16ToAir70SystemStatus_02": Converter("ConverterUInt16ToAir70SystemStatus_02","UIR", 1, 2, ""),
    "ConverterUInt16ToAir70VentilationMode_02": Converter("ConverterUInt16ToAir70VentilationMode_02","UIR", 1, 2, ""),
    "ConverterUInt16ToElanFanStatus": Converter("ConverterUInt16ToElanFanStatus","UIR", 1, 2, ""),
    "ConverterUInt16ToElanFrostStatus": Converter("ConverterUInt16ToElanFrostStatus","UIR", 1, 2, ""),
    "ConverterUInt16ToElanStatus": Converter("ConverterUInt16ToElanStatus","UIR", 1, 2, ""),
    "ConverterUInt16ToFanCtrlTypeOldFlair": Converter("ConverterUInt16ToFanCtrlTypeOldFlair","UIR", 1, 2, "0=MassBalance;1=ConstantFlow;2=ConstantPWM"),
    
    # TODO filter state converter is largely unused in favor of UInt16ToOnOffConverter which is a shame
    "ConverterUInt16ToFilterState": Converter("ConverterUInt16ToOnOff","UIR", 1, 2, "0=Clean;1=Dirty"),
    "ConverterUInt16ToFlairFrostStatus": Converter("ConverterUInt16ToFlairFrostStatus","UIR", 1, 2, "0=Initializing;1=Initializing;2=NoFrost;3=NoFrostDelay;4=FrostCtrlStartDelay;5=WaitForIcing;6=IceDetectedDelay;7=Preheater;8=HeaterCoolDown;9=FanCtrlStartDelay;10=FanCtrlWait;11=FanCtrl;12=FanCtrlFanOffDelay;13=FanCtrlFanOff;14=FanCtrlFanRestart;15=Error;16=TestMode"),
    "ConverterUInt16ToHeaterStatusOldFlair": Converter("ConverterUInt16ToHeaterStatusOldFlair","UIR", 1, 2, "0=Off;1=On;2=LockedValue;3=LockedValueMaximum"),
    "ConverterUInt16ToMRCDeviceStatus": Converter("ConverterUInt16ToMRCDeviceStatus","UIR", 1, 2, ""),
    "ConverterUInt16ToSystemStatus": Converter("ConverterUInt16ToSystemStatus","UIR", 1, 2, ""),
    "ConverterUInt16ToVentilationMode": Converter("ConverterUInt16ToVentilationMode","UIR", 1, 2, ""),
}

def find_converters():
    files_converters = glob.glob('./BCSServiceTool/View/Devices/**/*actual*view_*.xaml', recursive=True)
    device_to_name_param_to_converter = {}
    converters_str = "|".join(list_converters)

    for file in files_converters:
        # retrieve the device name
        match = re.search(f'BCSServiceTool/View/Devices.*\\\\(?P<name>\\w+)actual.*view_...xaml$', file)
        device_name_lower = match.group('name').lower()
        device_to_name_param_to_converter.setdefault(device_name_lower, {})

        converter_dict = {}
        with open(file) as f:
            file_str = f.read().replace('\n', ' ')

            # Find the right Converter based on the referenced StaticResource string
            # <local:ConverterUInt16ToFanMode x:Key="UInt16ToFanModeConverter"/>
            matches = re.finditer(f'<local:(?P<converter_file>Converter\\w*) x:Key="(?P<converter_str>\\w*Converter\\w*)"/>', file_str)
            for m in matches:
                converter_str = m.group('converter_str')
                converter_file = m.group('converter_file')
                converter_dict[converter_str] = converter_file

            # <my:ParameterField Name="paramDipswitch" Height="28" Grid.Column="1" Grid.ColumnSpan="3" Grid.Row="6"
            #                    HorizontalAlignment="Left" VerticalAlignment="Top" ColumnWidthName="160" ColumnWidthValue="100"
            #                    ColumnWidthUnit="5"
            #                    FieldValue="{Binding Path=ActualDipSwitch, Converter={StaticResource UInt16ToUNumberConverter}}"
            #                    FieldStatus="{Binding Path=ActualDipSwitchStatus}"/>

            matches = re.finditer(f'<my:ParameterField Name="(?P<name_param>\\w*)"([^<>]*)FieldValue="{{Binding Path=(?P<name_actual>\\w*), Converter={{StaticResource (?P<converter_str>{converters_str})}}', file_str)
            for m in matches:
                name_param = m.group('name_param')
                converter_file = converter_dict[m.group('converter_str')]
                converter = copy.deepcopy(converters_map[converter_file])
                converter.set_name_actual(m.group('name_actual'))
                converter.set_converter_str(m.group('converter_str'))

                device_to_name_param_to_converter[device_name_lower][name_param] = converter

            matches = re.finditer(f'<my:ParameterField Name="(?P<name_param>\\w*)"([^<>]*)FieldValue="{{Binding Path=(?P<name_actual>\\w*)}}', file_str)
            for m in matches:
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