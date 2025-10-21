"""
SAMM Turtle Writer

Converts SAMMModel objects back to Turtle format for saving.
"""

from rdflib import Graph, Namespace, RDF, Literal, URIRef, BNode
from rdflib.namespace import XSD
from rdflib.collection import Collection
from typing import Optional, List
from .model import (
    SAMMModel, Aspect, Property, Characteristic, Entity, Operation, Event,
    LocalizedString, ModelElement
)


# SAMM Namespaces
SAMM = Namespace("urn:samm:org.eclipse.esmf.samm:meta-model:2.2.0#")
SAMM_C = Namespace("urn:samm:org.eclipse.esmf.samm:characteristic:2.2.0#")
SAMM_E = Namespace("urn:samm:org.eclipse.esmf.samm:entity:2.2.0#")
UNIT = Namespace("urn:samm:org.eclipse.esmf.samm:unit:2.2.0#")


class SAMMWriter:
    """Writer for SAMM Turtle files."""

    def __init__(self, model: SAMMModel):
        self.model = model
        self.graph = Graph()
        self._bind_namespaces()

    def _bind_namespaces(self):
        """Bind standard and custom namespaces to the graph."""
        # Bind standard SAMM namespaces
        self.graph.bind('samm', SAMM)
        self.graph.bind('samm-c', SAMM_C)
        self.graph.bind('samm-e', SAMM_E)
        self.graph.bind('unit', UNIT)
        self.graph.bind('xsd', XSD)

        # Bind custom namespaces from model
        for prefix, namespace in self.model.prefixes.items():
            if prefix and prefix not in ['samm', 'samm-c', 'samm-e', 'unit', 'xsd']:
                self.graph.bind(prefix, Namespace(namespace))

        # Bind local namespace
        if self.model.namespace:
            self.graph.bind('', Namespace(self.model.namespace))

    def write_to_file(self, file_path: str):
        """Write the model to a Turtle file."""
        self._build_graph()
        self.graph.serialize(destination=file_path, format='turtle')

    def write_to_string(self) -> str:
        """Write the model to a Turtle string."""
        self._build_graph()
        return self.graph.serialize(format='turtle')

    def _build_graph(self):
        """Build the RDF graph from the SAMMModel."""
        # Write Aspect
        if self.model.aspect:
            self._write_aspect(self.model.aspect)

        # Write Entities
        for entity in self.model.entities.values():
            self._write_entity(entity)

        # Write standalone Characteristics
        for characteristic in self.model.characteristics.values():
            self._write_characteristic(characteristic)

        # Write standalone Properties
        for prop in self.model.properties.values():
            # Only write if not already part of Aspect/Entity
            if not self._is_part_of_aspect_or_entity(prop):
                self._write_property(prop)

        # Write Operations
        for operation in self.model.operations.values():
            # Only write if not already part of Aspect
            if not self._is_operation_in_aspect(operation):
                self._write_operation(operation)

        # Write Events
        for event in self.model.events.values():
            # Only write if not already part of Aspect
            if not self._is_event_in_aspect(event):
                self._write_event(event)

    def _is_part_of_aspect_or_entity(self, prop: Property) -> bool:
        """Check if property is already part of Aspect or Entity."""
        if self.model.aspect:
            if any(p.urn == prop.urn for p in self.model.aspect.properties):
                return True
        for entity in self.model.entities.values():
            if any(p.urn == prop.urn for p in entity.properties):
                return True
        return False

    def _is_operation_in_aspect(self, operation: Operation) -> bool:
        """Check if operation is already part of Aspect."""
        if self.model.aspect:
            return any(op.urn == operation.urn for op in self.model.aspect.operations)
        return False

    def _is_event_in_aspect(self, event: Event) -> bool:
        """Check if event is already part of Aspect."""
        if self.model.aspect:
            return any(e.urn == event.urn for e in self.model.aspect.events)
        return False

    def _write_aspect(self, aspect: Aspect):
        """Write an Aspect to the graph."""
        aspect_uri = URIRef(aspect.urn)
        self.graph.add((aspect_uri, RDF.type, SAMM.Aspect))
        self._write_common_attributes(aspect_uri, aspect)

        # Write properties list
        if aspect.properties:
            props_list = self._create_property_list(aspect.properties)
            self.graph.add((aspect_uri, SAMM.properties, props_list))

        # Write operations list
        if aspect.operations:
            ops_list = BNode()
            Collection(self.graph, ops_list, [URIRef(op.urn) for op in aspect.operations])
            self.graph.add((aspect_uri, SAMM.operations, ops_list))
            for operation in aspect.operations:
                self._write_operation(operation)

        # Write events list
        if aspect.events:
            events_list = BNode()
            Collection(self.graph, events_list, [URIRef(e.urn) for e in aspect.events])
            self.graph.add((aspect_uri, SAMM.events, events_list))
            for event in aspect.events:
                self._write_event(event)

    def _create_property_list(self, properties: List[Property]) -> BNode:
        """Create an RDF Collection for a list of properties."""
        prop_nodes = []
        for prop in properties:
            self._write_property(prop)

            # Check if we need a wrapper node for payloadName or optional
            if prop.payload_name or prop.optional or prop.not_in_payload:
                wrapper = BNode()
                self.graph.add((wrapper, SAMM.property, URIRef(prop.urn)))
                if prop.payload_name:
                    self.graph.add((wrapper, SAMM.payloadName, Literal(prop.payload_name)))
                if prop.optional:
                    self.graph.add((wrapper, SAMM.optional, Literal(True)))
                if prop.not_in_payload:
                    self.graph.add((wrapper, SAMM.notInPayload, Literal(True)))
                prop_nodes.append(wrapper)
            else:
                prop_nodes.append(URIRef(prop.urn))

        props_list = BNode()
        Collection(self.graph, props_list, prop_nodes)
        return props_list

    def _write_property(self, prop: Property):
        """Write a Property to the graph."""
        prop_uri = URIRef(prop.urn)
        self.graph.add((prop_uri, RDF.type, SAMM.Property))
        self._write_common_attributes(prop_uri, prop)

        # Write characteristic
        if prop.characteristic:
            self._write_characteristic(prop.characteristic)
            self.graph.add((prop_uri, SAMM.characteristic, URIRef(prop.characteristic.urn)))

        # Write example value
        if prop.example_value is not None:
            example_literal = self._python_to_literal(prop.example_value)
            self.graph.add((prop_uri, SAMM.exampleValue, example_literal))

        # Note: optional, payloadName, notInPayload are written in wrapper nodes

    def _write_characteristic(self, characteristic: Characteristic):
        """Write a Characteristic to the graph."""
        char_uri = URIRef(characteristic.urn)

        # Determine RDF type based on characteristic_type
        char_type_map = {
            "Measurement": SAMM_C.Measurement,
            "Quantifiable": SAMM_C.Quantifiable,
            "Enumeration": SAMM_C.Enumeration,
            "State": SAMM_C.State,
            "Collection": SAMM_C.Collection,
            "List": SAMM_C.List,
            "Set": SAMM_C.Set,
            "SortedSet": SAMM_C.SortedSet,
            "TimeSeries": SAMM_C.TimeSeries,
            "Either": SAMM_C.Either,
            "StructuredValue": SAMM_C.StructuredValue,
            "SingleEntity": SAMM_C.SingleEntity,
            "Trait": SAMM_C.Trait,
            "Code": SAMM_C.Code,
            "Duration": SAMM_C.Duration,
            "Boolean": SAMM_C.Boolean,
            "Text": SAMM_C.Text,
            "MultiLanguageText": SAMM_C.MultiLanguageText,
            "Timestamp": SAMM_C.Timestamp,
            "UnitReference": SAMM_C.UnitReference,
        }

        char_type = char_type_map.get(characteristic.characteristic_type, SAMM.Characteristic)
        self.graph.add((char_uri, RDF.type, char_type))
        self._write_common_attributes(char_uri, characteristic)

        # Write dataType
        if characteristic.data_type:
            self.graph.add((char_uri, SAMM.dataType, URIRef(characteristic.data_type)))

        # Write unit
        if characteristic.unit:
            self.graph.add((char_uri, SAMM_C.unit, URIRef(characteristic.unit)))

        # Write values (for Enumeration/State)
        if characteristic.values:
            values_list = BNode()
            value_literals = [self._python_to_literal(v) for v in characteristic.values]
            Collection(self.graph, values_list, value_literals)
            self.graph.add((char_uri, SAMM_C.values, values_list))

        # Write default value (for State)
        if characteristic.default_value is not None:
            default_literal = self._python_to_literal(characteristic.default_value)
            self.graph.add((char_uri, SAMM_C.defaultValue, default_literal))

        # Write elementCharacteristic (for Collection types)
        if characteristic.element_characteristic:
            self._write_characteristic(characteristic.element_characteristic)
            self.graph.add((char_uri, SAMM_C.elementCharacteristic,
                          URIRef(characteristic.element_characteristic.urn)))

        # Write left and right (for Either)
        if characteristic.left:
            self._write_characteristic(characteristic.left)
            self.graph.add((char_uri, SAMM_C.left, URIRef(characteristic.left.urn)))

        if characteristic.right:
            self._write_characteristic(characteristic.right)
            self.graph.add((char_uri, SAMM_C.right, URIRef(characteristic.right.urn)))

        # Write deconstructionRule (for StructuredValue)
        if characteristic.deconstruction_rule:
            self.graph.add((char_uri, SAMM_C.deconstructionRule,
                          Literal(characteristic.deconstruction_rule)))

        # Write elements (for StructuredValue)
        if characteristic.elements:
            elements_list = self._create_property_list(characteristic.elements)
            self.graph.add((char_uri, SAMM_C.elements, elements_list))

    def _write_entity(self, entity: Entity):
        """Write an Entity to the graph."""
        entity_uri = URIRef(entity.urn)
        entity_type = SAMM.AbstractEntity if entity.is_abstract else SAMM.Entity
        self.graph.add((entity_uri, RDF.type, entity_type))
        self._write_common_attributes(entity_uri, entity)

        # Write properties
        if entity.properties:
            props_list = self._create_property_list(entity.properties)
            self.graph.add((entity_uri, SAMM.properties, props_list))

        # Write extends
        if entity.extends:
            self.graph.add((entity_uri, SAMM.extends, URIRef(entity.extends)))

    def _write_operation(self, operation: Operation):
        """Write an Operation to the graph."""
        op_uri = URIRef(operation.urn)
        self.graph.add((op_uri, RDF.type, SAMM.Operation))
        self._write_common_attributes(op_uri, operation)

        # Write input
        if operation.input_properties:
            input_list = self._create_property_list(operation.input_properties)
            self.graph.add((op_uri, SAMM.input, input_list))

        # Write output
        if operation.output_property:
            self._write_property(operation.output_property)
            self.graph.add((op_uri, SAMM.output, URIRef(operation.output_property.urn)))

    def _write_event(self, event: Event):
        """Write an Event to the graph."""
        event_uri = URIRef(event.urn)
        self.graph.add((event_uri, RDF.type, SAMM.Event))
        self._write_common_attributes(event_uri, event)

        # Write parameters
        if event.parameters:
            params_list = self._create_property_list(event.parameters)
            self.graph.add((event_uri, SAMM.parameters, params_list))

    def _write_common_attributes(self, uri: URIRef, element: ModelElement):
        """Write common attributes (preferredName, description, see)."""
        # Write preferredName
        if element.preferred_name:
            for lang, text in element.preferred_name.values.items():
                self.graph.add((uri, SAMM.preferredName, Literal(text, lang=lang)))

        # Write description
        if element.description:
            for lang, text in element.description.values.items():
                self.graph.add((uri, SAMM.description, Literal(text, lang=lang)))

        # Write see
        for see_uri in element.see:
            self.graph.add((uri, SAMM.see, URIRef(see_uri)))

    def _python_to_literal(self, value) -> Literal:
        """Convert a Python value to an RDF Literal."""
        if isinstance(value, bool):
            return Literal(value, datatype=XSD.boolean)
        elif isinstance(value, int):
            return Literal(value, datatype=XSD.integer)
        elif isinstance(value, float):
            return Literal(value, datatype=XSD.float)
        else:
            return Literal(str(value))
