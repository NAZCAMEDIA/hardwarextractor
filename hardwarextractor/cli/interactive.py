"""Interactive CLI for HardwareXtractor."""

from __future__ import annotations

import sys
from typing import Optional

from hardwarextractor.cli.renderer import CLIRenderer
from hardwarextractor.engine.commands import CommandHandler
from hardwarextractor.engine.ficha_manager import FichaManager


class InteractiveCLI:
    """Interactive command-line interface for HardwareXtractor.

    Implements the flow defined in CLI_SPEC.md:
    1) Analizar componente
    2) Ver ficha agregada
    3) Exportar ficha
    4) Reset ficha
    5) Salir
    """

    VERSION = "1.0.0"

    def __init__(self):
        """Initialize the CLI."""
        self._renderer = CLIRenderer()
        self._handler = CommandHandler()
        self._running = True

    def run(self) -> None:
        """Run the interactive CLI loop."""
        self._print_welcome()

        while self._running:
            try:
                self._show_main_menu()
            except KeyboardInterrupt:
                print("\n")
                self._running = False
            except EOFError:
                self._running = False

        print(self._renderer.info("¡Hasta luego!"))

    def _print_welcome(self) -> None:
        """Print welcome message with ASCII art."""
        ascii_logo = """
  ██╗  ██╗██╗  ██╗████████╗██████╗  █████╗  ██████╗████████╗ ██████╗ ██████╗
  ██║  ██║╚██╗██╔╝╚══██╔══╝██╔══██╗██╔══██╗██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗
  ███████║ ╚███╔╝    ██║   ██████╔╝███████║██║        ██║   ██║   ██║██████╔╝
  ██╔══██║ ██╔██╗    ██║   ██╔══██╗██╔══██║██║        ██║   ██║   ██║██╔══██╗
  ██║  ██║██╔╝ ██╗   ██║   ██║  ██║██║  ██║╚██████╗   ██║   ╚██████╔╝██║  ██║
  ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝
"""
        from hardwarextractor.cli.renderer import Colors
        print(self._renderer._c(ascii_logo, Colors.CYAN))
        print(self._renderer._c(f"                           v{self.VERSION} - Hardware Specs Extractor", Colors.DIM))
        print()

    def _show_main_menu(self) -> None:
        """Show and handle the main menu."""
        menu = self._renderer.menu("MENÚ PRINCIPAL", [
            "Analizar componente",
            "Exportar ficha",
            "Reset ficha",
            "Salir",
        ])
        print(menu)

        choice = self._prompt("Selecciona opción: ")

        if choice == "1":
            self._analyze_component()
        elif choice == "2":
            self._export_ficha()
        elif choice == "3":
            self._reset_ficha()
        elif choice == "4":
            self._running = False
        else:
            print(self._renderer.error("Opción no válida"))
            print()

    def _analyze_component(self) -> None:
        """Handle component analysis flow."""
        print()
        input_text = self._prompt("Introduce modelo/PN/EAN/Texto: ")

        if not input_text.strip():
            print(self._renderer.error("Input vacío"))
            print()
            return

        print()
        import time
        start_time = time.time()

        # Process and show clean progress
        for event in self._handler.analyze_component(input_text):
            msg = event.message
            # Filter out noisy debug messages
            if msg.startswith("[SCRAPE]") or "HTML preview" in msg:
                continue
            # Show clean progress
            print(self._renderer.log(msg))

        elapsed = time.time() - start_time

        # Check orchestrator state for result
        if self._handler._last_component:
            # Success case
            component = self._handler._component_to_dict(self._handler._last_component)
            print(self._renderer.success(f"Completado en {elapsed:.1f}s"))
            print(self._renderer.component_result(component))

            # Check for reference warning
            has_ref = any(
                s.get("tier") == "REFERENCE"
                for s in component.get("specs", [])
            )
            if has_ref:
                print(self._renderer.warning(
                    "Este componente incluye datos no oficiales (REFERENCE)."
                ))
                print()

            # Auto-add to ficha
            result = self._handler.add_to_ficha()
            if result.get("status") == "success":
                print(self._renderer.success("Componente añadido a la ficha."))
            print()

            # Ask to export
            export = self._prompt("¿Exportar ahora? (No/CSV/XLSX/MD): ")
            if export.upper() in ("CSV", "XLSX", "MD"):
                self._do_export(export.upper())

        elif self._handler.orchestrator.last_candidates:
            # Needs selection
            candidates = [
                self._handler._candidate_to_dict(c)
                for c in self._handler.orchestrator.last_candidates
            ]
            print()
            print(self._renderer.candidates_list(candidates))
            print()

            choice = self._prompt("Selecciona candidato (1..N) o 0 para cancelar: ")
            try:
                idx = int(choice) - 1
                if idx < 0:
                    print(self._renderer.info("Cancelado"))
                    print()
                    return

                # Select and process
                for event in self._handler.select_candidate(idx):
                    print(self._renderer.log(event.message))

                if self._handler._last_component:
                    component = self._handler._component_to_dict(self._handler._last_component)
                    print()
                    print(self._renderer.component_result(component))

                    # Auto-add to ficha
                    result = self._handler.add_to_ficha()
                    if result.get("status") == "success":
                        print(self._renderer.success("Componente añadido a la ficha."))
                    print()

            except (ValueError, IndexError):
                print(self._renderer.error("Selección no válida"))
                print()
                return

        else:
            print(self._renderer.error("No se encontraron resultados"))
            print()

        # Ask for another search
        again = self._prompt("¿Hacer otra búsqueda? (Y/n): ")
        if again.lower() != "n":
            self._analyze_component()
        else:
            print()

    def _show_ficha(self) -> None:
        """Show the aggregated ficha."""
        print()
        result = self._handler.show_ficha()
        ficha = result.get("ficha", {})

        if ficha.get("component_count", 0) == 0:
            print(self._renderer.info("La ficha está vacía"))
        else:
            print(self._renderer.ficha_summary(ficha))

        print()

    def _export_ficha(self) -> None:
        """Handle ficha export."""
        print()

        if self._handler.ficha_manager.component_count == 0:
            print(self._renderer.error("La ficha está vacía, nada que exportar"))
            print()
            return

        format_choice = self._prompt("Formato (CSV/XLSX/MD): ")
        format_upper = format_choice.upper()

        if format_upper not in ("CSV", "XLSX", "MD"):
            print(self._renderer.error("Formato no válido"))
            print()
            return

        self._do_export(format_upper)

    def _do_export(self, format: str) -> None:
        """Perform the export."""
        default_ext = format.lower()
        default_path = f"./hxtractor_export.{default_ext}"

        path = self._prompt(f"Ruta de salida [{default_path}]: ")
        if not path.strip():
            path = default_path

        result = self._handler.export_ficha(format, path)

        if result.get("status") == "success":
            print(self._renderer.export_confirmation(result.get("path", path), format))
        else:
            print(self._renderer.error(result.get("message", "Export failed")))

        print()

    def _reset_ficha(self) -> None:
        """Handle ficha reset."""
        print()

        if self._handler.ficha_manager.component_count == 0:
            print(self._renderer.info("La ficha ya está vacía"))
            print()
            return

        confirm = self._prompt("Esto borrará la ficha actual. ¿Continuar? (y/N): ")

        if confirm.lower() == "y":
            self._handler.reset_ficha()
            print(self._renderer.success("Ficha reseteada"))
        else:
            print(self._renderer.info("Cancelado"))

        print()

    def _prompt(self, text: str) -> str:
        """Show a prompt and get input."""
        try:
            return input(text)
        except (KeyboardInterrupt, EOFError):
            raise


def main() -> None:
    """Entry point for CLI."""
    cli = InteractiveCLI()
    cli.run()


if __name__ == "__main__":
    main()
