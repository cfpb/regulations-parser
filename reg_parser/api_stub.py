import codecs
import json

def get_regulation_as_json(regulations_json_file):
    f = codecs.open(regulations_json_file, encoding='utf-8')
    return json.load(f)
