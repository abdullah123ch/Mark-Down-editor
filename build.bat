@echo off
echo Building MarkdownEditor...
C:\Program Files\Python313\python.exe" -m pyinstaller --onefile --noconsole ^
--add-data "icons;icons" ^
--add-data "theme;theme" ^
--icon=md.ico ^
--name MarkdownEditor ^
editor.py
echo Done!
pause

if %errorlevel% neq 0 (
    echo Build failed with error code %errorlevel%.
) else (
    echo Build completed successfully.
)