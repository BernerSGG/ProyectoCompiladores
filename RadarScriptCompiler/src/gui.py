"""Interfaz grafica tipo Cyber Radar Dashboard para RadarScriptCompiler."""

from __future__ import annotations

import io
import os
import re
import sys
from html import escape
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from tkinter import filedialog

import customtkinter as ctk

BASE_DIR = Path(getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SRC_ROOT = BASE_DIR / "src" if (BASE_DIR / "src").exists() else Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

COLOR_FONDO = "#07111f"
COLOR_PANEL = "#0b1730"
COLOR_PANEL_ALT = "#10203f"
COLOR_EDITOR = "#081426"
COLOR_TERMINAL = "#030813"
COLOR_BORDE = "#143354"
COLOR_DIVISOR = "#163b63"
COLOR_CYAN = "#00c8ff"
COLOR_CYAN_HOVER = "#00a6d4"
COLOR_VERDE = "#00ff9d"
COLOR_VERDE_HOVER = "#00d483"
COLOR_TEXTO = "#d9f3ff"
COLOR_TEXTO_SUAVE = "#82a9bb"
COLOR_AMARILLO = "#ffcc66"
COLOR_ROJO = "#ff5f7a"
COLOR_VIOLETA = "#8b7cff"
COLOR_NARANJA = "#ff9a3d"
FUENTE_UI = "Segoe UI"
FUENTE_CODIGO = "Consolas"

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


@dataclass
class CompilationArtifacts:
    """Textos y estados producidos durante la compilacion."""

    source: str
    lex_output: str
    sym_output: str
    int_output: str
    obj_output: str
    errors_output: str
    has_errors: bool


class CompilerPipeline:
    """Encapsula la compilacion y la ejecucion de la VM."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.outputs_dir = project_root / "outputs"
        self.lex_path = self.outputs_dir / "salida.lex"
        self.sym_path = self.outputs_dir / "salida.sym"
        self.int_path = self.outputs_dir / "salida.int"
        self.obj_path = self.outputs_dir / "salida.obj"
        self.errors_path = self.outputs_dir / "errores.txt"

    def compile_source(self, source_code: str) -> CompilationArtifacts:
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        limpiar_errores()

        tokens = lexer(source_code)
        exportar_tokens(tokens, str(self.lex_path))

        ast = parse_programa_ast(tokens)
        tabla = analizar_semantica(ast, str(self.sym_path))

        int_output = ""
        obj_output = ""
        has_errors = hay_errores()
        if not has_errors:
            quadruples = generar_codigo_intermedio(ast, str(self.int_path))
            obj = generar_codigo_objeto(quadruples, str(self.obj_path))
            int_output = formatear_codigo_intermedio(quadruples)
            obj_output = formatear_codigo_objeto(obj)
        else:
            self.int_path.write_text("", encoding="utf-8")
            self.obj_path.write_text("", encoding="utf-8")

        exportar_errores(str(self.errors_path))

        return CompilationArtifacts(
            source=source_code,
            lex_output=formatear_tokens(tokens),
            sym_output=formatear_tabla_simbolos(tabla),
            int_output=int_output,
            obj_output=obj_output,
            errors_output=formatear_errores(),
            has_errors=has_errors,
        )

    def execute_vm(self) -> str:
        if not self.obj_path.exists():
            raise FileNotFoundError(f"No se encontro el archivo objeto: {self.obj_path}")

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            ejecutar_archivo_objeto(str(self.obj_path))
        return buffer.getvalue().strip()


class DialogoTexto(ctk.CTkToplevel):
    """Ventana modal para avisos y errores extensos."""

    def __init__(self, master: ctk.CTk, titulo: str, contenido: str, color_primario: str) -> None:
        super().__init__(master)
        self.title(titulo)
        self.geometry("860x560")
        self.minsize(680, 420)
        self.configure(fg_color=COLOR_FONDO)
        self.transient(master)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        marco_titulo = ctk.CTkFrame(
            self,
            fg_color=COLOR_PANEL,
            corner_radius=18,
            border_width=1,
            border_color=color_primario,
        )
        marco_titulo.grid(row=0, column=0, padx=18, pady=(18, 10), sticky="ew")

        ctk.CTkLabel(
            marco_titulo,
            text=titulo,
            font=ctk.CTkFont(family=FUENTE_UI, size=21, weight="bold"),
            text_color=COLOR_TEXTO,
        ).pack(anchor="w", padx=18, pady=(14, 2))
        ctk.CTkLabel(
            marco_titulo,
            text="Visor de mensajes y diagnosticos del compilador",
            font=ctk.CTkFont(family=FUENTE_UI, size=12),
            text_color=COLOR_TEXTO_SUAVE,
        ).pack(anchor="w", padx=18, pady=(0, 14))

        marco_texto = ctk.CTkFrame(
            self,
            fg_color=COLOR_PANEL_ALT,
            corner_radius=18,
            border_width=1,
            border_color=COLOR_BORDE,
        )
        marco_texto.grid(row=1, column=0, padx=18, pady=(0, 10), sticky="nsew")
        marco_texto.grid_columnconfigure(0, weight=1)
        marco_texto.grid_rowconfigure(0, weight=1)

        self.texto = ctk.CTkTextbox(
            marco_texto,
            fg_color=COLOR_TERMINAL,
            text_color=COLOR_TEXTO,
            border_width=1,
            border_color=COLOR_DIVISOR,
            corner_radius=14,
            wrap="word",
            font=ctk.CTkFont(family=FUENTE_CODIGO, size=13),
            activate_scrollbars=True,
        )
        self.texto.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
        self.texto.delete("1.0", "end")
        self.texto.insert("end", contenido)
        self.texto.configure(state="disabled")

        acciones = ctk.CTkFrame(self, fg_color="transparent")
        acciones.grid(row=2, column=0, padx=18, pady=(0, 18), sticky="ew")
        acciones.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            acciones,
            text="Cerrar",
            command=self.destroy,
            corner_radius=12,
            height=42,
            fg_color=color_primario,
            hover_color=COLOR_CYAN_HOVER if color_primario == COLOR_CYAN else COLOR_VERDE_HOVER,
            text_color="#01131f",
            font=ctk.CTkFont(family=FUENTE_UI, size=14, weight="bold"),
        ).grid(row=0, column=1, sticky="e")


class App(ctk.CTk):
    """Aplicacion principal con diseno cyber radar."""

    TAB_ORDER = (
        "Codigo fuente",
        "Salida lexica",
        "Tabla de simbolos",
        "Codigo intermedio",
        "Codigo objeto",
    )
    PALABRAS_CLAVE = {"programa", "si", "entonces", "fin", "mientras", "hacer", "alerta", "reporte"}
    TIPOS = {"entero", "decimal", "cadena", "booleano"}
    BOOLEANOS = {"verdadero", "falso"}

    def __init__(self, project_root: Path) -> None:
        super().__init__()
        self.project_root = project_root
        self.pipeline = CompilerPipeline(project_root)
        self.current_file: Path | None = None
        self.last_artifacts: CompilationArtifacts | None = None
        self.last_compile_succeeded = False
        self.text_widgets: dict[str, ctk.CTkTextbox] = {}
        self.line_widgets: dict[str, ctk.CTkTextbox] = {}
        self.metrics_value_labels: dict[str, ctk.CTkLabel] = {}

        self.status_var = ctk.StringVar(value="Sistema listo")
        self.substatus_var = ctk.StringVar(value="Esperando archivo fuente")
        self.archivo_var = ctk.StringVar(value="Sin archivo")
        self.tokens_var = ctk.StringVar(value="0")
        self.errores_var = ctk.StringVar(value="0")
        self.tiempo_var = ctk.StringVar(value="0.000 s")
        self.vm_var = ctk.StringVar(value="En espera")

        self.title("RadarScript Compiler")
        self.geometry("1280x820")
        self.minsize(1000, 650)
        self.configure(fg_color=COLOR_FONDO)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.crear_header()
        self.crear_cuerpo()
        self.eventos_botones()
        self.after(180, self.refrescar_editors)

    def crear_header(self) -> None:
        header = ctk.CTkFrame(
            self,
            fg_color=COLOR_PANEL,
            corner_radius=0,
            border_width=0,
            height=94,
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        logo_glow = ctk.CTkFrame(
            header,
            fg_color="#09192f",
            corner_radius=18,
            border_width=1,
            border_color=COLOR_CYAN,
            width=70,
            height=70,
        )
        logo_glow.grid(row=0, column=0, padx=(20, 14), pady=12)
        logo_glow.grid_propagate(False)

        ctk.CTkLabel(
            logo_glow,
            text="RAD",
            text_color=COLOR_VERDE,
            font=ctk.CTkFont(family=FUENTE_UI, size=18, weight="bold"),
        ).place(relx=0.5, rely=0.42, anchor="center")
        ctk.CTkLabel(
            logo_glow,
            text="SCAN",
            text_color=COLOR_CYAN,
            font=ctk.CTkFont(family=FUENTE_UI, size=10, weight="bold"),
        ).place(relx=0.5, rely=0.70, anchor="center")

        titulos = ctk.CTkFrame(header, fg_color="transparent")
        titulos.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            titulos,
            text="RadarScript Compiler",
            text_color=COLOR_TEXTO,
            font=ctk.CTkFont(family=FUENTE_UI, size=28, weight="bold"),
        ).pack(anchor="w", pady=(12, 0))
        ctk.CTkLabel(
            titulos,
            text="Centro de control del compilador / Panel de monitoreo academico",
            text_color=COLOR_CYAN,
            font=ctk.CTkFont(family=FUENTE_UI, size=13),
        ).pack(anchor="w", pady=(4, 0))

        estado = ctk.CTkFrame(
            header,
            fg_color="#10203b",
            corner_radius=18,
            border_width=1,
            border_color=COLOR_VERDE,
        )
        estado.grid(row=0, column=2, padx=(18, 20), pady=18, sticky="e")

        ctk.CTkLabel(
            estado,
            textvariable=self.status_var,
            text_color=COLOR_VERDE,
            font=ctk.CTkFont(family=FUENTE_UI, size=13, weight="bold"),
        ).pack(anchor="center", padx=16, pady=(10, 2))
        ctk.CTkLabel(
            estado,
            textvariable=self.substatus_var,
            text_color=COLOR_TEXTO_SUAVE,
            font=ctk.CTkFont(family=FUENTE_UI, size=11),
        ).pack(anchor="center", padx=16, pady=(0, 10))

    def crear_cuerpo(self) -> None:
        cuerpo = ctk.CTkFrame(self, fg_color=COLOR_FONDO, corner_radius=0)
        cuerpo.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(
            cuerpo,
            width=255,
            fg_color=COLOR_PANEL,
            corner_radius=20,
            border_width=1,
            border_color=COLOR_BORDE,
        )
        self.sidebar.grid(row=0, column=0, sticky="ns", padx=(0, 16))
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(8, weight=1)

        self.area_principal = ctk.CTkFrame(cuerpo, fg_color="transparent")
        self.area_principal.grid(row=0, column=1, sticky="nsew")
        self.area_principal.grid_columnconfigure(0, weight=4)
        self.area_principal.grid_columnconfigure(1, weight=1)
        self.area_principal.grid_rowconfigure(0, weight=3)
        self.area_principal.grid_rowconfigure(1, weight=2)

        self.crear_sidebar()
        self.crear_panel_tabs()
        self.crear_panel_info()
        self.crear_consola_inferior()

    def crear_sidebar(self) -> None:
        ctk.CTkLabel(
            self.sidebar,
            text="Panel de control",
            text_color=COLOR_CYAN,
            font=ctk.CTkFont(family=FUENTE_UI, size=15, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(22, 6), sticky="w")

        ctk.CTkLabel(
            self.sidebar,
            text="Carga, compila, ejecuta y revisa cada fase del sistema.",
            text_color=COLOR_TEXTO_SUAVE,
            font=ctk.CTkFont(family=FUENTE_UI, size=12),
            wraplength=190,
            justify="left",
        ).grid(row=1, column=0, padx=20, pady=(0, 18), sticky="w")

        self.boton_cargar = self.crear_boton_sidebar("Cargar archivo", 2, COLOR_CYAN, COLOR_CYAN_HOVER, "ARCH")
        self.boton_compilar = self.crear_boton_sidebar("Compilar", 3, COLOR_VERDE, COLOR_VERDE_HOVER, "COMP")
        self.boton_ejecutar = self.crear_boton_sidebar("Ejecutar VM", 4, "#27a3ff", "#187ed3", "VM")
        self.boton_limpiar = self.crear_boton_sidebar("Limpiar", 5, "#223657", "#2b4670", "CLR")

        marco_archivo = ctk.CTkFrame(
            self.sidebar,
            fg_color=COLOR_PANEL_ALT,
            corner_radius=18,
            border_width=1,
            border_color=COLOR_DIVISOR,
        )
        marco_archivo.grid(row=6, column=0, padx=18, pady=18, sticky="ew")

        ctk.CTkLabel(
            marco_archivo,
            text="Archivo activo",
            text_color=COLOR_VERDE,
            font=ctk.CTkFont(family=FUENTE_UI, size=13, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(14, 4))
        ctk.CTkLabel(
            marco_archivo,
            textvariable=self.archivo_var,
            text_color=COLOR_TEXTO,
            font=ctk.CTkFont(family=FUENTE_UI, size=13),
            wraplength=182,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 14))

        marco_ayuda = ctk.CTkFrame(
            self.sidebar,
            fg_color="#0d1d38",
            corner_radius=18,
            border_width=1,
            border_color=COLOR_BORDE,
        )
        marco_ayuda.grid(row=7, column=0, padx=18, pady=(0, 18), sticky="ew")

        ctk.CTkLabel(
            marco_ayuda,
            text="RadarScript",
            text_color=COLOR_CYAN,
            font=ctk.CTkFont(family=FUENTE_UI, size=13, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(14, 4))
        ctk.CTkLabel(
            marco_ayuda,
            text="Sistema academico para analisis lexico, sintactico, semantico y ejecucion en VM.",
            text_color=COLOR_TEXTO_SUAVE,
            font=ctk.CTkFont(family=FUENTE_UI, size=12),
            wraplength=182,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 14))

        ctk.CTkLabel(
            self.sidebar,
            text="UMG / Compiladores",
            text_color="#557a91",
            font=ctk.CTkFont(family=FUENTE_UI, size=11),
        ).grid(row=8, column=0, padx=18, pady=(0, 18), sticky="sw")

    def crear_boton_sidebar(
        self,
        texto: str,
        fila: int,
        color: str,
        hover: str,
        icono: str,
    ) -> ctk.CTkButton:
        boton = ctk.CTkButton(
            self.sidebar,
            text=f"{icono}   {texto}",
            corner_radius=12,
            height=44,
            fg_color=color,
            hover_color=hover,
            border_width=1,
            border_color=color,
            text_color="#02101b" if color == COLOR_VERDE else COLOR_TEXTO,
            font=ctk.CTkFont(family=FUENTE_UI, size=14, weight="bold"),
            anchor="w",
        )
        boton.grid(row=fila, column=0, padx=18, pady=8, sticky="ew")
        return boton

    def crear_panel_tabs(self) -> None:
        panel_tabs = ctk.CTkFrame(
            self.area_principal,
            fg_color=COLOR_PANEL,
            corner_radius=20,
            border_width=1,
            border_color=COLOR_BORDE,
        )
        panel_tabs.grid(row=0, column=0, sticky="nsew", padx=(0, 16), pady=(0, 16))
        panel_tabs.grid_columnconfigure(0, weight=1)
        panel_tabs.grid_rowconfigure(1, weight=1)

        encabezado = ctk.CTkFrame(panel_tabs, fg_color="transparent")
        encabezado.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 8))
        encabezado.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            encabezado,
            text="Area de trabajo",
            text_color=COLOR_CYAN,
            font=ctk.CTkFont(family=FUENTE_UI, size=15, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            encabezado,
            text="Editor y salidas de compilacion",
            text_color=COLOR_TEXTO_SUAVE,
            font=ctk.CTkFont(family=FUENTE_UI, size=12),
        ).grid(row=0, column=1, sticky="e")

        self.tabview = ctk.CTkTabview(
            panel_tabs,
            fg_color=COLOR_PANEL_ALT,
            corner_radius=18,
            border_width=1,
            border_color=COLOR_DIVISOR,
            segmented_button_fg_color="#0a213d",
            segmented_button_selected_color=COLOR_CYAN,
            segmented_button_selected_hover_color=COLOR_CYAN_HOVER,
            segmented_button_unselected_color="#0c2747",
            segmented_button_unselected_hover_color="#123354",
            text_color="#04141f",
        )
        self.tabview.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")

        for title in self.TAB_ORDER:
            tab = self.tabview.add(title)
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)
            self.crear_editor_tab(tab, title)

    def crear_editor_tab(self, tab, titulo: str) -> None:
        contenedor = ctk.CTkFrame(
            tab,
            fg_color=COLOR_EDITOR,
            corner_radius=16,
            border_width=1,
            border_color=COLOR_DIVISOR,
        )
        contenedor.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
        contenedor.grid_columnconfigure(1, weight=1)
        contenedor.grid_rowconfigure(0, weight=1)

        lineas = ctk.CTkTextbox(
            contenedor,
            width=58,
            fg_color="#06111f",
            text_color="#527d94",
            border_width=0,
            corner_radius=12,
            wrap="none",
            font=ctk.CTkFont(family=FUENTE_CODIGO, size=12),
            activate_scrollbars=False,
        )
        lineas.grid(row=0, column=0, padx=(10, 0), pady=10, sticky="ns")
        lineas.insert("1.0", "1")
        lineas.configure(state="disabled")

        editor = ctk.CTkTextbox(
            contenedor,
            fg_color=COLOR_EDITOR,
            text_color=COLOR_TEXTO,
            border_width=0,
            corner_radius=12,
            wrap="none",
            font=ctk.CTkFont(family=FUENTE_CODIGO, size=13),
            activate_scrollbars=True,
        )
        editor.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.text_widgets[titulo] = editor
        self.line_widgets[titulo] = lineas

        self.vincular_eventos_editor(titulo)
        if titulo == "Codigo fuente":
            self.configurar_resaltado(editor)

    def crear_panel_info(self) -> None:
        panel_info = ctk.CTkFrame(
            self.area_principal,
            fg_color=COLOR_PANEL,
            corner_radius=20,
            border_width=1,
            border_color=COLOR_BORDE,
        )
        panel_info.grid(row=0, column=1, sticky="nsew", pady=(0, 16))
        panel_info.grid_columnconfigure(0, weight=1)
        panel_info.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            panel_info,
            text="Telemetria radar",
            text_color=COLOR_VERDE,
            font=ctk.CTkFont(family=FUENTE_UI, size=15, weight="bold"),
        ).grid(row=0, column=0, padx=18, pady=(16, 10), sticky="w")

        self.scroll_telemetria = ctk.CTkScrollableFrame(
            panel_info,
            fg_color="transparent",
            corner_radius=0,
            border_width=0,
            scrollbar_button_color="#123354",
            scrollbar_button_hover_color="#19456f",
        )
        self.scroll_telemetria.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.scroll_telemetria.grid_columnconfigure(0, weight=1)

        self.crear_tarjeta_info(self.scroll_telemetria, 0, "Estado", self.status_var, COLOR_CYAN)
        self.crear_tarjeta_info(self.scroll_telemetria, 1, "Tokens", self.tokens_var, COLOR_CYAN)
        self.crear_tarjeta_info(self.scroll_telemetria, 2, "Errores", self.errores_var, COLOR_ROJO)
        self.crear_tarjeta_info(self.scroll_telemetria, 3, "VM", self.vm_var, COLOR_VERDE)
        self.crear_tarjeta_info(self.scroll_telemetria, 4, "Tiempo", self.tiempo_var, COLOR_AMARILLO)

    def crear_tarjeta_info(self, parent, fila: int, titulo: str, variable: ctk.StringVar, acento: str) -> None:
        tarjeta = ctk.CTkFrame(
            parent,
            fg_color=COLOR_PANEL_ALT,
            corner_radius=16,
            border_width=1,
            border_color=acento,
        )
        tarjeta.grid(row=fila, column=0, padx=6, pady=8, sticky="ew")

        ctk.CTkLabel(
            tarjeta,
            text=titulo,
            text_color=acento,
            font=ctk.CTkFont(family=FUENTE_UI, size=12, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(12, 4))
        valor = ctk.CTkLabel(
            tarjeta,
            textvariable=variable,
            text_color=COLOR_TEXTO,
            font=ctk.CTkFont(family=FUENTE_UI, size=16, weight="bold"),
            wraplength=180,
            justify="left",
        )
        valor.pack(anchor="w", padx=14, pady=(0, 14))
        self.metrics_value_labels[titulo] = valor

    def crear_consola_inferior(self) -> None:
        panel_consola = ctk.CTkFrame(
            self.area_principal,
            fg_color=COLOR_PANEL,
            corner_radius=20,
            border_width=1,
            border_color=COLOR_BORDE,
        )
        panel_consola.grid(row=1, column=0, columnspan=2, sticky="nsew")
        panel_consola.grid_columnconfigure(0, weight=1)
        panel_consola.grid_rowconfigure(1, weight=1)

        cabecera = ctk.CTkFrame(panel_consola, fg_color="transparent")
        cabecera.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))
        cabecera.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            cabecera,
            text="Terminal / Registro de ejecucion",
            text_color=COLOR_VERDE,
            font=ctk.CTkFont(family=FUENTE_UI, size=15, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            cabecera,
            text="Mensajes del compilador y trazas de la maquina virtual",
            text_color=COLOR_TEXTO_SUAVE,
            font=ctk.CTkFont(family=FUENTE_UI, size=12),
        ).grid(row=0, column=1, sticky="e")

        self.terminal = ctk.CTkTextbox(
            panel_consola,
            fg_color=COLOR_TERMINAL,
            text_color=COLOR_VERDE,
            border_width=1,
            border_color=COLOR_VERDE,
            corner_radius=16,
            wrap="word",
            font=ctk.CTkFont(family=FUENTE_CODIGO, size=13),
            activate_scrollbars=True,
        )
        self.terminal.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")

    def eventos_botones(self) -> None:
        self.boton_cargar.configure(command=self.load_file)
        self.boton_compilar.configure(command=self.compile_source)
        self.boton_ejecutar.configure(command=self.execute_vm)
        self.boton_limpiar.configure(command=self.clear_all)

    def load_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo RadarScript",
            filetypes=[("RadarScript", "*.rdr"), ("Todos los archivos", "*.*")],
            initialdir=str(self.project_root / "tests"),
        )
        if not file_path:
            return

        try:
            path = Path(file_path)
            source_code = path.read_text(encoding="utf-8")
            self.current_file = path
            self.archivo_var.set(path.name)
            self._set_text("Codigo fuente", source_code)
            self._focus_tab("Codigo fuente")
            self.registrar_en_consola(f"[CARGA] Archivo cargado: {path}")
            self.actualizar_estado("Fuente cargada", "Lista para compilar")
        except OSError as error:
            self._handle_error("Error al cargar archivo", error)

    def compile_source(self) -> None:
        source_code = self._get_text("Codigo fuente")
        if not source_code.strip():
            self.last_compile_succeeded = False
            self.mostrar_aviso("No hay codigo fuente para compilar.")
            return

        inicio = perf_counter()
        try:
            self.actualizar_estado("Compilando", "Analizando y generando salidas")
            self.registrar_en_consola("[COMPILACION] Iniciando compilacion...")

            artifacts = self.pipeline.compile_source(source_code)
            duracion = perf_counter() - inicio

            self.last_artifacts = artifacts
            self.last_compile_succeeded = not artifacts.has_errors
            self._set_text("Salida lexica", artifacts.lex_output)
            self._set_text("Tabla de simbolos", artifacts.sym_output)
            self._set_text("Codigo intermedio", artifacts.int_output)
            self._set_text("Codigo objeto", artifacts.obj_output)

            cantidad_tokens = self.contar_tokens(artifacts.lex_output)
            cantidad_errores = self.contar_errores(artifacts.errors_output)
            self.tokens_var.set(str(cantidad_tokens))
            self.errores_var.set(str(cantidad_errores))
            self.tiempo_var.set(f"{duracion:.3f} s")

            if artifacts.has_errors:
                self.actualizar_terminal(artifacts.errors_output)
                self.vm_var.set("Bloqueada")
                self.actualizar_estado("Compilacion con errores", "Revisa la terminal y el visor")
                self.mostrar_error("Errores de compilacion", artifacts.errors_output)
            else:
                mensaje = "Compilacion completada correctamente.\n"
                self.actualizar_terminal(mensaje)
                self.vm_var.set("Compilada")
                self.actualizar_estado("Compilacion completa", "Lista para ejecutar")
                self._focus_tab("Salida lexica")
        except (OSError, ValueError, VirtualMachineError) as error:
            self.last_artifacts = None
            self.last_compile_succeeded = False
            self.tiempo_var.set(f"{perf_counter() - inicio:.3f} s")
            self._handle_error("Error de compilacion", error)

    def execute_vm(self) -> None:
        if not self.last_compile_succeeded:
            self.mostrar_aviso("La maquina virtual solo se ejecuta si la compilacion termina sin errores.")
            return

        try:
            self.actualizar_estado("Ejecutando VM", "Procesando codigo objeto")
            self.registrar_en_consola("[VM] Iniciando ejecucion...")
            vm_output = self.pipeline.execute_vm()
            salida = vm_output if vm_output else "Ejecucion completada sin salida."
            actual = self._get_terminal_text().strip()
            combinado = f"{actual}\n{salida}\n".strip() + "\n" if actual else salida + "\n"
            self.actualizar_terminal(combinado)
            ruta_resultado = self._ask_result_viewer_path()
            if ruta_resultado is not None:
                self._export_result_viewer(ruta_resultado, salida_vm=salida, registrar=False)
                self.registrar_en_consola(
                    f"[EXPORTACION] Resultado guardado en: {ruta_resultado} (abrible con doble clic)"
                )
            else:
                self.registrar_en_consola("[EXPORTACION] Guardado cancelado por el usuario.")
            self.vm_var.set("Ejecutada")
            self.actualizar_estado("Ejecucion finalizada", "Salida disponible en terminal")
        except (FileNotFoundError, VirtualMachineError, OSError) as error:
            self.vm_var.set("Error")
            self._handle_error("Error en la maquina virtual", error)

    def clear_all(self) -> None:
        for widget in self.text_widgets.values():
            widget.delete("1.0", "end")
        for widget in self.line_widgets.values():
            widget.configure(state="normal")
            widget.delete("1.0", "end")
            widget.insert("1.0", "1")
            widget.configure(state="disabled")

        self.terminal.delete("1.0", "end")
        self.current_file = None
        self.last_artifacts = None
        self.last_compile_succeeded = False
        self.archivo_var.set("Sin archivo")
        self.tokens_var.set("0")
        self.errores_var.set("0")
        self.tiempo_var.set("0.000 s")
        self.vm_var.set("En espera")
        self.actualizar_estado("Sistema listo", "Panel reiniciado")

    def actualizar_estado(self, principal: str, detalle: str) -> None:
        self.status_var.set(principal)
        self.substatus_var.set(detalle)

    def contar_tokens(self, contenido: str) -> int:
        return sum(1 for linea in contenido.splitlines() if linea.strip())

    def contar_errores(self, contenido: str) -> int:
        return sum(1 for linea in contenido.splitlines() if "|" in linea)

    def registrar_en_consola(self, mensaje: str) -> None:
        actual = self._get_terminal_text().strip()
        combinado = f"{actual}\n{mensaje}\n".strip() + "\n" if actual else mensaje + "\n"
        self.actualizar_terminal(combinado)

    def actualizar_terminal(self, contenido: str) -> None:
        self.terminal.delete("1.0", "end")
        self.terminal.insert("end", contenido)
        self.terminal.see("end")

    def _get_terminal_text(self) -> str:
        return self.terminal.get("1.0", "end").removesuffix("\n")

    def mostrar_aviso(self, mensaje: str) -> None:
        self.registrar_en_consola(f"[AVISO] {mensaje}")
        self.actualizar_estado("Aviso", "Se requiere atencion del usuario")
        dialogo = DialogoTexto(self, "Aviso", mensaje, COLOR_CYAN)
        self.wait_window(dialogo)

    def mostrar_error(self, titulo: str, mensaje: str) -> None:
        dialogo = DialogoTexto(self, titulo, self.formatear_errores(mensaje), COLOR_VERDE)
        self.wait_window(dialogo)

    def _handle_error(self, titulo: str, error: Exception) -> None:
        mensaje = str(error)
        self.registrar_en_consola(f"[ERROR] {titulo}: {mensaje}")
        self.actualizar_estado("Error", "Consulta la terminal para mas detalles")
        self.mostrar_error(titulo, mensaje)

    def formatear_errores(self, mensaje: str) -> str:
        if not mensaje.strip():
            return "No se recibieron detalles del error."

        if "REPORTE DE ERRORES" not in mensaje:
            return mensaje

        bloques: list[str] = []
        for linea in mensaje.splitlines():
            limpia = linea.strip()
            if not limpia or limpia == "REPORTE DE ERRORES":
                continue

            partes = [segmento.strip() for segmento in limpia.split("|")]
            if len(partes) < 4:
                bloques.append(limpia)
                continue

            bloques.append(
                "\n".join(
                    [
                        partes[0].upper(),
                        partes[1],
                        partes[2],
                        f"Descripcion: {partes[3]}",
                    ]
                )
            )

        if not bloques:
            return mensaje

        return "\n\n----------------------------------------\n\n".join(bloques)

    def _get_text(self, titulo: str) -> str:
        return self.text_widgets[titulo].get("1.0", "end").removesuffix("\n")

    def _set_text(self, titulo: str, contenido: str) -> None:
        widget = self.text_widgets[titulo]
        widget.delete("1.0", "end")
        widget.insert("end", contenido)
        widget.see("end")
        self.actualizar_lineas(titulo)
        if titulo == "Codigo fuente":
            self.resaltar_fuente()

    def _focus_tab(self, titulo: str) -> None:
        self.tabview.set(titulo)

    def _ask_result_viewer_path(self) -> Path | None:
        default_name = "salida_resultado.html"
        if self.current_file is not None:
            default_name = f"{self.current_file.stem}.html"

        save_path = filedialog.asksaveasfilename(
            title="Guardar resultado HTML",
            defaultextension=".html",
            initialfile=default_name,
            filetypes=[("Archivo HTML", "*.html"), ("Todos los archivos", "*.*")],
        )
        if not save_path:
            return None
        return Path(save_path)

    def _export_result_viewer(
        self,
        destino: Path,
        *,
        salida_vm: str,
        source_label: str | None = None,
        registrar: bool = True,
    ) -> None:
        salida = salida_vm if salida_vm.strip() else "Ejecucion completada sin salida."
        etiqueta = source_label or (self.current_file.name if self.current_file is not None else "Salida compilada")
        html_text = self._build_result_html(etiqueta, salida)
        destino.write_text(html_text, encoding="utf-8")
        if registrar:
            self.registrar_en_consola(f"[EXPORTACION] Resultado HTML guardado en: {destino}")

    def _build_result_html(self, fuente: str, salida_vm: str) -> str:
        titulo = escape(f"RadarScript Compiler | {fuente}")
        resultado = escape(salida_vm)
        fuente_segura = escape(fuente)
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo}</title>
    <style>
        :root {{
            color-scheme: dark;
            --fondo: #07111f;
            --panel: #0b1730;
            --borde: #143354;
            --acento: #00c8ff;
            --texto: #d9f3ff;
            --texto-suave: #82a9bb;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            min-height: 100vh;
            background:
                radial-gradient(circle at top, rgba(0, 200, 255, 0.18), transparent 32%),
                linear-gradient(180deg, #07111f 0%, #040a14 100%);
            color: var(--texto);
            font-family: "Segoe UI", sans-serif;
        }}

        main {{
            width: min(980px, calc(100% - 32px));
            margin: 32px auto;
            padding: 24px;
            border: 1px solid var(--borde);
            border-radius: 20px;
            background: rgba(11, 23, 48, 0.94);
            box-shadow: 0 24px 60px rgba(0, 0, 0, 0.35);
        }}

        h1 {{
            margin: 0 0 8px;
            font-size: 1.9rem;
        }}

        p {{
            margin: 0 0 20px;
            color: var(--texto-suave);
        }}

        pre {{
            margin: 0;
            padding: 20px;
            overflow: auto;
            border-radius: 16px;
            border: 1px solid var(--borde);
            background: #030813;
            color: #aef7ff;
            font-family: "Consolas", "Courier New", monospace;
            font-size: 14px;
            line-height: 1.55;
            white-space: pre-wrap;
            word-break: break-word;
        }}

        .badge {{
            display: inline-block;
            margin-bottom: 16px;
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(0, 200, 255, 0.12);
            color: var(--acento);
            border: 1px solid rgba(0, 200, 255, 0.28);
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <main>
        <span class="badge">Resultado ejecutado</span>
        <h1>{fuente_segura}</h1>
        <p>Este archivo HTML puede abrirse con doble clic y muestra solo la salida final del programa.</p>
        <pre>{resultado}</pre>
    </main>
</body>
</html>
"""

    def vincular_eventos_editor(self, titulo: str) -> None:
        widget = self.text_widgets[titulo]._textbox
        widget.bind("<KeyRelease>", lambda _e, name=titulo: self.al_cambiar_editor(name), add="+")
        widget.bind("<ButtonRelease-1>", lambda _e, name=titulo: self.al_cambiar_editor(name), add="+")
        widget.bind("<MouseWheel>", lambda _e, name=titulo: self.after(20, lambda: self.actualizar_lineas(name)), add="+")
        widget.bind("<FocusIn>", lambda _e, name=titulo: self.al_cambiar_editor(name), add="+")

    def al_cambiar_editor(self, titulo: str) -> None:
        self.actualizar_lineas(titulo)
        if titulo == "Codigo fuente":
            self.resaltar_fuente()

    def configurar_resaltado(self, editor: ctk.CTkTextbox) -> None:
        text = editor._textbox
        text.tag_config("palabra", foreground=COLOR_CYAN)
        text.tag_config("tipo", foreground=COLOR_VERDE)
        text.tag_config("booleano", foreground=COLOR_VIOLETA)
        text.tag_config("cadena", foreground=COLOR_AMARILLO)
        text.tag_config("comentario", foreground="#5b8aa3")
        text.tag_config("numero", foreground=COLOR_NARANJA)
        text.tag_config("linea_actual", background="#102746")

    def resaltar_fuente(self) -> None:
        text = self.text_widgets["Codigo fuente"]._textbox
        contenido = text.get("1.0", "end-1c")
        for tag in ("palabra", "tipo", "booleano", "cadena", "comentario", "numero", "linea_actual"):
            text.tag_remove(tag, "1.0", "end")

        for match in re.finditer(r"//.*$", contenido, flags=re.MULTILINE):
            text.tag_add("comentario", f"1.0+{match.start()}c", f"1.0+{match.end()}c")

        for match in re.finditer(r'"[^"\n]*"', contenido):
            text.tag_add("cadena", f"1.0+{match.start()}c", f"1.0+{match.end()}c")

        for match in re.finditer(r"\b\d+(?:\.\d+)?\b", contenido):
            text.tag_add("numero", f"1.0+{match.start()}c", f"1.0+{match.end()}c")

        for token in self.PALABRAS_CLAVE:
            for match in re.finditer(rf"\b{re.escape(token)}\b", contenido):
                text.tag_add("palabra", f"1.0+{match.start()}c", f"1.0+{match.end()}c")

        for token in self.TIPOS:
            for match in re.finditer(rf"\b{re.escape(token)}\b", contenido):
                text.tag_add("tipo", f"1.0+{match.start()}c", f"1.0+{match.end()}c")

        for token in self.BOOLEANOS:
            for match in re.finditer(rf"\b{re.escape(token)}\b", contenido):
                text.tag_add("booleano", f"1.0+{match.start()}c", f"1.0+{match.end()}c")

        linea = text.index("insert").split(".")[0]
        text.tag_add("linea_actual", f"{linea}.0", f"{linea}.0 lineend+1c")

    def actualizar_lineas(self, titulo: str) -> None:
        if titulo not in self.text_widgets or titulo not in self.line_widgets:
            return
        editor = self.text_widgets[titulo]
        lineas = self.line_widgets[titulo]
        contenido = editor.get("1.0", "end-1c")
        total = max(1, contenido.count("\n") + 1)
        numeros = "\n".join(str(i) for i in range(1, total + 1))
        lineas.configure(state="normal")
        lineas.delete("1.0", "end")
        lineas.insert("1.0", numeros)
        lineas.configure(state="disabled")
        lineas._textbox.yview_moveto(editor._textbox.yview()[0])

    def refrescar_editors(self) -> None:
        for titulo in self.TAB_ORDER:
            self.actualizar_lineas(titulo)
        self.resaltar_fuente()
        self.after(200, self.refrescar_editors)


def main() -> None:
    app = App(BASE_DIR)
    app.mainloop()


if __name__ == "__main__":
    main()
