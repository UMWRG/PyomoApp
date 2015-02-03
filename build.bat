cd Auto
pyinstaller -y --upx-dir=../../upx PyomoAutoRun.spec
xcopy dist\PyomoAutoRun\* ..\PyomoPlugin\plugins\PyomoAutoRun\ /Y /E
copy plugin.xml ..\PyomoPlugin\plugins\PyomoAutoRun\plugin.xml /Y
copy pyomo_auto_16.png ..\PyomoPlugin\plugins\PyomoAutoRun\pyomo_auto_16.png /Y
copy pyomo_auto_32.png ..\PyomoPlugin\plugins\PyomoAutoRun\pyomo_auto_32.png /Y
cd ../Export
pyinstaller -y --upx-dir=../../upx PyomoExport.spec
xcopy dist\PyomoExport\* ..\PyomoPlugin\plugins\PyomoExport\ /Y /E
copy plugin.xml ..\PyomoPlugin\plugins\PyomoExport\plugin.xml /Y
copy pyomo_export_16.png ..\PyomoPlugin\plugins\PyomoExport\pyomo_export_16.png /Y
copy pyomo_export_32.png ..\PyomoPlugin\plugins\PyomoExport\pyomo_export_32.png /Y
cd ../RunImport
pyinstaller -y --upx-dir=../../upx PyomoRunImport.spec
xcopy dist\PyomoRunImport\* ..\PyomoPlugin\plugins\PyomoRunImport\ /Y /E
copy plugin.xml ..\PyomoPlugin\plugins\PyomoRunImport\plugin.xml /Y
copy pyomo_import_16.png ..\PyomoPlugin\plugins\PyomoRunImport\pyomo_import_16.png /Y
copy pyomo_import_32.png ..\PyomoPlugin\plugins\PyomoRunImport\pyomo_import_32.png /Y
pause