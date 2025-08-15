<div align="center">

# 🚀 Easy Dataset CLI

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/CLI-Typer-green.svg" alt="CLI Framework">
  <img src="https://img.shields.io/badge/LLM-OpenAI%20%7C%20OpenRouter-orange.svg" alt="LLM Support">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

<p align="center">
  テキストファイルからQ&Aペアを生成するシンプルなCLIツール<br>
  LLMを使用してGenre-Audienceペアに基づいた多様なQ&Aデータセットを作成し、Genre別のXMLファイルとして出力します
</p>

</div>

## ✨ 特徴

- **🎯 シンプル**: データベース不要、マークダウンでGA定義
- **🔄 柔軟**: 複数のGenre-Audienceペアに対応
- **🛡️ 安定**: LLMからの直接XML出力で信頼性向上
- **⚡ 効率的**: テキスト分割とバッチ処理で大きなファイルにも対応

## 📦 インストール

```bash
# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# または
venv\Scripts\activate     # Windows

# 依存関係のインストール
pip install -e .
```

## 🚀 使用方法

### 📋 基本的なワークフロー

1. **GAペア定義ファイルの自動生成**
```bash
# 環境変数にAPIキーを設定
export OPENAI_API_KEY="your-api-key-here"

# 元の文章からGAペア定義を自動生成
uv run easy-dataset create-ga .\example\input\documents\sample_document.txt --output-dir .\example\output\sample_document --num-ga-pairs 10
```

2. **Q&Aペアの生成**
```bash
# GAペア定義を使ってQ&Aペアを生成
uv run easy-dataset generate .\example\input\documents\sample_document.txt --ga-file .\example\output\sample_document\ga\ga_definitions.xml --output-dir .\example\output\sample_document\ --chunk-size 500
```

### 💻 実行例

```powershell
PS C:\Prj\easy-dataset-cli> uv run easy-dataset --help
Usage: easy-dataset [OPTIONS] COMMAND [ARGS]...

テキストファイルからQ&Aペアを生成するシンプルなCLIツール。

╭─ Options ──────────────────────────────────────────────────────────────────╮
│ --install-completion            Install completion for the current shell.  │
│ --show-completion               Show completion for the current shell.      │
│ --help                -h        Show this message and exit.                │
╰────────────────────────────────────────────────────────────────────────────╯

╭─ Commands ─────────────────────────────────────────────────────────────────╮
│ create-ga   元の文章を分析し、GAペア定義をXML形式で生成し、Genreごとに     │
│             マークダウンファイルに保存します。                             │
│ generate    テキストファイルとGA定義からQ&Aペアを生成し、Genre別の        │
│             XMLファイルとして出力します。                                  │
╰────────────────────────────────────────────────────────────────────────────╯

PS C:\Prj\easy-dataset-cli> uv run easy-dataset create-ga .\example\input\documents\sample_document.txt --output-dir .\example\output\sample_document --num-ga-pairs 10
ファイルを読み込んでいます: example\input\documents\sample_document.txt
読み込んだテキスト長: 545 文字
LLMに最適なGAペアを提案させています...
コンテキスト長: 545 文字
LLMレスポンス長: 2534 文字
出力ディレクトリを作成しました: ga/, logs/, qa/
✓ LLMのrawレスポンスを保存しました: example\output\sample_document\logs\raw.md
XMLからGAペアを解析しています...
見つかったPairノード数: 10
✓ 学術論文 x コンピュータサイエンス研究者
✓ 技術ブログ x プログラミング初心者
✓ 教科書 x 大学生
✓ FAQ x 実務開発者
✓ 対話形式の記事 x 中高生
✓ 専門技術書 x データサイエンティスト
✓ ケーススタディ x ITプロジェクトマネージャー
✓ オンラインコース教材 x 社会人学習者
✓ 雑誌記事 x テック愛好者
✓ ワークショップ資料 x 教育者
✓ GA定義XMLファイルを保存しました: example\output\sample_document\ga\ga_definitions.xml
GA定義を保存しました: example\output\sample_document\ga\ga_definitions_学術論文.md
GA定義を保存しました: example\output\sample_document\ga\ga_definitions_技術ブログ.md
GA定義を保存しました: example\output\sample_document\ga\ga_definitions_教科書.md
GA定義を保存しました: example\output\sample_document\ga\ga_definitions_faq.md
GA定義を保存しました: example\output\sample_document\ga\ga_definitions_対話形式の記事.md
GA定義を保存しました: example\output\sample_document\ga\ga_definitions_専門技術書.md
GA定義を保存しました: example\output\sample_document\ga\ga_definitions_ケーススタディ.md
GA定義を保存しました: example\output\sample_document\ga\ga_definitions_オンラインコース教材.md
GA定義を保存しました: example\output\sample_document\ga\ga_definitions_雑誌記事.md
GA定義を保存しました: example\output\sample_document\ga\ga_definitions_ワークショップ資料.md
✓ 10個のGAペアを example\output\sample_document\ga に保存しました。
ヒント: 生成されたファイルをレビューし、必要に応じて編集してから `generate` コマンドで使用してください。

PS C:\Prj\easy-dataset-cli> uv run easy-dataset generate .\example\input\documents\sample_document.txt --ga-file .\example\output\sample_document\ga\ga_definitions.xml --output-dir .\example\output\sample_document\ --chunk-size 500
ファイルを読み込んでいます: example\input\documents\sample_document.txt
GAペアを解析しています: example\output\sample_document\ga\ga_definitions.xml
10 個のGAペアを見つけました。
テキストをチャンクに分割しています...
2 個のチャンクを作成しました。
出力ディレクトリを作成しました: ga/, logs/, qa/
Genre: ワークショップ資料 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00
合計 120 個のQ&Aペアを生成しました。
XMLファイルを example\output\sample_document\qa に保存しています...
- ✓ 学術論文.xml
- ✓ 技術ブログ.xml
- ✓ 教科書.xml
- ✓ FAQ.xml
- ✓ 対話形式の記事.xml
- ✓ 専門技術書.xml
- ✓ ケーススタディ.xml
- ✓ オンラインコース教材.xml
- ✓ 雑誌記事.xml
- ✓ ワークショップ資料.xml
すべてのファイルの保存が完了しました。
```

### ⚙️ コマンドオプション

#### 🔧 create-ga コマンド
```bash
uv run easy-dataset create-ga [OPTIONS] FILE_PATH

Arguments:
  FILE_PATH  GAペアの定義を生成するための元のテキストファイル [required]

Options:
  -o, --output-dir DIRECTORY  生成されたGAペア定義ファイルを保存するディレクトリ [required]
  -m, --model TEXT           GAペア定義の生成に使用するLLMモデル名 [default: openrouter/openai/gpt-4o]
  -g, --num-ga-pairs INTEGER 生成するGAペアの数。指定しない場合はLLMが適切な数を決定します
  -h, --help                 Show this message and exit
```

#### 🔧 generate コマンド
```bash
uv run easy-dataset generate [OPTIONS] FILE_PATH

Arguments:
  FILE_PATH  元のテキストファイルへのパス [required]

Options:
  --ga-file PATH           Genre-Audienceペアを定義したXMLファイル [required]
  -o, --output-dir PATH    XMLファイルの出力ディレクトリ
  -m, --model TEXT         Q&Aペアの生成に使用するLLMモデル [default: openrouter/openai/gpt-4o]
  --chunk-size INTEGER     テキストチャンクの最大サイズ [default: 2000]
  --chunk-overlap INTEGER  チャンク間のオーバーラップサイズ [default: 200]
  -h, --help               Show this message and exit
```

## 📄 GA定義ファイルの形式

`create-ga`コマンドで自動生成されるGA定義ファイルはXML形式で保存されます：

```xml
<?xml version="1.0" encoding="utf-8"?>
<GADefinitions>
  <Pair>
    <Genre>学術論文</Genre>
    <GenreDescription>学術的で厳密な表現を用い、専門用語を正確に使用し、論理的で客観的な回答を提供します。</GenreDescription>
    <Audience>コンピュータサイエンス研究者</Audience>
    <AudienceDescription>コンピュータサイエンス分野の研究者向けに、最新の研究動向や理論的背景を含む専門的な内容を提供します。</AudienceDescription>
  </Pair>
  <Pair>
    <Genre>技術ブログ</Genre>
    <GenreDescription>実践的で親しみやすい表現を用い、具体例やコード例を交えて説明します。</GenreDescription>
    <Audience>プログラミング初心者</Audience>
    <AudienceDescription>プログラミングを学び始めた初心者向けに、基礎的な概念を分かりやすく説明します。</AudienceDescription>
  </Pair>
</GADefinitions>
```

また、各Genre別にマークダウンファイルも生成され、必要に応じて手動で編集できます。

## 📁 出力形式

`generate`コマンドの実行により、各GenreごとにXMLファイルが生成されます：

```xml
<?xml version="1.0" ?>
<QAPairs genre="学術論文">
  <Pair>
    <Audience>コンピュータサイエンス研究者</Audience>
    <Question>Pythonの設計哲学における主要な特徴は何ですか？</Question>
    <Answer>Pythonの設計哲学は「読みやすさ」を重視しており、シンプルで理解しやすい構文が特徴です。</Answer>
  </Pair>
</QAPairs>
```

生成されるファイル構造：
```
output_directory/
├── ga/
│   ├── ga_definitions.xml          # メインのGA定義ファイル
│   ├── ga_definitions_学術論文.md   # Genre別マークダウンファイル
│   ├── ga_definitions_技術ブログ.md
│   └── ...
├── qa/
│   ├── 学術論文.xml                # Genre別Q&Aファイル
│   ├── 技術ブログ.xml
│   └── ...
└── logs/
    └── raw.md                      # LLMの生レスポンス
```

## 🤖 サポートするLLMモデル

### 🔑 OpenAI（直接）
```bash
export OPENAI_API_KEY="sk-..."
easy-dataset generate document.txt -g ga.md -m gpt-4o
```

### 🌐 OpenRouter経由
```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
easy-dataset generate document.txt -g ga.md -m gpt-4o  # 自動でopenai/gpt-4oに変換
easy-dataset generate document.txt -g ga.md -m claude-3-sonnet  # 自動でanthropic/claude-3-sonnetに変換
```

## 📜 ライセンス

MIT License
