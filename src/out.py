import os
import shutil
import csv

from collections import namedtuple

import jsonpickle # type: ignore

from model import Sensor, INT16, UINT16, DeviceModel, VersionRange, VersionBase
from parameter import Parameter
from known_devices import known_devices
from sw_version import sw_version_to_friendly_str
from ebus_message import multiplier_to_divider, brink_wtw_commands_list
from parse_xaml import get_name

DEPRECATED_DIR = "ebusd-configuration-deprecated"
DUMP_DIR = "dump"
DEVICES_UNKNOWN_DIR = "ebusd-configuration-unknown-slave-address"
DEVICES_KNOWN_DIR = "ebusd-configuration-known-slave-address"
CSV_HEADER = '# type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment,field2,part (m/s),datatypes/templates,divider/values,unit,comment,field3,part (m/s),datatypes/templates,divider/values,unit,comment,field4,part (m/s),datatypes/templates,divider/values,unit,comment,field5,part (m/s),datatypes/templates,divider/values,unit,comment\n'


SensorDump = namedtuple('SensorDump', ['device_name', 'first_version', 'last_version', 'name', 'display_name_en', 'display_name_de', 'display_name_es', 'display_name_fr', 'display_name_it', 'display_name_nl', 'display_name_pl', 'id', 'unit', 'datatype', 'multiplier', 'values', 'length'])
ParameterDump = namedtuple('ParameterDump', ['device_name', 'first_version', 'last_version', 'name', 'display_name_en', 'display_name_de', 'display_name_es', 'display_name_fr', 'display_name_it', 'display_name_nl', 'display_name_pl', 'id', 'unit', 'datatype', 'multiplier', 'values', 'length', 'field_current', 'field_min', 'field_max', 'field_step', 'field_default'])

def recreate_dir(directory: str, language: str = ''):
    if len(language) > 0:
        joined_directory = os.path.join(directory, language)

        # Just for the first time we need to create the root language dirs
        if not os.path.exists(directory):
            os.mkdir(directory)
    else:
        joined_directory = directory

    if os.path.exists(joined_directory):
        shutil.rmtree(joined_directory)
    os.mkdir(joined_directory)

def dump_sensor(sensor: Sensor, device_name: str, version_range: VersionRange) -> SensorDump:
    dump_sensor_dict: dict[str, str] = {}
    dump_sensor_dict['device_name'] = device_name
    dump_sensor_dict['first_version'] = str(version_range.first_version)
    dump_sensor_dict['last_version'] = str(version_range.last_version)
    dump_sensor_dict['name'] = sensor.name_current.removeprefix('Current')
    dump_sensor_dict['display_name_en'] = get_name('parameterDescription' + sensor.name_description, 'en')
    dump_sensor_dict['display_name_de'] = get_name('parameterDescription' + sensor.name_description, 'de')
    dump_sensor_dict['display_name_es'] = get_name('parameterDescription' + sensor.name_description, 'es')
    dump_sensor_dict['display_name_fr'] = get_name('parameterDescription' + sensor.name_description, 'fr')
    dump_sensor_dict['display_name_it'] = get_name('parameterDescription' + sensor.name_description, 'it')
    dump_sensor_dict['display_name_nl'] = get_name('parameterDescription' + sensor.name_description, 'nl')
    dump_sensor_dict['display_name_pl'] = get_name('parameterDescription' + sensor.name_description, 'pl')
    dump_sensor_dict['id'] = f'0x{sensor.id:02x}'
    dump_sensor_dict['unit'] = sensor.unit
    dump_sensor_dict['datatype'] = sensor.datatype
    dump_sensor_dict['multiplier'] = str(sensor.converter.multiplier) if sensor.converter else "null"
    dump_sensor_dict['values'] = sensor.converter.values if sensor.converter else "null"
    dump_sensor_dict['length'] = str(sensor.converter.length) if sensor.converter else "null"
    return SensorDump(**dump_sensor_dict)


def dump_param(param: Parameter, device_name: str, version_range: VersionRange) -> ParameterDump:
    dump_param_dict: dict[str, str] = {}
    dump_param_dict['device_name'] = device_name
    dump_param_dict['first_version'] = str(version_range.first_version)
    dump_param_dict['last_version'] = str(version_range.last_version)
    dump_param_dict['name'] = param.name
    dump_param_dict['display_name_en'] = get_name('parameterSetDescription' + param.name, 'en')
    dump_param_dict['display_name_de'] = get_name('parameterSetDescription' + param.name, 'de')
    dump_param_dict['display_name_es'] = get_name('parameterSetDescription' + param.name, 'es')
    dump_param_dict['display_name_fr'] = get_name('parameterSetDescription' + param.name, 'fr')
    dump_param_dict['display_name_it'] = get_name('parameterSetDescription' + param.name, 'it')
    dump_param_dict['display_name_nl'] = get_name('parameterSetDescription' + param.name, 'nl')
    dump_param_dict['display_name_pl'] = get_name('parameterSetDescription' + param.name, 'pl')
    dump_param_dict['id'] = f'0x{param.id:02x}'
    dump_param_dict['unit'] = param.unit
    dump_param_dict['datatype'] = param.datatype
    dump_param_dict['multiplier'] = str(param.multiplier)
    dump_param_dict['values'] = param.values 
    dump_param_dict['length'] = '2'
    dump_param_dict['field_current'] = str(param.field_current)
    dump_param_dict['field_min'] = str(param.field_min)
    dump_param_dict['field_max'] = str(param.field_max)
    dump_param_dict['field_step'] = str(param.field_step)
    dump_param_dict['field_default'] = str(param.field_default)
    return ParameterDump(**dump_param_dict)

def csv_line_sensor(sensor: Sensor, language: str, device_name: str, slave_address: str) -> str:
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    assert sensor.converter
    values = sensor.converter.values
    type = sensor.converter.type
    
    if not (values := sensor.converter.values):
        values = multiplier_to_divider(sensor.converter.multiplier)

    return f'r,{device_name},{get_name('parameterDescription' + sensor.name_description, language)},{sensor.name_current.removeprefix('Current')},,{slave_address},4022,{sensor.id:02x},,,{type},{values},{sensor.unit},\n'


def csv_line_parameters_read(param: Parameter, language: str, device_name: str, slave_address: str) -> str:
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    datatype = convert_to_ebus_datatype(param.datatype)
    if values := param.values:
        comment = f'[default:{param.field_default}] - min/max/step fields of enum message omitted'
        return f'r,{device_name},{get_name('parameterSetDescription' + param.name, language)},{param.name},,{slave_address},4050,{param.id:02x},,,{datatype},{values},{param.unit},,,,IGN:6,,,,Default,,{datatype},{values},{param.unit},{comment}\n'
    else:
        values = multiplier_to_divider(param.multiplier)
        return f'r,{device_name},{get_name('parameterSetDescription' + param.name, language)},{param.name},,{slave_address},4050,{param.id:02x},,,{datatype},{values},{param.unit},,Min,,{datatype},{values},{param.unit},[min:{param.field_min}],Max,,{datatype},{values},{param.unit},[max:{param.field_max}],Step,,{datatype},{values},{param.unit},[step:{param.field_step}],Default,,{datatype},{values},{param.unit},[default:{param.field_default}]\n'


def csv_line_parameters_write(param: Parameter, language: str, device_name: str, slave_address: str) -> str:
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    datatype = convert_to_ebus_datatype(param.datatype)
    if not (values := param.values):
        values = multiplier_to_divider(param.multiplier)
    return f'w,{device_name},{get_name('parameterSetDescription' + param.name, language)},{param.name},,{slave_address},4080,{param.id:02x},,,{datatype},{values},{param.unit},[min:{param.field_min};max:{param.field_max};step:{param.field_step};default:{param.field_default}]\n'


def convert_to_ebus_datatype(datatype: str) -> str:
    if datatype == INT16:
        return "SIR"
    elif datatype == UINT16:
        return "UIR"
    else:
        raise RuntimeError(f'unexpected datatype {datatype}')


def csv_from_sensors(sensors: list[Sensor], language: str, device_name: str = '', slave_address = ''):
    file_str = ""
    for sensor in sensors:
        file_str += csv_line_sensor(sensor, language, device_name, slave_address, )
    return file_str


def csv_from_parameters(parameters: list[Parameter], language: str, is_plus: bool, device_name: str = '', slave_address: str = ''):
    file_str = ""
    for param in parameters:
        if is_plus or not param.is_plus_only: # Output if device is plus or param does not require plus 
            if not param.is_read_only:
                file_str += csv_line_parameters_write(param, language, device_name, slave_address)
            file_str += csv_line_parameters_read(param, language, device_name, slave_address)
    return file_str

COMMENT_HEADER = '''## This ebus config may work for Ubbink, VisionAIR, WOLF CWL series, Viessmann and some other systems that are just re-branded Brink devices
## sources:
## - Original idea and some dividers: https://github.com/dstrigl/ebusd-config-brink-renovent-excellent-300
## - Brink Service Tool (decompiled via Jetbrains DotPeak): https://www.brinkclimatesystems.nl/tools/software-brink-service-tool-en
## - Renovent 150 Datasheet: https://manuals.plus/brink/renovent-sky-150-plus-mechanical-ventilation-with-heat-recovery-manual
## - Modbus Module Datasheet: https://www.brinkclimatesystems.nl/documenten/modbus-uwa2-b-uwa2-e-installation-regulations-614882.pdf
## Message names are based on official Brink Service Tool translations with removed spaces and special characters. 
## Message comment is the name of the parameter as used internally in code (as to help if the translation itself is confusing)
## 
## For ebusd configuration files for the complete Brink portfolio go to https://github.com/pvyleta/ebusd-brink-hru
'''
COMMENT_COMMON_COMMANDS = '''
## COMMON HRU COMMANDS ## (WTWCommands.cs - Some of them might not be applicable for this device, use with caution)
'''
COMMENT_CURRENT_STATE = '''
## Curent state and sensors ##
'''
COMMENT_PARAMETERS = '''
## Configuration parameters ## (values in brackets next to field are definitions of those fields values from Brink Service Tool.)
'''

def device_name_comment(device_name: str, versions: VersionBase) -> str:
    if versions.first_version == versions.last_version:
        return f'\n## This file is for {device_name} SW version {sw_version_to_friendly_str(versions.first_version)} ##\n'
    else:
        return f'\n## This file is for {device_name} SW version from {sw_version_to_friendly_str(versions.first_version)} to {sw_version_to_friendly_str(versions.last_version)} ##\n'
        

def str_slave_and_circuit_mask(type: str, circuit: str = '', slave_address: str = '') -> str:
    return f'*{type},{circuit},,,,{slave_address},\n'

def slave_and_circuit_comment(circuit: str) -> str:
    comment = '\n## Slave address and Circuit ##\n'
    comment += '# Fill in the slave address of your device (hexa without \'0x\' prefix) instead of [fill_your_slave_address_here]\n'
    comment += '# Then just rename this file to [fill_your_slave_address_here].csv and you should be good to use it in ebusd.\n'
    comment += str_slave_and_circuit_mask('r', circuit, '[fill_your_slave_address_here]')
    comment += str_slave_and_circuit_mask('w', circuit, '[fill_your_slave_address_here]')
    return comment

def csv_known_device(sensors: list[Sensor], parameters: list[Parameter], device_name: str, language: str, is_plus: bool, slave_address: str = '') -> str:
    file_str = COMMENT_HEADER + '\n'+ str_slave_and_circuit_mask('r', device_name, slave_address) + str_slave_and_circuit_mask('w', device_name, slave_address)
    file_str += COMMENT_COMMON_COMMANDS
    for msg in brink_wtw_commands_list:
        file_str += msg.dump()
    file_str += COMMENT_CURRENT_STATE
    file_str += csv_from_sensors(sensors, language)
    file_str += COMMENT_PARAMETERS
    file_str += csv_from_parameters(parameters, language, True)
    return file_str
 

def write_known_devices(device_models: dict[str, DeviceModel], language: str):
    recreate_dir(DEVICES_KNOWN_DIR, language)
    for known_device in known_devices:
        with open(os.path.join(DEVICES_KNOWN_DIR, language, f'{known_device.slave_address:02x}.{known_device.device_name}.csv'), "w", encoding="utf-8", newline='\n') as text_file:
            device_model = device_models[known_device.device_name]
            latest_sensor_version_range = sorted(list(device_model.sensors.keys()))[-1]
            latest_parameter_version_range = sorted(list(device_model.parameters.keys()))[-1]
            text_file.write(CSV_HEADER)
            text_file.write(csv_known_device(device_model.sensors[latest_sensor_version_range], device_model.parameters[latest_parameter_version_range], known_device.device_name, language, True, f'{known_device.slave_address:02x}'))


# For many devices we know exactly what parameters are present in what version, 
# but unfortunately we do not know their default slave address. 
# In that case we just provide a 'sample' file where slave address must be filled
# in manually in the header, and after that it can be used by ebusd without any issues.
# Please, report back any slave address you find, so that our database of known
# adresses can be extended (and devices published directly back to ebusd-configuration repo)
def write_unknown_address_devices(device_models: dict[str, DeviceModel], language: str):
    recreate_dir(DEVICES_UNKNOWN_DIR, language)

    for device_name, device_model in device_models.items():
        # For devices with plus variant, we need to make the files twice:
        plus_versions: list[bool] = [False, True] if device_model.has_plus_variant else [False]
        for plus_version in plus_versions:
            for subversion in device_model.version_sub_ranges:
                with open(os.path.join(DEVICES_UNKNOWN_DIR, language, f'{device_name}.{subversion.first_version}.{subversion.last_version}{'.plus' if plus_version else ''}.csv'), "w", encoding="utf-8", newline='\n') as text_file:
                    file_str = CSV_HEADER
                    file_str += COMMENT_HEADER
                    file_str += device_name_comment(device_name, subversion)
                    file_str += slave_and_circuit_comment(device_name)
                    file_str += COMMENT_COMMON_COMMANDS
                    for msg in brink_wtw_commands_list:
                        if device_name == 'DecentralAir70' and msg.name == 'FilterNotificationFlow':
                            # This unit already defines this parameter later
                            continue
                        elif device_name in ['ValveT01', 'MultiRoomCtrlT01'] and msg.name not in ['FactoryReset', 'ResetNotifications', 'RequestErrorList']:
                            # Other than these messages are not meaningful for a valve
                            continue
                        file_str += msg.dump()
                    for version_range, sensors in device_model.sensors.items():
                        if version_range.contains(subversion):
                            file_str += COMMENT_CURRENT_STATE
                            file_str += csv_from_sensors(sensors, language)
                    for version_range, parameters in device_model.parameters.items():
                        if version_range.contains(subversion):
                            file_str += COMMENT_PARAMETERS
                            file_str += csv_from_parameters(parameters, language, plus_version)
                    text_file.write(file_str)


# This functionality is kept for reference, but in general is deprecated in favor of other output styles
# Contents of output_dir are always cleaned before writing
# File format is [device_name].[lowest_sw_version].[highest_sw_version].[sensors|params|params.plus].csv
def write_output_DEPRECATED(device_models: dict[str, DeviceModel], language: str):
    recreate_dir(DEPRECATED_DIR, language)

    for device_name, device_model in device_models.items():
        for version_range, sensors in device_model.sensors.items():
            with open(os.path.join(DEPRECATED_DIR, language, f'{device_name}.{version_range.first_version}.{version_range.last_version}.sensors.csv'), "w", encoding="utf-8", newline='\n') as text_file:
                text_file.write(CSV_HEADER + str_slave_and_circuit_mask('r', device_name) + str_slave_and_circuit_mask('w', device_name))
                text_file.write(csv_from_sensors(sensors, language))

        for version_range, parameters in device_model.parameters.items():
            with open(os.path.join(DEPRECATED_DIR, language, f'{device_name}.{version_range.first_version}.{version_range.last_version}.params.csv'), "w", encoding="utf-8", newline='\n') as text_file:
                text_file.write(CSV_HEADER + str_slave_and_circuit_mask('r', device_name) + str_slave_and_circuit_mask('w', device_name))
                text_file.write(csv_from_parameters(parameters, language, False))
            if device_model.has_plus_variant: 
                with open(os.path.join(DEPRECATED_DIR, language, f'{device_name}.{version_range.first_version}.{version_range.last_version}.params.plus.csv'), "w", encoding="utf-8", newline='\n') as text_file:
                    text_file.write(CSV_HEADER + str_slave_and_circuit_mask('r', device_name) + str_slave_and_circuit_mask('w', device_name))
                    text_file.write(csv_from_parameters(parameters, language, True))


def write_dump(device_models: dict[str, DeviceModel]):
    recreate_dir(DUMP_DIR)

    sensors_all: list[SensorDump] = []
    params_all: list[ParameterDump] = []


    for device_name, device_model in device_models.items():
        for version_range, sensors in device_model.sensors.items():
            sensors_all.extend([dump_sensor(sensor, device_name, version_range) for sensor in sensors])

        for version_range, parameters in device_model.parameters.items():
            params_all.extend([dump_param(param, device_name, version_range) for param in parameters])

    # Write out JSON and CVS of all params and sensors for an further processing in different tools
    jsonpickle.set_encoder_options('json', sort_keys=True, indent=4)
    sensors_all.sort()
    params_all.sort()

    with open(os.path.join(DUMP_DIR, 'sensors.json'), "w", encoding="utf-8", newline='\n') as text_file:
        text_file.write(jsonpickle.dumps([sensor._asdict() for sensor in sensors_all]))
  
    with open(os.path.join(DUMP_DIR, 'params.json'), "w", encoding="utf-8", newline='\n') as text_file:
        text_file.write(jsonpickle.dumps([param._asdict() for param in params_all]))
  
    with open(os.path.join(DUMP_DIR, 'sensors.csv'), "w", encoding="utf-8", newline='\n') as text_file:
        csv_writer = csv.writer(text_file)
        keys_sensors = sensors_all[0]._fields
        print(f'CSV Dump Sensor keys: {keys_sensors}')
        csv_writer.writerow(keys_sensors)
        for sensor in sensors_all:
            csv_writer.writerow(sensor)

    with open(os.path.join(DUMP_DIR, 'params.csv'), "w", encoding="utf-8", newline='\n') as text_file:
        csv_writer = csv.writer(text_file)
        keys_params = params_all[0]._fields
        print(f'CSV Dump Params keys: {keys_params}')
        csv_writer.writerow(keys_params)
        for param in params_all:
            csv_writer.writerow(param)
