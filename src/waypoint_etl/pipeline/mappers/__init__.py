"""Aplicação do mapeamento De/Para."""

from .loader import MappingError, load_mapping, parse_mapping
from .mapper import MappedRecord, MappingResult, apply_mapping, map_record
from .schema import FieldMapping, MappingTemplate, SourceSpec
from .transforms import apply_transforms, available_transforms, is_known_transform

__all__ = [
    "FieldMapping",
    "MappedRecord",
    "MappingError",
    "MappingResult",
    "MappingTemplate",
    "SourceSpec",
    "apply_mapping",
    "apply_transforms",
    "available_transforms",
    "is_known_transform",
    "load_mapping",
    "map_record",
    "parse_mapping",
]
