ご要望に基づき、SAMM（Semantic Aspect Meta Model）のモデル定義と、それに対応する**通常のJSONペイロード**の具体例を作成します。

**【AAS JSONについて再確認】**
前回申し上げました通り、提供されたソースには、SAMMのアスペクトモデルをAAS（Asset Administration Shell）の特定の構造にラップするための具体的なJSON仕様や例は含まれていません。したがって、ここではSAMMのランタイムデータ構造のシリアライズに焦点を当てます。

---

## 1. SAMMに基づく通常のJSONペイロード例

SAMMのアスペクトモデルはRDF/Turtle形式で定義されますが、ランタイムデータとしてやり取りされる際は、そのモデルのプロパティ構造に基づいた名前のないJSONオブジェクトとしてシリアライズされます。

以下の例では、まずRDF/Turtle形式でモデルを定義し、次にそのモデルに準拠するランタイムJSONペイロードを示します。

### 例 1: 基本的なスカラー型とMeasurement (単位情報を含まない)

この例は、最も単純なブール値と、単位を持つ測定値（Measurement）で構成されるアスペクトを示します。Measurementの場合、単位情報（`unit:kilometrePerHour`）はモデルに存在しますが、**ランタイムペイロードには含まれません**。

#### モデル定義（RDF/Turtle抜粋）
```turtle
@prefix : <urn:samm:com.mycompany.myapplication:1.0.0#> .
... (省略)
@prefix samm-c: <urn:samm:org.eclipse.esmf.samm:characteristic:2.2.0#> .
@prefix unit: <urn:samm:org.eclipse.esmf.samm:unit:2.2.0#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

:Movement a samm:Aspect ;
    samm:properties ( :isMoving :speed ) .

:isMoving a samm:Property ;
    samm:characteristic samm-c:Boolean .

:speed a samm:Property ;
    samm:characteristic :Speed .

:Speed a samm-c:Measurement ;
    samm:dataType xsd:float ;
    samm-c:unit unit:kilometrePerHour .
```

#### 対応するJSONペイロード（インスタンス）

`isMoving`はブール値に、`speed`は数値（浮動小数点）にマッピングされます。

```json
{
  "isMoving": true,
  "speed": 0.5 
}
```

### 例 2: コレクション（リスト）とペイロード名の上書き

この例では、JSON配列にシリアライズされるリスト（Collection）特性と、プロパティ名をペイロード内で変更する（`samm:payloadName`を使用）例を示します。

#### モデル定義（RDF/Turtle抜粋）
```turtle
...
:MyAspect a samm:Aspect ;
    samm:properties (
        [ samm:property :materialNumber; samm:payloadName "partId" ] 
        :coordinates
    ) .

:materialNumber a samm:Property ;
    samm:characteristic samm-c:Text .

:coordinates a samm:Property ;
    samm:characteristic [ 
        a samm-c:List; 
        samm:dataType xsd:float 
    ] . 
```

#### 対応するJSONペイロード（インスタンス）

`materialNumber`は`partId`としてシリアライズされ、`:coordinates`はJSON配列としてシリアライズされます。

```json
{
  "partId": "XYZ-7890",
  "coordinates": [
    10.5,
    22.1,
    -5.0
  ]
}
```

### 例 3: MultiLanguage Text (多言語テキスト)

`rdf:langString`（または`samm-c:MultiLanguageText`）を使用する場合、値は言語タグをキーとするJSONオブジェクトとしてシリアライズされます。

#### モデル定義（RDF/Turtle抜粋）
```turtle
...
:Notification a samm:Aspect ;
    samm:properties ( :statusDescription ) .

:statusDescription a samm:Property ;
    samm:characteristic samm-c:MultiLanguageText .
```

#### 対応するJSONペイロード（インスタンス）

単一のプロパティが、複数の言語タグ（`en`, `de`など）を持つオブジェクトになります。

```json
{
  "statusDescription": {
    "en": "Process completed.",
    "de": "Prozess abgeschlossen."
  }
}
```

### 例 4: Either 特性 (左または右のいずれか)

`samm-c:Either`特性は、エラーメッセージまたは成功値など、2つの異なる型のうちのいずれか一方を返す場合に用いられます。ペイロードでは、その値は**厳密に`left`または`right`のキー**を持つJSONオブジェクトとして表現されます。

以下の例では、成功時には整数値（`SpeedValue`）を返し、エラー時にはエラーエンティティ（`ErrorEntity`）を返します。

#### モデル定義（RDF/Turtle抜粋）
```turtle
...
:speedProperty a samm:Property ; samm:characteristic :Result . 
:Result a samm-c:Either ; 
    samm-c:left :ErrorMessage ; 
    samm-c:right :SpeedValue . 
:ErrorMessage a samm-c:SingleEntity ; samm:dataType :ErrorEntity . 
:SpeedValue a samm-c:Quantifiable ; samm:dataType xsd:integer . 
:ErrorEntity a samm:Entity ; samm:properties ( :errorCode :errorDescription ) . 
```

#### 対応するJSONペイロード（インスタンス）

**ケース A: 成功時（右側 `right` が有効な場合）**
速度が整数値として返されます。
```json
{ 
  "speedProperty": { 
    "right": 60 
  } 
}
```

**ケース B: エラー時（左側 `left` が有効な場合）**
エラーエンティティ（`ErrorEntity`）が再帰的にシリアライズされて返されます。
```json
{ 
  "speedProperty": { 
    "left": { 
      "errorCode": "E1001",
      "errorDescription": "Sensor data unavailable."
    } 
  } 
}
```

### 例 5: Unit Reference (動的な単位の参照)

通常、単位はモデルのメタデータとしてペイロードから除外されますが、`samm-c:UnitReference`特性を使用すると、単位のCURIEがランタイムデータとしてペイロードに含まれます。

#### モデル定義（RDF/Turtle抜粋）
```turtle
...
:ValueWithDynamicUnit a samm:Aspect ; 
    samm:properties ( :value :unit ) . 

:value a samm:Property ; 
    samm:characteristic :FloatValue . 
:FloatValue a samm:Characteristic ; 
    samm:dataType xsd:float . 

:unit a samm:Property ; 
    samm:characteristic samm-c:UnitReference .
```

#### 対応するJSONペイロード（インスタンス）

値と、ユニットカタログ内の単位への参照（CURIE）の両方が含まれます。

```json
{ 
  "value" : 2.25, 
  "unit" : "unit:hectopascal" 
}
```