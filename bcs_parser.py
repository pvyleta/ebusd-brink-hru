import copy

import out
import sensor_data
import config_data
import command_ebus
import current_param
import params
import  dev

# TODO add special instructions and special handling
# TODO add default slave address for the known devices
# TODO fill in dipswitch values for known devices

# This script expects BCSServiceTool via JetBrains DotPeak in its child folder

dict_devices_sensor = sensor_data.get_dict_devices_sensor()

# Now we have added all known converters to all known fields - but there are potential missed matches -> we calculate their count for debugging purposses
sensors_without_converters_set = set()   
used_converters_set = set()        
for device, sensors in dict_devices_sensor.items():
    for sensor in sensors:
        if sensor.converter:
            used_converters_set.add(sensor.converter)
        else:
            sensors_without_converters_set.add(sensor.name_current + "_" + device.name)

if params.DEBUG:
    print("converters_map = {") 
    for converter in sorted([converter.name for converter in used_converters_set]):
        print(f'    "{converter}": "",')
    print("}")
      

# Get datatype for sensors
device_to_current_param = current_param.get_device_to_current_param()
sensors_without_datatypes = 0
sensor_datatypes_set = set()
for device, sensors in dict_devices_sensor.items():
    d_copy = copy.deepcopy(device)

    # flair units have a shared converter under the name 'flair'
    if "Flair" in d_copy.name:
        d_copy.name = "Flair"
    # This Particular Vitovent comes in too many flavors but only one converter
    elif "Vitovent300WH32S" in d_copy.name:
        d_copy.name = "Vitovent300WH32S"

    for sensor in sensors:
        if current_param := device_to_current_param[d_copy].get(sensor.name_current):
            sensor.datatype = current_param.datatype
            sensor_datatypes_set.add(sensor.datatype)
        else:
            sensors_without_datatypes +=1
            if params.DEBUG:
                print("Warning: No current_param for device: " + str(device) + " sensor: " + str(sensor.name_current))

print("sensor_datatypes_set: " + str(sensor_datatypes_set))
print("sensors_without_datatypes: "+ str(sensors_without_datatypes) )
print("sensors_without_converters_set: " + str(len(sensors_without_converters_set)) )

out.write_csv_files(dict_devices_sensor, config_data.get_device_parameters())

print("SUCCESS")
