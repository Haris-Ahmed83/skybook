#!/bin/bash

echo ""
echo "=========================================="
echo "  SKY BOOK — Flight Booking System"
echo "=========================================="
echo ""

echo "[1/2] Installing required Python packages..."
pip install flask flask-cors flask-jwt-extended bcrypt -q 2>/dev/null || pip3 install flask flask-cors flask-jwt-extended bcrypt -q
echo "  Packages ready!"
echo ""

echo "[2/2] Starting SkyBook Backend Server..."
echo "  Backend running at: http://localhost:5000"
echo ""

# Open the frontend in browser
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$SCRIPT_DIR/skybook_frontend.html"
else
    xdg-open "$SCRIPT_DIR/skybook_frontend.html" 2>/dev/null || \
    sensible-browser "$SCRIPT_DIR/skybook_frontend.html" 2>/dev/null || \
    echo "  Please open skybook_frontend.html manually in your browser."
fi

echo "  =========================================="
echo "   Demo Login:"
echo "   Email   : demo@skybook.app"
echo "   Password: Demo1234!"
echo "  =========================================="
echo ""
echo "  Press CTRL+C to stop the server."
echo ""

python3 skybook_backend.py 2>/dev/null || python skybook_backend.py
