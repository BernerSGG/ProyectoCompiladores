# RadarScriptCompiler

## 1. Descripcion del proyecto

`RadarScriptCompiler` es un compilador academico desarrollado en Python para un lenguaje de programacion didactico llamado `RadarScript`. El proyecto implementa un flujo completo de compilacion que abarca desde la lectura de un archivo fuente `.rdr` hasta la generacion de codigo objeto y su ejecucion en una maquina virtual propia.

La solucion fue construida con una arquitectura modular, separando cada fase clasica de un compilador en componentes independientes. Esto facilita el mantenimiento del codigo, la validacion de resultados intermedios y el analisis del comportamiento de cada etapa del proceso.

## 2. Objetivo del compilador

El objetivo principal del proyecto es demostrar, en un contexto academico, el funcionamiento integral de un compilador mediante la implementacion de las siguientes fases:

- Analisis lexico
- Analisis sintactico
- Analisis semantico
- Generacion de codigo intermedio
- Generacion de codigo objeto
- Ejecucion del programa compilado en una maquina virtual

Ademas de cumplir una funcion demostrativa, el proyecto permite visualizar artefactos intermedios y reportes de error, lo cual aporta valor pedagogico durante pruebas, exposiciones y actividades de laboratorio.

## 3. Arquitectura del sistema

El proyecto sigue una arquitectura por etapas, donde cada modulo tiene una responsabilidad bien definida y entrega su salida a la fase siguiente.

### Modulos principales

- `src/lexer/lexer.py`
  Responsable del analisis lexico. Lee el codigo fuente y lo convierte en una secuencia de tokens.
- `src/parser/parser.py`
  Responsable del analisis sintactico. Valida la estructura del programa y construye un AST simplificado.
- `src/semantic/semantic.py`
  Responsable del analisis semantico. Verifica declaraciones, tipos de datos y compatibilidad de operaciones.
- `src/intermediate/intermediate.py`
  Genera una representacion intermedia basada en cuadruplos.
- `src/codegen/codegen.py`
  Traduce los cuadruplos a codigo objeto en pseudoensamblador academico.
- `src/vm/vm.py`
  Ejecuta el archivo objeto generado por la fase de code generation.
- `src/diagnostics.py`
  Centraliza el registro, formato y exportacion de errores.
- `src/gui.py`
  Proporciona una interfaz grafica en Tkinter para cargar archivos, compilar, visualizar resultados, ejecutar la VM y guardar el resultado final en HTML.
- `src/main.py`
  Permite ejecutar el flujo completo desde consola.

### Vista general de la arquitectura

```text
Archivo .rdr
   |
   v
Lexer
   |
   v
Parser / AST
   |
   v
Analizador semantico / Tabla de simbolos
   |
   v
Codigo intermedio (.int)
   |
   v
Codigo objeto (.obj)
   |
   v
Maquina virtual
   |
   v
Salida final en terminal
```

## 4. Flujo de compilacion

El flujo implementado por el sistema es el siguiente:

1. El usuario escribe o carga un programa fuente con extension `.rdr`.
2. El lexer analiza el contenido caracter por caracter y produce tokens.
3. El parser valida la gramatica del lenguaje y construye la estructura sintactica.
4. El analizador semantico verifica:
   - Variables declaradas
   - Variables duplicadas
   - Compatibilidad de tipos
   - Condiciones validas en estructuras de control
5. Si no hay errores, el sistema genera codigo intermedio en forma de cuadruplos.
6. El generador de codigo transforma los cuadruplos a pseudoensamblador.
7. La maquina virtual interpreta el archivo `.obj` y ejecuta el programa.
8. El sistema produce salidas intermedias y finales en archivos y en pantalla.

### Archivos generados

- `outputs/salida.lex`: salida del analisis lexico
- `outputs/salida.sym`: tabla de simbolos
- `outputs/salida.int`: codigo intermedio
- `outputs/salida.obj`: codigo objeto
- `outputs/errores.txt`: reporte de errores

## 5. Tecnologias utilizadas

- `Python 3`
  Lenguaje principal del proyecto.
- `Tkinter`
  Biblioteca estandar de Python utilizada para la interfaz grafica.
- `Pathlib`
  Utilizado para manejo de rutas y archivos.
- `Dataclasses`
  Utilizado para encapsular artefactos generados durante la compilacion.

No se requieren frameworks externos para la ejecucion basica del proyecto.

## 6. Instrucciones de instalacion

### Requisitos previos

- Tener instalado `Python 3.10` o superior
- Tener acceso a una terminal o consola del sistema

### Clonar o copiar el proyecto

Ubique el proyecto en una carpeta local, por ejemplo:

```powershell
cd C:\ruta\del\proyecto
```

### Crear entorno virtual

```powershell
python -m venv .venv
```

### Activar entorno virtual

En Windows:

```powershell
.venv\Scripts\Activate.ps1
```

En Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Instalar dependencias

El proyecto utiliza principalmente librerias estandar de Python, por lo que no requiere una instalacion extensa. Si se desea dejar preparado un entorno limpio, basta con verificar que `tkinter` este disponible en la instalacion de Python.

## 7. Instrucciones de uso

### Ejecucion por interfaz grafica

Desde la raiz del proyecto:

```powershell
python .\gui.py
```

O bien:

```powershell
python .\src\gui.py
```

### Funcionalidades de la interfaz

- Cargar un archivo `.rdr`
- Visualizar el codigo fuente
- Compilar el programa
- Consultar la salida lexica
- Consultar la tabla de simbolos
- Consultar el codigo intermedio
- Consultar el codigo objeto
- Ejecutar la maquina virtual
- Revisar errores en la terminal interna
- Guardar el resultado final de la VM como archivo HTML

### Ejecucion por consola

```powershell
python .\main.py
```

Este modo ejecuta el flujo completo de compilacion y luego lanza la VM utilizando el archivo de prueba configurado en el proyecto.

## 8. Ejemplo de entrada y salida

### Ejemplo de entrada

Archivo: `tests/ejemplo_grande.rdr`

```text
programa operativo_radar_extendido;

entero distancia_norte;
entero distancia_sur;
entero ciclos_revision;
entero contador_alertas;
decimal viento_norte;
decimal viento_sur;
decimal lluvia_actual;
cadena zona_critica;

distancia_norte = 180;
distancia_sur = 95;
ciclos_revision = 4;
contador_alertas = 0;
viento_norte = 82.5;
viento_sur = 48.0;
lluvia_actual = 63.7;
zona_critica = "NORTE";

si viento_norte > 70 entonces
    contador_alertas = contador_alertas + 1;
    alerta("Viento fuerte detectado en " + zona_critica);
fin

si lluvia_actual > 60 entonces
    contador_alertas = contador_alertas + 1;
    alerta("Lluvia intensa detectada en " + zona_critica);
fin

reporte("Proceso finalizado");
```

### Ejemplo de salida esperada

Salida final en ejecucion:

```text
ALERTA: Viento fuerte detectado en NORTE
ALERTA: Lluvia intensa detectada en NORTE
REPORTE: Proceso finalizado
```

Despues de ejecutar la VM desde la interfaz, el sistema tambien permite guardar este resultado final como un archivo `.html` en la ubicacion elegida por el usuario.

### Ejemplo de artefactos generados

- `salida.lex`: lista formateada de tokens
- `salida.sym`: tabla de simbolos con variables y tipos
- `salida.int`: cuadruplos del programa
- `salida.obj`: instrucciones pseudoensamblador

## 9. Estructura de carpetas explicada

```text
RadarScriptCompiler/
|-- gui.py
|-- main.py
|-- README.md
|-- outputs/
|   |-- errores.txt
|   |-- salida.int
|   |-- salida.lex
|   |-- salida.obj
|   |-- salida.sym
|   `-- vm_test.obj
|-- src/
|   |-- diagnostics.py
|   |-- gui.py
|   |-- main.py
|   |-- codegen/
|   |   `-- codegen.py
|   |-- intermediate/
|   |   `-- intermediate.py
|   |-- lexer/
|   |   `-- lexer.py
|   |-- parser/
|   |   `-- parser.py
|   |-- semantic/
|   |   `-- semantic.py
|   `-- vm/
|       `-- vm.py
`-- tests/
    |-- ejemplo.rdr
    |-- ejemplo_grande.rdr
    |-- ejemplomalo.rdr
    `-- ejemplomalo_grande.rdr
```

### Descripcion de carpetas

- `src/`
  Contiene la implementacion principal del compilador.
- `tests/`
  Incluye programas de ejemplo para validacion del compilador.
- `outputs/`
  Almacena las salidas generadas por las diferentes fases del proceso.
- `main.py` y `gui.py`
  Son lanzadores desde la raiz del proyecto para facilitar la ejecucion.

## 10. Manejo de errores

El proyecto incluye un modulo centralizado de diagnosticos en `src/diagnostics.py`. Este componente recopila errores y genera un reporte unificado durante la compilacion.

### Tipos de errores contemplados

- `Errores lexicos`
  Detectan simbolos invalidos, numeros mal formados y cadenas sin cerrar.
- `Errores sintacticos`
  Detectan estructuras incompletas, tokens inesperados y omision de simbolos obligatorios.
- `Errores semanticos`
  Detectan variables no declaradas, variables duplicadas, incompatibilidad de tipos y uso invalido de condiciones.

### Formato del reporte

Los errores se registran indicando:

- Tipo de error
- Linea aproximada
- Columna aproximada
- Descripcion del problema

El reporte se exporta automaticamente en:

```text
outputs/errores.txt
```

## 11. Capturas

Para la version final del informe o entrega, se recomienda agregar las siguientes capturas de pantalla:

- `Captura 1: Ventana principal`
  Mostrar la interfaz grafica abierta con el archivo `.rdr` cargado.
- `Captura 2: Salida lexica`
  Mostrar la pestana donde se visualizan los tokens generados.
- `Captura 3: Tabla de simbolos`
  Mostrar la salida del analisis semantico.
- `Captura 4: Codigo intermedio`
  Mostrar los cuadruplos generados.
- `Captura 5: Codigo objeto`
  Mostrar el pseudoensamblador generado.
- `Captura 6: Ejecucion de la VM`
  Mostrar la terminal con las salidas `ALERTA` y `REPORTE`.
- `Captura 7: Manejo de errores`
  Mostrar la compilacion del archivo `ejemplomalo.rdr` con el reporte correspondiente.

Estas capturas pueden insertarse en esta seccion del `README` o en un documento anexo, como manual de usuario o informe tecnico.

## 12. Conclusion

`RadarScriptCompiler` representa una implementacion academica completa de un compilador modular, construida para demostrar de forma practica las fases fundamentales del proceso de compilacion. Su estructura por componentes, la generacion de artefactos intermedios y la integracion con una maquina virtual permiten observar con claridad la transformacion progresiva de un programa fuente hacia su ejecucion final.

El proyecto cumple una funcion formativa importante, ya que no solo compila programas escritos en `RadarScript`, sino que tambien facilita el analisis de errores, la depuracion del lenguaje y la comprension del ciclo completo de compilacion. Por ello, constituye una base solida para exposiciones universitarias, mejoras futuras y extensiones del lenguaje.
