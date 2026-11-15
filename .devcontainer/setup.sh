
#!/bin/bash
set -e

echo "Preparando entorno Python..."

python3 -m venv .venv

.venv/bin/python -m pip install --upgrade pip

if [ -f requirements.txt ]; then
    .venv/bin/python -m pip install -r requirements.txt
fi

echo "================================"
echo "INSTALACION COMPLETADA"
echo "================================"
