# easy_dataset_cli/text_splitter.py
"""テキスト分割関連機能"""

from typing import List, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """LangChainのTextSplitterを使ってテキストをチャンクに分割する"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    docs = text_splitter.create_documents([text])
    return [doc.page_content for doc in docs]


def get_chunk_with_surrounding_context(
    chunks: List[str],
    target_index: int,
    context_before: int = 1,
    context_after: int = 1
) -> Tuple[str, List[str]]:
    """
    指定したインデックスのチャンクと前後のコンテキストを取得する

    Args:
        chunks: チャンクのリスト
        target_index: 対象となるチャンクのインデックス
        context_before: 前方のコンテキストとして含めるチャンク数
        context_after: 後方のコンテキストとして含めるチャンク数

    Returns:
        Tuple[str, List[str]]: (対象チャンク, コンテキストチャンクのリスト)
    """
    # 対象チャンクを取得
    target_chunk = chunks[target_index]

    # コンテキストチャンクを取得
    context_chunks = []

    # 前方のコンテキスト
    start_idx = max(0, target_index - context_before)
    for i in range(start_idx, target_index):
        if i >= 0 and i < len(chunks):
            context_chunks.append(f"[前文脈{i+1}]: {chunks[i]}")

    # 後方のコンテキスト
    end_idx = min(len(chunks), target_index + context_after + 1)
    for i in range(target_index + 1, end_idx):
        if i >= 0 and i < len(chunks):
            context_chunks.append(f"[後文脈{i+1}]: {chunks[i]}")

    return target_chunk, context_chunks


def create_augmented_chunks(
    chunks: List[str],
    context_before: int = 1,
    context_after: int = 1,
    max_context_length: int = 4000
) -> List[Tuple[str, str, List[str]]]:
    """
    全てのチャンクに対して前後のコンテキストを付与した新しいチャンクリストを作成する

    Args:
        chunks: 元のチャンクリスト
        context_before: 前方のコンテキストとして含めるチャンク数
        context_after: 後方のコンテキストとして含めるチャンク数
        max_context_length: コンテキストの最大文字数（トークンサイズ制限対策）

    Returns:
        List[Tuple[str, str, List[str]]]: [(対象チャンク, 文脈付きチャンク, コンテキスト情報リスト), ...]
    """
    augmented_chunks = []

    for i, chunk in enumerate(chunks):
        target_chunk, context_chunks = get_chunk_with_surrounding_context(
            chunks, i, context_before, context_after
        )

        # コンテキストを結合して一つの文字列にまとめる
        context_text = "\n\n".join(context_chunks)

        # トークンサイズ制限対策：コンテキストが長すぎる場合は後ろから切り詰める
        if len(context_text) > max_context_length:
            # コンテキストを後ろから順に切り詰め
            current_context = ""
            reversed_context = context_chunks[::-1]  # 後ろから順に

            for ctx in reversed_context:
                if len(current_context) + len(ctx) + 2 <= max_context_length:
                    current_context = ctx + "\n\n" + current_context
                else:
                    break

            context_text = current_context.rstrip()

        # 対象チャンクとコンテキストを組み合わせ
        augmented_content = f"### 【メイン本文】: ------------- \n```\n{target_chunk}\n```\n\n ### 【周辺文脈】: -------------\n```\n{context_text}\n```"

        augmented_chunks.append((target_chunk, augmented_content, context_chunks))

    return augmented_chunks
