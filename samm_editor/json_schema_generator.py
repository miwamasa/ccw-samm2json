"""
JSON Schema Generator

Generates JSON Schema from SAMM Aspect Models according to the SAMM specification.
"""

import json
from typing import Dict, Any, Optional, List
from .model import (
    SAMMModel, Aspect, Property, Characteristic, Entity
)


class JSONSchemaGenerator:
    """Generates JSON Schema from SAMM models."""

    def __init__(self, model: SAMMModel):
        self.model = model
        self.definitions = {}

    def generate(self) -> Dict[str, Any]:
        """Generate JSON Schema for the Aspect."""
        if not self.model.aspect:
            raise ValueError("No Aspect found in the model")

        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {},
            "definitions": {}
        }

        # Add aspect description
        if self.model.aspect.description:
            schema["description"] = self._get_english_text(self.model.aspect.description.values)

        # Add aspect title
        if self.model.aspect.preferred_name:
            schema["title"] = self._get_english_text(self.model.aspect.preferred_name.values)

        # Generate properties
        required_props = []
        for prop in self.model.aspect.properties:
            if prop.not_in_payload:
                continue

            prop_name = prop.payload_name or self._get_local_name(prop.urn)
            schema["properties"][prop_name] = self._generate_property_schema(prop)

            if not prop.optional:
                required_props.append(prop_name)

        if required_props:
            schema["required"] = required_props

        # Add definitions for entities
        if self.definitions:
            schema["definitions"] = self.definitions

        return schema

    def _generate_property_schema(self, prop: Property) -> Dict[str, Any]:
        """Generate schema for a single property."""
        prop_schema = {}

        # Add description
        if prop.description:
            prop_schema["description"] = self._get_english_text(prop.description.values)

        # Add title
        if prop.preferred_name:
            prop_schema["title"] = self._get_english_text(prop.preferred_name.values)

        # Generate schema based on characteristic
        if prop.characteristic:
            char_schema = self._generate_characteristic_schema(prop.characteristic)
            prop_schema.update(char_schema)

        return prop_schema

    def _generate_characteristic_schema(self, char: Characteristic) -> Dict[str, Any]:
        """Generate schema for a characteristic."""
        char_type = char.characteristic_type

        # Handle Boolean
        if char_type == "Boolean":
            return {"type": "boolean"}

        # Handle collection types
        elif char_type in ["Collection", "List", "Set", "SortedSet", "TimeSeries"]:
            return self._generate_collection_schema(char)

        # Handle Either type
        elif char_type == "Either":
            return self._generate_either_schema(char)

        # Handle Enumeration/State
        elif char_type in ["Enumeration", "State"]:
            return self._generate_enumeration_schema(char)

        # Handle SingleEntity
        elif char_type == "SingleEntity" or (char.data_type and self._is_entity(char.data_type)):
            return self._generate_entity_schema(char)

        # Handle MultiLanguageText
        elif char_type == "MultiLanguageText" or char.data_type == "rdf:langString":
            return self._generate_multilanguage_schema()

        # Handle scalar types
        else:
            return self._generate_scalar_schema(char)

    def _generate_collection_schema(self, char: Characteristic) -> Dict[str, Any]:
        """Generate schema for collection characteristics."""
        schema = {"type": "array"}

        if char.element_characteristic:
            schema["items"] = self._generate_characteristic_schema(char.element_characteristic)
        elif char.data_type:
            # Check if dataType is an Entity
            if self._is_entity(char.data_type):
                entity_name = self._get_local_name(char.data_type)
                if entity_name not in self.definitions:
                    entity = self.model.entities.get(char.data_type)
                    if entity:
                        self.definitions[entity_name] = self._generate_entity_definition(entity)
                schema["items"] = {"$ref": f"#/definitions/{entity_name}"}
            else:
                schema["items"] = self._xsd_to_json_type(char.data_type)

        # For Set and SortedSet, add uniqueItems
        if char.characteristic_type in ["Set", "SortedSet"]:
            schema["uniqueItems"] = True

        return schema

    def _generate_either_schema(self, char: Characteristic) -> Dict[str, Any]:
        """Generate schema for Either characteristic."""
        schema = {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }

        if char.left:
            schema["properties"]["left"] = self._generate_characteristic_schema(char.left)

        if char.right:
            schema["properties"]["right"] = self._generate_characteristic_schema(char.right)

        # Either requires exactly one of left or right
        schema["oneOf"] = [
            {"required": ["left"]},
            {"required": ["right"]}
        ]

        return schema

    def _generate_enumeration_schema(self, char: Characteristic) -> Dict[str, Any]:
        """Generate schema for Enumeration/State characteristic."""
        schema = {}

        if char.values:
            schema["enum"] = char.values

        # Try to infer type from values or dataType
        if char.data_type:
            base_type = self._xsd_to_json_type(char.data_type)
            if "type" in base_type:
                schema["type"] = base_type["type"]

        return schema

    def _generate_entity_schema(self, char: Characteristic) -> Dict[str, Any]:
        """Generate schema for Entity characteristic."""
        entity_urn = char.data_type

        if not entity_urn or not self._is_entity(entity_urn):
            return {"type": "object"}

        # Check if entity is already in definitions
        entity_name = self._get_local_name(entity_urn)

        if entity_name not in self.definitions:
            entity = self.model.entities.get(entity_urn)
            if entity:
                self.definitions[entity_name] = self._generate_entity_definition(entity)

        return {"$ref": f"#/definitions/{entity_name}"}

    def _generate_entity_definition(self, entity: Entity) -> Dict[str, Any]:
        """Generate schema definition for an Entity."""
        entity_schema = {
            "type": "object",
            "properties": {}
        }

        if entity.description:
            entity_schema["description"] = self._get_english_text(entity.description.values)

        # Handle inheritance
        if entity.extends:
            parent_entity = self.model.entities.get(entity.extends)
            if parent_entity:
                parent_name = self._get_local_name(entity.extends)
                if parent_name not in self.definitions:
                    self.definitions[parent_name] = self._generate_entity_definition(parent_entity)

                # Use allOf to combine parent and current entity
                entity_schema = {
                    "allOf": [
                        {"$ref": f"#/definitions/{parent_name}"},
                        {
                            "type": "object",
                            "properties": {}
                        }
                    ]
                }
                # Add properties to the second element
                target_schema = entity_schema["allOf"][1]
            else:
                target_schema = entity_schema
        else:
            target_schema = entity_schema

        # Add properties
        required_props = []
        for prop in entity.properties:
            if prop.not_in_payload:
                continue

            prop_name = prop.payload_name or self._get_local_name(prop.urn)
            target_schema["properties"][prop_name] = self._generate_property_schema(prop)

            if not prop.optional:
                required_props.append(prop_name)

        if required_props:
            target_schema["required"] = required_props

        return entity_schema

    def _generate_multilanguage_schema(self) -> Dict[str, Any]:
        """Generate schema for MultiLanguageText."""
        return {
            "type": "object",
            "patternProperties": {
                "^[a-z]{2}(-[A-Z]{2})?$": {
                    "type": "string"
                }
            },
            "additionalProperties": False
        }

    def _generate_scalar_schema(self, char: Characteristic) -> Dict[str, Any]:
        """Generate schema for scalar characteristics."""
        schema = {}

        if char.data_type:
            schema.update(self._xsd_to_json_type(char.data_type))

        # Add description if available
        if char.description:
            schema["description"] = self._get_english_text(char.description.values)

        return schema

    def _xsd_to_json_type(self, xsd_type: str) -> Dict[str, Any]:
        """Map XSD data types to JSON Schema types."""
        # Remove namespace prefix
        local_type = xsd_type.split('#')[-1] if '#' in xsd_type else xsd_type.split(':')[-1]

        type_mapping = {
            # Boolean
            "boolean": {"type": "boolean"},

            # String types
            "string": {"type": "string"},
            "anyURI": {"type": "string", "format": "uri"},
            "curie": {"type": "string"},
            "hexBinary": {"type": "string"},
            "base64Binary": {"type": "string", "contentEncoding": "base64"},

            # Integer types
            "integer": {"type": "integer"},
            "int": {"type": "integer"},
            "long": {"type": "integer"},
            "short": {"type": "integer"},
            "byte": {"type": "integer"},
            "nonNegativeInteger": {"type": "integer", "minimum": 0},
            "positiveInteger": {"type": "integer", "minimum": 1},
            "unsignedLong": {"type": "integer", "minimum": 0},
            "unsignedInt": {"type": "integer", "minimum": 0},
            "unsignedShort": {"type": "integer", "minimum": 0},
            "unsignedByte": {"type": "integer", "minimum": 0},

            # Number types
            "decimal": {"type": "number"},
            "float": {"type": "number"},
            "double": {"type": "number"},

            # Date/Time types
            "date": {"type": "string", "format": "date"},
            "time": {"type": "string", "format": "time"},
            "dateTime": {"type": "string", "format": "date-time"},
            "dateTimeStamp": {"type": "string", "format": "date-time"},
            "gYear": {"type": "string"},
            "gMonth": {"type": "string"},
            "gDay": {"type": "string"},
            "gYearMonth": {"type": "string"},
            "gMonthDay": {"type": "string"},
            "duration": {"type": "string"},
            "dayTimeDuration": {"type": "string"},
            "yearMonthDuration": {"type": "string"},
        }

        return type_mapping.get(local_type, {"type": "string"})

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

    def _get_english_text(self, lang_dict: Dict[str, str]) -> str:
        """Get English text from a language dictionary."""
        return lang_dict.get('en', lang_dict.get('', list(lang_dict.values())[0] if lang_dict else ''))

    def generate_string(self, indent: int = 2) -> str:
        """Generate JSON Schema as a formatted JSON string."""
        return json.dumps(self.generate(), indent=indent)
