
#!/bin/bash
set -e

echo "Instalando herramientas graficas..."

sudo apt-get update

sudo apt-get install -y \
    xvfb \
    x11vnc \
    fluxbox \
    websockify \
    novnc \
    python3-tk

echo "Instalando dependencias Python..."

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Comprobando Tkinter..."

python -c "import tkinter; print('Tkinter OK')"

echo "Instalacion completada."
