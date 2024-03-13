class Device:
    def __init__(self, name: str, view_no: str, first_version: str, last_version: str):
        self.name = name
        self.view_no = view_no
        self.first_version = first_version
        self.last_version = last_version

    def __eq__(self, other):
        return str(self) == str(other)
    
    def __str__(self):
        return str([vars(self)[key] for key in sorted(vars(self).keys())])
    
    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return str(self)
    
class DeviceView:
    def __init__(self, name, view_no):
        self.name = name
        self.view_no = view_no

    def __eq__(self, other):
        return str(self) == str(other)
    
    def __str__(self):
        return str([vars(self)[key] for key in sorted(vars(self).keys())])
    
    def __hash__(self):
        return hash(str(self))
    
    def __repr__(self):
        return str(self)
    