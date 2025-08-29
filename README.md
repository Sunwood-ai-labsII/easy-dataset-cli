<div align="center">

![](https://github.com/user-attachments/assets/865632a4-911f-4de4-867d-c65cef365d79)

# 🚀 Easy Dataset CLI

<p align="center">

  ![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)
  ![CLI Framework](https://img.shields.io/badge/CLI-Typer-green.svg)
  ![LLM Support](https://img.shields.io/badge/LLM-OpenAI%20%7C%20OpenRouter-orange.svg)
  ![Output Format](https://img.shields.io/badge/Format-Alpaca%20%7C%20XML-purple.svg)
  ![Hugging Face](https://img.shields.io/badge/🤗-Hugging%20Face-yellow.svg)
  ![License](https://img.shields.io/badge/License-MIT-green.svg)
  
</p>

<p align="center">
  テキストファイルからQ&Aペアを生成するシンプルなCLIツール<br>
  LLMを使用してGenre-Audienceペアに基づいた多様なQ&Aデータセットを作成し、<br>
  <strong>Alpaca形式JSON</strong>やGenre別XMLファイルとして出力、<strong>Hugging Face Hub</strong>への直接アップロードも対応
</p>

</div>

## ✨ 特徴

- **🎯 シンプル**: データベース不要、マークダウンでGA定義
- **🔄 柔軟**: 複数のGenre-Audienceペアに対応
- **🛡️ 安定**: LLMからの直接XML出力で信頼性向上
- **⚡ 効率的**: テキスト分割とバッチ処理で大きなファイルにも対応
- **🦙 Alpaca対応**: 生成されたQ&AペアをAlpaca形式のJSONで出力
- **🤗 HF統合**: Hugging Face Hubへの直接アップロード機能
- **📊 データセットカード**: 自動的なREADME.md生成でデータセット情報を整理
- **🔄 変換機能**: 既存XMLファイルからAlpaca形式への変換コマンド
- **🔍 自動GA検出**: バッチ処理時に各ファイルに対応するGA定義を自動検出
- **📁 バッチ処理強化**: 複数ファイルの同時処理と個別出力対応
- **🌐 周辺コンテキストモード**: チャンク前後のチャンクをコンテキストとして活用し、文脈理解を向上
- **📌 ドキュメント冒頭活用**: 周辺コンテキスト使用時、ドキュメントの冒頭3000文字を常に付与して文脈の安定性を向上

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

# 元の文章からGAペア定義を自動生成（デフォルト: 8000文字まで使用）
uv run easy-dataset create-ga ./example/input/documents/sample_document.txt --output-dir ./example/output/sample_document --num-ga-pairs 2

# より大きなファイルの場合、コンテキストを制限して処理時間を短くする
uv run easy-dataset create-ga ./large_document.txt --output-dir ./output --num-ga-pairs 3 --max-context-length 4000

# フォルダ内の全ファイルに対してGAペアをバッチ生成
uv run easy-dataset create-ga ./example/input/documents/ --output-dir ./example/output/batch_ga_output --num-ga-pairs 2 --max-context-length 6000
```

2. **Q&Aペアの生成**

#### 単一ファイルの場合
```bash
# GAペア定義を使ってQ&Aペアを生成
uv run easy-dataset generate ./example/input/documents/sample_document.txt --ga-file ./example/output/sample_document/ga/ga_definitions.xml --output-dir ./example/output/sample_document/ --chunk-size 2000
```

#### 複数ファイル（バッチ処理）の場合
```bash
# 複数のテキストファイルをバッチ処理
uv run easy-dataset generate ./example/input/documents/ --ga-file ./example/output/sample_document/ga/ga_definitions.xml --output-dir ./example/output/batch_output/ --chunk-size 2000 --use-surrounding-context 
```

#### 自動GA検出機能を使用したバッチ処理
```bash
# 各ファイルに対応するGA定義を自動検出してバッチ処理
uv run easy-dataset generate ./example/input/documents/ --ga-base-dir ./example/output/batch_ga_output/ --output-dir ./example/output/batch_qa_output/ --chunk-size 2000 --use-surrounding-context 
```

### 🦙 Alpaca形式とHugging Face連携の使用例

#### Alpaca形式での出力
```bash
# Q&A生成と同時にAlpaca形式のJSONファイルを出力
uv run easy-dataset generate .\example\input\documents\sample_document.txt \
  --ga-file .\example\output\sample_document\ga\ga_definitions.xml \
  --output-dir .\example\output\sample_document\ \
  --export-alpaca
```

#### 思考フロー付きQ&Aの生成
```bash
# 思考フローを含むQ&Aペアを生成
uv run easy-dataset generate .\example\input\documents\sample_document.txt \
  --ga-file .\example\output\sample_document\ga\ga_definitions.xml \
  --output-dir .\example\output\sample_document\ \
  --use-thinking

# 思考フローと全文コンテキストを併用して生成
uv run easy-dataset generate .\example\input\documents\sample_document.txt \
  --ga-file .\example\output\sample_document\ga\ga_definitions.xml \
  --output-dir .\example\output\sample_document\ \
  --use-thinking \
  --use-fulltext

# 周辺チャンクモードを使ったQ&A生成
uv run easy-dataset generate .\example\input\documents\sample_document.txt \
  --ga-file .\example\output\sample_document\ga\ga_definitions.xml \
  --output-dir .\example\output\sample_document\ \
  --use-surrounding-context \
  --context-before 1 \
  --context-after 2
```

#### Hugging Face Hubへの直接アップロード
```bash
# 環境変数でトークンを設定
set HUGGINGFACE_TOKEN=hf_your_token_here

# データセット生成とHugging Face Hubアップロードを一度に実行
uv run easy-dataset generate .\example\input\documents\sample_document.txt \
  --ga-file .\example\output\sample_document\ga\ga_definitions.xml \
  --output-dir .\example\output\sample_document\ \
  --export-alpaca \
  --upload-hf \
  --hf-repo-name username/my-qa-dataset
```

#### 既存XMLファイルの変換とアップロード
```bash
# 既存のXMLファイルをAlpaca形式に変換してHugging Face Hubにアップロード
uv run easy-dataset convert-to-alpaca .\example\output\sample_document\qa \
  --output-file dataset.json \
  --upload-hf \
  --hf-repo-name username/my-qa-dataset \
  --hf-private
```

### ⚙️ コマンドオプション

#### 🔧 create-ga コマンド
```bash
uv run easy-dataset create-ga [OPTIONS] FILE_PATH

Arguments:
  FILE_PATH  GAペアの定義を生成するための元のテキストファイルまたはフォルダ [required]

Options:
  -o, --output-dir DIRECTORY        生成されたGAペア定義ファイルを保存するディレクトリ [required]
  -m, --model TEXT                 GAペア定義の生成に使用するLLMモデル名 [default: openrouter/openai/gpt-oss-120b]
  -g, --num-ga-pairs INTEGER       生成するGAペアの数。指定しない場合はLLMが適切な数を決定します
  -l, --max-context-length INTEGER GA生成時にLLMに渡すコンテキストの最大文字数[default: 8000]
  -h, --help                       Show this message and exit
```

#### 🔧 generate コマンド
```bash
uv run easy-dataset generate [OPTIONS] FILE_PATH

Arguments:
  FILE_PATH  元のテキストファイルへのパス [required]

Options:
  --ga-file PATH           Genre-Audienceペアを定義したXMLファイル。バッチ処理で全ファイルに共通の定義を適用する場合に使用します。
  --ga-base-dir PATH       GA定義フォルダの親ディレクトリ。バッチ処理時に各入力ファイルに対応するGA定義を自動検出する場合に使用します。
  -o, --output-dir PATH    XMLファイルの出力ディレクトリ
  -m, --model TEXT         Q&Aペアの生成に使用するLLMモデル [default: openrouter/openai/gpt-4o]
  --chunk-size INTEGER     テキストチャンクの最大サイズ [default: 2000]
  --chunk-overlap INTEGER  チャンク間のオーバーラップサイズ [default: 200]
  -f, --use-fulltext       全文をコンテキストとして含めてQA生成を行います。より文脈を理解したQAが生成されますが、処理時間とコストが増加します。
  -T, --use-thinking       各Q&Aペアに思考プロセスを追加して生成します。より深い理解と説明が可能になりますが、処理時間とコストが増加します。
  -S, --use-surrounding-context 各チャンクの前後チャンクをコンテキストとして含めてQA生成を行います。より文脈を理解したQAが生成されますが、処理時間とコストが増加します。
  --context-before INTEGER 周辺コンテキストとして含める前方チャンク数 [default: 1]
  --context-after INTEGER  周辺コンテキストとして含める後方チャンク数 [default: 1]
  -h, --help               Show this message and exit
```

#### 🔗 周辺コンテキストモード（`--use-surrounding-context`オプション）

`--use-surrounding-context`オプションを使用すると、各チャンクの前後チャンクをコンテキストとして含めることで、より文脈を理解した高品質なQ&Aペアを生成できます。`--use-fulltext`よりも処理コストが低く抑えられます。

- **`--context-before INTEGER`**: 前方のコンテキストとして含めるチャンク数（デフォルト: 1）
- **`--context-after INTEGER`**: 後方のコンテキストとして含めるチャンク数（デフォルト: 1）

追加の仕様（v0.2.x以降）:
- **ドキュメント冒頭を自動付与**: 周辺コンテキストモード有効時は、各プロンプトの先頭にドキュメントの冒頭3000文字が自動的に付与されます。
  - 目的: 各チャンクの前後だけでは文脈が曖昧になるケースを防ぎ、全体のトピックや用語の基調を共有するため
  - 上限: 3000文字（固定）
  - コスト: プロンプト長が増えるため、わずかにトークン消費が増加します

**使用例:**
```bash
# 各チャンクの前後1チャンクずつをコンテキストとして使用
uv run easy-dataset generate document.txt \
  --ga-file ga_definitions.xml \
  --use-surrounding-context

# 前2チャンク、後1チャンクをコンテキストとして使用
uv run easy-dataset generate document.txt \
  --ga-file ga_definitions.xml \
  --use-surrounding-context \
  --context-before 2 \
  --context-after 1
```

このモードは、長いドキュメントにおいて各チャンクの意味を理解するのに役立ち、トークンサイズ制限を回避しつつ文脈理解を向上させます。
加えて、ドキュメント冒頭（最大3000文字）を毎回付与することで、用語や話題の基調が共有され、質問・回答の一貫性が高まります。

#### 📝 GA定義ファイルの自動検出機能

`--ga-base-dir`オプションを使用すると、バッチ処理時に各入力ファイルに対応するGA定義ファイルを自動的に検出して使用します。

**動作仕様:**
- 入力ディレクトリ内の各テキストファイル（例: `doc_A.txt`）の名前を取得
- `--ga-base-dir`で指定されたパスとファイル名を組み合わせて対応するGA定義ファイルのパスを自動生成（例: `<ga-base-dir>/doc_A/ga/ga_definitions.xml`）
- そのGA定義ファイルを使って該当ファイルのQ&A生成を行う
- 入力ディレクトリ内のすべてのファイルに対して上記処理を繰り返す

**使用例:**
```bash
# 各ファイルに対応するGA定義を自動検出してバッチ処理
uv run easy-dataset generate ./example/input/documents/ \
  --ga-base-dir ./example/output/batch_ga_output/ \
  --output-dir ./example/output/batch_qa_output/
```

**ディレクトリ構造の例:**
```
example/
├── input/documents/
│   ├── doc_A.txt
│   ├── doc_B.txt
│   └── doc_C.txt
├── output/batch_ga_output/
│   ├── doc_A/
│   │   └── ga/
│   │       └── ga_definitions.xml
│   ├── doc_B/
│   │   └── ga/
│   │       └── ga_definitions.xml
│   └── doc_C/
│       └── ga/
│           └── ga_definitions.xml
└── output/batch_qa_output/
    ├── doc_A/
    │   ├── ga/
    │   ├── logs/
    │   └── qa/
    ├── doc_B/
    │   ├── ga/
    │   ├── logs/
    │   └── qa/
    └── doc_C/
        ├── ga/
        ├── logs/
        └── qa/
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

### 📄 XML形式（デフォルト）

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

### 🦙 Alpaca形式（`--export-alpaca`オプション）

`--export-alpaca`オプションを使用すると、機械学習で広く使用されるAlpaca形式のJSONファイルが生成されます：

```json
[
  {
    "instruction": "Pythonの設計哲学における主要な特徴は何ですか？",
    "input": "",
    "output": "Pythonの設計哲学は「読みやすさ」を重視しており、シンプルで理解しやすい構文が特徴です。",
    "genre": "学術論文",
    "audience": "コンピュータサイエンス研究者"
  },
  {
    "instruction": "Pythonのインタープリター型言語としての利点は何ですか？",
    "input": "",
    "output": "インタープリター型のため、コンパイル不要で即座にコードを実行でき、開発サイクルが高速化されます。",
    "genre": "技術ブログ",
    "audience": "プログラミング初心者"
  }
]
```

### 📊 自動生成されるデータセットカード

Alpaca形式で出力する際、以下の情報を含むREADME.mdが自動生成されます：

- **データセット概要**: エントリ数、形式、言語、ライセンス
- **ジャンル分布**: 含まれるすべてのジャンルのリスト
- **対象読者分布**: 含まれるすべての対象読者のリスト
- **使用方法**: Hugging Face Datasetsでの読み込み例
- **メタデータ**: Hugging Face Hub用のYAMLフロントマター

### 📁 生成されるファイル構造

#### 単一ファイル処理の場合

```
output_directory/
├── ga/
│   ├── ga_definitions.xml          # メインのGA定義ファイル
│   ├── ga_definitions_学術論文.md   # Genre別マークダウンファイル
│   ├── ga_definitions_技術ブログ.md
│   └── ...
├── qa/
│   ├── 学術論文.xml                # Genre別Q&AファイルXML形式）
│   ├── 技術ブログ.xml
│   └── ...
├── logs/
│   └── raw.md                      # LLMの生レスポンス
├── dataset_alpaca.json             # 🦙 Alpaca形式のデータセット（--export-alpacaオプション使用時）
└── README.md                       # 📊 データセットカード（--export-alpacaオプション使用時）
```

#### バッチ処理の場合（--ga-fileオプション使用）

```
output_directory/
├── doc_A/                          # 各入力ファイル用フォルダ
│   ├── ga/
│   ├── qa/
│   ├── logs/
│   ├── dataset_alpaca.json         # Alpaca形式（--export-alpaca使用時）
│   └── README.md                   # データセットカード（--export-alpaca使用時）
├── doc_B/
│   ├── ga/
│   ├── qa/
│   ├── logs/
│   ├── dataset_alpaca.json
│   └── README.md
└── doc_C/
    ├── ga/
    ├── qa/
    ├── logs/
    ├── dataset_alpaca.json
    └── README.md
```

#### バッチ処理の場合（--ga-base-dirオプション使用）

```
output_directory/
├── doc_A/                          # 各入力ファイル用フォルダ
│   ├── ga/                         # 空のフォルダ（GA定義は自動検出）
│   ├── qa/
│   ├── logs/
│   ├── dataset_alpaca.json         # Alpaca形式（--export-alpaca使用時）
│   └── README.md                   # データセットカード（--export-alpaca使用時）
├── doc_B/
│   ├── ga/
│   ├── qa/
│   ├── logs/
│   ├── dataset_alpaca.json
│   └── README.md
└── doc_C/
    ├── ga/
    ├── qa/
    ├── logs/
    ├── dataset_alpaca.json
    └── README.md

# GA定義ファイルは以下のパスから自動検出されます
# <ga-base-dir>/doc_A/ga/ga_definitions.xml
# <ga-base-dir>/doc_B/ga/ga_definitions.xml
# <ga-base-dir>/doc_C/ga/ga_definitions.xml
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

## 🤗 Hugging Face Hub統合

### 🔑 環境変数の設定

```bash
# Windows (cmd)
set HUGGINGFACE_TOKEN=hf_your_token_here

# Windows (PowerShell)
$env:HUGGINGFACE_TOKEN="hf_your_token_here"

# Linux/macOS
export HUGGINGFACE_TOKEN="hf_your_token_here"
```

### 📤 データセットのアップロード

```bash
# 生成と同時にHugging Face Hubにアップロード
uv run easy-dataset generate document.txt \
  --ga-file ga.xml \
  --export-alpaca \
  --upload-hf \
  --hf-repo-name username/my-dataset

# 既存XMLファイルを変換してアップロード
uv run easy-dataset convert-to-alpaca ./qa_directory \
  --upload-hf \
  --hf-repo-name username/my-dataset \
  --hf-private  # プライベートリポジトリとして作成
```

### 📥 アップロード後の使用方法

```python
from datasets import load_dataset

# Hugging Face Hubからデータセットを読み込み
dataset = load_dataset("username/my-dataset")

# データセットの内容を確認
print(dataset['train'][0])
# {
#   'instruction': 'Pythonの設計哲学における主要な特徴は何ですか？',
#   'input': '',
#   'output': 'Pythonの設計哲学は「読みやすさ」を重視しており...',
#   'genre': '学術論文',
#   'audience': 'コンピュータサイエンス研究者'
# }

# ファインチューニング用のデータ準備
def format_instruction(example):
    return f"### 指示:\n{example['instruction']}\n\n### 回答:\n{example['output']}"

formatted_dataset = dataset.map(lambda x: {"text": format_instruction(x)})
```

### 📊 自動生成されるデータセットカードの例

アップロード時に自動生成されるREADME.mdには以下の情報が含まれます：

```yaml
---
license: mit
task_categories:
- question-answering
- text-generation
language:
- ja
tags:
- alpaca
- qa
- japanese
size_categories:
- n<1K  # データ量に応じて自動設定
---
```

- **データセット概要**: エントリ数、形式、言語、ライセンス
- **ジャンル・対象読者分布**: 含まれるすべてのカテゴリ
- **使用方法**: Hugging Face Datasetsでの読み込み例
- **生成ツール情報**: easy-dataset-cliへのリンク

## 📜 ライセンス

MIT License

## 🔗 参考情報

本プロジェクトは以下のOSSと論文を参考に開発されています：

### 📦 参考OSS
- **[Easy Dataset](https://github.com/ConardLi/easy-dataset)**

### 📄 参考論文
- **[Dataset Generation for Instruction Tuning](https://arxiv.org/html/2507.04009v1)**
