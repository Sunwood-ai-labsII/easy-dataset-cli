uv run easy-dataset generate .\example\input\documents\sample_document.txt  --ga-file .\example\output\sample_document\ga\ga_definitions.xml  --output-dir .\example\output\sample_document\ --use-thinking --append
uv run easy-dataset create-ga ./example/input/documents/ --output-dir ./example/output/sample_document_batch --num-ga-pairs 2

uv run easy-dataset create-ga example/input/documents/ --output-dir ./test_output/test_batch2 --max-context-length 3000 --num-ga-pairs 2
uv run easy-dataset generate ./example/input/documents/ --ga-base-dir ./test_output/test_batch2/ --output-dir ./test_output/test_batch2/ --chunk-size 2000 --use-surrounding-context  --append

uv run easy-dataset generate .\example\input\documents\sample_document.txt  --ga-file .\example\output\sample_document\ga\ga_definitions.xml  --output-dir .\example\output\sample_document\ --use-thinking --append