# SAMM Model Editor - 使い方

## 概要

SAMM Model Editorは、SAMM (Semantic Aspect Meta Model) のモデルをTurtle形式で編集し、JSON SchemaとJSONインスタンス例を生成するツールです。

## インストール

```bash
# 依存関係のインストール
pip install -r requirements.txt

# パッケージのインストール（オプション）
pip install -e .
```

## 基本的な使い方

### 1. モデル情報の表示

Turtleファイルの内容を確認します。

```bash
python -m samm_editor.cli info examples/Movement.ttl
```

出力例:
```
SAMM Model: examples/Movement.ttl
Namespace: urn:samm:com.example.myapplication:1.0.0#

Aspect: urn:samm:com.example.myapplication:1.0.0#Movement
  Name: Movement
  Description: Describes the movement status and speed of an object
  Properties: 2
  Operations: 0
  Events: 0

Entities: 0
Characteristics: 2
Properties: 2
```

### 2. JSON Schemaの生成

SAMMモデルからJSON Schemaを生成します。

```bash
# 標準出力に表示
python -m samm_editor.cli generate-schema examples/Movement.ttl

# ファイルに保存
python -m samm_editor.cli generate-schema examples/Movement.ttl -o movement_schema.json
```

### 3. JSONインスタンス例の生成

SAMMモデルから例となるJSONインスタンスを生成します。

```bash
# 標準出力に表示
python -m samm_editor.cli generate-instance examples/Movement.ttl

# ファイルに保存
python -m samm_editor.cli generate-instance examples/Movement.ttl -o movement_instance.json
```

### 4. SchemaとInstanceの同時生成

```bash
python -m samm_editor.cli generate-all examples/Product.ttl \
  --schema product_schema.json \
  --instance product_instance.json
```

### 5. モデルの検証

SAMMモデルの基本的な検証を行います。

```bash
python -m samm_editor.cli validate examples/Movement.ttl
```

### 6. モデルの変換

Turtleファイルを読み込んで、再フォーマットして保存します。

```bash
python -m samm_editor.cli convert examples/Movement.ttl -o output.ttl
```

## サンプルモデル

### 例1: Movement.ttl（シンプルなモデル）

スカラー型とMeasurement特性を含む基本的なモデルです。

```turtle
:Movement a samm:Aspect ;
    samm:properties ( :isMoving :speed ) .

:isMoving a samm:Property ;
    samm:characteristic samm-c:Boolean ;
    samm:exampleValue true .

:speed a samm:Property ;
    samm:characteristic :Speed ;
    samm:exampleValue 0.5 .

:Speed a samm-c:Measurement ;
    samm:dataType xsd:float ;
    samm-c:unit unit:kilometrePerHour .
```

生成されるJSON Schema:
```json
{
  "type": "object",
  "properties": {
    "isMoving": {
      "type": "boolean"
    },
    "speed": {
      "type": "number"
    }
  },
  "required": ["isMoving", "speed"]
}
```

生成されるJSONインスタンス:
```json
{
  "isMoving": true,
  "speed": 0.5
}
```

### 例2: Product.ttl（Entityとコレクションを含むモデル）

Entityとコレクション（List）を含む複雑なモデルです。

```turtle
:ProductCatalog a samm:Aspect ;
    samm:properties ( :products ) .

:products a samm:Property ;
    samm:characteristic :ProductList .

:ProductList a samm-c:List ;
    samm:dataType :Product .

:Product a samm:Entity ;
    samm:properties ( :productId :productName :price :inStock ) .
```

生成されるJSON Schemaには、Entity定義が含まれます:
```json
{
  "type": "object",
  "properties": {
    "products": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/Product"
      }
    }
  },
  "definitions": {
    "Product": {
      "type": "object",
      "properties": {
        "productId": {"type": "string"},
        "productName": {"type": "string"},
        "price": {"type": "number"},
        "inStock": {"type": "boolean"}
      }
    }
  }
}
```

## Python APIの使用

プログラムから直接使用する場合:

```python
from samm_editor.parser import SAMMParser
from samm_editor.json_schema_generator import JSONSchemaGenerator
from samm_editor.json_instance_generator import JSONInstanceGenerator

# Turtleファイルの読み込み
parser = SAMMParser()
model = parser.parse_file('examples/Movement.ttl')

# JSON Schemaの生成
schema_gen = JSONSchemaGenerator(model)
schema = schema_gen.generate()

# JSONインスタンスの生成
instance_gen = JSONInstanceGenerator(model)
instance = instance_gen.generate()

# 結果の出力
print(schema_gen.generate_string())
print(instance_gen.generate_string())
```

## 対応している SAMM 要素

### Characteristics
- Boolean
- Text
- Measurement / Quantifiable
- Enumeration / State
- Collection / List / Set / SortedSet
- TimeSeries
- Either
- SingleEntity
- MultiLanguageText
- UnitReference

### 構造
- Aspect
- Property
- Entity
- Operation (パース可能、JSON生成には未対応)
- Event (パース可能、JSON生成には未対応)

### データ型
- XSD標準型（boolean, string, integer, float, decimal, dateTime等）
- rdf:langString
- samm:curie

## トラブルシューティング

### エラー: "No Aspect found in the model"

Turtleファイルに`samm:Aspect`が定義されていることを確認してください。

### エラー: "Object of type Decimal is not JSON serializable"

このエラーは修正済みです。最新版のコードを使用してください。

### JSON Schemaにプロパティのtypeが含まれない

Characteristicに`samm:dataType`が定義されているか、または事前定義されたCharacteristic（samm-c:Boolean等）を使用していることを確認してください。

## さらなる情報

- SAMM仕様: https://eclipse-esmf.github.io/samm-specification/snapshot/index.html
- プロジェクトのREADME: README.md
- 仕様ドキュメント: spec/ディレクトリ
