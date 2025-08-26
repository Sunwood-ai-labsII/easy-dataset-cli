uv run easy-dataset create-ga .\example\input\documents\Touhou_Chireiden.md --output-dir .\example\output\Touhou_Chireiden10 --num-ga-pairs 3

uv run easy-dataset generate .\example\input\documents\Touhou_Chireiden.md  --ga-file .\example\output\Touhou_Chireiden10\ga\ga_definitions.xml --output-dir .\example\output\Touhou_Chireiden10\ --chunk-size 1000 --use-fulltext --append

uv run easy-dataset convert-to-alpaca .\example\output\Touhou_Chireiden10\qa --output-file example\output\Touhou_Chireiden10\dataset.json --upload-hf --hf-repo-name MakiAi/Orin-Instruct-Alpaca-JP-v10
