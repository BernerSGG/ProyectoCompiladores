"""Python 3 module for the RadarScript syntax parser."""

from __future__ import annotations

try:
    from diagnostics import agregar_error, linea_con_error_lexico, linea_critica, marcar_linea_critica
except ImportError:
    from src.diagnostics import agregar_error, linea_con_error_lexico, linea_critica, marcar_linea_critica


# This file defines the parser responsible for consuming tokens and building
# the syntactic structure of a RadarScript program.

Token = tuple[str, str, int, int]

DECLARATION_TYPES = {"entero", "decimal", "cadena", "booleano"}
BLOCK_ENDERS = {"fin"}
RELATIONAL_OPERATORS = {">", "<", ">=", "<=", "==", "!="}
ADDITIVE_OPERATORS = {"+", "-"}
MULTIPLICATIVE_OPERATORS = {"*", "/"}
BUILTIN_FUNCTIONS = {"alerta", "reporte"}


class SyntaxErrorRadar(Exception):
    """Represents a RadarScript syntax error with location information."""


class Parser:
    """Recursive descent parser for RadarScript token streams."""

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.position = 0
        self.ast: dict[str, object] = {"type": "program", "name": "desconocido", "line": 1, "column": 1, "body": []}

    def current_token(self) -> Token | None:
        """Return the current token or None if the stream is exhausted."""
        if self.position >= len(self.tokens):
            return None
        return self.tokens[self.position]

    def advance(self) -> Token | None:
        """Consume and return the current token."""
        token = self.current_token()
        if token is not None:
            self.position += 1
        return token

    def parse(self) -> bool:
        """Validate the full token stream and build a partial AST."""
        self.ast = self.parse_programa()
        return True

    def parse_programa(self) -> dict[str, object]:
        """Parse the main RadarScript program structure."""
        program_token = self.expect("PALABRA_RESERVADA", "programa", "se esperaba 'programa'")
        program_name = self.expect("IDENTIFICADOR", description="se esperaba identificador de programa")
        self.expect("SIMBOLO", ";", "se esperaba ';'")

        body: list[dict[str, object]] = []
        while self.current_token() is not None:
            if linea_con_error_lexico(self.current_token()[2]):
                self.skip_current_line()
                continue
            if self.is_declaration():
                declaration = self.parse_declaracion()
                if declaration is not None:
                    body.append(declaration)
            else:
                statement = self.parse_sentencia()
                if statement is not None:
                    body.append(statement)

        return {
            "type": "program",
            "name": program_name[1],
            "line": program_token[2],
            "column": program_token[3],
            "body": body,
        }

    def parse_declaracion(self) -> dict[str, object] | None:
        """Parse a variable declaration."""
        type_token = self.expect("TIPO", description="se esperaba tipo de dato")
        identifier = self.expect("IDENTIFICADOR", description="se esperaba identificador")
        self.expect("SIMBOLO", ";", "se esperaba ';'")
        return {
            "type": "declaration",
            "var_type": type_token[1],
            "name": identifier[1],
            "line": type_token[2],
            "column": type_token[3],
        }

    def parse_sentencia(self) -> dict[str, object] | None:
        """Parse a generic executable statement."""
        token = self.current_token()
        if token is None:
            return None

        token_type, lexeme, line, column = token

        if linea_con_error_lexico(line):
            self.skip_current_line()
            return None

        if token_type == "IDENTIFICADOR":
            return self.parse_asignacion()

        if token_type == "PALABRA_RESERVADA" and lexeme == "si":
            return self.parse_condicional()

        if token_type == "PALABRA_RESERVADA" and lexeme == "mientras":
            return self.parse_ciclo()

        if token_type == "PALABRA_RESERVADA" and lexeme in BUILTIN_FUNCTIONS:
            return self.parse_funcion()

        agregar_error("Error sintáctico", line, column, f"token inesperado '{lexeme}'", critical=True)
        marcar_linea_critica(line)
        self.synchronize()
        return None

    def parse_asignacion(self) -> dict[str, object]:
        """Parse an assignment statement."""
        identifier = self.expect("IDENTIFICADOR", description="se esperaba identificador")
        self.expect("OPERADOR", "=", "se esperaba '='")
        expression = self.parse_comparacion()
        if expression.get("error"):
            self.synchronize()
        self.expect("SIMBOLO", ";", "se esperaba ';'")
        return {
            "type": "assignment",
            "target": identifier[1],
            "value": expression,
            "line": identifier[2],
            "column": identifier[3],
        }

    def parse_condicional(self) -> dict[str, object]:
        """Parse a conditional block."""
        token = self.expect("PALABRA_RESERVADA", "si", "se esperaba 'si'")
        condition = self.parse_condicion()
        if condition.get("error"):
            self.synchronize_to_block_end()
            self.expect("PALABRA_RESERVADA", "fin", "se esperaba 'fin'")
            return {
                "type": "if",
                "condition": condition,
                "body": [],
                "line": token[2],
                "column": token[3],
            }

        entonces = self.expect("PALABRA_RESERVADA", "entonces", "se esperaba 'entonces'")
        if entonces[1] != "entonces":
            self.synchronize_to_block_end()
            self.expect("PALABRA_RESERVADA", "fin", "se esperaba 'fin'")
            return {
                "type": "if",
                "condition": condition,
                "body": [],
                "line": token[2],
                "column": token[3],
            }
        body = self.parse_bloque()
        self.expect("PALABRA_RESERVADA", "fin", "se esperaba 'fin'")
        return {
            "type": "if",
            "condition": condition,
            "body": body,
            "line": token[2],
            "column": token[3],
        }

    def parse_ciclo(self) -> dict[str, object]:
        """Parse a while loop block."""
        token = self.expect("PALABRA_RESERVADA", "mientras", "se esperaba 'mientras'")
        condition = self.parse_condicion()
        if condition.get("error"):
            self.synchronize_to_block_end()
            self.expect("PALABRA_RESERVADA", "fin", "se esperaba 'fin'")
            return {
                "type": "while",
                "condition": condition,
                "body": [],
                "line": token[2],
                "column": token[3],
            }

        hacer = self.expect("PALABRA_RESERVADA", "hacer", "se esperaba 'hacer'")
        if hacer[1] != "hacer":
            self.synchronize_to_block_end()
            self.expect("PALABRA_RESERVADA", "fin", "se esperaba 'fin'")
            return {
                "type": "while",
                "condition": condition,
                "body": [],
                "line": token[2],
                "column": token[3],
            }
        body = self.parse_bloque()
        self.expect("PALABRA_RESERVADA", "fin", "se esperaba 'fin'")
        return {
            "type": "while",
            "condition": condition,
            "body": body,
            "line": token[2],
            "column": token[3],
        }

    def parse_funcion(self) -> dict[str, object]:
        """Parse a built-in function call."""
        token = self.expect("PALABRA_RESERVADA", description="se esperaba funcion integrada")
        if token[1] not in BUILTIN_FUNCTIONS:
            agregar_error("Error sintáctico", token[2], token[3], f"función no permitida '{token[1]}'")

        self.expect("SIMBOLO", "(", "se esperaba '('")
        argument = self.parse_argumento_funcion()
        if argument.get("error"):
            self.synchronize()
        self.expect("SIMBOLO", ")", "se esperaba ')'")
        self.expect("SIMBOLO", ";", "se esperaba ';'")
        return {
            "type": "call",
            "name": token[1],
            "argument": argument,
            "line": token[2],
            "column": token[3],
        }

    def parse_argumento_funcion(self) -> dict[str, object]:
        """Parse the single argument accepted by built-in functions."""
        token = self.current_token()
        if token is None:
            return self.synthetic_literal("", "cadena", 1, 1)
        if linea_con_error_lexico(token[2]):
            self.skip_current_line()
            return self.synthetic_error(token[2], token[3])
        return self.parse_comparacion()

    def parse_bloque(self) -> list[dict[str, object]]:
        """Parse consecutive statements until a block terminator is found."""
        statements: list[dict[str, object]] = []
        while True:
            token = self.current_token()
            if token is None:
                agregar_error("Error sintáctico", self.last_line(), self.last_column(), "estructura incompleta, se esperaba 'fin'", critical=True)
                return statements
            if token[0] == "PALABRA_RESERVADA" and token[1] in BLOCK_ENDERS:
                return statements
            if self.is_declaration():
                declaration = self.parse_declaracion()
                if declaration is not None:
                    statements.append(declaration)
                continue
            statement = self.parse_sentencia()
            if statement is not None:
                statements.append(statement)

    def parse_condicion(self) -> dict[str, object]:
        """Parse a conditional expression."""
        return self.parse_comparacion()

    def parse_comparacion(self) -> dict[str, object]:
        """Parse an expression that may include a relational comparison."""
        left = self.parse_expresion()
        if left.get("error"):
            return left
        token = self.current_token()
        if token is not None and token[0] == "OPERADOR" and token[1] in RELATIONAL_OPERATORS:
            operator = self.advance()
            right = self.parse_expresion()
            if right.get("error"):
                return right
            return {
                "type": "binary_op",
                "operator": operator[1],
                "left": left,
                "right": right,
                "line": operator[2],
                "column": operator[3],
            }
        return left

    def parse_expresion(self) -> dict[str, object]:
        """Parse an expression with additive precedence."""
        node = self.parse_termino()
        if node.get("error"):
            return node
        while True:
            token = self.current_token()
            if token is None or token[0] != "OPERADOR" or token[1] not in ADDITIVE_OPERATORS:
                return node
            operator = self.advance()
            right = self.parse_termino()
            if right.get("error"):
                return right
            node = {
                "type": "binary_op",
                "operator": operator[1],
                "left": node,
                "right": right,
                "line": operator[2],
                "column": operator[3],
            }

    def parse_termino(self) -> dict[str, object]:
        """Parse an expression term with multiplicative precedence."""
        node = self.parse_factor()
        if node.get("error"):
            return node
        while True:
            token = self.current_token()
            if token is None or token[0] != "OPERADOR" or token[1] not in MULTIPLICATIVE_OPERATORS:
                return node
            operator = self.advance()
            right = self.parse_factor()
            if right.get("error"):
                return right
            node = {
                "type": "binary_op",
                "operator": operator[1],
                "left": node,
                "right": right,
                "line": operator[2],
                "column": operator[3],
            }

    def parse_factor(self) -> dict[str, object]:
        """Parse an atomic expression element."""
        token = self.current_token()
        if token is None:
            agregar_error("Error sintáctico", self.last_line(), self.last_column(), "estructura incompleta", critical=True)
            return self.synthetic_error(self.last_line(), self.last_column())

        token_type, lexeme, line, column = token

        if linea_con_error_lexico(line):
            self.skip_current_line()
            return self.synthetic_error(line, column)

        if linea_critica(line):
            self.synchronize()
            return self.synthetic_error(line, column)

        if token_type in {"IDENTIFICADOR", "NUMERO", "CADENA", "BOOLEANO"}:
            self.advance()
            if token_type == "IDENTIFICADOR":
                return {"type": "identifier", "name": lexeme, "line": line, "column": column}
            if token_type == "NUMERO":
                value_type = "decimal" if "." in lexeme else "entero"
                return {"type": "literal", "value_type": value_type, "value": lexeme, "line": line, "column": column}
            if token_type == "BOOLEANO":
                return {"type": "literal", "value_type": "booleano", "value": lexeme, "line": line, "column": column}
            return {"type": "literal", "value_type": "cadena", "value": lexeme, "line": line, "column": column}

        if token_type == "SIMBOLO" and lexeme == "(":
            self.advance()
            expression = self.parse_expresion()
            self.expect("SIMBOLO", ")", "se esperaba ')'")
            return expression

        agregar_error("Error sintáctico", line, column, f"expresión no válida cerca de '{lexeme}'", critical=True)
        marcar_linea_critica(line)
        self.synchronize()
        return self.synthetic_error(line, column)

    def expect(
        self,
        expected_type: str,
        expected_lexeme: str | None = None,
        description: str | None = None,
    ) -> Token:
        """Consume the next token if it matches the expected shape."""
        token = self.current_token()
        if token is None:
            agregar_error("Error sintáctico", self.last_line(), self.last_column(), description or "estructura incompleta", critical=True)
            return ("ERROR", "", self.last_line(), self.last_column())

        token_type, lexeme, line, column = token
        if token_type == expected_type and (expected_lexeme is None or lexeme == expected_lexeme):
            self.position += 1
            return token

        critical = expected_type == "SIMBOLO" and expected_lexeme == ";"
        agregar_error(
            "Error sintáctico",
            line,
            column,
            description or f"se esperaba '{expected_lexeme or expected_type}'",
            critical=critical,
        )
        if critical:
            marcar_linea_critica(line)
        if expected_type == "SIMBOLO" and expected_lexeme == ";":
            self.synchronize()
            return ("SIMBOLO", ";", line, column)
        if expected_type == "PALABRA_RESERVADA" and expected_lexeme == "fin":
            return ("PALABRA_RESERVADA", "fin", line, column)

        self.position += 1
        return token

    def is_declaration(self) -> bool:
        """Return True when the current token starts a declaration."""
        token = self.current_token()
        return token is not None and token[0] == "TIPO" and token[1] in DECLARATION_TYPES

    def synchronize(self) -> None:
        """Recover after an error by advancing to ';' or 'fin'."""
        while self.current_token() is not None:
            token = self.current_token()
            if token[1] == ";":
                self.advance()
                return
            if token[1] == "fin":
                return
            self.advance()

    def synchronize_to_block_end(self) -> None:
        """Advance until the parser reaches the end of a block."""
        while self.current_token() is not None:
            token = self.current_token()
            if token[1] == "fin":
                return
            self.advance()

    def skip_current_line(self) -> None:
        """Skip tokens that belong to the current source line."""
        token = self.current_token()
        if token is None:
            return
        linea = token[2]
        while self.current_token() is not None and self.current_token()[2] == linea:
            actual = self.current_token()
            self.advance()
            if actual[1] == ";":
                return

    def synthetic_literal(self, value: str, value_type: str, line: int, column: int) -> dict[str, object]:
        """Create a placeholder literal node used after recoverable errors."""
        return {"type": "literal", "value_type": value_type, "value": value, "line": line, "column": column}

    def synthetic_error(self, line: int, column: int) -> dict[str, object]:
        """Create a placeholder node representing a broken expression."""
        return {
            "type": "literal",
            "value_type": "desconocido",
            "value": "0",
            "line": line,
            "column": column,
            "error": True,
        }

    def last_line(self) -> int:
        """Return the best-known current line."""
        token = self.current_token()
        if token is not None:
            return token[2]
        if self.tokens:
            return self.tokens[-1][2]
        return 1

    def last_column(self) -> int:
        """Return the best-known current column."""
        token = self.current_token()
        if token is not None:
            return token[3]
        if self.tokens:
            return self.tokens[-1][3]
        return 1


def parse_programa(tokens: list[Token]) -> bool:
    """Validate a full RadarScript program."""
    parser = Parser(tokens)
    return parser.parse()


def parse_programa_ast(tokens: list[Token]) -> dict[str, object]:
    """Validate and return a simple AST for a RadarScript program."""
    parser = Parser(tokens)
    parser.parse()
    return parser.ast
