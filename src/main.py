from out import write_known_devices, write_dump, write_unknown_address_devices
from converters import find_converters, device_to_name_current_to_name_param, converters_map
from sensor import get_dict_devices_sensor
from parameter import get_device_parameters
from command_ebus import get_commands_dict
from model import DeviceModel, VersionRange, VersionBase, DEBUG
from sw_version import Version
from parse_xaml import file_suffix_dict

# TODO Rework so that first dump is generated, and then output is created from dump - that way dump can be manually edited in future if the brink service tool becomes unavailable, and we can still generate arbitrary output.
# TODO Simplify output to less files by removing redundancy and extending parameter ranges
# TODO create common base class for sensors and parameters, so that we can check for dupes etc.
# TODO translate the fields names
# TODO translate the values in enums
# TODO add conditionals for csv_known_device (output of devices with known slave addresses) for dipswitch value and software version
# TODO consider to hack the scanning through scan with different ID. the units might be willing to accept it

# Note: AirControlEBusCommands specify the commands of the wall controller, and it should be in thery to control
#       the wall controller, which would then control the HRU - that would be convenient. unfortunately, my Air Control 
#       does not reply on its 0x24 slave address and at this point I have no idea what to do it more.

# This script expects BCSServiceTool decompiled via JetBrains DotPeak in its child folder

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


# Reorder to more layered structure
device_models: dict[str, DeviceModel] = {}
for device, sensors in dict_devices_sensor.items():
    device_model = device_models.setdefault(device.device_name, DeviceModel(device.device_name))
    device_model.sensors[device.version] = sensors

for device, parameters in dict_devices_parameters.items():

    # sanity check, that all device parameter definitions for one device are consistent in having or not having a plus variant
    if device.device_name in device_models:
        device_model.has_plus_variant == device.has_plus_variant

    device_model = device_models.setdefault(device.device_name, DeviceModel(device.device_name))
    device_model.parameters[device.version] = parameters
    device_model.has_plus_variant = device.has_plus_variant


# Add all sw-version-sub-ranges. We take advantage of having only two sets of non-intersecting version ranges. We merge the first/last versions, and make a joined list, and then construct a set out of it.
for device_model in device_models.values():
    version_set: set[Version] = set()
    for version_range in device_model.parameters.keys():
        version_set.add(Version(version_range.first_version, 'first'))
        version_set.add(Version(version_range.last_version, 'last'))
    for version_range in device_model.sensors.keys():
        version_set.add(Version(version_range.first_version, 'first'))
        version_set.add(Version(version_range.last_version, 'last'))
    
    version_list: list[Version] = sorted(list(version_set))
    while len(version_list) > 0:
        first = version_list.pop(0)

        # If the next version is first again, insert artificial last version. 
        # Note: can happen if the two original set of ranges did not start at the same number, e.g. params start at 10806, sensors start at 10803
        if version_list[0].type == 'first':
            version_list.insert(0, Version(version_list[0].version-1, 'last'))

        last = version_list.pop(0)

        # Sanity checks
        assert first.type == 'first'
        assert last.type == 'last'

        device_model.version_sub_ranges.add(VersionBase(first.version, last.version))
    
    if DEBUG:
        print(f'{device_model.name} {sorted(list(device_model.version_sub_ranges))}')


if DEBUG:
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
                    # print(f"WARNING: Sensor {sensor} from previous version not present in version {sensor_version} for device {device_model.name}")
                    pass
                
            previous_sensors = sensors

        parameters_versions: list[VersionRange] = sorted(list(device_model.parameters.keys()))
        previous_parameters = device_model.parameters[parameters_versions[0]] # initialize to the first version
        for parameter_version in parameters_versions:
            parameters = device_model.parameters[parameter_version]
            for parameter in previous_parameters:
                # This fails for surprising amount of devices. Either we need to fix somethign deep in parameter creation, or we just cannot make it subsets. or it is plus vs basic?
                if parameter not in parameters:
                    # print(f"WARNING: Parameter {parameter} from previous version not present in version {parameter_version} for device {device_model.name}")
                    pass
                
            previous_parameters = parameters


print("len(device_models): " + str(len(device_models)))
print("unused_converters_set: " + str(unused_converters_set))
print("sensors_without_converters_set: " + str(len(sensors_without_converters_set)))

write_dump(device_models)

for language in file_suffix_dict:
    write_unknown_address_devices(device_models, language)
    write_known_devices(device_models, language)

print("SUCCESS")
