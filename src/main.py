from out import write_csv_files
from converters import Converter
from sensor_data import get_dict_devices_sensor
from config_data import get_device_parameters

# TODO add special instructions and special handling
# TODO add default slave address for the known devices
# TODO fill in dipswitch values for known devices

# This script expects BCSServiceTool via JetBrains DotPeak in its child folder

dict_devices_sensor = get_dict_devices_sensor()
device_parameters = get_device_parameters()

# Now we have added all known converters to all known fields - but there are potential missed matches -> we calculate their count for debugging purposses
sensors_without_converters_set = set()
used_converters_set: set[Converter]= set()
for device, sensors in dict_devices_sensor.items():
    for sensor in sensors:
        if sensor.converter:
            used_converters_set.add(sensor.converter)
        else:
            sensors_without_converters_set.add(sensor.name_current + "_" + device.name)

print("sensors_without_converters_set: " + str(len(sensors_without_converters_set)))

write_csv_files(dict_devices_sensor, device_parameters)

print("SUCCESS")
