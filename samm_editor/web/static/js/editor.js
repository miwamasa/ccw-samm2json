/**
 * SAMM Model Editor - Tree-based Editor
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
    initializeEditor();
    setupEventHandlers();
});

function initializeEditor() {
    // Initialize with empty model
    createDefaultModel();
    buildTree();
}

function createDefaultModel() {
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
}

function buildTree() {
    const treeData = modelToTreeData(currentModel);

    $('#treeView').jstree('destroy');
    $('#treeView').jstree({
        'core': {
            'data': treeData,
            'check_callback': true,
            'themes': {
                'name': 'default',
                'responsive': true
            }
        }
    });

    // Handle node selection
    $('#treeView').on('select_node.jstree', function(e, data) {
        selectedNode = data.node;
        showFormForNode(data.node);
        updateToolbarButtons();
    });
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

        // Add Properties
        if (model.aspect.properties && model.aspect.properties.length > 0) {
            const propsFolder = {
                id: 'folder_properties',
                text: 'Properties',
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
                }
            });

            aspectNode.children.push(propsFolder);
        }

        // Add Entities folder
        const entitiesFolder = {
            id: 'folder_entities',
            text: 'Entities',
            type: 'folder',
            icon: '📁',
            state: { opened: true },
            children: []
        };

        Object.keys(model.entities).forEach(entityId => {
            const entity = model.entities[entityId];
            entitiesFolder.children.push({
                id: 'entity_' + entityId,
                text: entity.preferredName?.en || entityId,
                type: 'entity',
                icon: '📄',
                data: entity
            });
        });

        if (entitiesFolder.children.length > 0) {
            aspectNode.children.push(entitiesFolder);
        }

        nodes.push(aspectNode);
    }

    return nodes;
}

function showFormForNode(node) {
    const formEditor = $('#formEditor');
    const nodeType = node.type;
    const nodeData = node.data;

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
                <input type="text" class="form-control" name="id" value="${aspect.id || ''}" readonly>
            </div>
            <div class="form-group">
                <label class="form-label">名前 (英語)</label>
                <input type="text" class="form-control" name="preferredName_en" value="${aspect.preferredName?.en || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">説明 (英語)</label>
                <textarea class="form-control" name="description_en" rows="3">${aspect.description?.en || ''}</textarea>
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
                <input type="text" class="form-control" name="id" value="${property.id || ''}" readonly>
            </div>
            <div class="form-group">
                <label class="form-label">名前 (英語)</label>
                <input type="text" class="form-control" name="preferredName_en" value="${property.preferredName?.en || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">説明 (英語)</label>
                <textarea class="form-control" name="description_en" rows="3">${property.description?.en || ''}</textarea>
            </div>
            <div class="form-group">
                <label class="form-label">Characteristic タイプ</label>
                <select class="form-control" name="characteristicType">
                    <option value="Text" ${property.characteristicType === 'Text' ? 'selected' : ''}>Text</option>
                    <option value="Boolean" ${property.characteristicType === 'Boolean' ? 'selected' : ''}>Boolean</option>
                    <option value="Measurement" ${property.characteristicType === 'Measurement' ? 'selected' : ''}>Measurement</option>
                    <option value="Enumeration" ${property.characteristicType === 'Enumeration' ? 'selected' : ''}>Enumeration</option>
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">サンプル値</label>
                <input type="text" class="form-control" name="exampleValue" value="${property.exampleValue || ''}">
            </div>
            <div class="form-check">
                <input class="form-check-input" type="checkbox" name="optional" ${property.optional ? 'checked' : ''}>
                <label class="form-check-label">オプショナル</label>
            </div>
            <button type="submit" class="btn btn-primary btn-sm mt-3">保存</button>
        </form>
    `;
}

function buildEntityForm(entity) {
    return `
        <form id="nodeForm">
            <div class="form-group">
                <label class="form-label">ID</label>
                <input type="text" class="form-control" name="id" value="${entity.id || ''}" readonly>
            </div>
            <div class="form-group">
                <label class="form-label">名前 (英語)</label>
                <input type="text" class="form-control" name="preferredName_en" value="${entity.preferredName?.en || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">説明 (英語)</label>
                <textarea class="form-control" name="description_en" rows="3">${entity.description?.en || ''}</textarea>
            </div>
            <div class="form-check">
                <input class="form-check-input" type="checkbox" name="isAbstract" ${entity.isAbstract ? 'checked' : ''}>
                <label class="form-check-label">Abstract Entity</label>
            </div>
            <button type="submit" class="btn btn-primary btn-sm mt-3">保存</button>
        </form>
    `;
}

function attachFormHandlers() {
    $('#nodeForm').on('submit', function(e) {
        e.preventDefault();
        saveForm();
    });
}

function saveForm() {
    if (!selectedNode || !selectedNode.data) return;

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
            updates[key] = formData.has(key);
        } else {
            updates[key] = value;
        }
    }

    // Update model
    Object.assign(selectedNode.data, updates);

    // Update tree node text
    if (updates.preferredName && updates.preferredName.en) {
        $('#treeView').jstree('rename_node', selectedNode, updates.preferredName.en);
    }

    showMessage('保存しました', 'success');
}

function setupEventHandlers() {
    // Add Property button
    $('#addPropertyBtn').on('click', function() {
        addProperty();
    });

    // Add Entity button
    $('#addEntityBtn').on('click', function() {
        addEntity();
    });

    // Delete button
    $('#deleteNodeBtn').on('click', function() {
        deleteNode();
    });

    // Load example handlers
    $('.load-example').on('click', function(e) {
        e.preventDefault();
        const exampleName = $(this).data('example');
        loadExample(exampleName);
    });

    // Generate Turtle
    $('#generateTurtleBtn').on('click', function() {
        generateTurtle();
    });

    // Generate Schema
    $('#generateSchemaBtn').on('click', function() {
        generateFromTurtle('schema');
    });

    // Generate Instance
    $('#generateInstanceBtn').on('click', function() {
        generateFromTurtle('instance');
    });

    // Copy buttons
    $('#copyTurtleBtn').on('click', () => copyToClipboard('turtleOutput'));
    $('#copySchemaBtn').on('click', () => copyToClipboard('schemaOutput'));
    $('#copyInstanceBtn').on('click', () => copyToClipboard('instanceOutput'));

    // Download buttons
    $('#downloadTurtleBtn').on('click', () => downloadContent('turtleOutput', 'model.ttl'));
    $('#downloadSchemaBtn').on('click', () => downloadContent('schemaOutput', 'schema.json'));
    $('#downloadInstanceBtn').on('click', () => downloadContent('instanceOutput', 'instance.json'));
}

function updateToolbarButtons() {
    const hasSelection = selectedNode !== null;
    const isAspect = selectedNode && selectedNode.type === 'aspect';
    const isFolder = selectedNode && selectedNode.type === 'folder';
    const isDeletable = hasSelection && !isAspect && !isFolder;

    $('#addPropertyBtn').prop('disabled', !isAspect);
    $('#addEntityBtn').prop('disabled', !isAspect);
    $('#deleteNodeBtn').prop('disabled', !isDeletable);
}

function addProperty() {
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

    currentModel.properties[newId] = newProperty;
    currentModel.aspect.properties.push(newId);

    buildTree();
    showMessage('Propertyを追加しました', 'success');
}

function addEntity() {
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

    buildTree();
    showMessage('Entityを追加しました', 'success');
}

function deleteNode() {
    if (!selectedNode || !confirm('この要素を削除しますか？')) return;

    const nodeId = selectedNode.data.id;
    const nodeType = selectedNode.type;

    if (nodeType === 'property') {
        delete currentModel.properties[nodeId];
        const index = currentModel.aspect.properties.indexOf(nodeId);
        if (index > -1) {
            currentModel.aspect.properties.splice(index, 1);
        }
    } else if (nodeType === 'entity') {
        delete currentModel.entities[nodeId];
    }

    buildTree();
    $('#formEditor').html('<div class="empty-state"><div>📝</div><p>ツリーから要素を選択して編集</p></div>');
    selectedNode = null;
    updateToolbarButtons();
    showMessage('削除しました', 'success');
}

async function loadExample(exampleName) {
    try {
        const response = await fetch(`/api/load-example/${exampleName}`);
        const result = await response.json();

        if (result.success) {
            // Parse the turtle to build model
            const parseResult = await fetch('/api/parse', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ turtle: result.turtle })
            });

            const parseData = await parseResult.json();

            if (parseData.success) {
                // Convert parsed info to our model structure
                convertParsedToModel(parseData.info, result.turtle);
                buildTree();
                showMessage(`サンプル "${exampleName}" を読み込みました`, 'success');
            }
        }
    } catch (error) {
        showMessage('読み込みエラー: ' + error.message, 'danger');
    }
}

function convertParsedToModel(info, turtleContent) {
    // Store the original turtle for later use
    currentModel._originalTurtle = turtleContent;
    currentModel.namespace = info.namespace;

    if (info.aspect) {
        const aspectId = info.aspect.urn.split('#')[1];
        currentModel.aspect = {
            id: aspectId,
            urn: info.aspect.urn,
            type: 'aspect',
            preferredName: { en: info.aspect.name },
            description: { en: info.aspect.description },
            properties: [],
            operations: [],
            events: []
        };

        // Note: For full implementation, we'd need to parse properties and entities
        // from the turtle content. For now, we'll store the turtle and generate it back.
    }
}

async function generateTurtle() {
    // If we have original turtle, use it
    if (currentModel._originalTurtle) {
        $('#turtleOutput').text(currentModel._originalTurtle);
        return;
    }

    // Otherwise, generate from model
    const turtle = modelToTurtle(currentModel);
    $('#turtleOutput').text(turtle);
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
    }

    return turtle;
}

async function generateFromTurtle(type) {
    const turtle = $('#turtleOutput').text();

    if (!turtle || turtle.startsWith('//')) {
        showMessage('先にTurtleを生成してください', 'warning');
        return;
    }

    try {
        const endpoint = type === 'schema' ? '/api/generate-schema' : '/api/generate-instance';
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ turtle })
        });

        const result = await response.json();

        if (result.success) {
            const output = type === 'schema' ? result.schema : result.instance;
            const formatted = JSON.stringify(output, null, 2);
            $(`#${type}Output`).text(formatted);
            showMessage(`JSON ${type} を生成しました`, 'success');
        } else {
            showMessage('生成エラー: ' + result.error, 'danger');
        }
    } catch (error) {
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
