"""Python 3 entry point for the RadarScriptCompiler project."""

from __future__ import annotations

from pathlib import Path

try:
    from codegen.codegen import formatear_codigo_objeto, generar_codigo_objeto
    from diagnostics import exportar_errores, formatear_errores, hay_errores, limpiar_errores
    from intermediate.intermediate import formatear_codigo_intermedio, generar_codigo_intermedio
    from lexer.lexer import exportar_tokens, formatear_tokens, lexer
    from parser.parser import parse_programa_ast
    from semantic.semantic import analizar_semantica, formatear_tabla_simbolos
    from vm.vm import VirtualMachineError, ejecutar_archivo_objeto
except ImportError:
    from src.codegen.codegen import formatear_codigo_objeto, generar_codigo_objeto
    from src.diagnostics import exportar_errores, formatear_errores, hay_errores, limpiar_errores
    from src.intermediate.intermediate import formatear_codigo_intermedio, generar_codigo_intermedio
    from src.lexer.lexer import exportar_tokens, formatear_tokens, lexer
    from src.parser.parser import parse_programa_ast
    from src.semantic.semantic import analizar_semantica, formatear_tabla_simbolos
    from src.vm.vm import VirtualMachineError, ejecutar_archivo_objeto


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_FILE = PROJECT_ROOT / "tests" / "ejemplo.rdr"
LEX_OUTPUT_FILE = PROJECT_ROOT / "outputs" / "salida.lex"
SYM_OUTPUT_FILE = PROJECT_ROOT / "outputs" / "salida.sym"
INT_OUTPUT_FILE = PROJECT_ROOT / "outputs" / "salida.int"
OBJ_OUTPUT_FILE = PROJECT_ROOT / "outputs" / "salida.obj"
ERROR_OUTPUT_FILE = PROJECT_ROOT / "outputs" / "errores.txt"


def cargar_codigo(ruta_archivo: Path) -> str:
    """Read RadarScript source code from disk."""
    if not ruta_archivo.exists():
        raise FileNotFoundError(f"No se encontro el archivo fuente: {ruta_archivo}")
    return ruta_archivo.read_text(encoding="utf-8")


def imprimir_tokens(tokens: list[tuple[str, str, int, int]]) -> None:
    """Print token sequence to the console."""
    print(formatear_tokens(tokens))


def mostrar_fase(nombre: str) -> None:
    """Print a clear header for the current phase."""
    print(f"\n[{nombre}]")


def imprimir_errores() -> None:
    """Write and print the diagnostics report only when errors exist."""
    if not hay_errores():
        return

    exportar_errores(str(ERROR_OUTPUT_FILE))
    print(formatear_errores())
    print(f"Reporte de errores guardado en: {ERROR_OUTPUT_FILE}")


def compilar_programa() -> bool:
    """Run compilation only and return True when no errors were collected."""
    limpiar_errores()

    mostrar_fase("FASE 1 - Compilacion")

    mostrar_fase("Lectura")
    codigo = cargar_codigo(SOURCE_FILE)

    mostrar_fase("1. Lexer")
    tokens = lexer(codigo)
    imprimir_tokens(tokens)
    exportar_tokens(tokens, str(LEX_OUTPUT_FILE))
    print(f"Salida lexica guardada en: {LEX_OUTPUT_FILE}")

    mostrar_fase("2. Parser")
    ast = parse_programa_ast(tokens)
    print("Analisis sintactico completado.")

    mostrar_fase("3. Semantico")
    tabla_simbolos = analizar_semantica(ast, str(SYM_OUTPUT_FILE))
    print(formatear_tabla_simbolos(tabla_simbolos))
    print(f"Salida semantica guardada en: {SYM_OUTPUT_FILE}")

    if hay_errores():
        imprimir_errores()
        return False

    mostrar_fase("4. Intermedio")
    cuadruplos = generar_codigo_intermedio(ast, str(INT_OUTPUT_FILE))
    print(formatear_codigo_intermedio(cuadruplos))
    print(f"Salida intermedia guardada en: {INT_OUTPUT_FILE}")

    mostrar_fase("5. Codigo Objeto")
    instrucciones = generar_codigo_objeto(cuadruplos, str(OBJ_OUTPUT_FILE))
    print(formatear_codigo_objeto(instrucciones))
    print(f"Codigo objeto guardado en: {OBJ_OUTPUT_FILE}")

    exportar_errores(str(ERROR_OUTPUT_FILE))
    print("Compilacion completada correctamente.")
    return True


def ejecutar_vm_compilada() -> None:
    """Run the virtual machine as a separate phase."""
    mostrar_fase("FASE 2 - Ejecucion (VM)")
    ejecutar_archivo_objeto(str(OBJ_OUTPUT_FILE))
    print("Ejecucion finalizada.")


def main() -> None:
    """Run the full RadarScript compilation pipeline."""
    try:
        if not compilar_programa():
            return

        ejecutar_vm_compilada()
    except FileNotFoundError as error:
        print(f"Error: {error}")
    except VirtualMachineError as error:
        print(f"Error de maquina virtual: {error}")
    finally:
        exportar_errores(str(ERROR_OUTPUT_FILE))


if __name__ == "__main__":
    main()
