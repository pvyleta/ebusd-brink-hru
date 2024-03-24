import os
import shutil
import csv

from collections import namedtuple

import jsonpickle # type: ignore

from model import Sensor, DeviceVersion, INT16, UINT16
from parameter import Parameter, DeviceParameters
from known_devices import known_devices
from ebus_message import multiplier_to_divider, brink_wtw_commands_list


OUTPUT_DIR = "ebusd-configuration"
DUMP_DIR = "dump"
KNOWN_DEVICES_EN_DIR = "ebusd-configuration-en"
KNOWN_DEVICES_DE_DIR = "ebusd-configuration-de"
CSV_HEADER = '# type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment,field2,part (m/s),datatypes/templates,divider/values,unit,comment,field3,part (m/s),datatypes/templates,divider/values,unit,comment,field4,part (m/s),datatypes/templates,divider/values,unit,comment,field5,part (m/s),datatypes/templates,divider/values,unit,comment\n'


SensorDump = namedtuple('SensorDump', ['device_name', 'first_version', 'last_version', 'name', 'id', 'unit', 'datatype', 'multiplier', 'values', 'length'])
ParameterDump = namedtuple('ParameterDump', ['device_name', 'first_version', 'last_version', 'name', 'id', 'unit', 'datatype', 'multiplier', 'values', 'length', 'field_current', 'field_min', 'field_max', 'field_step', 'field_default'])

def dump_sensor(sensor: Sensor, device_version: DeviceVersion) -> SensorDump:
    dump_sensor_dict: dict[str, str] = {}
    dump_sensor_dict['device_name'] = device_version.device_name
    dump_sensor_dict['first_version'] = str(device_version.version.first_version)
    dump_sensor_dict['last_version'] = str(device_version.version.last_version)
    dump_sensor_dict['name'] = sensor.name_current.removeprefix('Current')
    dump_sensor_dict['id'] = f'0x{sensor.id:02x}'
    dump_sensor_dict['unit'] = sensor.unit
    dump_sensor_dict['datatype'] = sensor.datatype
    dump_sensor_dict['multiplier'] = str(sensor.converter.multiplier) if sensor.converter else "null"
    dump_sensor_dict['values'] = sensor.converter.values if sensor.converter else "null"
    dump_sensor_dict['length'] = str(sensor.converter.length) if sensor.converter else "null"
    return SensorDump(**dump_sensor_dict)


def dump_param(param: Parameter, device_version: DeviceVersion) -> ParameterDump:
    dump_param_dict: dict[str, str] = {}
    dump_param_dict['device_name'] = device_version.device_name
    dump_param_dict['first_version'] = str(device_version.version.first_version)
    dump_param_dict['last_version'] = str(device_version.version.last_version)
    dump_param_dict['name'] = param.name
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


def csv_line_sensor(sensor: Sensor, device_name: str, slave_address: str) -> str:
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    assert sensor.converter
    values = sensor.converter.values
    type = sensor.converter.type
    
    if not (values := sensor.converter.values):
        values = multiplier_to_divider(sensor.converter.multiplier)

    return f'r,{device_name},{sensor.name_current.removeprefix('Current')},{sensor.name_description},,{slave_address},4022,{sensor.id:02x},,,{type},{values},{sensor.unit},\n'


def csv_line_parameters_read(param: Parameter, device_name: str, slave_address: str) -> str:
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    datatype = convert_to_ebus_datatype(param.datatype)
    if values := param.values:
        comment = f'[default:{param.field_default}] - min/max/step fields of enum message omitted'
        return f'r,{device_name},{param.name},{param.name},,{slave_address},4050,{param.id:02x},,,{datatype},{values},{param.unit},,,,IGN:6,,,,Default,,{datatype},{values},{param.unit},{comment}\n'
    else:
        values = multiplier_to_divider(param.multiplier)
        return f'r,{device_name},{param.name},{param.name},,{slave_address},4050,{param.id:02x},,,{datatype},{values},{param.unit},,Min,,{datatype},{values},{param.unit},[min:{param.field_min}],Max,,{datatype},{values},{param.unit},[max:{param.field_max}],Step,,{datatype},{values},{param.unit},[step:{param.field_step}],Default,,{datatype},{values},{param.unit},[default:{param.field_default}]\n'


def csv_line_parameters_write(param: Parameter, device_name: str, slave_address: str) -> str:
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    datatype = convert_to_ebus_datatype(param.datatype)
    if not (values := param.values):
        values = multiplier_to_divider(param.multiplier)
    return f'w,{device_name},{param.name},{param.name},,{slave_address},4080,{param.id:02x},,,{datatype},{values},{param.unit},[min:{param.field_min};max:{param.field_max};step:{param.field_step};default:{param.field_default}]\n'


def convert_to_ebus_datatype(datatype: str) -> str:
    if datatype == INT16:
        return "SIR"
    elif datatype == UINT16:
        return "UIR"
    else:
        raise RuntimeError(f'unexpected datatype {datatype}')


def csv_from_sensors(sensors: list[Sensor], device_name: str, slave_address = ''):
    file_str = ""
    for sensor in sensors:
        file_str += csv_line_sensor(sensor, device_name, slave_address)
    return file_str


def csv_from_parameters(parameters: list[Parameter], device_name: str, is_plus: bool, slave_address: str = ''):
    file_str = ""
    for param in parameters:
        if is_plus or not param.is_plus_only: # Output if device is plus or param does not require plus 
            if not param.is_read_only:
                file_str += csv_line_parameters_write(param, device_name, slave_address)
            file_str += csv_line_parameters_read(param, device_name, slave_address)
    return file_str


# TODO add conditionals for plus
# TODO add conditionals for dipswitch value
# TODO figure out what to do with the versions... for start, we can include the latest version, but then we will need to add some conditionals on current sw version -> which would be worth to add to scan, scan can likely be added per device
def csv_known_device(sensors: list[Sensor], device_name: str, parameters: list[Parameter], is_plus: bool, slave_address: str = '') -> str:
    file_str = '''## This ebus config may work for Ubbink, VisionAIR, WOLF CWL series, Viessmann and some other systems that are just re-branded Brink devices
## This file is based on plus version in latest SW version - basic version and older SW versions might not have all the parameters implemented.
## sources:
## - Original idea and some dividers: https://github.com/dstrigl/ebusd-config-brink-renovent-excellent-300
## - Brink Service Tool (decompiled via Jetbrains DotPeak): https://www.brinkclimatesystems.nl/tools/software-brink-service-tool-en
## - Renovent 150 Datasheet: https://manuals.plus/brink/renovent-sky-150-plus-mechanical-ventilation-with-heat-recovery-manual
## - Modbus Module Datasheet: https://www.brinkclimatesystems.nl/documenten/modbus-uwa2-b-uwa2-e-installation-regulations-614882.pdf

## COMMON HRU COMMANDS ## (WTWCommands.cs)
'''
    for msg in brink_wtw_commands_list:
        file_str += msg.dump(device_name, slave_address)
    file_str += '''
## Curent state and sensors ##
'''
    file_str += csv_from_sensors(sensors, device_name, slave_address)
    file_str += '''
## Configuration parameters ##
'''
    file_str += csv_from_parameters(parameters, device_name, True, slave_address)
    return file_str
 


def get_latest_sw_for_device(device_name: str, devices: list[DeviceVersion]):
    for device in devices:
        if device.device_name == device_name and device.version.last_version == 99999:
            return device
    return None

# Contents of output_dir are always cleaned before writing
# File format is [device_name].[lowest_sw_version].[highest_sw_version].[params|sensors.basic|sensors.plus].csv
def write_output(dict_devices_sensor: dict[DeviceVersion, list[Sensor]], dict_devices_parameter: dict[DeviceParameters, list[Parameter]]):
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.mkdir(OUTPUT_DIR)

    sensors_all: list[SensorDump] = []
    params_all: list[ParameterDump] = []
    for device, sensors in dict_devices_sensor.items():
        sensors_all.extend([dump_sensor(sensor, device) for sensor in sensors])
        with open(os.path.join(OUTPUT_DIR, f'{device.device_name}.{device.version.first_version}.{device.version.last_version}.sensors.csv'), "w", encoding="utf-8") as text_file:
            text_file.write(CSV_HEADER)
            text_file.write(csv_from_sensors(sensors, device.device_name))

    for device_param, parameters in dict_devices_parameter.items():
        params_all.extend([dump_param(param, device_param) for param in parameters])
        with open(os.path.join(OUTPUT_DIR, f'{device_param.device_name}.{device_param.version.first_version}.{device_param.version.last_version}.params.basic.csv'), "w", encoding="utf-8") as text_file:
            text_file.write(CSV_HEADER)
            text_file.write(csv_from_parameters(parameters, device_param.device_name, False))

        with open(os.path.join(OUTPUT_DIR, f'{device_param.device_name}.{device_param.version.first_version}.{device_param.version.last_version}.params.plus.csv'), "w", encoding="utf-8") as text_file:
            text_file.write(CSV_HEADER)
            text_file.write(csv_from_parameters(parameters, device_param.device_name, True))

    if os.path.exists(KNOWN_DEVICES_EN_DIR):
        shutil.rmtree(KNOWN_DEVICES_EN_DIR)
    os.mkdir(KNOWN_DEVICES_EN_DIR)
    for known_device in known_devices:
        with open(os.path.join(KNOWN_DEVICES_EN_DIR, f'{known_device.slave_address:02x}.{known_device.device_name}.csv'), "w", encoding="utf-8") as text_file:
            latest_device_sensors = get_latest_sw_for_device(known_device.device_name, list(dict_devices_sensor.keys()))
            latest_device_params = get_latest_sw_for_device(known_device.device_name, list(dict_devices_parameter.keys()))
            text_file.write(CSV_HEADER)
            text_file.write(csv_known_device(dict_devices_sensor[latest_device_sensors], known_device.device_name, dict_devices_parameter[latest_device_params], True, f'{known_device.slave_address:02x}'))

    if os.path.exists(DUMP_DIR):
        shutil.rmtree(DUMP_DIR)
    os.mkdir(DUMP_DIR)

    # Write out JSON and CVS of all params and sensors for an further processing in different tools
    jsonpickle.set_encoder_options('json', sort_keys=True, indent=4)
    sensors_all.sort()
    params_all.sort()

    with open(os.path.join(DUMP_DIR, 'sensors.json'), "w", encoding="utf-8") as text_file:
        text_file.write(jsonpickle.dumps([sensor._asdict() for sensor in sensors_all]))
  
    with open(os.path.join(DUMP_DIR, 'params.json'), "w", encoding="utf-8") as text_file:
        text_file.write(jsonpickle.dumps([param._asdict() for param in params_all]))
  
    with open(os.path.join(DUMP_DIR, 'sensors.csv'), "w", encoding="utf-8") as text_file:
        csv_writer = csv.writer(text_file)
        keys_sensors = sensors_all[0]._fields
        print(f'CSV Dump Sensor keys: {keys_sensors}')
        csv_writer.writerow(keys_sensors)
        for sensor in sensors_all:
            csv_writer.writerow(sensor)

    with open(os.path.join(DUMP_DIR, 'params.csv'), "w", encoding="utf-8") as text_file:
        csv_writer = csv.writer(text_file)
        keys_params = params_all[0]._fields
        print(f'CSV Dump Params keys: {keys_params}')
        csv_writer.writerow(keys_params)
        for param in params_all:
            csv_writer.writerow(param)
