import os
import shutil
import csv

import jsonpickle # type: ignore

from dev import Device
from config_data import Parameter, DeviceParameters
from sensor_data import Sensor
from params import INT16, UINT16


OUTPUT_DIR = "ebusd-configuration"
DUMP_DIR = "dump"
CSV_HEADER = '# type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment,field2,part (m/s),datatypes/templates,divider/values,unit,comment,field3,part (m/s),datatypes/templates,divider/values,unit,comment,field4,part (m/s),datatypes/templates,divider/values,unit,comment,field5,part (m/s),datatypes/templates,divider/values,unit,comment\n'

def multiplier_to_divider(multiplier: float) -> str:
    if multiplier < 1.0:
        return str(int(1 / multiplier))
    elif multiplier > 1.0:
        return str(-int(multiplier))
    else:
        return ""


def csv_line_sensor(sensor: Sensor) -> str:
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    assert sensor.converter
    values = sensor.converter.values
    type = sensor.converter.type

    return f'r,{sensor.device_name},{sensor.name_current.removeprefix('Current')},{sensor.name_description},,,4022,{sensor.id:02x},,,{type},{values},{sensor.unit},\n'


def csv_line_param_read(param: Parameter) -> str:
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    datatype = convert_to_ebus_datatype(param.datatype)
    if values := param.values:
        comment = f'[default:{param.field_default}] - min/max/step fields of enum message omitted'
        return f'r,{param.device_name},{param.name},{param.name},,,4050,{param.id:02x},,,{datatype},{values},{param.unit},,,,IGN:3,,,,Default,,{datatype},{values},{param.unit},{comment}\n'
    else:
        values = multiplier_to_divider(param.multiplier)
        return f'r,{param.device_name},{param.name},{param.name},,,4050,{param.id:02x},,,{datatype},{values},{param.unit},,Min,,{datatype},,{param.unit},[min:{param.field_min}],Max,,{datatype},,{param.unit},[max:{param.field_max}],Step,,{datatype},,{param.unit},[step:{param.field_step}],Default,,{datatype},,{param.unit},[default:{param.field_default}]\n'


def csv_line_param_write(param: Parameter) -> str:
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    datatype = convert_to_ebus_datatype(param.datatype)
    if not (values := param.values):
        values = multiplier_to_divider(param.multiplier)
    return f'w,{param.device_name},{param.name},{param.name},,,4080,{param.id:02x},,,{datatype},{values},{param.unit},[min:{param.field_min},max:{param.field_max},step:{param.field_step},default:{param.field_default}]\n'


def convert_to_ebus_datatype(datatype: str) -> str:
    if datatype == INT16:
        return "SIR"
    elif datatype == UINT16:
        return "UIR"
    else:
        raise RuntimeError(f'unexpected datatype {datatype}')


def csv_from_sensors(sensors):
    file_str = CSV_HEADER
    for sensor in sensors:
        file_str += csv_line_sensor(sensor)
    return file_str


def csv_from_device_param(parameters: list[Parameter], is_plus: bool):
    file_str = CSV_HEADER
    for param in parameters:
        if is_plus or not param.is_plus_only: # Output if device is plus or param does not require plus 
            file_str += csv_line_param_read(param)
            if not param.is_read_only:
                file_str += csv_line_param_write(param)
    return file_str


def dump_sensor(sensor: Sensor) -> dict[str, str]:
    dump_sensor_dict: dict[str, str] = {}
    dump_sensor_dict['device_name'] = sensor.device_name
    dump_sensor_dict['first_version'] = str(sensor.first_version)
    dump_sensor_dict['last_version'] = str(sensor.last_version)
    dump_sensor_dict['name'] = sensor.name_current.removeprefix('Current')
    dump_sensor_dict['id'] = f'0x{sensor.id:02x}'
    dump_sensor_dict['unit'] = sensor.unit
    dump_sensor_dict['datatype'] = sensor.datatype
    dump_sensor_dict['multiplier'] = str(sensor.converter.multiplier) if sensor.converter else "null"
    dump_sensor_dict['values'] = sensor.converter.values if sensor.converter else "null"
    dump_sensor_dict['length'] = str(sensor.converter.length) if sensor.converter else "null"
    return dump_sensor_dict


def dump_param(param: Parameter) -> dict[str, str]:
    dump_param_dict: dict[str, str] = {}
    dump_param_dict['device_name'] = param.device_name
    dump_param_dict['first_version'] = str(param.first_version)
    dump_param_dict['last_version'] = str(param.last_version)
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
    return dump_param_dict


# Contents of output_dir are always cleaned before writing
# File format is [device_name].[lowest_sw_version].[highest_sw_version].[params|sensors.basic|sensors.plus].csv
def write_output(dict_devices_sensor: dict[Device, list[Sensor]], dict_devices_parameter: dict[DeviceParameters, list[Parameter]]):
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.mkdir(OUTPUT_DIR)

    sensors_all: list[Sensor] = []
    params_all: list[Parameter] = []
    for device, sensors in dict_devices_sensor.items():
        sensors_all.extend(sensors)
        with open(os.path.join(OUTPUT_DIR, f'{device.name}.{device.first_version}.{device.last_version}.sensors.csv'), "w", encoding="utf-8") as text_file:
            text_file.write(csv_from_sensors(sensors))

    for device_param, parameters in dict_devices_parameter.items():
        params_all.extend(parameters)
        with open(os.path.join(OUTPUT_DIR, f'{device_param.name}.{device_param.first_version}.{device_param.last_version}.params.basic.csv'), "w", encoding="utf-8") as text_file:
            text_file.write(csv_from_device_param(parameters, False))

        with open(os.path.join(OUTPUT_DIR, f'{device_param.name}.{device_param.first_version}.{device_param.last_version}.params.plus.csv'), "w", encoding="utf-8") as text_file:
            text_file.write(csv_from_device_param(parameters, True))

    if os.path.exists(DUMP_DIR):
        shutil.rmtree(DUMP_DIR)
    os.mkdir(DUMP_DIR)

    # Write out JSON and CVS of all params and sensors for an further processing in different tools
    jsonpickle.set_encoder_options('json', sort_keys=True, indent=4)
    sensors_all.sort()
    params_all.sort()
    sensors_dump = [dump_sensor(sensor) for sensor in sensors_all]
    params_dump = [dump_param(param) for param in params_all]

    with open(os.path.join(DUMP_DIR, 'sensors.json'), "w", encoding="utf-8") as text_file:
        text_file.write(jsonpickle.dumps(sensors_dump))
  
    with open(os.path.join(DUMP_DIR, 'params.json'), "w", encoding="utf-8") as text_file:
        text_file.write(jsonpickle.dumps(params_dump))
  
    with open(os.path.join(DUMP_DIR, 'sensors.csv'), "w", encoding="utf-8") as text_file:
        csv_writer = csv.writer(text_file)
        keys = sensors_dump[0].keys()
        print(f'CSV Dump Sensor keys: {keys}')
        csv_writer.writerow(keys)
        for sensor in sensors_dump:
            csv_writer.writerow(sensor.values())

    with open(os.path.join(DUMP_DIR, 'params.csv'), "w", encoding="utf-8") as text_file:
        csv_writer = csv.writer(text_file)
        keys = params_dump[0].keys()
        print(f'CSV Dump Params keys: {keys}')
        csv_writer.writerow(keys)
        for param in params_dump:
            csv_writer.writerow(param.values())
