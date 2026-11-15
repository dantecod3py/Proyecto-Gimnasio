
#!/bin/bash
set -e

export DISPLAY=:1

echo "Iniciando pantalla virtual..."

Xvfb :1 -screen 0 1280x800x24 &
sleep 2

echo "Iniciando escritorio..."

fluxbox &

echo "Iniciando servidor VNC..."

x11vnc -display :1 -nopw -forever -shared \
    -localhost -rfbport 5900 &

echo "Iniciando noVNC..."

websockify --web=/usr/share/novnc \
    0.0.0.0:6080 localhost:5900 &

echo "Escritorio preparado en el puerto 6080"

wait
