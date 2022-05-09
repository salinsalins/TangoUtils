import json


class Configuration(dict):
    def __init__(self, file_name: str = None, default: dict = None):
        if default is None:
            default = {}
        super().__init__(default)
        self.file_name = file_name
        self.read()

    def get(self, key, default=None):
        try:
            result = super().get(key, default)
            if default is not None and result is not None:
                result = type(default)(result)
        except:
            result = default
        self[key] = result
        return result

    # def __getitem__(self, key):
    #     return self.data[key]
    #
    # def __setitem__(self, key, value):
    #     self.data[key] = value
    #     return
    #
    # def __contains__(self, key):
    #     return key in self.data

    def find(self, value):
        for key in self:
            if self[key] == value:
                return key
        return None

    def read(self, file_name=None, append=True):
        if file_name is not None:
            self.file_name = file_name
        try:
            # Read config from file
            with open(self.file_name, 'r') as configfile:
                data = json.loads(configfile.read())
            # import data
            if not append:
                self.clear()
            for d in data:
                self[d] = data[d]
            return True
        except:
            return False

    def write(self, file_name=None):
        if file_name is None:
            file_name = self.file_name
        else:
            self.file_name = file_name
        if not file_name:
            return False
        with open(file_name, 'w') as configfile:
            configfile.write(json.dumps(self, indent=4))
        return True
