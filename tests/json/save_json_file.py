import json

file_path = "/home/user/Projects/pyCharm/pyRobotics/tests/json/json_file.json"
data = {"hmin": 45, "hmax": 255}

with open(file_path, "w", encoding="utf-8") as file:
    json.dump(data, file)

