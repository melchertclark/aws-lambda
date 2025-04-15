#!/bin/bash
set -e

rm -rf build/ package.zip
mkdir build
pip install -r requirements.txt -t build/
cp -r src/* build/
cd build
zip -r ../package.zip .
cd ..
echo "✅ Zipped code+deps to package.zip"
