pyinstaller --upx-dir=../../upx PyomoRunImport.spec>test.dat
xcopy dist\PyomoRunImport\* ..\PyomoPlugin\plugins\PyomoRunImport\ /Y /s
copy plugin.xml ..\PyomoPlugin\plugins\PyomoRunImport\plugin.xml /Y
pause
