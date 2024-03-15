import out
import sensor_data
import config_data
import converters

# TODO add special instructions and special handling
# TODO add default slave address for the known devices
# TODO fill in dipswitch values for known devices

# This script expects BCSServiceTool via JetBrains DotPeak in its child folder

dict_devices_sensor = sensor_data.get_dict_devices_sensor()
device_parameters = config_data.get_device_parameters()

# Now we have added all known converters to all known fields - but there are potential missed matches -> we calculate their count for debugging purposses
sensors_without_converters_set = set()
used_converters_set: set[converters.Converter]= set()
for device, sensors in dict_devices_sensor.items():
    for sensor in sensors:
        if sensor.converter:
            used_converters_set.add(sensor.converter)
        else:
            sensors_without_converters_set.add(sensor.name_current + "_" + device.name)

print("sensors_without_converters_set: " + str(len(sensors_without_converters_set)))

out.write_csv_files(dict_devices_sensor, device_parameters)

print("SUCCESS")
