pyinstaller -y --upx-dir=../../upx PyomoExport.spec
xcopy dist\PyomoExport\* ..\PyomoPlugin\plugins\PyomoExport\ /Y /s
copy plugin.xml ..\PyomoPlugin\plugins\PyomoExport\plugin.xml /Y
copy pyomo_export_16.png ..\PyomoPlugin\plugins\PyomoExport\pyomo_export_16.png /Y
copy pyomo_export_32.png ..\PyomoPlugin\plugins\PyomoExport\pyomo_export_32.png /Y
pause
