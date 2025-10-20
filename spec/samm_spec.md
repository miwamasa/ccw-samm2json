Semantic Aspect Meta Model (SAMM)の仕様について、提供された資料に基づき以下に要点をまとめます。SAMMは、Digital TwinのAspect Modelを記述するためのセマンティックなメタモデルです。
1. SAMMの目的と基本的な構造
SAMMの役割
• Semantic Aspect Meta Model (SAMM) は、Aspect Modelを構築するための要素を規定します。
• Digital Twinは、物理的または仮想的なアセット（資産）の一貫したセマンティクスを持つデジタル表現であり、Aspectがその機能を提供します。
• Aspect Model は、Aspectの構造を形式的（機械可読）な形式で記述するモデルです。
• Aspect Modelには、ランタイムデータ構造に関する情報（例：プロパティの名前）と、ランタイムデータの一部ではない情報（例：単位や値の範囲）の両方が含まれます。
• SAMMおよびAspect Modelは、Resource Description Format (RDF) とTerse RDF Triple Language (TTL/Turtle) 構文を使用して指定されます。
モデルファイルの規則
• 各Aspect Modelは、個別のTTL (Turtle) ファイルで定義する必要があります。
• Turtleファイルの名前は、そのファイルに含まれるAspectと同じでなければなりません。
• ファイルはUTF-8でエンコードされている必要があります。
• モデル要素の定義間には、1行の空行を入れるべきです。
2. 主要なメタモデル要素
SAMMは、Aspect Modelを構築するための基本的な構成要素を定義しています。
要素
説明
属性の例
Aspect
各Aspect Modelのルート要素であり、モデルごとに1回だけ出現する必要があります。Properties、Operations、Eventsを持ちます。
samm:properties, samm:operations, samm:events
Property
名前付きの値を表します。1つのPropertyは正確に1つのCharacteristicを持ちます。
samm:characteristic, samm:exampleValue
Characteristic
Propertyの意味を記述します（データ型、コレクション、単位など）。
samm:dataType
Entity
複数の値の論理的なカプセル化であり、Propertiesを持ちます。他のEntityまたはAbstract Entityを拡張できます。
samm:properties, samm:extends
Abstract Entity
共有される概念の論理的なカプセル化であり、直接インスタンス化することはできません。Propertyを共有するために使用されます。
samm:properties
Operation
Aspectに対してトリガーできるアクションを表します。入力Property（複数可）と、最大1つの出力Propertyを持ちます。
samm:input, samm:output
Event
タイミングが重要な単一の発生を表します。パラメータProperty（複数可）を持ちます。
samm:parameters
Constraint
Characteristicに適用される制限（値の範囲や最大長など）を表します。
-
すべてのモデル要素に共通する属性 すべてのモデル要素（Aspect、Property、Characteristic、Entity、Operationなど）は以下の属性を持ちます。
• samm:preferredName: 特定の言語における人間が読める名前。少なくとも1つ、"en"の言語タグ付きで定義されている必要があります。
• samm:description: 特定の言語における人間が読める説明。少なくとも1つ、"en"の言語タグ付きで定義されている必要があります。
• samm:see: 外部の分類法、オントロジー、または標準文書の関連要素への参照（xsd:anyURI型）。
3. 命名規則と識別子
命名規則
• モデル要素の命名は、Javaのクラス、プロパティ、メソッドの命名規則に従います。
• Aspect、Entity、Event、Constraint、Characteristicの名前はUpperCamelCaseに従います。
• Property、Operation、Unitの名前はlowerCamelCaseに従います。
ネームスペースとプレフィックス
• SAMMの要素識別子およびAspect Model要素の識別子は、URN構文（Uniform Resource Name）を使用します。
• Aspect Modelファイルは、SAMMのプレフィックス定義で開始する必要があります。
• **空のネームスペース（:）**は、Aspectとその要素が定義されるバージョン付きのローカルネームスペースとして使用されるべきです。
• SAMMメタモデルで使用される予約済みのプレフィックスとURNの一部を以下に示します。
    ◦ samm:: urn:samm:org.eclipse.esmf.samm:meta-model:2.2.0#
    ◦ samm-c:: urn:samm:org.eclipse.esmf.samm:characteristic:2.2.0#
    ◦ samm-e:: urn:samm:org.eclipse.esmf.samm:entity:2.2.0#
    ◦ unit:: urn:samm:org.eclipse.esmf.samm:unit:2.2.0#
    ◦ xsd:: http://www.w3.org/2001/XMLSchema#
4. Characteristicsと制約
Characteristicは、Propertyにセマンティクス（意味）を付与するための重要な要素です。
4.1. 主要なCharacteristicクラス
Characteristicクラスは抽象的な概念を記述し、使用時にインスタンス化が必要です。
• Measurement / Quantifiable: 測定値または定量化可能な値を表し、samm-c:unit 属性を使用して単位カタログで定義された単位を参照します。
• Enumeration: 可能な値のリストを表します。samm-c:valuesで可能な値をリストします。
• State: Enumerationのサブクラスで、samm-c:defaultValue属性によりデフォルト値を指定できます。
• Collection (List, Set, Sorted Set): 値のグループを表します。Listは順序があり重複を許容し、Setは順序がなく重複を許容せず、SortedSetは順序があり重複を許容しません。
• TimeSeries: 記録された正確な時点を持つ値を含む SortedSet の特殊なサブクラスです。
• Either: Propertyの値が2つの可能な型（非連結和）のいずれかを持てることを記述します。samm-c:leftとsamm-c:rightでそれぞれCharacteristicを参照します。
• StructuredValue: スカラー文字列様の値空間を持ち、明確な構造を持つPropertyを記述します。正規表現（samm-c:deconstructionRule）で値を部分に分解し、samm-c:elementsで各部分をPropertyにリンクします。
• Single Entity: データ型がEntityであるPropertyを記述します。
4.2. 制約（Constraints）
制約は、Trait (samm-c:Trait) を使用してベースCharacteristicに追加されます。
• Range Constraint: Propertyの値の範囲を制限します。数値型および日時型のデータ型に適用できます。samm-c:maxValueまたはsamm-c:minValueの少なくとも一方が必要です。
• Length Constraint: 文字列様の値空間の長さ、またはコレクションの要素数を制限します。xsd:nonNegativeIntegerとしてsamm-c:maxValueまたはsamm-c:minValueの少なくとも一方が必要です。
• Regular Expression Constraint: 文字列値を正規表現に制限します。
• Encoding Constraint: Propertyのエンコーディングを制限します（例：samm:US-ASCII、samm:UTF-8）。
5. データ型とJSONマッピング
データ型 SAMMで許容されるデータ型は、XML Schema Definition 1.1 (XSD) のサブセットと、RDF仕様の rdf:langString に基づいています。
• スカラー型: samm:Entity 以外のすべてのデータ型はスカラー型です。
• 主要なデータ型: xsd:string, xsd:boolean, xsd:decimal, 各種整数型（xsd:int, xsd:longなど）, 浮動小数点数型（xsd:float, xsd:double）, 日時型（xsd:date, xsd:dateTime）, バイナリデータ型, xsd:anyURI, samm:curie, rdf:langString などが含まれます。
• rdf:langString は明示的な言語タグを持つ文字列を表し、ローカライズされたテキストに使用されます。
JSONペイロードへのマッピング Aspect ModelのランタイムデータはJSONペイロードとしてシリアル化されます。
• Aspect Modelは、名前のないJSONオブジェクトとしてシリアル化されます。
• データ型マッピングの概要:
    ◦ XSDブール値はJSONブール値にマップされます。
    ◦ すべての数値型（整数、浮動小数点数、xsd:decimalなど）はJSONの数値にマップされます。
    ◦ EntityはJSONオブジェクトにマップされます。
    ◦ 日付/時刻、xsd:anyURI、samm:curieなどの他のスカラー型は、JSON文字列にマップされます。
    ◦ rdf:langStringを持つPropertyは、言語タグをキーとし、ローカライズされた文字列を値とする名前付きJSONオブジェクトとしてシリアル化されます。
• コレクション: PropertyのCharacteristicが Collection, List, Set, または Sorted Set の場合、名前付きJSON配列としてシリアル化されます。
• samm:optional: Propertyがオプショナルとしてマークされている場合、ペイロードに含まれないか、または値が null になる可能性があります。
• samm:payloadName: PropertyがAspectまたはEntityで使用される際、ランタイムペイロードでのキー名を定義できます。
• ペイロードに含まれない要素: Characteristic、Constraint、Operation、Eventは、ランタイムペイロードのシリアル化の対象外です。
6. 事前定義されたEntity
SAMMメタモデルのスコープで定義されている一般的に適用可能なEntityがあります。
• TimeSeriesEntity (samm-e:TimeSeriesEntity): Time Series Characteristicとともに使用され、特定の時点での値を表現するために、timestamp（Timestamp Characteristicを持つ）と value（Abstract Property）の2つのPropertyをラップします。
• Quantity Entity (samm-e:Quantity): 数値とそれに対応する物理単位を表します。value（Abstract Property）と unit（Unit Reference Characteristicを持つ）という2つのPropertyを持ちます。
• Point 3D (samm-e:Point3d): $\text{R}^3$空間の点を記述します。3つのAbstract Property (x, y, z) を持ちます。
• File Resource (samm-e:FileResource): 相対的または絶対的なロケーションとMIMEタイプを持つリソースを記述します。
