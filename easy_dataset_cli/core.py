# easy_dataset_cli/core.py
"""統合インターフェース - 各モジュールの機能を統合"""

# 各モジュールから必要な関数をインポート
from .ga_parser import (
    parse_ga_file,
    parse_ga_definitions_from_xml
)
from .generators import (
    generate_qa_for_chunk_with_ga,
    generate_qa_for_chunk_with_ga_and_fulltext,
    generate_qa_for_chunk_with_ga_and_thinking,
    generate_qa_for_chunk_with_surrounding_context,
    generate_ga_definitions
)
from .text_splitter import (
    split_text,
    get_chunk_with_surrounding_context,
    create_augmented_chunks
)
from .xml_utils import convert_to_xml_by_genre, load_existing_xml_file, aggregate_logs_xml_to_qa
from .file_utils import (
    create_output_directories,
    save_ga_definitions_by_genre,
    sanitize_filename,
    find_text_files,
    batch_process_files
)
from .alpaca_converter import (
    convert_all_xml_to_alpaca,
    upload_to_huggingface,
    create_dataset_card
)

# 後方互換性のため、すべての関数を再エクスポート
__all__ = [
    # GA解析関連
    'parse_ga_file',
    'parse_ga_definitions_from_xml',
    
    # Q&A生成関連
    'generate_qa_for_chunk_with_ga',
    'generate_qa_for_chunk_with_ga_and_fulltext',
    'generate_qa_for_chunk_with_ga_and_thinking',
    'generate_qa_for_chunk_with_surrounding_context',
    'generate_ga_definitions',

    # テキスト分割
    'split_text',
    'get_chunk_with_surrounding_context',
    'create_augmented_chunks',
    
    # XML処理
    'convert_to_xml_by_genre',
    'load_existing_xml_file',
    'aggregate_logs_xml_to_qa',
    
    # ファイル操作
    'create_output_directories',
    'save_ga_definitions_by_genre',
    'sanitize_filename',
    'find_text_files',
    'batch_process_files',
    
    # アルパカ変換・アップロード
    'convert_all_xml_to_alpaca',
    'upload_to_huggingface',
    'create_dataset_card'
]
