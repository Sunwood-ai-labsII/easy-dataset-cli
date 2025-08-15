<div align="center">

![](https://github.com/user-attachments/assets/865632a4-911f-4de4-867d-c65cef365d79)

# 🚀 Easy Dataset CLI

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/CLI-Typer-green.svg" alt="CLI Framework">
  <img src="https://img.shields.io/badge/LLM-OpenAI%20%7C%20OpenRouter-orange.svg" alt="LLM Support">
  <img src="https://img.shields.io/badge/Format-Alpaca%20%7C%20XML-purple.svg" alt="Output Format">
  <img src="https://img.shields.io/badge/🤗-Hugging%20Face-yellow.svg" alt="Hugging Face">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
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

### 🦙 Alpaca形式とHugging Face連携の使用例

#### Alpaca形式での出力
```bash
# Q&A生成と同時にAlpaca形式のJSONファイルを出力
uv run easy-dataset generate .\example\input\documents\sample_document.txt \
  --ga-file .\example\output\sample_document\ga\ga_definitions.xml \
  --output-dir .\example\output\sample_document\ \
  --export-alpaca
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

