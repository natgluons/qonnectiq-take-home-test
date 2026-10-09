"""Parsers for the two well-report PDF layouts and glossary DOCX."""
from .dgos import parse_dgos
from .ddr import parse_ddr
from .glossary import parse_glossary

__all__ = ["parse_dgos", "parse_ddr", "parse_glossary"]
