from out import write_output
from converters import Converter, device_to_name_current_to_name_param
from sensor_data import get_dict_devices_sensor
from config_data import get_device_parameters
from command_ebus import get_commands_dict

# TODO add special instructions and special handling - e.g. factory reset, errors reset, filter reset...
# TODO add default slave address for the known devices
# TODO fill in dipswitch values for known devices

# This script expects BCSServiceTool via JetBrains DotPeak in its child folder


device_to_name_current_to_name_param_dict = device_to_name_current_to_name_param()
cmd_dict, cmd_bytes_dict = get_commands_dict()

dict_devices_sensor = get_dict_devices_sensor(device_to_name_current_to_name_param_dict, cmd_dict, cmd_bytes_dict)
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

write_output(dict_devices_sensor, device_parameters)

print("SUCCESS")
