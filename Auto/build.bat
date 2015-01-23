pyinstaller -y --upx-dir=../../upx PyomoAutoRun.spec
xcopy dist\PyomoAutoRun\* ..\PyomoPlugin\plugins\PyomoAutoRun\ /Y /E
copy plugin.xml ..\PyomoPlugin\plugins\PyomoAutoRun\plugin.xml /Y
pause
