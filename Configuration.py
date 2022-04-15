import json


class Configuration:
    def __init__(self, file_name=None, default=None):
        if default is None:
            default = {}
        self.data = default
        self.file_name = None
        self.read(file_name)

    def get(self, name, default=None):
        try:
            result = self.data.get(name, default)
            if default is not None:
                result = type(default)(result)
        except:
            result = default
        self.data[name] = result
        return result

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value
        return

    def __contains__(self, key):
        return key in self.data

    def find(self, value):
        for key in self.data:
            if self.data[key] == value:
                return key
        return None

    def read(self, file_name, append=True):
        try:
            self.file_name = file_name
            # Read config from file
            with open(file_name, 'r') as configfile:
                data = json.loads(configfile.read())
            # import data
            if append:
                for d in data:
                    self.data[d] = data[d]
            else:
                self.data = data
            return True
        except:
            return False

    def write(self, file_name=None):
        if file_name is None:
            file_name = self.file_name
        if file_name is None:
            return False
        with open(file_name, 'w') as configfile:
            configfile.write(json.dumps(self.data, indent=4))
        return True
