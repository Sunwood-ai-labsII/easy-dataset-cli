# Easy Dataset CLI

テキストファイルからQ&Aペアを生成するシンプルなCLIツールです。LLMを使用してGenre-Audienceペアに基づいた多様なQ&Aデータセットを作成し、Genre別のXMLファイルとして出力します。

## 特徴

- **シンプル**: データベース不要、マークダウンでGA定義
- **柔軟**: 複数のGenre-Audienceペアに対応
- **安定**: LLMからの直接XML出力で信頼性向上
- **効率的**: テキスト分割とバッチ処理で大きなファイルにも対応

## インストール

```bash
# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# または
venv\Scripts\activate     # Windows

# 依存関係のインストール
pip install -e .
```

## 使用方法

### 新しいワークフロー（推奨）

1. **GAペア定義ファイルの自動生成**
```bash
# 環境変数にAPIキーを設定
export OPENAI_API_KEY="your-api-key-here"

# 元の文章からGAペア定義を自動生成
easy-dataset create-ga sample_document.txt --output ga-definitions.md
```

2. **（任意）生成されたGA定義のレビュー・編集**
```bash
# テキストエディタで内容を確認・修正
notepad ga-definitions.md  # Windows
# または
nano ga-definitions.md     # Linux/macOS
```

3. **Q&Aペアの生成**
```bash
# GAペア定義を使ってQ&Aペアを生成
easy-dataset generate sample_document.txt --ga-file ga-definitions.md --output-dir ./results
```

### 従来の方法（手動でGA定義を作成）

```bash
# 手動で作成したGA定義ファイルを使用
easy-dataset generate sample_document.txt --ga-file sample_ga_definition.md --output-dir ./results
```

### コマンドオプション

#### create-ga コマンド
```bash
easy-dataset create-ga [OPTIONS] FILE_PATH

Arguments:
  FILE_PATH  GAペアの定義を生成するための元のテキストファイル

Options:
  -o, --output PATH    生成されたGAペア定義を保存するファイルパス [required]
  -m, --model TEXT     GAペア定義の生成に使用するLLMモデル [default: gpt-4o]
  -h, --help           ヘルプを表示
```

#### generate コマンド
```bash
easy-dataset generate [OPTIONS] FILE_PATH

Arguments:
  FILE_PATH  元のテキストファイルへのパス

Options:
  -g, --ga-file PATH        Genre-Audienceペアを定義したMarkdownファイル [required]
  -o, --output-dir PATH     XMLファイルの出力ディレクトリ（省略時はコンソール出力）
  -m, --model TEXT          Q&Aペアの生成に使用するLLMモデル [default: gpt-4o]
  --chunk-size INTEGER      テキストチャンクの最大サイズ [default: 2000]
  --chunk-overlap INTEGER   チャンク間のオーバーラップサイズ [default: 200]
  -h, --help                ヘルプを表示
```

## GA定義ファイルの形式

Genre-Audienceペアをマークダウン形式で定義します：

```markdown
# Genre: 学術論文
学術的で厳密な表現を用い、専門用語を正確に使用し、論理的で客観的な回答を提供します。

# Audience: 大学生
大学レベルの知識を持つ学習者向けに、基礎概念から応用まで段階的に説明します。

---

# Genre: 技術ブログ
実践的で親しみやすい表現を用い、具体例やコード例を交えて説明します。

# Audience: エンジニア
実務経験のある開発者向けに、実装の詳細や最適化のポイントを重視した内容を提供します。
```

## 出力形式

各GenreごとにXMLファイルが生成されます：

```xml
<?xml version="1.0" ?>
<QAPairs genre="学術論文">
  <Pair>
    <Audience>大学生</Audience>
    <Question>Pythonの設計哲学における主要な特徴は何ですか？</Question>
    <Answer>Pythonの設計哲学は「読みやすさ」を重視しており、シンプルで理解しやすい構文が特徴です。</Answer>
  </Pair>
</QAPairs>
```

## サポートするLLMモデル

### OpenAI（直接）
```bash
export OPENAI_API_KEY="sk-..."
easy-dataset generate document.txt -g ga.md -m gpt-4o
```

### OpenRouter経由
```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
easy-dataset generate document.txt -g ga.md -m gpt-4o  # 自動でopenai/gpt-4oに変換
easy-dataset generate document.txt -g ga.md -m claude-3-sonnet  # 自動でanthropic/claude-3-sonnetに変換
```

### その他のプロバイダー
- Anthropic: `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku`
- Ollama: `ollama/llama3`, `ollama/mistral`
- その他litellmがサポートするすべてのモデル

### 推奨モデル
- **高品質**: `gpt-4o`, `claude-3-opus`
- **バランス**: `gpt-4`, `claude-3-sonnet`
- **高速**: `gpt-3.5-turbo`, `claude-3-haiku`

## ライセンス

MIT License