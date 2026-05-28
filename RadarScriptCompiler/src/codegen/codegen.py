"""Python 3 module for the RadarScript code generator."""

from __future__ import annotations

from pathlib import Path


# This file defines the code generation stage responsible for translating
# intermediate instructions into target object or executable output.

Quadruple = tuple[str, str, str, str]

ARITHMETIC_MAP = {
    "+": "ADD",
    "-": "SUB",
    "*": "MUL",
    "/": "DIV",
}

COMPARISON_MAP = {
    ">": "GT",
    "<": "LT",
    "==": "EQ",
    ">=": "GTE",
    "<=": "LTE",
    "!=": "NEQ",
}


class CodeGenerator:
    """Convert RadarScript quadruples into stack-based pseudo-assembly."""

    def __init__(self) -> None:
        self.instructions: list[str] = []
        self.temp_definitions: dict[str, Quadruple] = {}

    def generate(self, quadruples: list[Quadruple]) -> list[str]:
        """Translate quadruples into pseudo-assembly."""
        self.instructions = []
        self.temp_definitions = self._collect_temp_definitions(quadruples)

        for quadruple in quadruples:
            operator, arg1, arg2, result = quadruple
            if self._is_temporary(result) and operator not in {"ALERTA", "REPORTE"}:
                continue
            self._translate_quadruple(quadruple)

        self.instructions.append("HALT")
        return self.instructions

    def export(self, ruta_salida: str) -> None:
        """Write generated pseudo-assembly to a .obj file."""
        Path(ruta_salida).write_text(formatear_codigo_objeto(self.instructions), encoding="utf-8")

    def _collect_temp_definitions(self, quadruples: list[Quadruple]) -> dict[str, Quadruple]:
        """Index quadruples that define temporaries."""
        definitions: dict[str, Quadruple] = {}
        for quadruple in quadruples:
            operator, _arg1, _arg2, result = quadruple
            if self._is_temporary(result) and operator not in {"IF_FALSE", "GOTO", "LABEL"}:
                definitions[result] = quadruple
        return definitions

    def _translate_quadruple(self, quadruple: Quadruple) -> None:
        """Translate one intermediate quadruple."""
        operator, arg1, arg2, result = quadruple

        if operator == "=":
            self._emit_assignment(arg1, result)
            return

        if operator == "IF_FALSE":
            self._emit_expression(arg1)
            self.instructions.append(f"JMPF {result}")
            return

        if operator == "GOTO":
            self.instructions.append(f"JMP {result}")
            return

        if operator == "LABEL":
            self.instructions.append(f"{result}:")
            return

        if operator == "ALERTA":
            self._emit_expression(arg1)
            self.instructions.append("ALERTA")
            return

        if operator == "REPORTE":
            self._emit_expression(arg1)
            self.instructions.append("REPORTE")
            return

        raise ValueError(f"Cuadruplo no soportado para codegen: {quadruple}")

    def _emit_assignment(self, source: str, target: str) -> None:
        """Emit object code for an assignment."""
        if self._is_temporary(source):
            self._emit_expression(source)
            self.instructions.append(f"STORE {target}")
            return

        self.instructions.append(f"MOV {target}, {source}")

    def _emit_expression(self, value: str) -> None:
        """Emit instructions that leave an expression result on the stack."""
        if not self._is_temporary(value):
            self.instructions.append(f"LOAD {value}")
            return

        if value not in self.temp_definitions:
            raise ValueError(f"Temporal no definido en codegen: {value}")

        operator, arg1, arg2, _result = self.temp_definitions[value]

        if operator in ARITHMETIC_MAP:
            self._emit_operand(arg1, use_push=False)
            self._emit_operand(arg2, use_push=True)
            self.instructions.append(ARITHMETIC_MAP[operator])
            return

        if operator in COMPARISON_MAP:
            self._emit_operand(arg1, use_push=False)
            self._emit_operand(arg2, use_push=True)
            self.instructions.append(COMPARISON_MAP[operator])
            return

        if operator == "CONCAT":
            self._emit_operand(arg1, use_push=False)
            self._emit_operand(arg2, use_push=False)
            self.instructions.append("CONCAT")
            return

        raise ValueError(f"Expresion temporal no soportada para codegen: {self.temp_definitions[value]}")

    def _emit_operand(self, value: str, use_push: bool) -> None:
        """Emit one operand for a stack-based operation."""
        if self._is_temporary(value):
            self._emit_expression(value)
            return

        instruction = "PUSH" if use_push else "LOAD"
        self.instructions.append(f"{instruction} {value}")

    def _is_temporary(self, value: str) -> bool:
        """Return True when a value name matches the temporary pattern."""
        return value.startswith("t") and value[1:].isdigit()


def formatear_codigo_objeto(instructions: list[str]) -> str:
    """Format object code with the academic project header."""
    lineas = ["Código objeto (.obj)", ""]
    lineas.extend(instructions)
    return "\n".join(lineas)


def generar_codigo_objeto(quadruples: list[Quadruple], ruta_salida: str) -> list[str]:
    """Generate and export pseudo-assembly from quadruples."""
    generator = CodeGenerator()
    instructions = generator.generate(quadruples)
    generator.export(ruta_salida)
    return instructions
