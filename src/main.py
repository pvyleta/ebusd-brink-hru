from out import write_output
from converters import find_converters, device_to_name_current_to_name_param, converters_map
from sensor_data import get_dict_devices_sensor
from config_data import get_device_parameters
from command_ebus import get_commands_dict

# TODO add special instructions and special handling - e.g. factory reset, errors reset, filter reset...
# TODO add default slave address for the known devices
# TODO add names of parameters parsed through the stringresources.de-de.xaml

# This script expects BCSServiceTool via JetBrains DotPeak in its child folder


device_to_name_current_to_name_param_dict = device_to_name_current_to_name_param()
cmd_dict, cmd_bytes_dict = get_commands_dict()
device_to_name_param_to_converter = find_converters()

dict_devices_sensor = get_dict_devices_sensor(device_to_name_param_to_converter, device_to_name_current_to_name_param_dict, cmd_dict, cmd_bytes_dict)
device_parameters = get_device_parameters()

# Check some statistics of missing/unused stuff from the conversion for debugging purposses
sensors_without_converters_set = set()
used_converters_set: set[str] = set()
for device, sensors in dict_devices_sensor.items():
    for sensor in sensors:
        if sensor.converter:
            used_converters_set.add(sensor.converter.name)
        else:
            sensors_without_converters_set.add(sensor.name_current + "_" + device.name)

converters_set: set[str] = {c for c in converters_map.keys()}
unused_converters_set = converters_set - used_converters_set

print("unused_converters_set: " + str(unused_converters_set))
print("sensors_without_converters_set: " + str(len(sensors_without_converters_set)))

write_output(dict_devices_sensor, device_parameters)

print("SUCCESS")
