import copy

import converters
import out
import sensor_data
import config_data

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
    "CurrentSoftwareVersionUIFModule" : "paramBaseSoftwareVersion", # Vitovent300WH32SC325 speciality
    "CurrentHardwareVersionUIFModule" : "paramBaseHardwareVersion", # Vitovent300WH32SC325 speciality
}

# Some parameters seem not to be present in UI at all - we fabricate the converters on other knowledge
manual_current_to_converter = {
    "CurrentDipswitchValue" : "UInt16ToUNumberConverter", # paramDipswitch; conversion missing for Flair units and few others for no apparent reason
    "CurrentEBusAddressing" : "unknown", # 
    "CurrenteBusPowerStatus": "UInt16ToEBusPowerStateConverter", # paramEBusPowerState; Assumed from decentralair70actualstateview_01.xaml
    "CurrentEBusSyncGenErrorCount" : "UInt16ToUNumberConverter", # paramSyncGenErrorCount; conversion missing for Flair units and few others for no apparent reason
    "CurrentExhaustFanPWMValue" : "UInt16ToUNumberConverter",  # paramFanPWMSetpoint; Assumed from decentralair70actualstateview_01.xaml
    "CurrentHardwareVersionExtensionModule" : "unknown", # Vitovent300WH32SC325 speciality
    "CurrentInletFanPWMValue" : "UInt16ToUNumberConverter",  # paramFanPWMSetpoint; Assumed from decentralair70actualstateview_01.xaml
    "CurrentPerilexPosition" : "UInt16ToFanSwitchConverter", # paramPerilexPosition; Mising for Sky units
    "CurrentSoftwareVersion" : "default", # Missing for many units, but present for some
    "CurrentSoftwareVersionExtensionModule" : "unknown", # Vitovent300WH32SC325 speciality

    # Some flair specific stuff
    "CurrentDeviceID" : "unknown", 
    "CurrentDeviceType" : "unknown",
    "CurrentImageVersionUIFModule" : "unknown", # Not easy to figure out, DynamicResource, parameterDescriptionUIFImageVersion
    "CurrentLanguageVersionUIFModule" : "unknown", # Not easy to figure out, DynamicResource, parameterDescriptionUIFLanguageVersion
    "CurrentLocalUIFSwitchPosition" : "unknown",
    "CurrentUIFButtonsStatus" : "unknown",

    # Some random fields that seems almost forgotten for some units, as they exist for the rest, taken from other places almost at random
    "CurrentBypassCurrent" : "UInt16ToUNumberConverter", 
    "CurrentBypassStatus" : "UInt16ToBypassStatusConverter", 
    "CurrentContact1Position" : "UInt16ToOnOffConverter", 
    "CurrentContact2Position" : "UInt16ToOnOffConverter", 
    "CurrentEWTStatus" : "UInt16ToEWTStatusConverter", 
    "CurrentExhaustFlow" : "UInt16ToUNumberConverter", 
    "CurrentHumidityBoostState" : "UInt16ToHumidityBoostStateConverter", 
    "CurrentInletFlow" : "UInt16ToUNumberConverter", 
    "CurrentInsideTemperature" : "Int16ToTemperatureConverterFact10", 
    "CurrentMRCConfigurationStatus" : "unknown", 
    "CurrentOptionTemperature" : "Int16ToTemperatureConverterFact10", 
    "CurrentPostheaterPower" : "UInt16ToUNumberConverter", 
    "CurrentPostheaterStatus" : "UInt16ToHeaterStatusConverter", 
    "CurrentPressureExhaust" : "UInt16ToPressureConverter", 
    "CurrentPressureInlet" : "UInt16ToPressureConverter", 
    "CurrentRelativeHumidity" : "Int16ToPercentageFact10Converter", 
}
    
# assign converters to each sensor in each device
dict_devices_sensor = sensor_data.get_dict_devices_sensor()
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
            device_converters_unused.pop(name_param, None)
            continue
        
        # Try the 'base' flair converter as a backup for vitovent units
        if "vitovent" in device_name_lower:
            if converter := device_to_name_param_to_converter["flair"].get(name_param, None):
                sensor.converter = converter
                device_to_name_param_to_converter_unused["flair"].pop(name_param, None)
                continue
        
        # For some parameters the convertors are listed, but the conversion path is broken, so we manually connect the dots
        name_param_manual = manual_current_to_param_conversion.get(sensor.name_current, None)
        if converter := device_converters.get(name_param_manual, None):
            sensor.converter = converter
            device_converters_unused.pop(name_param_manual, None)
            continue

        # If everything else fails, we have manually searched for the most suitable converter from otehr units
        # TODO Mark these sensors somehow, since there may have been a reason the parameter was hidden for certain units
        # TODO the device type is likely viessmann/brink, so we might figure that out from code
        if converter := manual_current_to_converter.get(sensor.name_current, None):
            sensor.converter = converter
            device_converters_unused.pop(name_param_manual, None)
            continue
        
        print(f"Error: Sensor not found: device: {device.name} lower: {device_name_lower} name: {sensor.name} name_current: {sensor.name_current} name_param: {name_param}")
            
# Now we have added all known converters to all known fields - but there are potential missed matches -> we calculate their count for debugging purposses
sensors_without_converters_set = set()        
for device_name_lower,  device in dict_devices_sensor.items():
    for sensor in device.sensors:
        if sensor.converter == "":
            sensors_without_converters_set.add(sensor.name + "_" + device_name_lower)
            
print("sensors_without_converters_set: " + str(len(sensors_without_converters_set)) )

converter_sensor_unused_set = set()  
for device_name_lower, device in device_to_name_param_to_converter_unused.items():
    for sensor_name in device:       
        converter_sensor_unused_set.add(sensor_name + "_" + device_name_lower)

print("converter_fields_without_sensor_set: "+ str(len(converter_sensor_unused_set)) )

out.write_files(dict_devices_sensor, config_data.get_devices_param())
