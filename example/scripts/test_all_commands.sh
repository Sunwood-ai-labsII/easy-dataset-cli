#!/bin/bash

# =============================================================================
# Easy Dataset CLI - 実行テストスクリプト
# =============================================================================

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# テスト用設定
INPUT_FILE="./example/input/documents/sample_document.txt"
SHORT_FILE="./example/input/documents/test_short.md"
OUTPUT_DIR="./test_output"

print_step() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
}

run_command() {
    echo -e "\n${PURPLE}実行中: $1${NC}"
    eval "$1"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 成功${NC}"
    else
        echo -e "${RED}✗ 失敗${NC}"
        echo "エラーが発生しました。続行しますか? [y/N]"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 準備
print_step "準備: 出力ディレクトリの作成"
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"
echo -e "${GREEN}出力ディレクトリを作成しました: $OUTPUT_DIR${NC}"

# 1. ヘルプコマンドの確認
print_step "1. ヘルプコマンドの確認"
run_command "uv run easy-dataset --help"

# 2. create-ga コマンドのテスト
print_step "2. GA定義ファイルの生成"
run_command "uv run easy-dataset create-ga '$INPUT_FILE' --output-dir '$OUTPUT_DIR'"

echo -e "\n${CYAN}生成されたGA定義ファイルを確認:${NC}"
if [ -f "$OUTPUT_DIR/ga/ga_definitions.xml" ]; then
    echo -e "${GREEN}✓ GA定義ファイルが生成されました${NC}"
    echo "最初の20行を表示:"
    head -20 "$OUTPUT_DIR/ga/ga_definitions.xml"
else
    echo -e "${RED}✗ GA定義ファイルが見つかりません${NC}"
fi

# 3. generate コマンドのテスト（基本）
print_step "3. Q&A生成（基本モード）"
run_command "uv run easy-dataset generate '$INPUT_FILE' --ga-file '$OUTPUT_DIR/ga/ga_definitions.xml' --output-dir '$OUTPUT_DIR/qa_basic' --num-qa-pairs 2"

echo -e "\n${CYAN}生成されたQ&Aファイルを確認:${NC}"
find "$OUTPUT_DIR/qa_basic" -name "*.xml" -type f 2>/dev/null | head -1 | while read -r file; do
    if [ -n "$file" ]; then
        echo -e "${GREEN}✓ Q&Aファイルが生成されました: $file${NC}"
        echo "内容の一部:"
        head -15 "$file"
    fi
done

# 4. generate コマンドのテスト（周辺コンテキストモード）
print_step "4. Q&A生成（周辺コンテキストモード）"
run_command "uv run easy-dataset generate '$INPUT_FILE' --ga-file '$OUTPUT_DIR/ga/ga_definitions.xml' --output-dir '$OUTPUT_DIR/qa_context' --use-surrounding-context --context-before 1 --context-after 1 --num-qa-pairs 2"

# 5. generate コマンドのテスト（Alpaca出力）
print_step "5. Q&A生成（Alpaca形式出力）"
run_command "uv run easy-dataset generate '$INPUT_FILE' --ga-file '$OUTPUT_DIR/ga/ga_definitions.xml' --output-dir '$OUTPUT_DIR/qa_alpaca' --export-alpaca --num-qa-pairs 2"

echo -e "\n${CYAN}生成されたAlpacaファイルを確認:${NC}"
find "$OUTPUT_DIR/qa_alpaca" -name "*.json" -type f 2>/dev/null | head -1 | while read -r file; do
    if [ -n "$file" ]; then
        echo -e "${GREEN}✓ Alpacaファイルが生成されました: $file${NC}"
        echo "内容の一部:"
        head -5 "$file"
    fi
done

# 6. convert-to-alpaca コマンドのテスト
print_step "6. XMLファイルをAlpaca形式に変換"
run_command "uv run easy-dataset convert-to-alpaca '$OUTPUT_DIR/qa_basic' --output-file '$OUTPUT_DIR/converted_dataset.json'"

echo -e "\n${CYAN}変換されたファイルを確認:${NC}"
if [ -f "$OUTPUT_DIR/converted_dataset.json" ]; then
    echo -e "${GREEN}✓ 変換完了: $OUTPUT_DIR/converted_dataset.json${NC}"
    echo "内容の一部:"
    head -5 "$OUTPUT_DIR/converted_dataset.json"
else
    echo -e "${RED}✗ 変換ファイルが見つかりません${NC}"
fi

# 7. aggregate-logs コマンドのテスト
print_step "7. ログファイルの集約"
# テスト用にlogsディレクトリを作成してファイルをコピー
mkdir -p "$OUTPUT_DIR/logs"
find "$OUTPUT_DIR/qa_basic" -name "*.xml" -type f -exec cp {} "$OUTPUT_DIR/logs/" \; 2>/dev/null || echo "コピー対象のファイルがありません"

run_command "uv run easy-dataset aggregate-logs '$OUTPUT_DIR' --qa-dir '$OUTPUT_DIR/aggregated'"

echo -e "\n${CYAN}集約結果を確認:${NC}"
if [ -d "$OUTPUT_DIR/aggregated" ]; then
    file_count=$(find "$OUTPUT_DIR/aggregated" -name "*.xml" -type f | wc -l)
    echo -e "${GREEN}✓ ファイルが集約されました: $file_count 件${NC}"
else
    echo -e "${RED}✗ 集約ディレクトリが見つかりません${NC}"
fi

# 8. 短いファイルでのテスト
if [ -f "$SHORT_FILE" ]; then
    print_step "8. 短いファイルでのテスト"
    run_command "uv run easy-dataset create-ga '$SHORT_FILE' --output-dir '$OUTPUT_DIR/short'"
    run_command "uv run easy-dataset generate '$SHORT_FILE' --ga-file '$OUTPUT_DIR/short/ga/ga_definitions.xml' --output-dir '$OUTPUT_DIR/short_qa' --num-qa-pairs 1"
else
    print_step "8. 短いファイルテスト（スキップ）"
    echo -e "${YELLOW}test_short.md が見つからないためスキップします${NC}"
fi

# 結果サマリー
print_step "テスト完了サマリー"
echo -e "${GREEN}すべてのコマンドテストが完了しました！${NC}"
echo ""
echo "生成されたファイル:"
echo "📁 出力ディレクトリ: $OUTPUT_DIR"
find "$OUTPUT_DIR" -type f -name "*.xml" -o -name "*.json" | head -10 | while read -r file; do
    echo "  📄 $file"
done

echo ""
echo -e "${CYAN}次のステップ:${NC}"
echo "1. 生成されたファイルの内容を確認"
echo "2. 必要に応じてパラメータを調整"
echo "3. 実際のドキュメントで本格運用"

echo ""
echo -e "${BLUE}各コマンドの詳細ヘルプ:${NC}"
echo "uv run easy-dataset create-ga --help"
echo "uv run easy-dataset generate --help"
echo "uv run easy-dataset convert-to-alpaca --help"
echo "uv run easy-dataset aggregate-logs --help"
