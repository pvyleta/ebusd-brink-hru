

import xml.etree.ElementTree as ET
import re
from typing import Dict

# This functon was written by ChatGPT after pretty painful back and forth asking and me debugging the code...
def parse_xaml(file_name: str) -> Dict[str, str]:
    tree: ET.ElementTree = ET.parse(file_name)
    root: ET.Element = tree.getroot()

    # Create a dictionary to store key-value pairs
    result: Dict[str, str] = {}

    # Iterate through the XML tree
    for elem in root.iter():
        # Check if the element is a String element within a ResourceDictionary
        if elem.tag.endswith('}String'):
            # Extract Key and Value attributes
            element_key = elem.attrib.get("{http://schemas.microsoft.com/winfx/2006/xaml}Key")
            if element_key is not None:
                element_value = elem.text.strip() if elem.text is not None else ""
                result[element_key] = element_value

    return result

english_dict = parse_xaml('./BCSServiceTool/resources/languages/stringresources.xaml')

def get_english_name(param_name: str) -> str:
    if name := english_dict.get(param_name):
        return name
    elif param_name == 'parameterDescriptionDeviceType':
        # This is currently known to be the only one missing parameter from the dictionary
        return 'Device Type'
    else:
        print (f'ERROR english_dict: missing {param_name}')
        return param_name
    
def to_camel_case(text):
    # Find all alphanumeric sequences
    words = re.findall(r'[a-zA-Z0-9]+', text)
    # Convert each word to CamelCase
    camel_case_words = []
    for word in words:
        if word.isalpha():
            camel_case_word = word[0].upper() + word[1:]
        else:
            camel_case_word = word
        camel_case_words.append(camel_case_word)
    # Join the words to form the CamelCase text
    return ''.join(camel_case_words)


def get_name(param_name: str, language: str = 'en'):
    return to_camel_case(get_english_name(param_name))