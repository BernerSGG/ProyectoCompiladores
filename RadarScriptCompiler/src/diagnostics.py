"""Shared diagnostics support for RadarScriptCompiler."""

from __future__ import annotations

from pathlib import Path


errores: list[str] = []
_errores_por_tipo_linea: set[tuple[str, int]] = set()
_lineas_criticas: set[int] = set()
_lineas_con_error_lexico: set[int] = set()
_lineas_con_error_sintactico: set[int] = set()


def limpiar_errores() -> None:
    """Reset the global diagnostics state."""
    errores.clear()
    _errores_por_tipo_linea.clear()
    _lineas_criticas.clear()
    _lineas_con_error_lexico.clear()
    _lineas_con_error_sintactico.clear()


def agregar_error(
    tipo: str,
    linea: int,
    columna: int,
    descripcion: str,
    *,
    critical: bool = False,
) -> None:
    """Append a formatted diagnostic message unless this type already exists on the line."""
    clave = (tipo, linea)
    if clave in _errores_por_tipo_linea:
        return

    if linea in _lineas_criticas and not critical:
        return

    errores.append(f"{tipo} | Línea {linea} | Columna {columna} | {descripcion}")
    _errores_por_tipo_linea.add(clave)

    if tipo == "Error léxico":
        _lineas_con_error_lexico.add(linea)
    if tipo == "Error sintáctico":
        _lineas_con_error_sintactico.add(linea)
    if critical:
        _lineas_criticas.add(linea)


def marcar_linea_critica(linea: int) -> None:
    """Prevent non-critical follow-up diagnostics on the same line."""
    _lineas_criticas.add(linea)


def linea_critica(linea: int) -> bool:
    """Return True when a line has been marked as critical."""
    return linea in _lineas_criticas


def linea_con_error_lexico(linea: int) -> bool:
    """Return True when the lexer already reported an error on the line."""
    return linea in _lineas_con_error_lexico


def linea_con_error_sintactico(linea: int) -> bool:
    """Return True when the parser already reported an error on the line."""
    return linea in _lineas_con_error_sintactico


def hay_errores() -> bool:
    """Return True when diagnostics have been collected."""
    return bool(errores)


def formatear_errores() -> str:
    """Return the academic diagnostics report text."""
    if not errores:
        return ""

    lineas = ["REPORTE DE ERRORES", ""]
    lineas.extend(errores)
    return "\n".join(lineas)


def exportar_errores(ruta_salida: str) -> None:
    """Write the diagnostics report to disk."""
    Path(ruta_salida).write_text(formatear_errores(), encoding="utf-8")
