import out
import sensor_data
import config_data
import params

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
      
print("sensors_without_converters_set: " + str(len(sensors_without_converters_set)) )

out.write_csv_files(dict_devices_sensor, config_data.get_device_parameters())

print("SUCCESS")
