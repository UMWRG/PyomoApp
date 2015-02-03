pyinstaller -y --upx-dir=../../upx PyomoRunImport.spec
xcopy dist\PyomoRunImport\* ..\PyomoPlugin\plugins\PyomoRunImport\ /Y /s
copy plugin.xml ..\PyomoPlugin\plugins\PyomoRunImport\plugin.xml /Y
copy pyomo_import_16.png ..\PyomoPlugin\plugins\PyomoRunImport\pyomo_import_16.png /Y
copy pyomo_import_32.png ..\PyomoPlugin\plugins\PyomoRunImport\pyomo_import_32.png /Y
pause
