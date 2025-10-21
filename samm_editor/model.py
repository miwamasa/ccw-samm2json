"""
SAMM Model Data Structures

Defines Python classes for representing SAMM model elements.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class LocalizedString:
    """A string with language tags (rdf:langString)."""
    values: Dict[str, str] = field(default_factory=dict)  # lang -> text


@dataclass
class ModelElement:
    """Base class for all SAMM model elements."""
    urn: str
    preferred_name: Optional[LocalizedString] = None
    description: Optional[LocalizedString] = None
    see: List[str] = field(default_factory=list)


@dataclass
class Characteristic(ModelElement):
    """A Characteristic describes the semantics of a Property."""
    data_type: Optional[str] = None
    characteristic_type: str = "Characteristic"  # e.g., Measurement, Collection, etc.

    # For Measurement/Quantifiable
    unit: Optional[str] = None

    # For Enumeration/State
    values: List[Any] = field(default_factory=list)
    default_value: Optional[Any] = None

    # For Collection types
    element_characteristic: Optional['Characteristic'] = None

    # For Either
    left: Optional['Characteristic'] = None
    right: Optional['Characteristic'] = None

    # For StructuredValue
    deconstruction_rule: Optional[str] = None
    elements: List['Property'] = field(default_factory=list)


@dataclass
class Property(ModelElement):
    """A Property represents a named value."""
    characteristic: Optional[Characteristic] = None
    example_value: Optional[Any] = None
    optional: bool = False
    payload_name: Optional[str] = None
    not_in_payload: bool = False


@dataclass
class Entity(ModelElement):
    """An Entity is a logical encapsulation of multiple values."""
    properties: List[Property] = field(default_factory=list)
    extends: Optional[str] = None  # URN of parent entity
    is_abstract: bool = False


@dataclass
class Operation(ModelElement):
    """An Operation represents an action that can be triggered."""
    input_properties: List[Property] = field(default_factory=list)
    output_property: Optional[Property] = None


@dataclass
class Event(ModelElement):
    """An Event represents a single occurrence where timing is important."""
    parameters: List[Property] = field(default_factory=list)


@dataclass
class Aspect(ModelElement):
    """An Aspect is the root element of an Aspect Model."""
    properties: List[Property] = field(default_factory=list)
    operations: List[Operation] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)


@dataclass
class SAMMModel:
    """Container for a complete SAMM Aspect Model."""
    aspect: Optional[Aspect] = None
    entities: Dict[str, Entity] = field(default_factory=dict)
    characteristics: Dict[str, Characteristic] = field(default_factory=dict)
    properties: Dict[str, Property] = field(default_factory=dict)
    operations: Dict[str, Operation] = field(default_factory=dict)
    events: Dict[str, Event] = field(default_factory=dict)

    namespace: str = ""  # The local namespace URN
    prefixes: Dict[str, str] = field(default_factory=dict)  # prefix -> namespace URI
