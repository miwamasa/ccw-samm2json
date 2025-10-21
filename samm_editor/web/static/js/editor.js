/**
 * SAMM Model Editor - Tree-based Editor (Debug Version)
 */

// Global model data
let currentModel = {
    namespace: 'urn:samm:com.example:1.0.0#',
    aspect: null,
    entities: {},
    properties: {},
    characteristics: {}
};

let selectedNode = null;

// Initialize on document ready
$(document).ready(function() {
    console.log('Initializing SAMM Editor...');
    try {
        initializeEditor();
        setupEventHandlers();
        console.log('Editor initialized successfully');
    } catch (error) {
        console.error('Initialization error:', error);
        showMessage('初期化エラー: ' + error.message, 'danger');
    }
});

function initializeEditor() {
    // Initialize with empty model
    createDefaultModel();
    buildTree();
}

function createDefaultModel() {
    console.log('Creating default model...');
    currentModel = {
        namespace: 'urn:samm:com.example:1.0.0#',
        aspect: {
            id: 'MyAspect',
            urn: 'urn:samm:com.example:1.0.0#MyAspect',
            type: 'aspect',
            preferredName: { en: 'My Aspect' },
            description: { en: 'Example aspect model' },
            properties: [],
            operations: [],
            events: []
        },
        entities: {},
        properties: {},
        characteristics: {}
    };
    console.log('Default model created:', currentModel);
}

function buildTree() {
    console.log('Building tree from model:', currentModel);
    const treeData = modelToTreeData(currentModel);
    console.log('Tree data:', treeData);

    // Destroy existing tree
    $('#treeView').jstree('destroy');

    // Create new tree
    $('#treeView').jstree({
        'core': {
            'data': treeData,
            'check_callback': true,
            'themes': {
                'name': 'default',
                'responsive': true
            }
        },
        'types': {
            'aspect': { 'icon': '📦' },
            'folder': { 'icon': '📁' },
            'property': { 'icon': '🔹' },
            'entity': { 'icon': '📄' }
        },
        'plugins': ['types']
    });

    // Handle node selection
    $('#treeView').off('select_node.jstree').on('select_node.jstree', function(e, data) {
        console.log('Node selected:', data.node);
        selectedNode = data.node;
        showFormForNode(data.node);
        updateToolbarButtons();
    });

    // Auto-select Aspect node after tree is ready
    $('#treeView').off('ready.jstree').on('ready.jstree', function() {
        console.log('Tree ready, selecting aspect...');
        if (currentModel.aspect) {
            const aspectNodeId = 'aspect_' + currentModel.aspect.id;
            $('#treeView').jstree('select_node', aspectNodeId);
        }
    });

    console.log('Tree built successfully');
}

function modelToTreeData(model) {
    const nodes = [];

    // Root: Aspect
    if (model.aspect) {
        const aspectNode = {
            id: 'aspect_' + model.aspect.id,
            text: model.aspect.preferredName?.en || model.aspect.id,
            type: 'aspect',
            icon: '📦',
            state: { opened: true },
            data: model.aspect,
            children: []
        };

        // Add Properties folder
        const propsFolder = {
            id: 'folder_properties',
            text: 'Properties (' + model.aspect.properties.length + ')',
            type: 'folder',
            icon: '📁',
            state: { opened: true },
            children: []
        };

        model.aspect.properties.forEach((propId, index) => {
            const prop = model.properties[propId];
            if (prop) {
                propsFolder.children.push({
                    id: 'property_' + propId,
                    text: prop.preferredName?.en || propId,
                    type: 'property',
                    icon: '🔹',
                    data: prop
                });
            } else {
                console.warn('Property not found:', propId);
            }
        });

        aspectNode.children.push(propsFolder);

        // Add Entities folder
        const entitiesFolder = {
            id: 'folder_entities',
            text: 'Entities (' + Object.keys(model.entities).length + ')',
            type: 'folder',
            icon: '📁',
            state: { opened: true },
            children: []
        };

        Object.keys(model.entities).forEach(entityId => {
            const entity = model.entities[entityId];
            const entityNode = {
                id: 'entity_' + entityId,
                text: entity.preferredName?.en || entityId,
                type: 'entity',
                icon: '📄',
                data: entity,
                state: { opened: true },
                children: []
            };

            // Add entity's properties as children
            if (entity.properties && entity.properties.length > 0) {
                const entityPropsFolder = {
                    id: 'folder_entity_properties_' + entityId,
                    text: 'Properties (' + entity.properties.length + ')',
                    type: 'folder',
                    icon: '📁',
                    state: { opened: true },
                    children: []
                };

                entity.properties.forEach(propId => {
                    const prop = model.properties[propId];
                    if (prop) {
                        entityPropsFolder.children.push({
                            id: 'entity_property_' + entityId + '_' + propId,
                            text: prop.preferredName?.en || propId,
                            type: 'property',
                            icon: '🔹',
                            data: prop
                        });
                    }
                });

                entityNode.children.push(entityPropsFolder);
            }

            entitiesFolder.children.push(entityNode);
        });

        aspectNode.children.push(entitiesFolder);

        nodes.push(aspectNode);
    } else {
        console.error('No aspect in model!');
    }

    return nodes;
}

function showFormForNode(node) {
    console.log('Showing form for node:', node);
    const formEditor = $('#formEditor');
    // Check node.data first (where jsTree stores our data), then fall back to node.original
    const nodeType = node.type || (node.original ? node.original.type : null);
    const nodeData = node.data || (node.original ? node.original.data : null);

    console.log('Node type:', nodeType, 'Node data:', nodeData);

    if (!nodeData) {
        formEditor.html('<div class="empty-state"><div>📁</div><p>フォルダは編集できません</p></div>');
        return;
    }

    let formHtml = '';

    switch (nodeType) {
        case 'aspect':
            formHtml = buildAspectForm(nodeData);
            break;
        case 'property':
            formHtml = buildPropertyForm(nodeData);
            break;
        case 'entity':
            formHtml = buildEntityForm(nodeData);
            break;
        default:
            formHtml = '<div class="empty-state"><div>❓</div><p>このタイプは編集できません</p></div>';
    }

    formEditor.html(formHtml);
    attachFormHandlers();
}

function buildAspectForm(aspect) {
    return `
        <form id="nodeForm">
            <div class="form-group">
                <label class="form-label">ID</label>
                <input type="text" class="form-control form-control-sm" name="id" value="${aspect.id || ''}" readonly>
            </div>
            <div class="form-group">
                <label class="form-label">名前 (英語)</label>
                <input type="text" class="form-control form-control-sm" name="preferredName_en" value="${aspect.preferredName?.en || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">説明 (英語)</label>
                <textarea class="form-control form-control-sm" name="description_en" rows="3">${aspect.description?.en || ''}</textarea>
            </div>
            <button type="submit" class="btn btn-primary btn-sm">保存</button>
        </form>
    `;
}

function buildPropertyForm(property) {
    return `
        <form id="nodeForm">
            <div class="form-group">
                <label class="form-label">ID</label>
                <input type="text" class="form-control form-control-sm" name="id" value="${property.id || ''}" readonly>
            </div>
            <div class="form-group">
                <label class="form-label">名前 (英語)</label>
                <input type="text" class="form-control form-control-sm" name="preferredName_en" value="${property.preferredName?.en || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">説明 (英語)</label>
                <textarea class="form-control form-control-sm" name="description_en" rows="2">${property.description?.en || ''}</textarea>
            </div>
            <div class="form-group">
                <label class="form-label">Characteristic タイプ</label>
                <select class="form-control form-control-sm" name="characteristicType">
                    <option value="Text" ${property.characteristicType === 'Text' ? 'selected' : ''}>Text</option>
                    <option value="Boolean" ${property.characteristicType === 'Boolean' ? 'selected' : ''}>Boolean</option>
                    <option value="Measurement" ${property.characteristicType === 'Measurement' ? 'selected' : ''}>Measurement</option>
                    <option value="Enumeration" ${property.characteristicType === 'Enumeration' ? 'selected' : ''}>Enumeration</option>
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">サンプル値</label>
                <input type="text" class="form-control form-control-sm" name="exampleValue" value="${property.exampleValue || ''}">
            </div>
            <div class="form-check">
                <input class="form-check-input" type="checkbox" name="optional" id="optionalCheck" ${property.optional ? 'checked' : ''}>
                <label class="form-check-label" for="optionalCheck">オプショナル</label>
            </div>
            <button type="submit" class="btn btn-primary btn-sm mt-3">保存</button>
        </form>
    `;
}

function buildEntityForm(entity) {
    // Build properties list display
    let propertiesHtml = '';
    if (entity.properties && entity.properties.length > 0) {
        propertiesHtml = '<div class="form-group"><label class="form-label">Properties</label><ul class="list-group list-group-sm">';
        entity.properties.forEach(propId => {
            const prop = currentModel.properties[propId];
            const propName = prop ? (prop.preferredName?.en || propId) : propId;
            propertiesHtml += `<li class="list-group-item list-group-item-sm py-1">${propName}</li>`;
        });
        propertiesHtml += '</ul><small class="form-text text-muted">ツリーから+Propertyボタンでプロパティを追加できます</small></div>';
    } else {
        propertiesHtml = '<div class="form-group"><label class="form-label">Properties</label><p class="text-muted small">プロパティなし（+Propertyボタンで追加）</p></div>';
    }

    return `
        <form id="nodeForm">
            <div class="form-group">
                <label class="form-label">ID</label>
                <input type="text" class="form-control form-control-sm" name="id" value="${entity.id || ''}" readonly>
            </div>
            <div class="form-group">
                <label class="form-label">名前 (英語)</label>
                <input type="text" class="form-control form-control-sm" name="preferredName_en" value="${entity.preferredName?.en || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">説明 (英語)</label>
                <textarea class="form-control form-control-sm" name="description_en" rows="2">${entity.description?.en || ''}</textarea>
            </div>
            <div class="form-check">
                <input class="form-check-input" type="checkbox" name="isAbstract" id="abstractCheck" ${entity.isAbstract ? 'checked' : ''}>
                <label class="form-check-label" for="abstractCheck">Abstract Entity</label>
            </div>
            ${propertiesHtml}
            <button type="submit" class="btn btn-primary btn-sm mt-3">保存</button>
        </form>
    `;
}

function attachFormHandlers() {
    $('#nodeForm').off('submit').on('submit', function(e) {
        e.preventDefault();
        saveForm();
    });
}

function saveForm() {
    // Check node.data first (where jsTree stores our data), then fall back to node.original
    const nodeData = selectedNode ? (selectedNode.data || (selectedNode.original ? selectedNode.original.data : null)) : null;

    if (!selectedNode || !nodeData) {
        console.error('No node selected or no data');
        return;
    }

    console.log('Saving form for node:', selectedNode);

    const formData = new FormData(document.getElementById('nodeForm'));
    const updates = {};

    for (let [key, value] of formData.entries()) {
        if (key.startsWith('preferredName_')) {
            const lang = key.split('_')[1];
            if (!updates.preferredName) updates.preferredName = {};
            updates.preferredName[lang] = value;
        } else if (key.startsWith('description_')) {
            const lang = key.split('_')[1];
            if (!updates.description) updates.description = {};
            updates.description[lang] = value;
        } else if (key === 'optional' || key === 'isAbstract') {
            updates[key] = true;  // checkbox is checked
        } else {
            updates[key] = value;
        }
    }

    // Handle unchecked checkboxes
    if (!formData.has('optional') && nodeData.hasOwnProperty('optional')) {
        updates.optional = false;
    }
    if (!formData.has('isAbstract') && nodeData.hasOwnProperty('isAbstract')) {
        updates.isAbstract = false;
    }

    console.log('Updates:', updates);

    // Update the data object
    Object.assign(nodeData, updates);

    // IMPORTANT: Also update currentModel directly to ensure changes persist
    const nodeId = nodeData.id;
    const nodeType = selectedNode.type || (selectedNode.original ? selectedNode.original.type : null);

    if (nodeType === 'property' && currentModel.properties[nodeId]) {
        Object.assign(currentModel.properties[nodeId], updates);
        console.log('Updated currentModel.properties[' + nodeId + ']:', currentModel.properties[nodeId]);
    } else if (nodeType === 'entity' && currentModel.entities[nodeId]) {
        Object.assign(currentModel.entities[nodeId], updates);
        console.log('Updated currentModel.entities[' + nodeId + ']:', currentModel.entities[nodeId]);
    } else if (nodeType === 'aspect' && currentModel.aspect) {
        Object.assign(currentModel.aspect, updates);
        console.log('Updated currentModel.aspect:', currentModel.aspect);
    }

    // Update tree node text
    if (updates.preferredName && updates.preferredName.en) {
        $('#treeView').jstree('rename_node', selectedNode, updates.preferredName.en);
    }

    showMessage('保存しました', 'success');
}

function setupEventHandlers() {
    console.log('Setting up event handlers...');

    // Add Property button
    $('#addPropertyBtn').off('click').on('click', function() {
        console.log('Add Property clicked');
        addProperty();
    });

    // Add Entity button
    $('#addEntityBtn').off('click').on('click', function() {
        console.log('Add Entity clicked');
        addEntity();
    });

    // Delete button
    $('#deleteNodeBtn').off('click').on('click', function() {
        console.log('Delete clicked');
        deleteNode();
    });

    // Load example handlers
    $('.load-example').off('click').on('click', function(e) {
        e.preventDefault();
        const exampleName = $(this).data('example');
        console.log('Loading example:', exampleName);
        loadExample(exampleName);
    });

    // Generate Turtle
    $('#generateTurtleBtn').off('click').on('click', function() {
        console.log('Generate Turtle clicked');
        generateTurtle();
    });

    // Generate Schema
    $('#generateSchemaBtn').off('click').on('click', function() {
        console.log('Generate Schema clicked');
        generateFromTurtle('schema');
    });

    // Generate Instance
    $('#generateInstanceBtn').off('click').on('click', function() {
        console.log('Generate Instance clicked');
        generateFromTurtle('instance');
    });

    // Copy buttons
    $('#copyTurtleBtn').off('click').on('click', () => copyToClipboard('turtleOutput'));
    $('#copySchemaBtn').off('click').on('click', () => copyToClipboard('schemaOutput'));
    $('#copyInstanceBtn').off('click').on('click', () => copyToClipboard('instanceOutput'));

    // Download buttons
    $('#downloadTurtleBtn').off('click').on('click', () => downloadContent('turtleOutput', 'model.ttl'));
    $('#downloadSchemaBtn').off('click').on('click', () => downloadContent('schemaOutput', 'schema.json'));
    $('#downloadInstanceBtn').off('click').on('click', () => downloadContent('instanceOutput', 'instance.json'));

    console.log('Event handlers set up');
}

function updateToolbarButtons() {
    const hasSelection = selectedNode !== null;
    // Check node.data first (where jsTree stores our data), then fall back to node.original
    const nodeType = selectedNode ? (selectedNode.type || (selectedNode.original ? selectedNode.original.type : null)) : null;
    const nodeData = selectedNode ? (selectedNode.data || (selectedNode.original ? selectedNode.original.data : null)) : null;

    const isAspect = nodeType === 'aspect';
    const isEntity = nodeType === 'entity';
    const isFolder = nodeType === 'folder';
    const isDeletable = hasSelection && !isAspect && !isFolder && nodeData;

    // +Property button: enabled for Aspect OR Entity
    $('#addPropertyBtn').prop('disabled', !isAspect && !isEntity);
    // +Entity button: enabled only for Aspect
    $('#addEntityBtn').prop('disabled', !isAspect);
    $('#deleteNodeBtn').prop('disabled', !isDeletable);

    console.log('Toolbar updated - nodeType:', nodeType, 'isAspect:', isAspect, 'isEntity:', isEntity, 'isDeletable:', isDeletable);
}

function addProperty() {
    console.log('Adding property...');
    const nodeType = selectedNode ? (selectedNode.type || (selectedNode.original ? selectedNode.original.type : null)) : null;
    const nodeData = selectedNode ? (selectedNode.data || (selectedNode.original ? selectedNode.original.data : null)) : null;

    if (!nodeType || (nodeType !== 'aspect' && nodeType !== 'entity')) {
        console.error('Cannot add property - no aspect or entity selected');
        showMessage('AspectまたはEntityを選択してください', 'warning');
        return;
    }

    const newId = 'property' + Date.now();
    const newProperty = {
        id: newId,
        urn: currentModel.namespace + newId,
        type: 'property',
        preferredName: { en: 'New Property' },
        description: { en: '' },
        characteristicType: 'Text',
        optional: false
    };

    // Add to global properties
    currentModel.properties[newId] = newProperty;

    // Add to aspect or entity
    if (nodeType === 'aspect') {
        currentModel.aspect.properties.push(newId);
        console.log('Property added to aspect:', newProperty);
    } else if (nodeType === 'entity' && nodeData) {
        if (!nodeData.properties) {
            nodeData.properties = [];
        }
        nodeData.properties.push(newId);
        // Also update the entity in currentModel.entities
        if (currentModel.entities[nodeData.id]) {
            if (!currentModel.entities[nodeData.id].properties) {
                currentModel.entities[nodeData.id].properties = [];
            }
            currentModel.entities[nodeData.id].properties.push(newId);
        }
        console.log('Property added to entity:', nodeData.id, newProperty);
    }

    console.log('Current model:', currentModel);

    buildTree();
    showMessage('Propertyを追加しました', 'success');
}

function addEntity() {
    console.log('Adding entity...');
    const newId = 'Entity' + Date.now();
    const newEntity = {
        id: newId,
        urn: currentModel.namespace + newId,
        type: 'entity',
        preferredName: { en: 'New Entity' },
        description: { en: '' },
        properties: [],
        isAbstract: false
    };

    currentModel.entities[newId] = newEntity;

    console.log('Entity added:', newEntity);
    console.log('Current model:', currentModel);

    buildTree();
    showMessage('Entityを追加しました', 'success');
}

function deleteNode() {
    if (!selectedNode) {
        console.error('No node selected');
        return;
    }

    if (!confirm('この要素を削除しますか？')) return;

    console.log('Deleting node:', selectedNode);

    // Check node.data first (where jsTree stores our data), then fall back to node.original
    const nodeType = selectedNode.type || (selectedNode.original ? selectedNode.original.type : null);
    const nodeData = selectedNode.data || (selectedNode.original ? selectedNode.original.data : null);

    if (!nodeData || !nodeData.id) {
        console.error('No node data or ID');
        return;
    }

    const nodeId = nodeData.id;

    if (nodeType === 'property') {
        // Check if this is an entity property (node id starts with 'entity_property_')
        if (selectedNode.id.startsWith('entity_property_')) {
            // Extract entity ID from node id: entity_property_EntityID_PropertyID
            const parts = selectedNode.id.split('_');
            if (parts.length >= 4) {
                const entityId = parts[2];
                const entity = currentModel.entities[entityId];
                if (entity && entity.properties) {
                    const index = entity.properties.indexOf(nodeId);
                    if (index > -1) {
                        entity.properties.splice(index, 1);
                        console.log('Property removed from entity:', entityId, nodeId);
                    }
                }
            }
        } else {
            // This is an aspect property
            const index = currentModel.aspect.properties.indexOf(nodeId);
            if (index > -1) {
                currentModel.aspect.properties.splice(index, 1);
                console.log('Property removed from aspect:', nodeId);
            }
        }
        // Remove from global properties
        delete currentModel.properties[nodeId];
        console.log('Property deleted:', nodeId);
    } else if (nodeType === 'entity') {
        delete currentModel.entities[nodeId];
        console.log('Entity deleted:', nodeId);
    }

    buildTree();
    $('#formEditor').html('<div class="empty-state"><div>📝</div><p>ツリーから要素を選択して編集</p></div>');
    selectedNode = null;
    updateToolbarButtons();
    showMessage('削除しました', 'success');
}

async function loadExample(exampleName) {
    console.log('Loading example:', exampleName);
    try {
        const response = await fetch(`/api/load-example/${exampleName}`);
        const result = await response.json();

        console.log('Example loaded:', result);

        if (result.success) {
            // Simply store the turtle and mark that we have original content
            currentModel._originalTurtle = result.turtle;

            // Parse to get basic info and rebuild simple tree
            const parseResult = await fetch('/api/parse', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ turtle: result.turtle })
            });

            const parseData = await parseResult.json();
            console.log('Parse result:', parseData);

            if (parseData.success) {
                // Create model from parsed data
                currentModel.namespace = parseData.info.namespace;
                currentModel.properties = {};
                currentModel.entities = {};
                currentModel.characteristics = {};

                // Populate properties
                if (parseData.info.properties) {
                    parseData.info.properties.forEach(prop => {
                        currentModel.properties[prop.id] = {
                            id: prop.id,
                            urn: prop.urn,
                            type: 'property',
                            preferredName: prop.preferredName || { en: '' },
                            description: prop.description || { en: '' },
                            characteristicType: prop.characteristicType || 'Text',
                            optional: prop.optional || false
                        };
                    });
                }

                // Populate entities
                if (parseData.info.entities) {
                    parseData.info.entities.forEach(entity => {
                        currentModel.entities[entity.id] = {
                            id: entity.id,
                            urn: entity.urn,
                            type: 'entity',
                            preferredName: entity.preferredName || { en: '' },
                            description: entity.description || { en: '' },
                            isAbstract: entity.isAbstract || false,
                            properties: entity.properties || []
                        };
                    });
                }

                // Create aspect with property references
                if (parseData.info.aspect) {
                    const aspectId = parseData.info.aspect.urn.split('#')[1];
                    currentModel.aspect = {
                        id: aspectId,
                        urn: parseData.info.aspect.urn,
                        type: 'aspect',
                        preferredName: { en: parseData.info.aspect.name },
                        description: { en: parseData.info.aspect.description },
                        properties: parseData.info.aspect.properties || [],
                        operations: [],
                        events: []
                    };
                }

                console.log('Model fully loaded:', currentModel);
                buildTree();

                // Auto-generate turtle in output
                $('#turtleOutput').text(result.turtle);

                showMessage(`サンプル "${exampleName}" を読み込みました`, 'success');
            }
        }
    } catch (error) {
        console.error('Load error:', error);
        showMessage('読み込みエラー: ' + error.message, 'danger');
    }
}

async function generateTurtle() {
    console.log('Generating Turtle...');

    // If we have original turtle, use it
    if (currentModel._originalTurtle) {
        $('#turtleOutput').text(currentModel._originalTurtle);
        showMessage('Turtleを表示しました', 'info');
        return;
    }

    // Otherwise, generate from model
    const turtle = modelToTurtle(currentModel);
    $('#turtleOutput').text(turtle);
    showMessage('Turtleを生成しました', 'success');
}

function modelToTurtle(model) {
    let turtle = `@prefix : <${model.namespace}> .\n`;
    turtle += '@prefix samm: <urn:samm:org.eclipse.esmf.samm:meta-model:2.2.0#> .\n';
    turtle += '@prefix samm-c: <urn:samm:org.eclipse.esmf.samm:characteristic:2.2.0#> .\n';
    turtle += '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\n';

    if (model.aspect) {
        const aspect = model.aspect;
        turtle += `:${aspect.id} a samm:Aspect ;\n`;
        turtle += `    samm:preferredName "${aspect.preferredName.en}"@en ;\n`;
        turtle += `    samm:description "${aspect.description.en}"@en ;\n`;

        if (aspect.properties.length > 0) {
            turtle += `    samm:properties ( ${aspect.properties.map(p => ':' + p).join(' ')} ) .\n\n`;
        } else {
            turtle += `    samm:properties ( ) .\n\n`;
        }

        // Add properties
        aspect.properties.forEach(propId => {
            const prop = model.properties[propId];
            if (prop) {
                turtle += `:${prop.id} a samm:Property ;\n`;
                turtle += `    samm:preferredName "${prop.preferredName.en}"@en ;\n`;
                if (prop.description.en) {
                    turtle += `    samm:description "${prop.description.en}"@en ;\n`;
                }
                turtle += `    samm:characteristic samm-c:${prop.characteristicType} .\n\n`;
            }
        });

        // Add entities
        Object.values(model.entities).forEach(entity => {
            turtle += `:${entity.id} a samm:Entity ;\n`;
            turtle += `    samm:preferredName "${entity.preferredName.en}"@en ;\n`;
            if (entity.description.en) {
                turtle += `    samm:description "${entity.description.en}"@en ;\n`;
            }
            turtle += `    samm:properties ( ) .\n\n`;
        });
    }

    return turtle;
}

async function generateFromTurtle(type) {
    const turtle = $('#turtleOutput').text();

    if (!turtle || turtle.startsWith('//')) {
        showMessage('先にTurtleを生成してください', 'warning');
        return;
    }

    console.log('Generating', type, 'from turtle');

    try {
        const endpoint = type === 'schema' ? '/api/generate-schema' : '/api/generate-instance';
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ turtle })
        });

        const result = await response.json();
        console.log('Generation result:', result);

        if (result.success) {
            const output = type === 'schema' ? result.schema : result.instance;
            const formatted = JSON.stringify(output, null, 2);
            $(`#${type}Output`).text(formatted);
            showMessage(`JSON ${type} を生成しました`, 'success');
        } else {
            showMessage('生成エラー: ' + result.error, 'danger');
        }
    } catch (error) {
        console.error('Generation error:', error);
        showMessage('生成エラー: ' + error.message, 'danger');
    }
}

function copyToClipboard(elementId) {
    const text = $('#' + elementId).text();
    navigator.clipboard.writeText(text).then(() => {
        showMessage('クリップボードにコピーしました', 'success');
    });
}

function downloadContent(elementId, filename) {
    const text = $('#' + elementId).text();
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function showMessage(message, type = 'info') {
    console.log('Message:', message, type);
    const messageArea = $('#messageArea');
    const alertDiv = $(`
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `);

    messageArea.append(alertDiv);

    setTimeout(() => {
        alertDiv.alert('close');
    }, 5000);
}
