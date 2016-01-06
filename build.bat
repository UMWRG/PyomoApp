cd Auto
pyinstaller -y --upx-dir=../../upx PyomoAutoRun.spec
xcopy dist\PyomoAutoRun\* ..\release\PyomoApp\plugins\PyomoFiles\ /Y /E
copy pyomo_auto_16.png ..\release\PyomoApp\plugins\PyomoAutoRun\pyomo_auto_16.png /Y
copy pyomo_auto_32.png ..\release\PyomoApp\plugins\PyomoAutoRun\pyomo_auto_32.png /Y
copy p*.bat ..\release\PyomoApp\plugins\PyomoAutoRun\p*.bat /Y
copy plugin.xml ..\release\PyomoApp\plugins\PyomoAutoRun\plugin.xml /Y

cd ../Export
pyinstaller -y --upx-dir=../../upx PyomoExport.spec
xcopy dist\PyomoExport\* ..\release\PyomoApp\plugins\PyomoFiles\ /Y /E
copy pyomo_export_16.png ..\release\PyomoApp\plugins\PyomoExport\pyomo_export_16.png /Y
copy pyomo_export_32.png ..\release\PyomoApp\plugins\PyomoExport\pyomo_export_32.png /Y
copy p*.bat ..\release\PyomoApp\plugins\PyomoExport\p*.bat /Y
copy plugin.xml ..\release\PyomoApp\plugins\PyomoExport\plugin.xml /Y

cd ../RunImport
pyinstaller -y --upx-dir=../../upx PyomoRunImport.spec
xcopy dist\PyomoRunImport\* ..\release\PyomoApp\plugins\PyomoFiles\ /Y /E
copy pyomo_import_16.png ..\release\PyomoApp\plugins\PyomoRunImport\pyomo_import_16.png /Y
copy pyomo_import_32.png ..\release\PyomoApp\plugins\PyomoRunImport\pyomo_import_32.png /Y
copy p*.bat ..\release\PyomoApp\plugins\PyomoRunImport\p*.bat /Y
copy plugin.xml ..\release\PyomoApp\plugins\PyomoRunImport\plugin.xml /Y

pause
