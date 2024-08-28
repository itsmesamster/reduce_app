import pathlib
from xml.dom.minidom import parse


file_path = pathlib.Path(__file__).parent.resolve()


DEVELOPMENT_PROBLEM_RESPONSE_01_XML = parse(
    f"{file_path}/development_problem_response.xml"
).toxml()


with open(f"{file_path}/development_problem_response.yaml", "r") as f:
    DEVELOPMENT_PROBLEM_RESPONSE_01_YAML = f.read()
