"""
SAMM Web Editor Flask Application
"""

from flask import Flask, render_template, request, jsonify, send_file
import json
import io
import traceback
from pathlib import Path

from ..parser import SAMMParser
from ..writer import SAMMWriter
from ..json_schema_generator import JSONSchemaGenerator
from ..json_instance_generator import JSONInstanceGenerator
from ..model import SAMMModel


# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


@app.route('/')
def index():
    """Main editor page."""
    return render_template('index.html')


@app.route('/api/parse', methods=['POST'])
def parse_turtle():
    """Parse Turtle content and return model information."""
    try:
        data = request.get_json()
        turtle_content = data.get('turtle', '')

        if not turtle_content.strip():
            return jsonify({'error': 'Empty Turtle content'}), 400

        # Parse the Turtle content
        parser = SAMMParser()
        model = parser.parse_string(turtle_content)

        # Extract model information
        info = {
            'namespace': model.namespace,
            'aspect': None,
            'entities': [],
            'properties': [],
            'characteristics': []
        }

        if model.aspect:
            # Extract property IDs from Property objects
            prop_ids = [p.urn.split('#')[1] if '#' in p.urn else p.urn for p in model.aspect.properties]

            info['aspect'] = {
                'urn': model.aspect.urn,
                'name': model.aspect.preferred_name.values.get('en', '') if model.aspect.preferred_name else '',
                'description': model.aspect.description.values.get('en', '') if model.aspect.description else '',
                'properties': prop_ids,
                'properties_count': len(model.aspect.properties),
                'operations_count': len(model.aspect.operations),
                'events_count': len(model.aspect.events)
            }

        for entity_urn, entity in model.entities.items():
            # Extract property IDs from Property objects
            entity_prop_ids = [p.urn.split('#')[1] if '#' in p.urn else p.urn for p in entity.properties]

            entity_info = {
                'urn': entity_urn,
                'id': entity_urn.split('#')[1] if '#' in entity_urn else entity_urn,
                'preferredName': entity.preferred_name.values if entity.preferred_name else {'en': ''},
                'description': entity.description.values if entity.description else {'en': ''},
                'isAbstract': entity.is_abstract,
                'properties': entity_prop_ids
            }
            info['entities'].append(entity_info)

        for prop_urn, prop in model.properties.items():
            prop_info = {
                'urn': prop_urn,
                'id': prop_urn.split('#')[1] if '#' in prop_urn else prop_urn,
                'preferredName': prop.preferred_name.values if prop.preferred_name else {'en': ''},
                'description': prop.description.values if prop.description else {'en': ''},
                'optional': prop.optional,
                'characteristicType': 'Text',  # Default
            }
            if prop.characteristic:
                # prop.characteristic is a Characteristic object, not a string
                if isinstance(prop.characteristic, str):
                    # If it's a URN string (backward compatibility)
                    char_type = prop.characteristic.split('#')[-1] if '#' in prop.characteristic else 'Text'
                else:
                    # It's a Characteristic object
                    char_type = prop.characteristic.urn.split('#')[-1] if '#' in prop.characteristic.urn else 'Text'
                prop_info['characteristicType'] = char_type
            info['properties'].append(prop_info)

        for char_urn in model.characteristics.keys():
            info['characteristics'].append(char_urn)

        return jsonify({
            'success': True,
            'info': info
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 400


@app.route('/api/generate-schema', methods=['POST'])
def generate_schema():
    """Generate JSON Schema from Turtle content."""
    try:
        data = request.get_json()
        turtle_content = data.get('turtle', '')

        if not turtle_content.strip():
            return jsonify({'error': 'Empty Turtle content'}), 400

        # Parse and generate schema
        parser = SAMMParser()
        model = parser.parse_string(turtle_content)

        generator = JSONSchemaGenerator(model)
        schema = generator.generate()

        return jsonify({
            'success': True,
            'schema': schema
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 400


@app.route('/api/generate-instance', methods=['POST'])
def generate_instance():
    """Generate JSON instance example from Turtle content."""
    try:
        data = request.get_json()
        turtle_content = data.get('turtle', '')

        if not turtle_content.strip():
            return jsonify({'error': 'Empty Turtle content'}), 400

        # Parse and generate instance
        parser = SAMMParser()
        model = parser.parse_string(turtle_content)

        generator = JSONInstanceGenerator(model)
        instance = generator.generate()

        return jsonify({
            'success': True,
            'instance': instance
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 400


@app.route('/api/validate', methods=['POST'])
def validate_model():
    """Validate Turtle content."""
    try:
        data = request.get_json()
        turtle_content = data.get('turtle', '')

        if not turtle_content.strip():
            return jsonify({'error': 'Empty Turtle content'}), 400

        # Parse the model
        parser = SAMMParser()
        model = parser.parse_string(turtle_content)

        # Basic validation
        errors = []
        warnings = []

        if not model.aspect:
            errors.append("No Aspect found in the model")

        if model.aspect:
            if not model.aspect.preferred_name or 'en' not in model.aspect.preferred_name.values:
                warnings.append("Aspect should have preferredName with 'en' language tag")

            if not model.aspect.description or 'en' not in model.aspect.description.values:
                warnings.append("Aspect should have description with 'en' language tag")

            if len(model.aspect.properties) == 0:
                warnings.append("Aspect has no properties")

        return jsonify({
            'success': True,
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 400


@app.route('/api/load-example/<example_name>')
def load_example(example_name):
    """Load an example Turtle file."""
    try:
        # Sanitize the example name
        if '..' in example_name or '/' in example_name:
            return jsonify({'error': 'Invalid example name'}), 400

        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent
        example_path = project_root / 'examples' / f'{example_name}.ttl'

        if not example_path.exists():
            return jsonify({'error': 'Example not found'}), 404

        turtle_content = example_path.read_text(encoding='utf-8')

        return jsonify({
            'success': True,
            'turtle': turtle_content,
            'name': example_name
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/download', methods=['POST'])
def download_file():
    """Download generated content as a file."""
    try:
        data = request.get_json()
        content = data.get('content', '')
        filename = data.get('filename', 'download.txt')
        content_type = data.get('content_type', 'text/plain')

        # Create a BytesIO object
        file_stream = io.BytesIO(content.encode('utf-8'))
        file_stream.seek(0)

        return send_file(
            file_stream,
            mimetype=content_type,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def run_app(host='127.0.0.1', port=5000, debug=True):
    """Run the Flask application."""
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_app()
