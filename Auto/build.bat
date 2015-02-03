pyinstaller -y --upx-dir=../../upx PyomoAutoRun.spec
xcopy dist\PyomoAutoRun\* ..\PyomoPlugin\plugins\PyomoAutoRun\ /Y /E
copy plugin.xml ..\PyomoPlugin\plugins\PyomoAutoRun\plugin.xml /Y
copy pyomo_auto_16.png ..\PyomoPlugin\plugins\PyomoAutoRun\pyomo_auto_16.png /Y
copy pyomo_auto_32.png ..\PyomoPlugin\plugins\PyomoAutoRun\pyomo_auto_32.png /Y
pause
