"""Python 3 module for the RadarScript intermediate representation."""

from __future__ import annotations

from pathlib import Path


# This file defines the intermediate code generation stage used to transform
# parsed and validated structures into an internal representation.

Node = dict[str, object]
Quadruple = tuple[str, str, str, str]
DISPLAY_OPERATORS = {
    "IF_FALSE": "JF",
    "GOTO": "JMP",
}


class IntermediateCodeGenerator:
    """Generate quadruples from a simple RadarScript AST."""

    def __init__(self) -> None:
        self.quadruples: list[Quadruple] = []
        self.temp_counter = 0
        self.label_counter = 0

    def generate(self, estructura: Node | list[Node]) -> list[Quadruple]:
        """Generate quadruples for a full program or statement list."""
        self.quadruples = []
        self.temp_counter = 0
        self.label_counter = 0

        for statement in self._extract_body(estructura):
            self._generate_statement(statement)

        return self.quadruples

    def export(self, ruta_salida: str) -> None:
        """Write the generated quadruples to a .int file."""
        contenido = formatear_codigo_intermedio(self.quadruples)
        Path(ruta_salida).write_text(contenido, encoding="utf-8")

    def _extract_body(self, estructura: Node | list[Node]) -> list[Node]:
        """Normalize the parser structure to a list of statements."""
        if isinstance(estructura, list):
            return estructura

        if estructura.get("type") == "program":
            body = estructura.get("body", [])
            if isinstance(body, list):
                return body

        raise ValueError("La estructura del programa no es valida para generar codigo intermedio.")

    def _generate_statement(self, node: Node) -> None:
        """Generate quadruples for a single statement node."""
        node_type = str(node.get("type"))

        if node_type == "declaration":
            return

        if node_type == "assignment":
            value = self._generate_expression(node["value"])
            self._emit("=", value, "", str(node["target"]))
            return

        if node_type == "call":
            argument = self._generate_expression(node["argument"])
            self._emit(str(node["name"]).upper(), argument, "", "")
            return

        if node_type == "if":
            self._generate_if(node)
            return

        if node_type == "while":
            self._generate_while(node)
            return

        raise ValueError(f"Nodo no soportado en codigo intermedio: {node_type}")

    def _generate_if(self, node: Node) -> None:
        """Generate quadruples for a conditional block."""
        false_label = self._new_label()
        condition = self._generate_expression(node["condition"])
        self._emit("IF_FALSE", condition, "", false_label)
        self._generate_block(node.get("body", []))
        self._emit("LABEL", "", "", false_label)

    def _generate_while(self, node: Node) -> None:
        """Generate quadruples for a while loop."""
        start_label = self._new_label()
        end_label = self._new_label()

        self._emit("LABEL", "", "", start_label)
        condition = self._generate_expression(node["condition"])
        self._emit("IF_FALSE", condition, "", end_label)
        self._generate_block(node.get("body", []))
        self._emit("GOTO", "", "", start_label)
        self._emit("LABEL", "", "", end_label)

    def _generate_block(self, body: object) -> None:
        """Generate quadruples for each statement in a block."""
        if not isinstance(body, list):
            raise ValueError("Bloque invalido para codigo intermedio.")
        for statement in body:
            if not isinstance(statement, dict):
                raise ValueError("Sentencia invalida en bloque intermedio.")
            self._generate_statement(statement)

    def _generate_expression(self, node: object) -> str:
        """Generate quadruples for an expression and return its result name."""
        if not isinstance(node, dict):
            raise ValueError("Expresion invalida para codigo intermedio.")

        node_type = str(node.get("type"))

        if node_type == "identifier":
            return str(node["name"])

        if node_type == "literal":
            return str(node["value"])

        if node_type == "binary_op":
            left = self._generate_expression(node["left"])
            right = self._generate_expression(node["right"])
            temp = self._new_temp()
            operator = str(node.get("runtime_operator", node["operator"]))
            self._emit(operator, left, right, temp)
            return temp

        raise ValueError(f"Expresion no soportada en codigo intermedio: {node_type}")

    def _new_temp(self) -> str:
        """Return a fresh temporary name."""
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def _new_label(self) -> str:
        """Return a fresh label name."""
        self.label_counter += 1
        return f"L{self.label_counter}"

    def _emit(self, operator: str, arg1: str, arg2: str, result: str) -> None:
        """Append a quadruple to the intermediate code output."""
        self.quadruples.append((operator, arg1, arg2, result))


def generar_codigo_intermedio(
    estructura: Node | list[Node], ruta_salida: str
) -> list[Quadruple]:
    """Generate and export quadruples for a RadarScript program."""
    generator = IntermediateCodeGenerator()
    quadruples = generator.generate(estructura)
    generator.export(ruta_salida)
    return quadruples


def _normalizar_operador(operator: str) -> str:
    """Return the academic display name for an operator."""
    return DISPLAY_OPERATORS.get(operator, operator)


def _normalizar_campo(value: str) -> str:
    """Replace empty fields with '-' for display."""
    if value in {"", "None"}:
        return "-"
    return value


def formatear_cuadruplo(quadruple: Quadruple) -> str:
    """Format one quadruple using the academic output style."""
    operator, arg1, arg2, result = quadruple
    operator = _normalizar_operador(operator)
    arg1 = _normalizar_campo(arg1)
    arg2 = _normalizar_campo(arg2)
    result = _normalizar_campo(result)
    return f"({operator}, {arg1}, {arg2}, {result})"


def formatear_codigo_intermedio(quadruples: list[Quadruple]) -> str:
    """Format a quadruple sequence for .int files and console output."""
    lineas = ["Código intermedio (.int)", ""]
    lineas.extend(formatear_cuadruplo(quadruple) for quadruple in quadruples)
    return "\n".join(lineas)
