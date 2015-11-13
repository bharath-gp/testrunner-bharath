import json
from os import path


class JSONGenerator:
    def __init__(self, template, input_dict):
        pwd = path.dirname(__file__)
        file_path = path.join(pwd, "directory_structure.json")
        self.template = file_path

        self.input = input_dict
        self.object = None

    def test(self, obj, template_json):
        if isinstance(template_json, dict):
            for key in template_json.keys():
                if isinstance(template_json[key], unicode):
                    if template_json[key]:
                        obj[key] = template_json[key]
                    else:
                        obj[key] = self.input[key]
                    continue
                if isinstance(template_json[key], list):
                    obj[key] = []
                    if template_json[key]:
                        obj[key].extend(template_json[key])
                    elif self.input[key]:
                        obj[key].extend(self.input[key])
                    continue
                if isinstance(template_json[key], dict):
                    if key in self.input:
                        iterate = self.input[key]
                        if not isinstance(iterate, list):
                            iterate = [iterate]
                        for item in iterate:
                            obj[item] = {}
                            self.test(obj[item], template_json[key])
                    else:
                        obj[key] = {}
                        self.test(obj[key], template_json[key])

    def generate(self):
        input1 = json.load(open(self.template, 'r'))
        self.object = {}
        self.test(self.object, input1)