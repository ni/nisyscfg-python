import ast
from pathlib import Path

import nisyscfg.hardware_resource
import nisyscfg.properties


def _annotated_names(statements: list[ast.stmt]) -> set[str]:
    return {
        statement.target.id
        for statement in statements
        if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name)
    }


def _class_node(module: ast.Module, name: str) -> ast.ClassDef:
    for statement in ast.walk(module):
        if isinstance(statement, ast.ClassDef) and statement.name == name:
            return statement
    raise AssertionError("Class {} was not found".format(name))


def _type_checking_names(class_node: ast.ClassDef) -> set[str]:
    for statement in class_node.body:
        if (
            isinstance(statement, ast.If)
            and isinstance(statement.test, ast.Name)
            and statement.test.id == "TYPE_CHECKING"
        ):
            return _annotated_names(statement.body)
    raise AssertionError("TYPE_CHECKING declarations were not found")


def _runtime_property_names(target: type) -> set[str]:
    return {
        name
        for name, value in vars(target).items()
        if isinstance(value, nisyscfg.properties.Property)
    }


def test_hardware_resource_property_declarations_match_property_bag() -> None:
    source_path = Path(nisyscfg.hardware_resource.__file__)
    module = ast.parse(source_path.read_text(encoding="utf-8"))

    hardware_resource = _class_node(module, "HardwareResource")
    declared = _type_checking_names(hardware_resource) - {"pxi", "xnet"}
    assert declared == _runtime_property_names(nisyscfg.hardware_resource.HardwareResource)

    pxi_descriptor = vars(nisyscfg.hardware_resource.HardwareResource)["pxi"]
    assert isinstance(pxi_descriptor, nisyscfg.properties.Expert)
    pxi_protocol = _class_node(module, "_PxiResourceProperties")
    assert _annotated_names(pxi_protocol.body) == _runtime_property_names(pxi_descriptor._expert)

    xnet_descriptor = vars(nisyscfg.hardware_resource.HardwareResource)["xnet"]
    assert isinstance(xnet_descriptor, nisyscfg.properties.Expert)
    xnet_protocol = _class_node(module, "_XnetResourceProperties")
    assert _annotated_names(xnet_protocol.body) == _runtime_property_names(xnet_descriptor._expert)
