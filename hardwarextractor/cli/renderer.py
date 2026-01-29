"""CLI renderer for formatting output."""

from __future__ import annotations

import sys
from typing import Any, Optional


# ANSI color codes
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright foreground
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"

    # Background
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"


# Status icons
class Icons:
    CHECK = "✓"
    CROSS = "✗"
    ARROW = "→"
    WARNING = "⚠"
    INFO = "ℹ"
    SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class CLIRenderer:
    """Renders CLI output with colors and formatting."""

    def __init__(self, use_colors: bool = True, width: int = 80):
        """Initialize the renderer.

        Args:
            use_colors: Whether to use ANSI colors
            width: Terminal width for formatting
        """
        self._use_colors = use_colors and sys.stdout.isatty()
        self._width = width

    def _c(self, text: str, *colors: str) -> str:
        """Apply colors to text if enabled."""
        if not self._use_colors:
            return text
        color_codes = "".join(colors)
        return f"{color_codes}{text}{Colors.RESET}"

    def header(self, text: str) -> str:
        """Render a header."""
        line = "═" * (self._width - 2)
        return (
            f"╔{line}╗\n"
            f"║{self._c(text.center(self._width - 2), Colors.BOLD)}║\n"
            f"╚{line}╝"
        )

    def menu(self, title: str, options: list[str]) -> str:
        """Render a menu."""
        lines = [self.header(title), ""]
        for i, option in enumerate(options, 1):
            lines.append(f"  {self._c(str(i), Colors.CYAN)}) {option}")
        lines.append("")
        return "\n".join(lines)

    def table(
        self,
        headers: list[str],
        rows: list[list[str]],
        title: Optional[str] = None
    ) -> str:
        """Render a table."""
        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))

        # Build table
        lines = []

        # Title
        if title:
            total_width = sum(col_widths) + len(col_widths) * 3 + 1
            lines.append("┌" + "─" * (total_width - 2) + "┐")
            lines.append("│" + self._c(title.center(total_width - 2), Colors.BOLD) + "│")

        # Header separator
        sep = "┼".join("─" * (w + 2) for w in col_widths)
        lines.append("├" + sep + "┤")

        # Header row
        header_cells = [
            self._c(h.center(col_widths[i]), Colors.BOLD)
            for i, h in enumerate(headers)
        ]
        lines.append("│ " + " │ ".join(header_cells) + " │")

        # Separator
        lines.append("├" + sep + "┤")

        # Data rows
        for row in rows:
            cells = []
            for i, cell in enumerate(row):
                cell_str = str(cell) if cell is not None else ""
                if i < len(col_widths):
                    # Color based on content
                    if cell_str in ("OFFICIAL", "EXTRACTED_OFFICIAL"):
                        cell_str = self._c(cell_str.ljust(col_widths[i]), Colors.GREEN)
                    elif cell_str in ("REFERENCE", "EXTRACTED_REFERENCE"):
                        cell_str = self._c(cell_str.ljust(col_widths[i]), Colors.YELLOW)
                    elif cell_str == "CALCULATED":
                        cell_str = self._c(cell_str.ljust(col_widths[i]), Colors.CYAN)
                    elif cell_str in ("NA", "UNKNOWN"):
                        cell_str = self._c(cell_str.ljust(col_widths[i]), Colors.DIM)
                    else:
                        cell_str = cell_str.ljust(col_widths[i])
                    cells.append(cell_str)
            lines.append("│ " + " │ ".join(cells) + " │")

        # Bottom border
        lines.append("└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘")

        return "\n".join(lines)

    def log(self, message: str, icon: str = Icons.ARROW) -> str:
        """Render a log message."""
        return f"{self._c(icon, Colors.CYAN)} {message}"

    def success(self, message: str) -> str:
        """Render a success message."""
        return f"{self._c(Icons.CHECK, Colors.GREEN)} {self._c(message, Colors.GREEN)}"

    def error(self, message: str) -> str:
        """Render an error message."""
        return f"{self._c(Icons.CROSS, Colors.RED)} {self._c(message, Colors.RED)}"

    def warning(self, message: str) -> str:
        """Render a warning message."""
        return f"{self._c(Icons.WARNING, Colors.YELLOW)} {self._c(message, Colors.YELLOW)}"

    def info(self, message: str) -> str:
        """Render an info message."""
        return f"{self._c(Icons.INFO, Colors.BLUE)} {message}"

    def progress(self, current: int, total: int, message: str = "") -> str:
        """Render a progress indicator."""
        pct = int((current / total) * 100) if total > 0 else 0
        bar_width = 20
        filled = int(bar_width * current / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_width - filled)
        return f"{self._c(bar, Colors.CYAN)} {pct:3d}% {message}"

    def component_result(self, component: dict) -> str:
        """Render a component result."""
        lines = []

        # Header
        comp_type = component.get("type", "UNKNOWN")
        brand = component.get("brand", "")
        model = component.get("model", "")
        pn = component.get("part_number", "")

        title = f"TIPO: {comp_type} | {brand} {model}"
        if pn:
            title += f" ({pn})"

        lines.append(self.header(title))

        # Specs table
        specs = component.get("specs", [])
        if specs:
            headers = ["Campo", "Valor", "Status", "Tier", "Fuente"]
            rows = []
            for spec in specs:
                source = spec.get("source_name", "")
                if len(source) > 15:
                    source = source[:12] + "..."
                rows.append([
                    spec.get("label", spec.get("key", "")),
                    str(spec.get("value", "")),
                    spec.get("status", ""),
                    spec.get("tier", ""),
                    source,
                ])
            lines.append(self.table(headers, rows))

        return "\n".join(lines)

    def candidates_list(self, candidates: list[dict]) -> str:
        """Render a list of candidates for selection."""
        lines = [self.info("Selecciona un candidato:"), ""]

        for i, c in enumerate(candidates, 1):
            brand = c.get("brand", "")
            model = c.get("model", "")
            pn = c.get("part_number", "")
            source = c.get("source_name", "")
            score = c.get("score", 0)

            line = f"  {self._c(str(i), Colors.CYAN)}) "
            line += f"{self._c(brand, Colors.BOLD)} {model}"
            if pn:
                line += f" ({pn})"
            line += f" - {source} "
            line += f"[{self._c(f'{int(score*100)}%', Colors.DIM)}]"

            lines.append(line)

        lines.append("")
        lines.append(f"  {self._c('0', Colors.CYAN)}) Cancelar")

        return "\n".join(lines)

    def ficha_summary(self, ficha: dict) -> str:
        """Render a ficha summary."""
        lines = []

        # Header
        comp_count = ficha.get("component_count", 0)
        has_ref = ficha.get("has_reference", False)

        lines.append(self.header(f"FICHA TÉCNICA ({comp_count} componentes)"))
        lines.append("")

        # Warning banner if has reference data
        if has_ref:
            lines.append(self.warning(
                "Esta ficha contiene datos de fuentes no oficiales (REFERENCE)"
            ))
            lines.append("")

        # Components list
        components = ficha.get("components", [])
        if components:
            lines.append(self._c("Componentes:", Colors.BOLD))
            for c in components:
                comp_type = c.get("type", "")
                brand = c.get("brand", "")
                model = c.get("model", "")
                lines.append(f"  • {self._c(comp_type, Colors.CYAN)}: {brand} {model}")
            lines.append("")

        # Fields by section (summary)
        fields = ficha.get("fields_by_template", [])
        if fields:
            current_section = None
            for f in fields:
                section = f.get("section", "")
                if section != current_section:
                    if current_section is not None:
                        lines.append("")
                    lines.append(self._c(f"[{section}]", Colors.BOLD))
                    current_section = section

                value = f.get("value")
                if value is not None and value != "":
                    field_name = f.get("field", "")
                    tier = f.get("tier", "")
                    tier_indicator = ""
                    if tier == "REFERENCE":
                        tier_indicator = self._c(" (REF)", Colors.YELLOW)
                    elif tier == "OFFICIAL":
                        tier_indicator = self._c(" (OFF)", Colors.GREEN)

                    lines.append(f"  {field_name}: {value}{tier_indicator}")

        return "\n".join(lines)

    def export_confirmation(self, path: str, format: str) -> str:
        """Render export confirmation."""
        return self.success(f"Exportado: {path} ({format.upper()})")
