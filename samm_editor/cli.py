"""
SAMM Model Editor CLI

Command-line interface for the SAMM Model Editor.
"""

import click
import json
import sys
from pathlib import Path
from .parser import SAMMParser
from .writer import SAMMWriter
from .json_schema_generator import JSONSchemaGenerator
from .json_instance_generator import JSONInstanceGenerator
from .model import SAMMModel


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """SAMM Model Editor - Edit SAMM models and generate JSON Schema/instances."""
    pass


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
def info(input_file):
    """Display information about a SAMM model file."""
    try:
        parser = SAMMParser()
        model = parser.parse_file(input_file)

        click.echo(f"SAMM Model: {input_file}")
        click.echo(f"Namespace: {model.namespace}")
        click.echo()

        if model.aspect:
            click.echo(f"Aspect: {model.aspect.urn}")
            if model.aspect.preferred_name:
                click.echo(f"  Name: {model.aspect.preferred_name.values.get('en', '')}")
            if model.aspect.description:
                click.echo(f"  Description: {model.aspect.description.values.get('en', '')}")
            click.echo(f"  Properties: {len(model.aspect.properties)}")
            click.echo(f"  Operations: {len(model.aspect.operations)}")
            click.echo(f"  Events: {len(model.aspect.events)}")
            click.echo()

        click.echo(f"Entities: {len(model.entities)}")
        for entity_urn, entity in model.entities.items():
            click.echo(f"  - {entity_urn}")

        click.echo(f"Characteristics: {len(model.characteristics)}")
        click.echo(f"Properties: {len(model.properties)}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), help='Output file (default: stdout)')
def generate_schema(input_file, output):
    """Generate JSON Schema from a SAMM model."""
    try:
        parser = SAMMParser()
        model = parser.parse_file(input_file)

        generator = JSONSchemaGenerator(model)
        schema = generator.generate()

        schema_json = json.dumps(schema, indent=2)

        if output:
            Path(output).write_text(schema_json)
            click.echo(f"JSON Schema written to: {output}")
        else:
            click.echo(schema_json)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), help='Output file (default: stdout)')
def generate_instance(input_file, output):
    """Generate example JSON instance from a SAMM model."""
    try:
        parser = SAMMParser()
        model = parser.parse_file(input_file)

        generator = JSONInstanceGenerator(model)
        instance = generator.generate()

        instance_json = json.dumps(instance, indent=2)

        if output:
            Path(output).write_text(instance_json)
            click.echo(f"JSON instance written to: {output}")
        else:
            click.echo(instance_json)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), required=True, help='Output Turtle file')
def convert(input_file, output):
    """Convert/reformat a SAMM model file."""
    try:
        parser = SAMMParser()
        model = parser.parse_file(input_file)

        writer = SAMMWriter(model)
        writer.write_to_file(output)

        click.echo(f"Model written to: {output}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--schema', type=click.Path(), help='Output JSON Schema file')
@click.option('--instance', type=click.Path(), help='Output JSON instance file')
def generate_all(input_file, schema, instance):
    """Generate both JSON Schema and instance from a SAMM model."""
    try:
        parser = SAMMParser()
        model = parser.parse_file(input_file)

        # Generate schema
        if schema:
            generator = JSONSchemaGenerator(model)
            schema_json = generator.generate_string()
            Path(schema).write_text(schema_json)
            click.echo(f"JSON Schema written to: {schema}")

        # Generate instance
        if instance:
            generator = JSONInstanceGenerator(model)
            instance_json = generator.generate_string()
            Path(instance).write_text(instance_json)
            click.echo(f"JSON instance written to: {instance}")

        if not schema and not instance:
            click.echo("Please specify at least one output file (--schema or --instance)")
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
def validate(input_file):
    """Validate a SAMM model file."""
    try:
        parser = SAMMParser()
        model = parser.parse_file(input_file)

        # Basic validation
        errors = []

        if not model.aspect:
            errors.append("No Aspect found in the model")

        if model.aspect:
            if not model.aspect.preferred_name or 'en' not in model.aspect.preferred_name.values:
                errors.append("Aspect must have preferredName with 'en' language tag")

            if not model.aspect.description or 'en' not in model.aspect.description.values:
                errors.append("Aspect must have description with 'en' language tag")

        if errors:
            click.echo("Validation errors:")
            for error in errors:
                click.echo(f"  - {error}")
            sys.exit(1)
        else:
            click.echo("Model is valid!")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
