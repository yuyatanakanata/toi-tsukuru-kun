#!/bin/bash
cd "$(dirname "$0")"
echo "問いつくるくん を起動します..."
echo "ブラウザで http://localhost:8080 を開いてください"
echo "終了するには Ctrl+C"
echo ""
python3 app.py
