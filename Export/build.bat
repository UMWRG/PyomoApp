pyinstaller --upx-dir=../../upx PyomoExport.spec
xcopy dist\PyomoExport\* ..\PyomoPlugin\plugins\PyomoExport\ /Y /s
copy plugin.xml ..\PyomoPlugin\plugins\PyomoExport\plugin.xml /Y
pause
