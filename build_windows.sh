#!/bin/bash
docker run --rm -v $(pwd):/src cdrx/pyinstaller-windows bash -c "
pip install -r /src/Requirements.txt &&
pyinstaller --onefile /src/Banana.py &&
mkdir -p /src/dist/windows &&
mv dist/Banana.exe /src/dist/windows/
"