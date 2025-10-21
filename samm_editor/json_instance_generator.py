"""
JSON Instance Generator

Generates example JSON instances from SAMM Aspect Models.
"""

import json
from decimal import Decimal
from typing import Dict, Any, Optional, List
from .model import (
    SAMMModel, Aspect, Property, Characteristic, Entity
)


class JSONInstanceGenerator:
    """Generates example JSON instances from SAMM models."""

    def __init__(self, model: SAMMModel):
        self.model = model

    def _convert_value(self, value: Any) -> Any:
        """Convert Python values to JSON-compatible types."""
        if isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, dict):
            return {k: self._convert_value(v) for k, v in value.items()}
        elif isinstance(value, (list, tuple)):
            return [self._convert_value(v) for v in value]
        else:
            return value

    def generate(self) -> Dict[str, Any]:
        """Generate an example JSON instance for the Aspect."""
        if not self.model.aspect:
            raise ValueError("No Aspect found in the model")

        instance = {}

        for prop in self.model.aspect.properties:
            if prop.not_in_payload:
                continue

            # Skip optional properties in some cases (50% chance)
            if prop.optional:
                # For simplicity, we'll include optional properties
                pass

            prop_name = prop.payload_name or self._get_local_name(prop.urn)

            # Use example value if available
            if prop.example_value is not None:
                instance[prop_name] = self._convert_value(prop.example_value)
            elif prop.characteristic:
                instance[prop_name] = self._generate_characteristic_value(prop.characteristic)
            else:
                instance[prop_name] = None

        return instance

    def _generate_characteristic_value(self, char: Characteristic) -> Any:
        """Generate an example value for a characteristic."""
        char_type = char.characteristic_type

        # Handle collection types
        if char_type in ["Collection", "List", "Set", "SortedSet", "TimeSeries"]:
            return self._generate_collection_value(char)

        # Handle Either type
        elif char_type == "Either":
            return self._generate_either_value(char)

        # Handle Enumeration/State
        elif char_type in ["Enumeration", "State"]:
            return self._generate_enumeration_value(char)

        # Handle SingleEntity
        elif char_type == "SingleEntity" or (char.data_type and self._is_entity(char.data_type)):
            return self._generate_entity_value(char)

        # Handle MultiLanguageText
        elif char_type == "MultiLanguageText" or char.data_type == "rdf:langString":
            return self._generate_multilanguage_value()

        # Handle scalar types
        else:
            return self._generate_scalar_value(char)

    def _generate_collection_value(self, char: Characteristic) -> List[Any]:
        """Generate example value for collection characteristics."""
        # Generate 2-3 example items
        items = []
        count = 2

        for i in range(count):
            if char.element_characteristic:
                items.append(self._generate_characteristic_value(char.element_characteristic))
            elif char.data_type:
                # Check if dataType is an Entity
                if self._is_entity(char.data_type):
                    entity = self.model.entities.get(char.data_type)
                    if entity:
                        items.append(self._generate_entity_instance(entity))
                    else:
                        items.append({})
                else:
                    items.append(self._generate_default_value_for_type(char.data_type, i))
            else:
                items.append(f"item{i + 1}")

        return items

    def _generate_either_value(self, char: Characteristic) -> Dict[str, Any]:
        """Generate example value for Either characteristic."""
        # Generate the 'right' value by default (success case)
        if char.right:
            return {"right": self._generate_characteristic_value(char.right)}
        elif char.left:
            return {"left": self._generate_characteristic_value(char.left)}
        else:
            return {"right": "value"}

    def _generate_enumeration_value(self, char: Characteristic) -> Any:
        """Generate example value for Enumeration/State characteristic."""
        # Use default value if available
        if char.default_value is not None:
            return char.default_value

        # Use first value from enum
        if char.values and len(char.values) > 0:
            return char.values[0]

        # Generate based on dataType
        if char.data_type:
            return self._generate_default_value_for_type(char.data_type)

        return "ENUM_VALUE"

    def _generate_entity_value(self, char: Characteristic) -> Dict[str, Any]:
        """Generate example value for Entity characteristic."""
        entity_urn = char.data_type

        if not entity_urn or not self._is_entity(entity_urn):
            return {}

        entity = self.model.entities.get(entity_urn)
        if not entity:
            return {}

        return self._generate_entity_instance(entity)

    def _generate_entity_instance(self, entity: Entity) -> Dict[str, Any]:
        """Generate example instance for an Entity."""
        instance = {}

        # Handle inheritance
        if entity.extends:
            parent_entity = self.model.entities.get(entity.extends)
            if parent_entity:
                # Include parent properties
                instance.update(self._generate_entity_instance(parent_entity))

        # Add own properties
        for prop in entity.properties:
            if prop.not_in_payload:
                continue

            prop_name = prop.payload_name or self._get_local_name(prop.urn)

            # Use example value if available
            if prop.example_value is not None:
                instance[prop_name] = self._convert_value(prop.example_value)
            elif prop.characteristic:
                instance[prop_name] = self._generate_characteristic_value(prop.characteristic)
            else:
                instance[prop_name] = None

        return instance

    def _generate_multilanguage_value(self) -> Dict[str, str]:
        """Generate example value for MultiLanguageText."""
        return {
            "en": "English text",
            "de": "Deutscher Text"
        }

    def _generate_scalar_value(self, char: Characteristic) -> Any:
        """Generate example value for scalar characteristics."""
        if char.data_type:
            return self._generate_default_value_for_type(char.data_type)

        return "example_value"

    def _generate_default_value_for_type(self, xsd_type: str, index: int = 0) -> Any:
        """Generate a default value based on XSD type."""
        # Remove namespace prefix
        local_type = xsd_type.split('#')[-1] if '#' in xsd_type else xsd_type.split(':')[-1]

        type_defaults = {
            # Boolean
            "boolean": True,

            # String types
            "string": "example string",
            "anyURI": "https://example.com/resource",
            "curie": "ex:Resource",
            "hexBinary": "48656C6C6F",
            "base64Binary": "SGVsbG8gV29ybGQ=",

            # Integer types
            "integer": 42 + index,
            "int": 42 + index,
            "long": 1000 + index,
            "short": 10 + index,
            "byte": 1 + index,
            "nonNegativeInteger": 0 + index,
            "positiveInteger": 1 + index,
            "unsignedLong": 1000 + index,
            "unsignedInt": 100 + index,
            "unsignedShort": 10 + index,
            "unsignedByte": 1 + index,

            # Number types
            "decimal": 3.14 + index,
            "float": 1.5 + index * 0.5,
            "double": 2.718 + index * 0.1,

            # Date/Time types
            "date": "2024-01-15",
            "time": "14:30:00",
            "dateTime": "2024-01-15T14:30:00Z",
            "dateTimeStamp": "2024-01-15T14:30:00Z",
            "gYear": "2024",
            "gMonth": "--01",
            "gDay": "---15",
            "gYearMonth": "2024-01",
            "gMonthDay": "--01-15",
            "duration": "P1Y2M3DT4H5M6S",
            "dayTimeDuration": "P1DT2H",
            "yearMonthDuration": "P1Y2M",
        }

        return type_defaults.get(local_type, "example_value")

    def _is_entity(self, type_uri: str) -> bool:
        """Check if a type URI refers to an Entity."""
        return type_uri in self.model.entities

    def _get_local_name(self, urn: str) -> str:
        """Extract the local name from a URN."""
        if '#' in urn:
            return urn.split('#')[-1]
        elif '/' in urn:
            return urn.split('/')[-1]
        else:
            return urn

    def generate_string(self, indent: int = 2) -> str:
        """Generate JSON instance as a formatted JSON string."""
        return json.dumps(self.generate(), indent=indent, default=str)
