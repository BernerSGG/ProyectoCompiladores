"""Python 3 module for the RadarScript virtual machine."""

from __future__ import annotations

from pathlib import Path


# This file defines the virtual machine responsible for executing generated
# RadarScript object code or bytecode during testing and validation.


class VirtualMachineError(Exception):
    """Represents an execution error in the RadarScript virtual machine."""


class VirtualMachine:
    """Execute RadarScript pseudo-assembly instructions."""

    def __init__(self) -> None:
        self.stack: list[object] = []
        self.memory: dict[str, object] = {}
        self.instructions: list[str] = []
        self.labels: dict[str, int] = {}
        self.program_counter = 0

    def load_file(self, ruta_archivo: str) -> None:
        """Load and prepare an object file for execution."""
        path = Path(ruta_archivo)
        if not path.exists():
            raise FileNotFoundError(f"No se encontro el archivo objeto: {ruta_archivo}")

        source_lines = path.read_text(encoding="utf-8").splitlines()
        self.instructions = []
        self.labels = {}
        self.stack = []
        self.memory = {}
        self.program_counter = 0

        for line in source_lines:
            instruction = line.strip()
            if not instruction:
                continue
            if instruction == "Código objeto (.obj)":
                continue
            if instruction.endswith(":"):
                self.labels[instruction[:-1]] = len(self.instructions)
                continue
            self.instructions.append(instruction)

    def run(self) -> None:
        """Execute loaded instructions until HALT."""
        while self.program_counter < len(self.instructions):
            instruction = self.instructions[self.program_counter]
            self.program_counter += 1
            self._execute_instruction(instruction)

    def _execute_instruction(self, instruction: str) -> None:
        """Execute a single pseudo-assembly instruction."""
        parts = instruction.split(maxsplit=1)
        opcode = parts[0]
        operand_text = parts[1] if len(parts) > 1 else ""

        if opcode == "PUSH":
            self.stack.append(self._resolve_value(operand_text))
            return

        if opcode == "LOAD":
            self.stack.append(self._resolve_value(operand_text))
            return

        if opcode == "STORE":
            self._require_stack(1)
            self.memory[operand_text] = self.stack.pop()
            return

        if opcode == "MOV":
            target, source = self._split_operands(operand_text, expected=2)
            self.memory[target] = self._resolve_value(source)
            return

        if opcode == "ADD":
            self._binary_numeric_operation(lambda left, right: left + right)
            return

        if opcode == "SUB":
            self._binary_numeric_operation(lambda left, right: left - right)
            return

        if opcode == "MUL":
            self._binary_numeric_operation(lambda left, right: left * right)
            return

        if opcode == "DIV":
            self._binary_numeric_operation(self._safe_division)
            return

        if opcode == "GT":
            self._binary_comparison(lambda left, right: left > right)
            return

        if opcode == "LT":
            self._binary_comparison(lambda left, right: left < right)
            return

        if opcode == "EQ":
            self._binary_comparison(lambda left, right: left == right)
            return

        if opcode == "GTE":
            self._binary_comparison(lambda left, right: left >= right)
            return

        if opcode == "LTE":
            self._binary_comparison(lambda left, right: left <= right)
            return

        if opcode == "NEQ":
            self._binary_comparison(lambda left, right: left != right)
            return

        if opcode == "JMP":
            self.program_counter = self._resolve_label(operand_text)
            return

        if opcode == "JMPF":
            self._require_stack(1)
            condition = self.stack.pop()
            if not self._is_truthy(condition):
                self.program_counter = self._resolve_label(operand_text)
            return

        if opcode == "CONCAT":
            self._binary_concat()
            return

        if opcode == "ALERTA":
            self._require_stack(1)
            print(f"ALERTA: {self.stack.pop()}")
            return

        if opcode == "REPORTE":
            self._require_stack(1)
            print(f"REPORTE: {self.stack.pop()}")
            return

        if opcode == "HALT":
            self.program_counter = len(self.instructions)
            return

        raise VirtualMachineError(f"Instruccion no soportada: {instruction}")

    def _binary_numeric_operation(self, operation) -> None:
        """Apply a numeric binary operation using the top stack values."""
        left, right = self._pop_binary_operands()
        if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
            raise VirtualMachineError("Operacion numerica con operandos invalidos.")
        self.stack.append(operation(left, right))

    def _binary_comparison(self, comparison) -> None:
        """Apply a comparison using the top stack values."""
        left, right = self._pop_binary_operands()
        try:
            result = comparison(left, right)
        except TypeError as error:
            raise VirtualMachineError("Comparacion invalida entre operandos incompatibles.") from error
        self.stack.append(result)

    def _binary_concat(self) -> None:
        """Concatenate the top stack values as strings."""
        left, right = self._pop_binary_operands()
        self.stack.append(f"{left}{right}")

    def _pop_binary_operands(self) -> tuple[object, object]:
        """Pop two operands preserving left-to-right order."""
        self._require_stack(2)
        right = self.stack.pop()
        left = self.stack.pop()
        return left, right

    def _resolve_value(self, token: str) -> object:
        """Resolve a literal or variable reference."""
        cleaned = token.strip()
        if cleaned in self.memory:
            return self.memory[cleaned]
        if cleaned == "verdadero":
            return True
        if cleaned == "falso":
            return False
        if cleaned.startswith('"') and cleaned.endswith('"') and len(cleaned) >= 2:
            return cleaned[1:-1]
        if self._is_integer(cleaned):
            return int(cleaned)
        if self._is_decimal(cleaned):
            return float(cleaned)
        return cleaned

    def _resolve_label(self, label: str) -> int:
        """Return the instruction index for a label."""
        cleaned = label.strip()
        if cleaned not in self.labels:
            raise VirtualMachineError(f"Etiqueta no encontrada: {cleaned}")
        return self.labels[cleaned]

    def _split_operands(self, operand_text: str, expected: int) -> list[str]:
        """Split comma-separated operands."""
        parts = [part.strip() for part in operand_text.split(",")]
        if len(parts) != expected:
            raise VirtualMachineError(f"Operandos invalidos: {operand_text}")
        return parts

    def _require_stack(self, size: int) -> None:
        """Ensure the stack has enough values."""
        if len(self.stack) < size:
            raise VirtualMachineError("Stack insuficiente para ejecutar la instruccion.")

    def _is_truthy(self, value: object) -> bool:
        """Interpret a runtime value as a boolean condition."""
        if isinstance(value, bool):
            return value
        return bool(value)

    def _safe_division(self, left: float, right: float) -> float:
        """Perform division and guard against division by zero."""
        if right == 0:
            raise VirtualMachineError("Division por cero.")
        return left / right

    def _is_integer(self, value: str) -> bool:
        """Return True if the token is an integer literal."""
        if not value:
            return False
        if value[0] in {"+", "-"}:
            return value[1:].isdigit()
        return value.isdigit()

    def _is_decimal(self, value: str) -> bool:
        """Return True if the token is a decimal literal."""
        if value.count(".") != 1:
            return False
        signless = value[1:] if value[:1] in {"+", "-"} else value
        left, right = signless.split(".")
        return left.isdigit() and right.isdigit()


def ejecutar_archivo_objeto(ruta_archivo: str) -> None:
    """Load and execute a RadarScript object file."""
    vm = VirtualMachine()
    vm.load_file(ruta_archivo)
    vm.run()


def main() -> None:
    """Execute the default RadarScript object output file."""
    ruta_objeto = Path(__file__).resolve().parent.parent.parent / "outputs" / "salida.obj"
    ejecutar_archivo_objeto(str(ruta_objeto))


if __name__ == "__main__":
    main()
