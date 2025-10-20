ご質問ありがとうございます。SAMM（Semantic Aspect Meta Model）に基づくインスタンスのシリアライズについて、「通常のJSONペイロード」の仕様、および、AAS（Asset Administration Shell）のJSON仕様について、ソースに基づきご説明します。

**重要な注意点:** 提供されたソースは、**SAMMとそれに対応する標準的なJSONペイロードへのマッピング**に焦点を当てています。ソースには、**AAS (Asset Administration Shell) のJSONシリアライズ仕様に関する具体的な情報やマッピングルールは含まれていません**。したがって、AAS JSONについては、SAMM標準JSONペイロードとの関連性についてのみ言及し、仕様の作成はできません。

---

## 1. SAMMに基づく通常のJSONペイロード仕様

SAMMは、ランタイムデータ構造に関する情報と、ランタイムデータには含まれない情報（単位や値の範囲など）の両方を含むアスペクトモデルを定義するために使用されます。アスペクトモデルに準拠するアスペクトが提供する実際のランタイムデータは、以下のルールに従ってJSONペイロードとして構築されます。

### A. ペイロードの構造と一般的なルール

| 要素 | 仕様 | 参照 |
| :--- | :--- | :--- |
| **全体構造** | アスペクトモデルは、名前のないJSONオブジェクトとしてシリアライズされます。 | |
| **プロパティ名** | JSONオブジェクトのキーは、通常、プロパティのローカル名が使用されます。ただし、`samm:payloadName`属性が定義されている場合、その値がランタイムペイロードのキーとして使用されます。 | |
| **オプショナルなプロパティ** | `samm:optional true`としてマークされたプロパティは、ペイロードに含めても省略しても構いません。ペイロードに含まれる場合、その値は`null`になることが許容され、これはプロパティが省略された場合と同等に扱われます。`samm:optional false`を記述することは許可されていません。 | |
| **ペイロードに含まれない要素** | アスペクトモデルで定義されたCharacteristic（特性）、Operation（操作）、Event（イベント）は、JSONランタイムペイロードのシリアライズの対象外です。 | |

### B. データタイプのマッピング

SAMMで利用される豊富なXSD（XML Schema Definition）ベースのデータタイプは、JSONの限られたプリミティブタイプにマッピングされます。

| アスペクトモデルのデータタイプ (XSD/RDF) | 対応するJSONデータタイプ | 参照 |
| :--- | :--- | :--- |
| `xsd:boolean` | Boolean (`true`, `false`) | |
| `xsd:decimal`, `xsd:integer`, `xsd:float`, `xsd:double`など、すべての数値型 | **Number** | |
| `xsd:string`, `xsd:date`, `xsd:time`, `xsd:dateTime`など、日付/時刻型やURI型 (`xsd:anyURI`)、バイナリ型 (`xsd:hexBinary`)、CURIE (`samm:curie`) | **String** | |
| `rdf:langString` (多言語テキスト) | **JSON Object** (言語タグをキーとする) | |
| **Entity** (`samm:Entity`) | **JSON Object** (再帰的にシリアライズされる) | |

**【数値型の制限】**
JSONでの数値表現には制限があるため、**2⁵³-1**（JavaScriptの`Number.MAX_SAFE_INTEGER`）を超える整数値は、SAMMのデータタイプがそれを許可していたとしても、精度を失うことなく使用することはできません。これは、`xsd:integer`、`xsd:decimal`、`xsd:unsignedLong`などの非有界な数値型に影響します。

### C. 特定の特性（Characteristic）のマッピング

| 特性の種類 | 仕様 | 例示されるペイロード構造 | 参照 |
| :--- | :--- | :--- | :--- |
| **Entity / 複合型** | Propertyの有効なデータタイプがスカラーではない場合（Entityの場合）、プロパティ名はJSONオブジェクトのキーとなり、値は再帰的に同じルールを使用してシリアライズされます。Entityが他のEntityを拡張している場合 (`samm:extends`)、継承されたすべてのプロパティが含まれます。 | `{ "entityName": { "propertyA": value, "propertyB": value } }` | |
| **コレクション** (`Collection`, `List`, `Set`, `Sorted Set`, `TimeSeries`) | PropertyのCharacteristicがコレクションの場合、プロパティ名はJSON配列のキーとなり、値はJSON配列としてシリアライズされます。 | `{ "listName": [ element1, element2 ] }` | |
| **多言語テキスト** (`samm-c:MultiLanguageText`, `rdf:langString`) | 言語タグごとの値を持つJSONオブジェクトとしてシリアライズされます。 | `{ "text": { "en": "English string", "de": "German string" } }` | |
| **ユニット参照** (`samm-c:UnitReference`) | ペイロードには、Unitカタログ内のユニットへの参照として、その**CURIE**が文字列で含まれます。 | `{ "unit": "unit:hectopascal" }` | |
| **Either** (`samm-c:Either`) | 値は、厳密に**`left`または`right`のいずれか一方のキーを持つJSONオブジェクト**としてシリアライズされます。その値のデータタイプは、参照されている特性の有効なデータタイプに従います。 | **成功時:** `{ "result": { "right": 60 } }` **エラー時:** `{ "result": { "left": { "errorCode": "...", "errorDescription": "..." } } }` | |

---

## 2. AAS (Asset Administration Shell) JSON仕様について

提供されたソースには、**AAS JSONシリアライズの具体的な仕様に関する情報は含まれていません**。

ソースは、SAMMがデジタルトイン（Digital Twin）の側面（Aspects）の機能とデータのセマンティクスを記述するために使用されるメタモデルであることを示しており、デジタルトインシステムが生産およびロジスティクスの包括的なデジタル化の基盤を形成するとしています。

SAMMは、アスペクトモデルに準拠したランタイムデータ構造（ペイロード）を定義し、JSONへのマッピングルールを提供しますが、このマッピングが直接AAS標準で要求される特定のJSON構造（例：サブモデル要素やメタデータを含む構造）にどのように適合するかについては、この資料セットでは説明されていません。

したがって、AAS JSONの仕様を作成するには、SAMMのJSONペイロード（上記1.で定義）をAASの構造にどのようにラップするかを定義する、**外部のAAS固有のマッピング仕様**が必要となりますが、それは提供されたソースの範囲外です。