import copy

import converters
import out
import sensor_data
import config_data
import params


# TODO add special instructions and special handling
# TODO add default slave address for the known devices

# This script expects BCSServiceTool via JetBrains DotPeak in its child folder

# Get converters
device_to_name_param_to_converter = converters.find_converters()
device_to_name_param_to_converter_unused = copy.deepcopy(device_to_name_param_to_converter)
device_to_name_current_to_name_param_dict = converters.device_to_name_current_to_name_param()

# TODO status and value is switched - figure out reason, fix it:
    #   this.paramCO2Sensor1Status.ParameterName = this.FindResource((object) this._viewModel.ModelFlairParameterData.CurrentCO2Sensor1Value.Description).ToString();
    #   this.paramCO2Sensor1Value.ParameterName = string.Empty;

# For some parameters, there is no valid conversion in code, manually pick the best backups
manual_current_to_param_conversion = {
    "CurrentCO2Sensor1Status" : "paramCO2Sensor1Value", # conversion missing for all units for no apparent reason
    "CurrentCO2Sensor2Status" : "paramCO2Sensor2Value", # conversion missing for all units for no apparent reason
    "CurrentCO2Sensor3Status" : "paramCO2Sensor3Value", # conversion missing for all units for no apparent reason
    "CurrentCO2Sensor4Status" : "paramCO2Sensor4Value", # conversion missing for all units for no apparent reason
}

# Some parameters seem not to be present in UI at all - we fabricate the converters on other knowledge
# TODO test what fields are still used after recent changes
manual_current_to_converter = {
    "CurrentDipswitchValue" : "ConverterUInt16ToUNumber", # paramDipswitch; conversion missing for Flair units and few others for no apparent reason
    "CurrentEBusAddressing" : "ConverterUInt32ToEBusAddressing", # Manually created 'dummy' converter
    "CurrenteBusPowerStatus": "ConverterUInt16ToEBusPowerState", # paramEBusPowerState; Assumed from decentralair70actualstateview_01.xaml
    "CurrentEBusSyncGenErrorCount" : "ConverterUInt16ToUNumber", # paramSyncGenErrorCount; conversion missing for Flair units and few others for no apparent reason
    "CurrentExhaustFanPWMValue" : "ConverterUInt16ToUNumber",  # paramFanPWMSetpoint; Assumed from decentralair70actualstateview_01.xaml
    "CurrentInletFanPWMValue" : "ConverterUInt16ToUNumber",  # paramFanPWMSetpoint; Assumed from decentralair70actualstateview_01.xaml
    "CurrentPerilexPosition" : "ConverterUInt16ToFanSwitch", # paramPerilexPosition; Mising for Sky units
    "CurrentSoftwareVersion" : "ConverterByteArrayToSoftwareVersion", # Missing for many units, but present for some

    # Some flair specific stuff
    "CurrentDeviceID" : "ConverterUInt32ToDeviceID", # TODO for flair response is 4; for others (only elan) it is 1; ElanReadActualDeviceID
    "CurrentDeviceType" : "ConverterUInt16ToDeviceType",
    "CurrentUIFButtonsStatus" : "ConverterUInt16ToUIFButtonsStatus", # TODO flair length 2; elan length 1

    # Some random fields that seems almost forgotten for some units, as they exist for the rest, taken from other places almost at random
    "CurrentBypassCurrent" : "ConverterUInt16ToUNumber", 
    "CurrentBypassStatus" : "ConverterUInt16ToBypassStatus", 
    "CurrentContact1Position" : "ConverterUInt16ToOnOff", 
    "CurrentContact2Position" : "ConverterUInt16ToOnOff", 
    "CurrentEWTStatus" : "ConverterUInt16ToEWTStatus", 
    "CurrentExhaustFlow" : "ConverterUInt16ToUNumber", 
    "CurrentHumidityBoostState" : "ConverterUInt16ToHumidityBoostState", 
    "CurrentInletFlow" : "ConverterUInt16ToUNumber", 
    "CurrentInsideTemperature" : "ConverterInt16ToTemperatureFact10", 
    "CurrentMRCConfigurationStatus" : "ConverterByteArrayToMRCConfigurationStatus", 
    "CurrentOptionTemperature" : "ConverterInt16ToTemperatureFact10", 
    "CurrentPostheaterPower" : "ConverterUInt16ToUNumber", 
    "CurrentPostheaterStatus" : "ConverterUInt16ToHeaterStatus", # TODO This would not work on 'old flair'
    "CurrentPressureExhaust" : "ConverterUInt16ToPressure", 
    "CurrentPressureInlet" : "ConverterUInt16ToPressure", 
    "CurrentRelativeHumidity" : "ConverterInt16ToPercentageFact10", 
}
    
# assign converters to each sensor in each device
cmd_dict, cmd_bytes_dict = sensor_data.get_commands_dict()
dict_devices_sensor = sensor_data.get_dict_devices_sensor(cmd_dict, cmd_bytes_dict)
for device_name_lower, device in dict_devices_sensor.items():

    # flair units have a shared converter under the name 'flair'
    if "flair" in device_name_lower:
        device_name_lower = "flair"
    # This Particular Vitovent comes in too many flavors but only one converter
    elif "vitovent300wh32s" in device_name_lower:
        device_name_lower = "vitovent300wh32s"

    device_converters = device_to_name_param_to_converter[device_name_lower]
    device_converters_unused = device_to_name_param_to_converter_unused[device_name_lower]

    for sensor in device.sensors:
        # First, Try to match the converter through following the path in code from ebus to UI
        name_param = device_to_name_current_to_name_param_dict[device_name_lower].get(sensor.name_current, None)
        if converter := device_converters.get(name_param, None):
            sensor.converter = converter
            sensor.converter_match = "from_code"
            device_converters_unused.pop(name_param, None)
            continue
        
        # Try the 'base' flair converter as a backup for vitovent units
        if "vitovent" in device_name_lower:
            name_param_flair = device_to_name_current_to_name_param_dict["flair"].get(sensor.name_current, None)
            if converter := device_to_name_param_to_converter["flair"].get(name_param_flair, None):
                sensor.converter = converter
                sensor.converter_match = "from_code_flair"
                device_to_name_param_to_converter_unused["flair"].pop(name_param_flair, None)
                continue
        
        # For some parameters the convertors are listed, but the conversion path is broken, so we manually connect the dots
        name_param_manual = manual_current_to_param_conversion.get(sensor.name_current, None)
        if converter := device_converters.get(name_param_manual, None):
            sensor.converter = converter
            sensor.converter_match = "manual_param"
            device_converters_unused.pop(name_param_manual, None)
            continue

        # If everything else fails, we manually search for the most suitable converter from otehr units
        if converter := manual_current_to_converter.get(sensor.name_current, None):
            sensor.converter = converters.converters_map[converter]
            sensor.converter_match = "manual_full"
            continue
        
        print(f"Error: Sensor not found: device: {device.name} lower: {device_name_lower} name: {sensor.name} name_current: {sensor.name_current} name_param: {name_param}")
            
# Now we have added all known converters to all known fields - but there are potential missed matches -> we calculate their count for debugging purposses
sensors_without_converters_set = set()   
used_converters_set = set()        
for device_name_lower, device in dict_devices_sensor.items():
    for sensor in device.sensors:
        if sensor.converter:
            used_converters_set.add(sensor.converter)
        else:
            sensors_without_converters_set.add(sensor.name + "_" + device_name_lower)

if params.DEBUG:
    print("converters_map = {") 
    for converter in sorted(list(used_converters_set)):
        print(f'    "{converter}": "",')
    print("}")
      

# Get datatype for sensors
device_to_actual_param_to_datatype = sensor_data.get_device_to_actual_param_to_datatype()
sensors_without_datatypes = 0
sensor_datatypes_set = set()
default_converter_set = set()
unknown_converter_set = set()
for device_name_lower, device in dict_devices_sensor.items():

    # device_to_actual_param_to_datatype stores all flair units under "flair"
    if device_name_lower:
        device_name = "flair"
    else:
        device_name = device_name_lower

    for sensor in device.sensors:
        sensor.datatype = device_to_actual_param_to_datatype[device_name].get(sensor.converter.name_actual, None)
        sensor_datatypes_set.add(sensor.datatype)
        if not sensor.datatype:
            if params.DEBUG:
                print(sensor.name + " " + str(sensor.converter))
            sensors_without_datatypes +=1

        if sensor.converter.name == 'default':
            default_converter_set.add(device_name_lower + " " + sensor.name)
        elif sensor.converter.name == 'unknown':
            unknown_converter_set.add(device_name_lower + " " + sensor.name)

converter_sensor_unused_set = set()  
for device_name_lower, device in device_to_name_param_to_converter_unused.items():
    for sensor_name in device:       
        converter_sensor_unused_set.add(sensor_name + "_" + device_name_lower)

print("default_converter_set: " + str(default_converter_set))
print("unknown_converter_set: " + str(unknown_converter_set))
print("sensor_datatypes_set: " + str(sensor_datatypes_set))
print("sensors_without_datatypes: "+ str(sensors_without_datatypes) )
print("sensors_without_converters_set: " + str(len(sensors_without_converters_set)) )
print("converter_fields_without_sensor_set: "+ str(len(converter_sensor_unused_set)) )

out.write_csv_files(dict_devices_sensor, config_data.get_devices_param())

print("SUCCESS")
