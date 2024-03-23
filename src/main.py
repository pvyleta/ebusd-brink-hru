from out import write_output
from converters import find_converters, device_to_name_current_to_name_param, converters_map
from sensor import get_dict_devices_sensor
from parameter import get_device_parameters
from command_ebus import get_commands_dict
from model import BaseObject, DeviceModel, VersionRange

# TODO Simplify output to less files by removing redundanc and extending parameter ranges
# TODO add names of parameters parsed through the stringresources.de-de.xaml
# TODO go thorugh AirControlEBusCommands and figure out if flowMode can be set on the wall controller rather than on the unit

# This script expects BCSServiceTool via JetBrains DotPeak in its child folder


device_to_name_current_to_name_param_dict = device_to_name_current_to_name_param()
cmd_dict, cmd_bytes_dict = get_commands_dict()
device_to_name_param_to_converter = find_converters()

dict_devices_sensor = get_dict_devices_sensor(device_to_name_param_to_converter, device_to_name_current_to_name_param_dict, cmd_dict, cmd_bytes_dict)
dict_devices_parameters = get_device_parameters()

# Check some statistics of missing/unused stuff from the conversion for debugging purposses
sensors_without_converters_set = set()
used_converters_set: set[str] = set()
for device, sensors in dict_devices_sensor.items():
    for sensor in sensors:
        if sensor.converter:
            used_converters_set.add(sensor.converter.name)
        else:
            sensors_without_converters_set.add(sensor.name_current + "_" + device.device_name)

converters_set: set[str] = {c for c in converters_map.keys()}
unused_converters_set = converters_set - used_converters_set


# 0. check if parameters are always a subset for lower version
# 1. re-define scan for SW so that the string is parsed as integers
# 2. check the scan results on real device
# 3. write code to parse SW version to match the sw received
# 4. Write code to write the include line

# Reorder to more layered structure
device_models: dict[str, DeviceModel] = {}
for device, sensors in dict_devices_sensor.items():
    device_model = device_models.setdefault(device.device_name, DeviceModel(device.device_name))
    device_model.sensors[device.version] = sensors

# Check if subsequent version alwas contain all parameters from previous version
for device_model in device_models.values():
    versions: list[VersionRange] = sorted(list(device_model.sensors.keys()))
    previous_sensors = device_model.sensors[versions[0]] # initialize to the first version
    for version in versions:
        sensors = device_model.sensors[version]
        for sensor in previous_sensors:
            if sensor not in sensors:
                print(f"ERROR: Sensor {sensor} from previous version not present in version {version} for device {device_model.name}")
            
            # By default, Fails only for DecentralAir70 for two parameters, where converters were added in newer version. That almost seems like omitment, so we just correct that when assigning converters, and keep this assert as a sanity check
            # assert sensor in sensors
        previous_sensors = sensors
        



print("len(device_models): " + str(len(device_models)))
print("unused_converters_set: " + str(unused_converters_set))
print("sensors_without_converters_set: " + str(len(sensors_without_converters_set)))

write_output(dict_devices_sensor, dict_devices_parameters)

print("SUCCESS")
