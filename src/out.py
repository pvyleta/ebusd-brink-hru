import os
import shutil
import csv

import jsonpickle # type: ignore

from dev import Device
from config_data import Parameter, DeviceParameters
from sensor_data import Sensor


OUTPUT_DIR = "ebusd-configuration"
DUMP_DIR = "dump"
CSV_HEADER = '# type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment,field2,part (m/s),datatypes/templates,divider/values,unit,comment,field3,part (m/s),datatypes/templates,divider/values,unit,comment,field4,part (m/s),datatypes/templates,divider/values,unit,comment,field5,part (m/s),datatypes/templates,divider/values,unit,comment\n'


# TODO Add comment to converters that were filled manually
# TODO Add original min/max/step/default as a comment to fields
# TODO filter out converter values based on the range for any given appliance - it is possible some ppliances only support some values

def multiplier_to_divider(multiplier: str):
    multiplier_float = float(multiplier)
    if multiplier_float < 1:
        return str(int(1 / multiplier_float))
    elif multiplier_float > 1:
        return str(-int(multiplier_float))
    else:
        return ""


def csv_line_sensor(sensor: Sensor):
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    assert sensor.converter
    values = sensor.converter.values
    type = sensor.converter.type

    return f'r,{sensor.device_name},{sensor.name_current.removeprefix('Current')},{sensor.name_description},,,4022,{sensor.id},,,{type},{values},{sensor.unit},\n'


def csv_line_param_read(param: Parameter):
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    datatype = datatype_from_sign(param.is_signed)
    if values := param.values:
        comment = '"min/max/step" fields of this enum message omitted'
        return f'r,{param.device_name},{param.name},{param.name},,,4050,{param.id},,,{datatype},{values},{param.unit},,,,IGN:3,,,,Default,,{datatype},{values},{param.unit},{comment}\n'
    else:
        values = multiplier_to_divider(param.multiplier)
        return f'r,{param.device_name},{param.name},{param.name},,,4050,{param.id},,,{datatype},{values},{param.unit},,Max,,{datatype},,{param.unit},,Min,,{datatype},,{param.unit},,Step,,{datatype},,{param.unit},,Default,,{datatype},,{param.unit},\n'


def csv_line_param_write(param: Parameter):
    # type (r[1-9];w;u),circuit,name,[comment],[QQ],ZZ,PBSB,[ID],field1,part (m/s),datatypes/templates,divider/values,unit,comment
    datatype = datatype_from_sign(param.is_signed)
    if not (values := param.values):
        values = multiplier_to_divider(param.multiplier)
    return f'w,{param.device_name},{param.name},{param.name},,,4080,{param.id},,,{datatype},{values},{param.unit},\n'


# TODO add length checks from CMDs
def datatype_from_sign(is_signed):
    if is_signed == "true":
        return "SIR"
    elif is_signed == "false":
        return "UIR"
    else:
        raise 0


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


# TODO rename Sensor to State?
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
    with open(os.path.join(DUMP_DIR, 'sensors.json'), "w", encoding="utf-8") as text_file:
        text_file.write(jsonpickle.dumps(sensors_all, text_file))
  
    params_all.sort()
    with open(os.path.join(DUMP_DIR, 'params.json'), "w", encoding="utf-8") as text_file:
        text_file.write(jsonpickle.dumps(params_all, text_file))

    with open(os.path.join(DUMP_DIR, 'sensors.csv'), "w", encoding="utf-8") as text_file:
        csv_writer = csv.writer(text_file)
        keys = sensors_all[0].__dict__.keys()
        csv_writer.writerow(keys)
        for sensor in sensors_all:
            csv_writer.writerow([getattr(sensor, key) for key in keys])

    # TODO unify the fals/False capitalization in the output for various fields
    with open(os.path.join(DUMP_DIR, 'params.csv'), "w", encoding="utf-8") as text_file:
        csv_writer = csv.writer(text_file)
        keys = params_all[0].__dict__.keys()
        csv_writer.writerow(keys)
        for param in params_all:
            csv_writer.writerow([getattr(param, key) for key in keys])
