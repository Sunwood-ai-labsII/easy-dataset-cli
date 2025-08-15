uv run easy-dataset create-ga .\example\input\documents\Touhou_Chireiden.md --output-dir .\example\output\Touhou_Chireiden --num-ga-pairs 10

uv run easy-dataset generate .\example\input\documents\Touhou_Chireiden.md  --ga-file .\example\output\Touhou_Chireiden\ga\ga_definitions.xml --output-dir .\example\output\Touhou_Chireiden\ --chunk-size 500 --use-fulltext

uv run easy-dataset convert-to-alpaca .\example\output\Touhou_Chireiden\qa --output-file example\output\Touhou_Chireiden\dataset.json --upload-hf --hf-repo-name MakiAi/Orin-Instruct-Alpaca-JP-v7
