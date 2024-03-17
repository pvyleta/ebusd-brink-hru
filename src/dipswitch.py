# Based on manual for Set: 531780

class Dipswitch:
    def __init__(self, is_plus: bool, value: int, type: str = ""):
        self.is_plus = is_plus
        self.value = value
        self.type = type

# NOTE can we make this in ebusd as two fields, one 4bit, the other 1bit? LSB marks plus/basic
dipswitch_dict = {
    'Excellent180Basic'   : Dipswitch(False, 0b11111),
    'Excellent180Plus'    : Dipswitch(True,  0b11110),
    'Excellent300Basic'   : Dipswitch(False, 0b10111, 'type 4/0'),
    'Excellent300Plus'    : Dipswitch(True,  0b10110, 'type 4/0'),
    'Excellent300Basic'   : Dipswitch(False, 0b00111, 'type 2/2 and 3/1'),
    'Excellent300Plus'    : Dipswitch(True,  0b00110, 'type 2/2 and 3/1'),
    'Excellent400Basic'   : Dipswitch(False, 0b11101, 'type 4/0'),
    'Excellent400Plus'    : Dipswitch(True,  0b11100, 'type 4/0'),
    'Excellent400Basic'   : Dipswitch(False, 0b00101, 'type 2/2 and 3/1'),
    'Excellent400Plus'    : Dipswitch(True,  0b00100, 'type 2/2 and 3/1'),
    'Excellent450Basic'   : Dipswitch(False, 0b11011, 'type 4/0'),
    'Excellent450Plus'    : Dipswitch(True,  0b11010, 'type 4/0'),
    'RenoventElan300Basic': Dipswitch(False, 0b00011),
    'RenoventElan300Plus' : Dipswitch(True,  0b00010),
    'Sky150Basic'         : Dipswitch(False, 0b10011),
    'Sky150Plus'          : Dipswitch(True,  0b10010),
    'Sky200Basic'         : Dipswitch(False, 0b01001),
    'Sky200Plus'          : Dipswitch(True,  0b01000),
    'Sky300Basic'         : Dipswitch(False, 0b10101),
    'Sky300Plus'          : Dipswitch(True,  0b10100),
}

def get_ebusd_values_string():
    return ";".join([f'{dip.value}={dev}' for dev, dip in dipswitch_dict.items()])
