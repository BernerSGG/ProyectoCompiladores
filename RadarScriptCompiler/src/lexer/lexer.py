"""Python 3 module for the RadarScript lexical analyzer."""

from __future__ import annotations

from pathlib import Path

try:
    from diagnostics import agregar_error
except ImportError:
    from src.diagnostics import agregar_error


# This file defines the lexer responsible for converting RadarScript source
# code into a stream of tokens for later compilation stages.

Token = tuple[str, str, int, int]
TOKEN_COLUMN_WIDTH = 25

RESERVED_WORDS = {
    "programa": "PALABRA_RESERVADA",
    "si": "PALABRA_RESERVADA",
    "entonces": "PALABRA_RESERVADA",
    "fin": "PALABRA_RESERVADA",
    "mientras": "PALABRA_RESERVADA",
    "hacer": "PALABRA_RESERVADA",
    "alerta": "PALABRA_RESERVADA",
    "reporte": "PALABRA_RESERVADA",
}

TYPE_WORDS = {
    "entero": "TIPO",
    "decimal": "TIPO",
    "cadena": "TIPO",
    "booleano": "TIPO",
}

BOOLEAN_LITERALS = {
    "verdadero": "BOOLEANO",
    "falso": "BOOLEANO",
}

DOUBLE_OPERATORS = {
    "//": "COMENTARIO",
    ">=": "OPERADOR",
    "<=": "OPERADOR",
    "==": "OPERADOR",
    "!=": "OPERADOR",
}

SINGLE_OPERATORS = {
    "+": "OPERADOR",
    "-": "OPERADOR",
    "*": "OPERADOR",
    "/": "OPERADOR",
    ">": "OPERADOR",
    "<": "OPERADOR",
    "=": "OPERADOR",
}

SYMBOLS = {
    ";": "SIMBOLO",
    "(": "SIMBOLO",
    ")": "SIMBOLO",
}

DISPLAY_TOKEN_TYPES = {
    ("SIMBOLO", ";"): "PUNTO_Y_COMA",
    ("SIMBOLO", "("): "PARENTESIS_IZQ",
    ("SIMBOLO", ")"): "PARENTESIS_DER",
}


class LexicalError(Exception):
    """Represents a lexical analysis error with location information."""


def _classify_identifier(lexema: str) -> str:
    """Determine the token type for an identifier-like lexeme."""
    if lexema in RESERVED_WORDS:
        return RESERVED_WORDS[lexema]
    if lexema in TYPE_WORDS:
        return TYPE_WORDS[lexema]
    if lexema in BOOLEAN_LITERALS:
        return BOOLEAN_LITERALS[lexema]
    return "IDENTIFICADOR"


def _display_token_type(tipo: str, lexema: str) -> str:
    """Return the human-readable token label used in lexer output."""
    return DISPLAY_TOKEN_TYPES.get((tipo, lexema), tipo)


def lexer(codigo: str) -> list[Token]:
    """Analyze RadarScript source code and return a token list."""
    tokens: list[Token] = []
    posicion = 0
    linea = 1
    columna = 1

    while posicion < len(codigo):
        caracter = codigo[posicion]

        if caracter in {" ", "\t", "\r"}:
            posicion += 1
            columna += 1
            continue

        if caracter == "\n":
            posicion += 1
            linea += 1
            columna = 1
            continue

        if caracter.isalpha():
            inicio = posicion
            columna_inicial = columna
            while posicion < len(codigo) and (codigo[posicion].isalnum() or codigo[posicion] == "_"):
                posicion += 1
                columna += 1
            lexema = codigo[inicio:posicion]
            tokens.append((_classify_identifier(lexema), lexema, linea, columna_inicial))
            continue

        if caracter.isdigit():
            inicio = posicion
            columna_inicial = columna
            saw_dot = False
            numero_invalido = False

            while posicion < len(codigo):
                actual = codigo[posicion]
                if actual.isdigit():
                    posicion += 1
                    columna += 1
                    continue
                if actual == ".":
                    if saw_dot:
                        numero_invalido = True
                    saw_dot = True
                    posicion += 1
                    columna += 1
                    continue
                break

            lexema = codigo[inicio:posicion]
            if numero_invalido or lexema.endswith("."):
                agregar_error("Error léxico", linea, columna_inicial, f"número inválido '{lexema}'")
            else:
                tokens.append(("NUMERO", lexema, linea, columna_inicial))
            continue

        if caracter == '"':
            columna_inicial = columna
            posicion += 1
            columna += 1
            literal = ['"']
            cadena_cerrada = False
            linea_inicial = linea

            while posicion < len(codigo):
                actual = codigo[posicion]
                if actual == '"':
                    literal.append(actual)
                    posicion += 1
                    columna += 1
                    cadena_cerrada = True
                    break

                if actual == "\n":
                    break

                literal.append(actual)
                posicion += 1
                columna += 1

            if not cadena_cerrada:
                agregar_error("Error léxico", linea_inicial, columna_inicial, "cadena sin cerrar", critical=True)
                while posicion < len(codigo) and codigo[posicion] != "\n":
                    posicion += 1
                    columna += 1
            else:
                tokens.append(("CADENA", "".join(literal), linea_inicial, columna_inicial))
            continue

        possible_double = codigo[posicion:posicion + 2]
        if possible_double == "//":
            posicion += 2
            columna += 2
            while posicion < len(codigo) and codigo[posicion] != "\n":
                posicion += 1
                columna += 1
            continue

        if possible_double in DOUBLE_OPERATORS:
            tokens.append((DOUBLE_OPERATORS[possible_double], possible_double, linea, columna))
            posicion += 2
            columna += 2
            continue

        if caracter in SINGLE_OPERATORS:
            tokens.append((SINGLE_OPERATORS[caracter], caracter, linea, columna))
            posicion += 1
            columna += 1
            continue

        if caracter in SYMBOLS:
            tokens.append((SYMBOLS[caracter], caracter, linea, columna))
            posicion += 1
            columna += 1
            continue

        agregar_error("Error léxico", linea, columna, f"símbolo inválido '{caracter}'")
        posicion += 1
        columna += 1

    return tokens


def formatear_tokens(tokens: list[Token]) -> str:
    """Format tokens in aligned columns for console and .lex output."""
    lineas = ["Salida léxica (.lex)", ""]
    for tipo, lexema, _linea, _columna in tokens:
        tipo_mostrado = _display_token_type(tipo, lexema)
        lineas.append(f"{tipo_mostrado:<{TOKEN_COLUMN_WIDTH}}{lexema}")
    return "\n".join(lineas)


def exportar_tokens(tokens: list[Token], ruta_salida: str) -> None:
    """Write the token sequence to a .lex file."""
    Path(ruta_salida).write_text(formatear_tokens(tokens), encoding="utf-8")
