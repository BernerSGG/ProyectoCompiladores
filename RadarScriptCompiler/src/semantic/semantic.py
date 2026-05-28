"""Python 3 module for the RadarScript semantic analyzer."""

from __future__ import annotations

from pathlib import Path

try:
    from diagnostics import agregar_error, linea_con_error_lexico, linea_con_error_sintactico
except ImportError:
    from src.diagnostics import agregar_error, linea_con_error_lexico, linea_con_error_sintactico


# This file defines the semantic analysis stage, where symbol validation,
# type rules, and contextual checks for RadarScript are performed.

Node = dict[str, object]
SymbolTable = dict[str, str]
NUMERIC_TYPES = {"entero", "decimal"}
COMPARISON_OPERATORS = {">", "<", ">=", "<=", "==", "!="}
ARITHMETIC_OPERATORS = {"+", "-", "*", "/"}


class SemanticErrorRadar(Exception):
    """Represents a semantic analysis error with location information."""


class SemanticAnalyzer:
    """Perform semantic checks over a simple RadarScript AST."""

    def __init__(self) -> None:
        self.symbol_table: SymbolTable = {}

    def analyze(self, estructura: Node | list[Node]) -> SymbolTable:
        """Analyze a parser structure and return the resulting symbol table."""
        for statement in self._extract_body(estructura):
            self._analyze_statement(statement)
        return self.symbol_table

    def export_symbol_table(self, ruta_salida: str) -> None:
        """Write the symbol table to a .sym file."""
        Path(ruta_salida).write_text(formatear_tabla_simbolos(self.symbol_table), encoding="utf-8")

    def _extract_body(self, estructura: Node | list[Node]) -> list[Node]:
        """Normalize the parser structure to a flat statement list."""
        if isinstance(estructura, list):
            return estructura

        body = estructura.get("body", [])
        if isinstance(body, list):
            return body
        return []

    def _analyze_statement(self, node: Node) -> None:
        """Dispatch semantic analysis for a statement node."""
        line = int(node.get("line", 1))
        if linea_con_error_lexico(line) or linea_con_error_sintactico(line):
            return

        node_type = str(node.get("type"))

        if node_type == "declaration":
            self._analyze_declaration(node)
            return

        if node_type == "assignment":
            self._analyze_assignment(node)
            return

        if node_type == "if":
            self._analyze_condition(node["condition"], int(node["line"]), int(node["column"]))
            self._analyze_block(node.get("body", []))
            return

        if node_type == "while":
            self._analyze_condition(node["condition"], int(node["line"]), int(node["column"]))
            self._analyze_block(node.get("body", []))
            return

        if node_type == "call":
            self._infer_expression_type(node["argument"])

    def _analyze_block(self, body: object) -> None:
        """Analyze each statement in a block."""
        if not isinstance(body, list):
            return
        for statement in body:
            if isinstance(statement, dict):
                self._analyze_statement(statement)

    def _analyze_declaration(self, node: Node) -> None:
        """Register a declared variable in the symbol table."""
        name = str(node["name"])
        var_type = str(node["var_type"])
        line = int(node["line"])
        column = int(node["column"])

        if name in self.symbol_table:
            agregar_error("Error semántico", line, column, f"variable '{name}' duplicada")
            return

        self.symbol_table[name] = var_type

    def _analyze_assignment(self, node: Node) -> None:
        """Validate an assignment target and value type."""
        target = str(node["target"])
        line = int(node["line"])
        column = int(node["column"])

        if target not in self.symbol_table:
            agregar_error("Error semántico", line, column, f"variable '{target}' no declarada")
            target_type = "desconocido"
        else:
            target_type = self.symbol_table[target]

        value_type = self._infer_expression_type(node["value"])
        if target_type != "desconocido" and value_type != "desconocido":
            if not self._is_assignment_compatible(target_type, value_type):
                agregar_error("Error semántico", line, column, f"tipo incorrecto en asignación a '{target}'")

    def _analyze_condition(self, node: object, line: int, column: int) -> None:
        """Validate that a condition can be used in control flow."""
        condition_type = self._infer_expression_type(node)
        if condition_type not in {"booleano", "desconocido"}:
            agregar_error("Error semántico", line, column, "la condición debe ser de tipo booleano")

    def _infer_expression_type(self, node: object) -> str:
        """Infer the resulting type of an expression node."""
        if not isinstance(node, dict):
            return "desconocido"
        if node.get("error"):
            return "desconocido"
        line = int(node.get("line", 1))
        if linea_con_error_lexico(line) or linea_con_error_sintactico(line):
            return "desconocido"

        node_type = str(node.get("type"))

        if node_type == "literal":
            return str(node["value_type"])

        if node_type == "identifier":
            name = str(node["name"])
            line = int(node["line"])
            column = int(node["column"])
            if name not in self.symbol_table:
                agregar_error("Error semántico", line, column, f"variable '{name}' no declarada")
                return "desconocido"
            return self.symbol_table[name]

        if node_type == "binary_op":
            return self._infer_binary_operation_type(node)

        return "desconocido"

    def _infer_binary_operation_type(self, node: Node) -> str:
        """Infer and validate the type of a binary operation."""
        operator = str(node["operator"])
        left_type = self._infer_expression_type(node["left"])
        right_type = self._infer_expression_type(node["right"])
        line = int(node["line"])
        column = int(node["column"])

        if operator in ARITHMETIC_OPERATORS:
            if operator == "+" and left_type == "cadena" and right_type == "cadena":
                node["runtime_operator"] = "CONCAT"
                return "cadena"

            if left_type not in NUMERIC_TYPES or right_type not in NUMERIC_TYPES:
                agregar_error("Error semántico", line, column, f"operador '{operator}' requiere operandos numéricos")
                return "desconocido"

            node["runtime_operator"] = operator
            return "decimal" if "decimal" in {left_type, right_type} else "entero"

        if operator in COMPARISON_OPERATORS:
            node["runtime_operator"] = operator
            if operator in {">", "<", ">=", "<="}:
                if left_type not in NUMERIC_TYPES or right_type not in NUMERIC_TYPES:
                    agregar_error("Error semántico", line, column, f"operador '{operator}' requiere operandos numéricos")
                    return "desconocido"
                return "booleano"

            if left_type != right_type and not (
                left_type in NUMERIC_TYPES and right_type in NUMERIC_TYPES
            ):
                agregar_error("Error semántico", line, column, "comparación entre tipos incompatibles")
                return "desconocido"
            return "booleano"

        agregar_error("Error semántico", line, column, f"operador no soportado '{operator}'")
        return "desconocido"

    def _is_assignment_compatible(self, target_type: str, value_type: str) -> bool:
        """Return True if a value type can be assigned to the target type."""
        if target_type == value_type:
            return True
        return target_type == "decimal" and value_type == "entero"


def analizar_semantica(estructura: Node | list[Node], ruta_salida: str) -> SymbolTable:
    """Run semantic analysis and export the resulting symbol table."""
    analyzer = SemanticAnalyzer()
    tabla = analyzer.analyze(estructura)
    analyzer.export_symbol_table(ruta_salida)
    return tabla


def formatear_tabla_simbolos(tabla_simbolos: SymbolTable) -> str:
    """Format the symbol table aligned to the left using dynamic width."""
    lineas = ["Tabla de símbolos (.sym)", ""]
    if not tabla_simbolos:
        return "\n".join(lineas)

    max_len = max(len(nombre) for nombre in tabla_simbolos.keys())
    for identificador, tipo in tabla_simbolos.items():
        lineas.append(f"{identificador:<{max_len}} : {tipo}")
    return "\n".join(lineas)
