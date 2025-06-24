import json
import os


def load(filename):
    # loads the json content of a file
    # (error will be raised if file doesn't exist)

    file = {}
    with open(filename) as file:
        file = json.load(file)

    return file


def save(filename, content={}):
    # saves the json content to a file

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as outfile:
        json.dump(
            content,
            outfile,
            indent=2,
        )

    return outfile
