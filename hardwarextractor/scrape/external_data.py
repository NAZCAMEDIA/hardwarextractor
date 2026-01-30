#!/usr/bin/env python3
"""External data sources integration for hardware specs.

This module handles importing data from:
1. External APIs (Octopart, FindChips, etc.)
2. Public datasets (Kaggle, GitHub, etc.)
3. PDF datasheets (manufacturer specifications)
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from hardwarextractor.models.schemas import ComponentType, SpecField


# ============================================================================
# DATA SOURCE INTERFACES
# ============================================================================


@dataclass
class ExternalSpec:
    """A specification from an external source."""

    key: str
    value: str | int | float
    unit: Optional[str] = None
    confidence: float = 0.5
    source_name: str = "external"
    source_url: Optional[str] = None


@dataclass
class ExternalComponent:
    """A component from an external source."""

    brand: str
    model: str
    component_type: ComponentType
    specs: List[ExternalSpec] = field(default_factory=list)
    part_number: Optional[str] = None
    source_url: Optional[str] = None


class ExternalDataSource(ABC):
    """Base class for external data sources."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the data source."""
        pass

    @abstractmethod
    def search(
        self, query: str, component_type: ComponentType
    ) -> List[ExternalComponent]:
        """Search for components matching query."""
        pass

    @abstractmethod
    def get_specs(self, component_id: str) -> Optional[ExternalComponent]:
        """Get full specs for a specific component."""
        pass


# ============================================================================
# API SOURCES (placeholder implementations)
# ============================================================================


class OctopartAPI(ExternalDataSource):
    """Octopart API integration for hardware specs."""

    @property
    def name(self) -> str:
        return "Octopart"

    def search(
        self, query: str, component_type: ComponentType
    ) -> List[ExternalComponent]:
        # TODO: Implement Octopart API
        # API docs: https://octopart.com/api/docs
        # Requires API key, has rate limits
        return []

    def get_specs(self, component_id: str) -> Optional[ExternalComponent]:
        return None


class FindChipsAPI(ExternalDataSource):
    """FindChips API integration."""

    @property
    def name(self) -> str:
        return "FindChips"

    def search(
        self, query: str, component_type: ComponentType
    ) -> List[ExternalComponent]:
        # TODO: Implement FindChips API
        return []

    def get_specs(self, component_id: str) -> Optional[ExternalComponent]:
        return None


class DigiKeyAPI(ExternalDataSource):
    """DigiKey API integration."""

    @property
    def name(self) -> str:
        return "DigiKey"

    def search(
        self, query: str, component_type: ComponentType
    ) -> List[ExternalComponent]:
        # TODO: Implement DigiKey API
        # Requires API key, has rate limits
        return []

    def get_specs(self, component_id: str) -> Optional[ExternalComponent]:
        return None


# ============================================================================
# DATASET SOURCES
# ============================================================================


class KaggleDataset(ExternalDataSource):
    """Kaggle dataset integration."""

    @property
    def name(self) -> str:
        return "Kaggle"

    def search(
        self, query: str, component_type: ComponentType
    ) -> List[ExternalComponent]:
        # TODO: Load from Kaggle datasets
        # Popular datasets:
        # - CPU/GPU benchmarks
        # - Hardware specifications
        return []

    def get_specs(self, component_id: str) -> Optional[ExternalComponent]:
        return None


class GitHubDataset(ExternalDataSource):
    """GitHub repository data integration."""

    @property
    def name(self) -> str:
        return "GitHub"

    def search(
        self, query: str, component_type: ComponentType
    ) -> List[ExternalComponent]:
        # TODO: Load from GitHub repos with hardware specs
        return []

    def get_specs(self, component_id: str) -> Optional[ExternalComponent]:
        return None


# ============================================================================
# PDF DATASHEET EXTRACTION
# ============================================================================


class DatasheetExtractor:
    """Extract specs from PDF datasheets."""

    def __init__(self):
        self.pdf_lib = None
        self._init_pdf_lib()

    def _init_pdf_lib(self):
        """Initialize PDF extraction library."""
        try:
            import pdfplumber

            self.pdf_lib = "pdfplumber"
        except ImportError:
            try:
                import fitz  # PyMuPDF

                self.pdf_lib = "pymupdf"
            except ImportError:
                self.pdf_lib = None

    def is_available(self) -> bool:
        """Check if PDF extraction is available."""
        return self.pdf_lib is not None

    def extract_text(self, pdf_path: str) -> str:
        """Extract all text from PDF."""
        if self.pdf_lib == "pdfplumber":
            import pdfplumber

            with pdfplumber.open(pdf_path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        elif self.pdf_lib == "pymupdf":
            import fitz

            doc = fitz.open(pdf_path)
            return "\n".join(page.get_text() for page in doc.pages)
        return ""

    def extract_tables(self, pdf_path: str) -> List[List[List[str]]]:
        """Extract tables from PDF."""
        tables = []
        if self.pdf_lib == "pdfplumber":
            import pdfplumber

            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
        return tables

    def parse_specs(
        self, text: str, component_type: ComponentType
    ) -> List[ExternalSpec]:
        """Parse specs from extracted text."""
        specs = []

        # Common patterns for specs
        patterns = {
            "cores": r"(\d+)\s*(?:core|cores)",
            "threads": r"(\d+)\s*(?:thread|threads)",
            "clock": r"([\d.]+)\s*(?:ghz|mhz|ghz|gigahertz|megahertz)",
            "tdp": r"(\d+)\s*(?:w|watts|tdp)",
            "cache": r"(\d+)\s*(?:mb|kb|l3|l2|l1|cache)",
            "memory": r"(\d+)\s*(?:gb|mb)\s*(?:ddr\d*)",
            "vram": r"(\d+)\s*(?:gb|mb)\s*(?:gddr\d+|vram)",
            "bus_width": r"(\d+)\s*bit",
            "transistors": r"([\d,]+)\s*(?:million|billion|transistors)",
            "process": r"(\d+)\s*(?:nm|nanometer)",
        }

        text_lower = text.lower()

        for key, pattern in patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                value = match.group(1)
                try:
                    value = int(value.replace(",", ""))
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass

                specs.append(
                    ExternalSpec(
                        key=key,
                        value=value,
                        confidence=0.6,  # Lower confidence for extracted data
                        source_name="datasheet",
                    )
                )

        return specs


# ============================================================================
# MAIN INTEGRATION CLASS
# ============================================================================


class ExternalDataIntegrator:
    """Integrate hardware specs from multiple external sources."""

    def __init__(self):
        self.sources: List[ExternalDataSource] = []
        self.pdf_extractor = DatasheetExtractor()

        # Initialize available sources
        self._init_sources()

    def _init_sources(self):
        """Initialize available data sources."""
        # API sources (require API keys)
        # self.sources.append(OctopartAPI())
        # self.sources.append(FindChipsAPI())
        # self.sources.append(DigiKeyAPI())

        # Dataset sources
        self.sources.append(KaggleDataset())
        self.sources.append(GitHubDataset())

    def search_all(
        self, query: str, component_type: ComponentType
    ) -> List[ExternalComponent]:
        """Search all sources for a component."""
        results = []

        for source in self.sources:
            try:
                components = source.search(query, component_type)
                results.extend(components)
            except Exception as e:
                print(f"Warning: {source.name} search failed: {e}")

        return results

    def enrich_component(
        self, brand: str, model: str, component_type: ComponentType
    ) -> List[ExternalSpec]:
        """Enrich a component with data from external sources."""
        results = []

        # Search all sources
        components = self.search_all(f"{brand} {model}", component_type)

        for component in components:
            if (
                component.brand.lower() == brand.lower()
                and component.model.lower() == model.lower()
            ):
                results.extend(component.specs)

        return results

    def load_dataset(self, path: str, format: str = "json") -> List[ExternalComponent]:
        """Load a dataset file."""
        p = Path(path)

        if not p.exists():
            print(f"Warning: Dataset not found: {path}")
            return []

        if format == "json":
            with open(p) as f:
                data = json.load(f)
                return self._parse_json_dataset(data)
        elif format == "csv":
            import csv

            with open(p) as f:
                reader = csv.DictReader(f)
                return self._parse_csv_dataset(list(reader))

        return []

    def _parse_json_dataset(self, data: Dict | List) -> List[ExternalComponent]:
        """Parse JSON dataset."""
        # TODO: Implement based on dataset structure
        return []

    def _parse_csv_dataset(self, data: List[Dict]) -> List[ExternalComponent]:
        """Parse CSV dataset."""
        # TODO: Implement based on dataset structure
        return []

    def process_datasheets(
        self, directory: str, component_type: ComponentType
    ) -> List[ExternalComponent]:
        """Process all PDF datasheets in a directory."""
        results = []
        p = Path(directory)

        if not p.exists() or not self.pdf_extractor.is_available():
            return results

        for pdf_file in p.glob("*.pdf"):
            try:
                text = self.pdf_extractor.extract_text(str(pdf_file))
                specs = self.pdf_extractor.parse_specs(text, component_type)

                if specs:
                    results.append(
                        ExternalComponent(
                            brand="",  # Extract from filename
                            model=pdf_file.stem,
                            component_type=component_type,
                            specs=specs,
                            source_url=str(pdf_file),
                        )
                    )
            except Exception as e:
                print(f"Warning: Failed to process {pdf_file}: {e}")

        return results


# ============================================================================
# USAGE EXAMPLES
# ============================================================================


def main():
    """Example usage of external data integration."""

    integrator = ExternalDataIntegrator()

    # Check PDF extractor availability
    print(f"PDF extractor available: {integrator.pdf_extractor.is_available()}")

    # Search for a component
    results = integrator.search_all("Core i9-14900K", ComponentType.CPU)
    print(f"Found {len(results)} components")

    # Load a dataset
    # components = integrator.load_dataset("data/hardware_specs.json")

    # Process datasheets
    # components = integrator.process_datasheets("datasheets/", ComponentType.CPU)


if __name__ == "__main__":
    main()
