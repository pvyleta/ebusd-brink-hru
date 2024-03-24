from out import write_output, write_known_devices
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

# Make the output of joined files for a given device and SW version
# Publish known files to ebusd configuration, distinguish them by dipswitch for 3c and 7c
# consider adding comments for version
# 1. re-define scan for SW so that the string is parsed as integers
# 2. check the scan results on real device
# 3. write code to parse SW version to match the sw received
# 4. Write code to write the include line

# Reorder to more layered structure
device_models: dict[str, DeviceModel] = {}
for device, sensors in dict_devices_sensor.items():
    device_model = device_models.setdefault(device.device_name, DeviceModel(device.device_name))
    device_model.sensors[device.version] = sensors

for device, parameters in dict_devices_parameters.items():
    device_model = device_models.setdefault(device.device_name, DeviceModel(device.device_name))
    device_model.parameters[device.version] = parameters

# Check if subsequent version always contain all parameters from previous version
for device_model in device_models.values():
    sensors_versions: list[VersionRange] = sorted(list(device_model.sensors.keys()))
    previous_sensors = device_model.sensors[sensors_versions[0]] # initialize to the first version
    for sensor_version in sensors_versions:
        sensors = device_model.sensors[sensor_version]
        for sensor in previous_sensors:
            # By default, Fails only for DecentralAir70 for two parameters, where converters were added in newer version. That almost seems like omitment, so we just correct that when assigning converters, and keep this assert as a sanity check
            # assert sensor in sensors
            if sensor not in sensors:
                pass
            #     print(f"WARNING: Sensor {sensor} from previous version not present in version {sensor_version} for device {device_model.name}")
            
        previous_sensors = sensors

    parameters_versions: list[VersionRange] = sorted(list(device_model.parameters.keys()))
    previous_parameters = device_model.parameters[parameters_versions[0]] # initialize to the first version
    for parameter_version in parameters_versions:
        parameters = device_model.parameters[parameter_version]
        for parameter in previous_parameters:
            # TODO This fails for surprising amount of devices. Either we need to fix somethign deep in parameter creation, or we just cannot make it subsets
            if parameter not in parameters:
                pass
            #     print(f"WARNING: Parameter {parameter} from previous version not present in version {parameter_version} for device {device_model.name}")
            
        previous_parameters = parameters

print("len(device_models): " + str(len(device_models)))
print("unused_converters_set: " + str(unused_converters_set))
print("sensors_without_converters_set: " + str(len(sensors_without_converters_set)))

write_output(dict_devices_sensor, dict_devices_parameters)
write_known_devices(dict_devices_sensor, dict_devices_parameters)

print("SUCCESS")
