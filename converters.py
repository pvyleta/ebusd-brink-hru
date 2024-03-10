import glob
import re


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

def find_converters():
    # TODO we may need to extend this for 'allure' files
    # In these xaml files are the pairings between fields and the appropriate converters
    files_converters = glob.glob('./BCSServiceTool/View/Devices/**/*Actual*.xaml', recursive=True)
    device_to_sensor_to_converter = {}
    converters_str = "|".join(list_converters)

    # filter out only the device-specific files and retrieve the device name
    for file in files_converters:
        match = re.search(f'BCSServiceTool/View/Devices.*\\\\(?P<name>\\w+)actual.*view_...xaml$', file)
        if match:
            device_name_lower = match.group('name').lower()
            device_to_sensor_to_converter.setdefault(device_name_lower, {})
        else:
            print("converter: skipping file " + file)
            continue

        with open(file) as f:
            datafile = f.readlines()
            for line in datafile:
                    
                # strip potential "Actual" from the front to improve matching
                match = re.search(f'FieldValue=".Binding Path=(Actual)?(?P<converter_sensor>.*), Converter=.StaticResource (?P<converter>{converters_str})', line)
                if match:
                    converter_sensor = match.group('converter_sensor')
                    converter = match.group('converter')
                else: 
                    match = re.search(f'FieldValue="{{Binding Path=(Actual)?(?P<converter_sensor>.*)}}"', line)
                    if match:
                        converter_sensor = match.group('converter_sensor')
                        converter = "default"
                    else:
                        continue
                
                device_to_sensor_to_converter[device_name_lower][converter_sensor] = converter
    
    return device_to_sensor_to_converter

def device_to_name_current_to_name_param():
    device_to_name_current_to_name_param_dict = {}
    files = glob.glob('./BCSServiceTool/View/Devices/**/*Actual*.xaml.cs', recursive=True)
    for file in files:
        match = re.search(r'(\w{3,}?)\1+(.*)', file)
        if not match:
            print("converter2: skipping file " + file)
            continue

        name = match.group(1)
        name = name.lower()

        # Special case of Nather300 being in Nather dir breaking pattern for any other HRU
        if name == "nather":
            name += "300"
        
        device_to_name_current_to_name_param_dict.setdefault(name, {})

        with open(file) as f:
            datafile = f.readlines()
            for line in datafile:
                    
                # strip potential "Actual" from the front to improve matching
                # this.paramExtContact1.ParameterName = this.FindResource((object) this._viewModel.ModelFlairParameterData.CurrentExtContact1Position.Description).ToString();
                match = re.search(r'this\.param(?P<name_param>.*)(Actual)?\.ParameterName = this.FindResource..object. this._viewModel\..*\.Current(?P<name_current>.*)\.Description', line)
                if match:
                    device_to_name_current_to_name_param_dict[name][match.group('name_current')] = match.group('name_param')
                                
    return device_to_name_current_to_name_param_dict


def find_converters2():
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

            matches = re.finditer(f'<my:ParameterField Name="(?P<name_param>\\w*)"([^<>]*)FieldValue="{{Binding Path=(\\w*), Converter={{StaticResource (?P<converter>{converters_str})}}', file_str)
            for m in matches:
                if m:
                    name_param = m.group('name_param')
                    converter = m.group('converter')
                    device_to_name_param_to_converter[device_name_lower][name_param] = converter

            matches = re.finditer(f'<my:ParameterField Name="(?P<name_param>\\w*)"([^<>]*)FieldValue="{{Binding Path=(\\w*)}}', file_str)
            for m in matches:
                if m:
                    name_param = m.group('name_param')
                    converter = "default"
                    device_to_name_param_to_converter[device_name_lower][name_param] = converter
    
    return device_to_name_param_to_converter

def device_to_name_current_to_name_param2():
    device_to_name_current_to_name_param_dict = {}
    files = glob.glob('./BCSServiceTool/View/Devices/**/*Actual*.xaml.cs', recursive=True)
    for file in files:
        match = re.search(r'(\w{3,}?)\1+(.*)', file)
        if not match:
            print("converter2: skipping file " + file)
            continue

        name = match.group(1)
        name = name.lower()

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