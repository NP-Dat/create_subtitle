@echo off
echo ========================================
echo  Building Create Subtitle .exe
echo ========================================
echo.

call venv\Scripts\activate

pyinstaller ^
    --name "CreateSubtitle" ^
    --onedir ^
    --windowed ^
    --noconfirm ^
    --clean ^
    --hidden-import=faster_whisper ^
    --hidden-import=ctranslate2 ^
    --hidden-import=tokenizers ^
    --hidden-import=onnxruntime ^
    --hidden-import=av ^
    --collect-data=faster_whisper ^
    main.py

echo.
if %ERRORLEVEL% EQU 0 (
    echo Build successful!
    echo Output: dist\CreateSubtitle\CreateSubtitle.exe
) else (
    echo Build failed! Check the errors above.
)
echo.
pause
