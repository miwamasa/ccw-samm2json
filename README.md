# SAMM Model Editor

A Python-based tool for editing SAMM (Semantic Aspect Meta Model) models in Turtle format, and generating JSON Schema and JSON instance examples.

## Features

- **Read and write Turtle files**: Parse and serialize SAMM Aspect Models in RDF/Turtle format
- **Generate JSON Schema**: Automatically generate JSON Schema from SAMM models according to the SAMM specification
- **Generate JSON instances**: Create example JSON instances based on your SAMM models
- **Validate models**: Basic validation of SAMM model structure
- **Command-line interface**: Easy-to-use CLI for all operations

## Installation

### From source

```bash
pip install -r requirements.txt
pip install -e .
```

## Usage

### Command-line Interface

The tool provides several commands:

#### Display model information

```bash
samm-editor info examples/Movement.ttl
```

#### Generate JSON Schema

```bash
# Output to stdout
samm-editor generate-schema examples/Movement.ttl

# Output to file
samm-editor generate-schema examples/Movement.ttl -o schema.json
```

#### Generate JSON instance example

```bash
# Output to stdout
samm-editor generate-instance examples/Movement.ttl

# Output to file
samm-editor generate-instance examples/Movement.ttl -o instance.json
```

#### Generate both schema and instance

```bash
samm-editor generate-all examples/Movement.ttl --schema schema.json --instance instance.json
```

#### Validate a model

```bash
samm-editor validate examples/Movement.ttl
```

#### Convert/reformat a model

```bash
samm-editor convert examples/Movement.ttl -o output.ttl
```

### Python API

```python
from samm_editor.parser import SAMMParser
from samm_editor.writer import SAMMWriter
from samm_editor.json_schema_generator import JSONSchemaGenerator
from samm_editor.json_instance_generator import JSONInstanceGenerator

# Parse a Turtle file
parser = SAMMParser()
model = parser.parse_file('examples/Movement.ttl')

# Generate JSON Schema
schema_gen = JSONSchemaGenerator(model)
schema = schema_gen.generate()
print(schema_gen.generate_string())

# Generate JSON instance
instance_gen = JSONInstanceGenerator(model)
instance = instance_gen.generate()
print(instance_gen.generate_string())

# Write back to Turtle
writer = SAMMWriter(model)
writer.write_to_file('output.ttl')
```

## Examples

The `examples/` directory contains sample SAMM models:

- `Movement.ttl`: Simple model with scalar properties and measurements
- `Product.ttl`: Model with entities and collections

## SAMM Specification

This tool implements the SAMM (Semantic Aspect Meta Model) specification version 2.2.0.

For more information about SAMM, see:
- https://eclipse-esmf.github.io/samm-specification/snapshot/index.html

## Project Structure

```
samm_editor/
├── __init__.py
├── model.py                    # Data structures for SAMM models
├── parser.py                   # Turtle file parser
├── writer.py                   # Turtle file writer
├── json_schema_generator.py    # JSON Schema generation
├── json_instance_generator.py  # JSON instance generation
└── cli.py                      # Command-line interface
```

## Development

### Running tests

Create a test file:

```bash
# Test with example files
samm-editor info examples/Movement.ttl
samm-editor generate-schema examples/Movement.ttl
samm-editor generate-instance examples/Movement.ttl
```

## License

This project is open source.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
