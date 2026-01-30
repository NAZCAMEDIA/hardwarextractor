"""Interactive CLI for HardwareXtractor."""

from __future__ import annotations

import sys
from typing import Optional

from hardwarextractor.cli.renderer import CLIRenderer, Spinner, Colors
from hardwarextractor.core.feedback import get_feedback_collector
from hardwarextractor.core.github_reporter import send_feedback_report
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

    VERSION = "0.2.0"

    def __init__(self):
        """Initialize the CLI."""
        self._renderer = CLIRenderer()
        self._handler = CommandHandler()
        self._feedback = get_feedback_collector()
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
        print(self._renderer._c("                              © 2026 NAZCAMEDIA", Colors.DIM))
        print()
        # Beta banner
        print(self._renderer.beta_banner())

    def _show_main_menu(self) -> None:
        """Show and handle the main menu."""
        menu = self._renderer.menu("MENÚ PRINCIPAL", [
            "Analizar componente",
            "Exportar ficha",
            "Reset ficha",
            "Enviar feedback",
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
            self._send_manual_feedback()
        elif choice == "5":
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

        # Store input for feedback
        self._handler._last_input = input_text

        print()

        # Use spinner with automatic timed phases
        spinner = Spinner(use_colors=self._renderer._use_colors)
        spinner.start()

        # Process events (spinner updates automatically based on time)
        for event in self._handler.analyze_component(input_text):
            # Just consume events, spinner handles progress display
            pass

        # Stop spinner and show result
        if self._handler._last_component:
            spinner.stop("Análisis completado", success=True)
            component = self._handler._component_to_dict(self._handler._last_component)
            print()
            print(self._renderer.component_result(component))

            # Show reference sources for this component type
            comp_type = component.get("type", "")
            if comp_type:
                print(self._renderer.reference_sources(comp_type))

            # Check for reference warning
            has_ref = any(
                s.get("tier") == "REFERENCE"
                for s in component.get("specs", [])
            )
            if has_ref:
                print(self._renderer.warning(
                    "Este componente incluye datos no oficiales (REFERENCE)."
                ))

            # Auto-add to ficha
            result = self._handler.add_to_ficha()
            if result.get("status") == "success":
                print(self._renderer.success("Componente añadido a la ficha."))
            print()

            # Ask for feedback
            self._ask_feedback("success", component_type=comp_type)

            # Ask to export
            export = self._prompt("¿Exportar ahora? (No/CSV/XLSX/MD): ")
            if export.upper() in ("CSV", "XLSX", "MD"):
                self._do_export(export.upper())

        elif self._handler.orchestrator.last_candidates:
            spinner.stop("Se encontraron múltiples candidatos", success=True)
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

                # Select and process with spinner
                print()
                select_spinner = Spinner(use_colors=self._renderer._use_colors)
                select_spinner.start()

                for event in self._handler.select_candidate(idx):
                    # Just consume events, spinner handles progress display
                    pass

                if self._handler._last_component:
                    select_spinner.stop("Análisis completado", success=True)
                    component = self._handler._component_to_dict(self._handler._last_component)
                    print()
                    print(self._renderer.component_result(component))

                    # Show reference sources for this component type
                    comp_type = component.get("type", "")
                    if comp_type:
                        print(self._renderer.reference_sources(comp_type))

                    # Check for reference warning
                    has_ref = any(
                        s.get("tier") == "REFERENCE"
                        for s in component.get("specs", [])
                    )
                    if has_ref:
                        print(self._renderer.warning(
                            "Este componente incluye datos no oficiales (REFERENCE)."
                        ))

                    # Auto-add to ficha
                    result = self._handler.add_to_ficha()
                    if result.get("status") == "success":
                        print(self._renderer.success("Componente añadido a la ficha."))
                    print()

                    # Ask for feedback
                    self._ask_feedback("success", component_type=comp_type)
                else:
                    select_spinner.stop("No se pudieron obtener especificaciones", success=False)
                    print(self._renderer.warning(
                        "El scraping falló. Intenta con otro componente o verifica la conexión."
                    ))
                    print()

                    # Ask for feedback on failure
                    self._ask_feedback("error", error_msg="Scraping failed")

            except (ValueError, IndexError):
                print(self._renderer.error("Selección no válida"))
                print()
                return

        else:
            spinner.stop("No se encontraron resultados", success=False)
            print()

            # Ask for feedback on no results
            self._ask_feedback("no_results")

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

    def _send_manual_feedback(self) -> None:
        """Send manual feedback (not tied to a specific search)."""
        print()
        print(self._renderer._c("  ENVIAR FEEDBACK", Colors.BOLD))
        print(self._renderer._c("  ───────────────────────────────────────", Colors.DIM))
        print()
        print("  Cuéntanos tu experiencia, sugerencias o problemas encontrados.")
        print("  Tu feedback nos ayuda a mejorar HardwareXtractor.")
        print()

        # Get feedback type
        print("  Tipo de feedback:")
        print(f"    {self._renderer._c('1', Colors.CYAN)}) Bug o error")
        print(f"    {self._renderer._c('2', Colors.CYAN)}) Sugerencia de mejora")
        print(f"    {self._renderer._c('3', Colors.CYAN)}) Componente no soportado")
        print(f"    {self._renderer._c('4', Colors.CYAN)}) Otro")
        print()

        feedback_type = self._prompt("  Selecciona tipo (1-4): ")
        type_labels = {
            "1": "Bug o error",
            "2": "Sugerencia de mejora",
            "3": "Componente no soportado",
            "4": "Otro",
        }
        type_label = type_labels.get(feedback_type, "Otro")

        print()
        comment = self._prompt("  Describe tu feedback: ")

        if not comment.strip():
            print(self._renderer.info("Feedback cancelado (comentario vacío)"))
            print()
            return

        # Create manual feedback report
        import platform
        import sys
        from datetime import datetime

        title = f"[Feedback Beta] {type_label}"
        body = f"""## Tipo de feedback
{type_label}

## Comentario del usuario
> {comment}

## Información del sistema
- **Versión:** {self.VERSION}
- **OS:** {platform.system()} {platform.release()}
- **Python:** {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}
- **Timestamp:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---
*Feedback manual de HardwareXtractor Beta v{self.VERSION}*
"""

        print()
        print(self._renderer.feedback_sending())

        result = send_feedback_report(
            title=title,
            body=body,
            labels=["beta-feedback", "manual-feedback"],
        )

        if result.get("status") == "success":
            print(self._renderer.feedback_thanks(
                issue_url=result.get("issue_url", ""),
                issue_number=result.get("issue_number", 0),
            ))
        else:
            print(self._renderer.feedback_error(result.get("message", "Error desconocido")))

    def _ask_feedback(self, result: str, component_type: str = "", error_msg: str = "") -> None:
        """Ask user for feedback after a search.

        Args:
            result: Search result ("success", "no_results", "error")
            component_type: Type of component searched
            error_msg: Error message if applicable
        """
        # Capture search context
        last_input = getattr(self._handler, '_last_input', '')
        self._feedback.capture_search(
            input_text=last_input,
            component_type=component_type,
            result=result,
            error_message=error_msg,
        )

        # Show reminder every N searches
        if self._feedback.should_show_reminder():
            print(self._renderer.beta_reminder(self._feedback.search_count))

        # Ask if it worked
        worked = self._prompt(self._renderer.feedback_prompt_worked())

        if worked.lower() == 'n':
            # Ask what went wrong
            problem = self._prompt(self._renderer.feedback_prompt_problem())

            # Generate and send report
            report = self._feedback.generate_report(user_comment=problem)
            if report:
                print(self._renderer.feedback_sending())
                result = send_feedback_report(
                    title=report["title"],
                    body=report["body"],
                    labels=report["labels"],
                )

                if result.get("status") == "success":
                    print(self._renderer.feedback_thanks(
                        issue_url=result.get("issue_url", ""),
                        issue_number=result.get("issue_number", 0),
                    ))
                else:
                    print(self._renderer.feedback_error(result.get("message", "Error desconocido")))


def main() -> None:
    """Entry point for CLI."""
    cli = InteractiveCLI()
    cli.run()


if __name__ == "__main__":
    main()
