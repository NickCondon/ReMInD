@echo off
echo Building ReMInD executables...

echo Installing requirements...
pip install -r requirements_build.txt

echo Building Full Version...
pyinstaller --onefile --windowed --name "ReMInD_v2.27" --add-data "../src/metadata_extractors;metadata_extractors" ../src/ReMInD_v2.27.py

echo Building Lite Version...
pyinstaller --onefile --windowed --name "ReMInD_Lite_v2.27" --add-data "../src/metadata_extractors;metadata_extractors" ../src/ReMInD_Lite_v2.27.py

echo Moving executables to dist folder...
move dist\*.exe ..\dist\

echo Build complete!
pause
