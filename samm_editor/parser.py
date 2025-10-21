"""
SAMM Turtle Parser

Parses Turtle files containing SAMM Aspect Models and converts them to Python objects.
"""

from rdflib import Graph, Namespace, RDF, RDFS, Literal, URIRef
from rdflib.namespace import XSD
from typing import Optional, Dict, Any, List
from .model import (
    SAMMModel, Aspect, Property, Characteristic, Entity, Operation, Event,
    LocalizedString, ModelElement
)


# SAMM Namespaces
SAMM = Namespace("urn:samm:org.eclipse.esmf.samm:meta-model:2.2.0#")
SAMM_C = Namespace("urn:samm:org.eclipse.esmf.samm:characteristic:2.2.0#")
SAMM_E = Namespace("urn:samm:org.eclipse.esmf.samm:entity:2.2.0#")
UNIT = Namespace("urn:samm:org.eclipse.esmf.samm:unit:2.2.0#")


class SAMMParser:
    """Parser for SAMM Turtle files."""

    def __init__(self):
        self.graph = Graph()
        self.model = SAMMModel()

    def parse_file(self, file_path: str) -> SAMMModel:
        """Parse a Turtle file and return a SAMMModel."""
        self.graph.parse(file_path, format='turtle')
        self._extract_namespaces()
        self._parse_model()
        return self.model

    def parse_string(self, turtle_content: str) -> SAMMModel:
        """Parse Turtle content from a string and return a SAMMModel."""
        self.graph.parse(data=turtle_content, format='turtle')
        self._extract_namespaces()
        self._parse_model()
        return self.model

    def _extract_namespaces(self):
        """Extract namespace prefixes from the graph."""
        for prefix, namespace in self.graph.namespaces():
            self.model.prefixes[prefix] = str(namespace)
            # Find the local namespace (empty prefix or aspect namespace)
            if prefix == '' or prefix is None:
                self.model.namespace = str(namespace)

    def _parse_model(self):
        """Parse all model elements from the RDF graph."""
        # Parse Aspects
        for aspect_uri in self.graph.subjects(RDF.type, SAMM.Aspect):
            self.model.aspect = self._parse_aspect(aspect_uri)

        # Parse Entities
        for entity_uri in self.graph.subjects(RDF.type, SAMM.Entity):
            entity = self._parse_entity(entity_uri)
            self.model.entities[str(entity_uri)] = entity

        # Parse Abstract Entities
        for entity_uri in self.graph.subjects(RDF.type, SAMM.AbstractEntity):
            entity = self._parse_entity(entity_uri, is_abstract=True)
            self.model.entities[str(entity_uri)] = entity

        # Parse Characteristics
        for char_uri in self._find_all_characteristics():
            if str(char_uri) not in self.model.characteristics:
                characteristic = self._parse_characteristic(char_uri)
                self.model.characteristics[str(char_uri)] = characteristic

        # Parse standalone Properties (not part of Aspect/Entity)
        for prop_uri in self.graph.subjects(RDF.type, SAMM.Property):
            if str(prop_uri) not in self.model.properties:
                prop = self._parse_property(prop_uri)
                self.model.properties[str(prop_uri)] = prop

    def _find_all_characteristics(self) -> List[URIRef]:
        """Find all characteristic URIs in the graph."""
        characteristics = set()

        # Find all subjects that are typed as Characteristic or its subclasses
        char_types = [
            SAMM.Characteristic,
            SAMM_C.Measurement,
            SAMM_C.Quantifiable,
            SAMM_C.Enumeration,
            SAMM_C.State,
            SAMM_C.Collection,
            SAMM_C.List,
            SAMM_C.Set,
            SAMM_C.SortedSet,
            SAMM_C.TimeSeries,
            SAMM_C.Either,
            SAMM_C.StructuredValue,
            SAMM_C.SingleEntity,
            SAMM_C.Trait,
            SAMM_C.Code,
            SAMM_C.Duration,
            SAMM_C.Boolean,
            SAMM_C.Text,
            SAMM_C.MultiLanguageText,
            SAMM_C.Timestamp,
            SAMM_C.UnitReference,
        ]

        for char_type in char_types:
            for char_uri in self.graph.subjects(RDF.type, char_type):
                characteristics.add(char_uri)

        # Also find characteristics referenced by properties
        for prop_uri in self.graph.subjects(RDF.type, SAMM.Property):
            char_uri = self.graph.value(prop_uri, SAMM.characteristic)
            if char_uri:
                characteristics.add(char_uri)

        return list(characteristics)

    def _parse_aspect(self, aspect_uri: URIRef) -> Aspect:
        """Parse an Aspect element."""
        aspect = Aspect(urn=str(aspect_uri))
        self._parse_common_attributes(aspect_uri, aspect)

        # Parse properties
        properties_list = self.graph.value(aspect_uri, SAMM.properties)
        if properties_list:
            aspect.properties = self._parse_property_list(properties_list)

        # Parse operations
        operations_list = self.graph.value(aspect_uri, SAMM.operations)
        if operations_list:
            for op_uri in self.graph.items(operations_list):
                operation = self._parse_operation(op_uri)
                aspect.operations.append(operation)
                self.model.operations[str(op_uri)] = operation

        # Parse events
        events_list = self.graph.value(aspect_uri, SAMM.events)
        if events_list:
            for event_uri in self.graph.items(events_list):
                event = self._parse_event(event_uri)
                aspect.events.append(event)
                self.model.events[str(event_uri)] = event

        return aspect

    def _parse_property_list(self, properties_list) -> List[Property]:
        """Parse a list of properties (RDF Collection)."""
        properties = []
        for item in self.graph.items(properties_list):
            # Item can be a Property URI or a blank node with property + payloadName
            if (item, RDF.type, SAMM.Property) in self.graph:
                prop = self._parse_property(item)
            else:
                # Blank node with samm:property and optional samm:payloadName
                prop_uri = self.graph.value(item, SAMM.property)
                if prop_uri:
                    prop = self._parse_property(prop_uri)
                    # Check for payloadName override
                    payload_name = self.graph.value(item, SAMM.payloadName)
                    if payload_name:
                        prop.payload_name = str(payload_name)
                    # Check for optional override
                    optional = self.graph.value(item, SAMM.optional)
                    if optional:
                        prop.optional = bool(optional)
                    # Check for notInPayload
                    not_in_payload = self.graph.value(item, SAMM.notInPayload)
                    if not_in_payload:
                        prop.not_in_payload = bool(not_in_payload)
                else:
                    continue

            properties.append(prop)
            self.model.properties[str(prop.urn)] = prop

        return properties

    def _parse_property(self, prop_uri: URIRef) -> Property:
        """Parse a Property element."""
        prop = Property(urn=str(prop_uri))
        self._parse_common_attributes(prop_uri, prop)

        # Parse characteristic
        char_uri = self.graph.value(prop_uri, SAMM.characteristic)
        if char_uri:
            prop.characteristic = self._parse_characteristic(char_uri)
            self.model.characteristics[str(char_uri)] = prop.characteristic

        # Parse example value
        example = self.graph.value(prop_uri, SAMM.exampleValue)
        if example:
            prop.example_value = self._literal_to_python(example)

        # Parse optional
        optional = self.graph.value(prop_uri, SAMM.optional)
        if optional:
            prop.optional = bool(optional)

        # Parse payloadName
        payload_name = self.graph.value(prop_uri, SAMM.payloadName)
        if payload_name:
            prop.payload_name = str(payload_name)

        # Parse notInPayload
        not_in_payload = self.graph.value(prop_uri, SAMM.notInPayload)
        if not_in_payload:
            prop.not_in_payload = bool(not_in_payload)

        return prop

    def _parse_characteristic(self, char_uri: URIRef) -> Characteristic:
        """Parse a Characteristic element."""
        # Check if this is a predefined characteristic (e.g., samm-c:Boolean)
        char_uri_str = str(char_uri)
        if char_uri_str.startswith(str(SAMM_C)):
            # This is a predefined characteristic
            char_type_str = char_uri_str.split('#')[-1]
            characteristic = Characteristic(
                urn=char_uri_str,
                characteristic_type=char_type_str
            )
            # For predefined characteristics, infer data type
            if char_type_str == "Boolean":
                characteristic.data_type = str(XSD.boolean)
            elif char_type_str == "Text":
                characteristic.data_type = str(XSD.string)
            elif char_type_str == "Timestamp":
                characteristic.data_type = str(XSD.dateTime)
            return characteristic

        # Determine characteristic type
        char_types = list(self.graph.objects(char_uri, RDF.type))
        char_type_str = "Characteristic"

        for char_type in char_types:
            if char_type in [SAMM_C.Measurement, SAMM_C.Quantifiable, SAMM_C.Enumeration,
                            SAMM_C.State, SAMM_C.List, SAMM_C.Set, SAMM_C.SortedSet,
                            SAMM_C.Collection, SAMM_C.TimeSeries, SAMM_C.Either,
                            SAMM_C.StructuredValue, SAMM_C.SingleEntity, SAMM_C.Trait,
                            SAMM_C.Code, SAMM_C.Duration, SAMM_C.Boolean, SAMM_C.Text,
                            SAMM_C.MultiLanguageText, SAMM_C.Timestamp, SAMM_C.UnitReference]:
                char_type_str = char_type.split('#')[-1]
                break

        characteristic = Characteristic(
            urn=str(char_uri),
            characteristic_type=char_type_str
        )
        self._parse_common_attributes(char_uri, characteristic)

        # Parse dataType
        data_type = self.graph.value(char_uri, SAMM.dataType)
        if data_type:
            characteristic.data_type = str(data_type)

        # Parse unit (for Measurement/Quantifiable)
        unit = self.graph.value(char_uri, SAMM_C.unit)
        if unit:
            characteristic.unit = str(unit)

        # Parse values (for Enumeration/State)
        values_list = self.graph.value(char_uri, SAMM_C.values)
        if values_list:
            characteristic.values = [
                self._literal_to_python(v) for v in self.graph.items(values_list)
            ]

        # Parse default value (for State)
        default_value = self.graph.value(char_uri, SAMM_C.defaultValue)
        if default_value:
            characteristic.default_value = self._literal_to_python(default_value)

        # Parse elementCharacteristic (for Collection types)
        element_char = self.graph.value(char_uri, SAMM_C.elementCharacteristic)
        if element_char:
            characteristic.element_characteristic = self._parse_characteristic(element_char)

        # Parse left and right (for Either)
        left = self.graph.value(char_uri, SAMM_C.left)
        if left:
            characteristic.left = self._parse_characteristic(left)

        right = self.graph.value(char_uri, SAMM_C.right)
        if right:
            characteristic.right = self._parse_characteristic(right)

        # Parse deconstructionRule (for StructuredValue)
        deconstruction_rule = self.graph.value(char_uri, SAMM_C.deconstructionRule)
        if deconstruction_rule:
            characteristic.deconstruction_rule = str(deconstruction_rule)

        # Parse elements (for StructuredValue)
        elements_list = self.graph.value(char_uri, SAMM_C.elements)
        if elements_list:
            for prop_uri in self.graph.items(elements_list):
                prop = self._parse_property(prop_uri)
                characteristic.elements.append(prop)

        return characteristic

    def _parse_entity(self, entity_uri: URIRef, is_abstract: bool = False) -> Entity:
        """Parse an Entity element."""
        entity = Entity(urn=str(entity_uri), is_abstract=is_abstract)
        self._parse_common_attributes(entity_uri, entity)

        # Parse properties
        properties_list = self.graph.value(entity_uri, SAMM.properties)
        if properties_list:
            entity.properties = self._parse_property_list(properties_list)

        # Parse extends
        extends = self.graph.value(entity_uri, SAMM.extends)
        if extends:
            entity.extends = str(extends)

        return entity

    def _parse_operation(self, op_uri: URIRef) -> Operation:
        """Parse an Operation element."""
        operation = Operation(urn=str(op_uri))
        self._parse_common_attributes(op_uri, operation)

        # Parse input
        input_list = self.graph.value(op_uri, SAMM.input)
        if input_list:
            operation.input_properties = self._parse_property_list(input_list)

        # Parse output
        output_uri = self.graph.value(op_uri, SAMM.output)
        if output_uri:
            operation.output_property = self._parse_property(output_uri)

        return operation

    def _parse_event(self, event_uri: URIRef) -> Event:
        """Parse an Event element."""
        event = Event(urn=str(event_uri))
        self._parse_common_attributes(event_uri, event)

        # Parse parameters
        params_list = self.graph.value(event_uri, SAMM.parameters)
        if params_list:
            event.parameters = self._parse_property_list(params_list)

        return event

    def _parse_common_attributes(self, uri: URIRef, element: ModelElement):
        """Parse common attributes (preferredName, description, see)."""
        # Parse preferredName
        preferred_names = {}
        for name in self.graph.objects(uri, SAMM.preferredName):
            if isinstance(name, Literal):
                lang = name.language or 'en'
                preferred_names[lang] = str(name)
        if preferred_names:
            element.preferred_name = LocalizedString(values=preferred_names)

        # Parse description
        descriptions = {}
        for desc in self.graph.objects(uri, SAMM.description):
            if isinstance(desc, Literal):
                lang = desc.language or 'en'
                descriptions[lang] = str(desc)
        if descriptions:
            element.description = LocalizedString(values=descriptions)

        # Parse see
        for see_uri in self.graph.objects(uri, SAMM.see):
            element.see.append(str(see_uri))

    def _literal_to_python(self, literal: Literal) -> Any:
        """Convert an RDF Literal to a Python value."""
        if isinstance(literal, Literal):
            return literal.toPython()
        else:
            return str(literal)
