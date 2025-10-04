# ツール名: asq (読み方: アスク)

## このツールは何？ (目的)
  * 標準入力 (stdin) から受け取ったプロンプトを **LLM (大規模言語モデル) のAPI**に送信し、その応答を標準出力 (stdout) へ直接出力する。主にパイプ処理やシェルスクリプト内でのLLM活用を目的とする。

-----

## インストール

### 前提条件

  - Python 3.10以上
  - uv pythonパッケージマネージャー
  - 利用するLLMサービスのAPIキーが、環境変数（GOOGLE_API_KEY, OPENAI_API_KEYなど）に設定されていること

### リモートインストール

```bash
# GitHubリポジトリURLは仮のものを使用しています
uv tool install git+https://github.com/mas-matsushitax/asq.git
```

### ローカルインストール

```bash
# GitHubリポジトリURLは仮のものを使用しています
curl -L https://github.com/mas-matsushitax/asq/archive/refs/heads/main.zip --output asq-main.zip
unzip asq-main.zip
uv tool install ./asq-main
```

### pipを使用する場合

```bash
pip install git+https://github.com/mas-matsushitax/asq.git
```

### （参考）asqのアンインストール

```sh
uv tool uninstall asq
```

または

```sh
pip uninstall asq
```

-----

## コマンド仕様

### 基本コマンド:

`asq [arguments] --options`

-----

### 実行

標準入力の内容をプロンプトとしてLLMに送信し、結果を標準出力に出力する。

* **コマンド:** `asq`
* **引数 (Arguments):**
  * なし
* **オプション (Options):**

  * `-m, --model <モデル名>`: (任意) 使用するLLMのモデル名を指定（**デフォルト: gpt-4o-mini**）。LiteLLMがサポートする形式（例: `gpt-4o`, `claude-3-opus`, `gemini/gemini-2.5-pro` など）。

  * `-s, --system <システムプロンプト>`: (任意) LLMに渡す**システムプロンプト**を指定。

  * `-t, --temperature <値>`: (任意) サンプリング温度を指定（デフォルト: `0.7`）。`0.0`～`2.0`の範囲。

  * `-j, --json`: (任意) モデルに応答を **JSON形式**で強制させる（応答形式の指定）。

* **実行例:**
  ```sh
  # 標準入力から受け取った内容をデフォルトモデルで処理
  echo "「Python」の語源について簡潔に説明して" | asq

  # ファイルの内容をプロンプトとして使用し、gpt-4o-miniでJSON応答を取得
  cat requirements.txt | asq -m gpt-4o-mini -j --system "requirements.txtの内容を読み、必要なライブラリとその用途をJSON形式でリストアップしてください。"
  ```

* **仕様:**
  1. **標準入力 (stdin) から全てのデータ**を読み込み、これを**ユーザープロンプト**として設定する。
  2. **LiteLLM**ライブラリを用いてAPIリクエストを行う。
  3. モデル、システムプロンプト、温度、JSONモードの指定はオプションで行う。
  4. **APIキー**は環境変数から自動的に取得する。設定されていない場合はエラーメッセージを標準エラー出力 (stderr) に出力し、**非ゼロの終了コード**で終了する。
  5. LLMからの回答を待っている間は、リクエスト中はスピナーで待ち状態を表現する。
  6. LLMからの最終応答テキストを、ストリーミングではなく、全て受け取った後に**標準出力 (stdout) へ直接出力**する。
  7. LLMからのエラー応答や接続エラーは標準エラー出力（stderr）に出力し、非ゼロの終了コードで終了する。

-----

## 使用技術
  * **環境:** **uv**で環境構築
  * **言語:** **Python 3.10以上**
  * **ライブラリ:**
    * **click**: コマンドラインインターフェースの構築
    * **LiteLLM**: LLMの各種APIを統一的に扱うためのライブラリ
