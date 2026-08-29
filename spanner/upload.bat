@echo off
REM DEV SHORTCUT - copies the working tree straight onto the Pi and restarts,
REM without going through git. Use it to test uncommitted changes quickly.
REM
REM This leaves the Pi's git tree dirty and does NOT install systemd units or
REM requirements. For a real deploy use release.bat.
REM
REM Stops at the first failure so a half-uploaded tree is never restarted into.
call "%~dp0secrets.bat"

set HOST=rpi4b-weather
set LOGIN=-l klm -pw %passwd%

echo Uploading weather_daq...
pscp %LOGIN% ..\weather_daq\*.* klm@%HOST%:weather/weather_daq/
if errorlevel 1 goto failed

echo Uploading weather_web...
pscp %LOGIN% ..\weather_web\*.* klm@%HOST%:weather/weather_web/
if errorlevel 1 goto failed

pscp -r %LOGIN% ..\weather_web\templates klm@%HOST%:weather/weather_web/
if errorlevel 1 goto failed

echo Restarting services...
plink -batch %LOGIN% %HOST% "sudo systemctl restart weather_daq weather_web && sleep 3 && systemctl is-active weather_daq weather_web"
if errorlevel 1 goto restart_failed

echo.
echo Done - both services active.
exit /b 0

:restart_failed
echo.
echo RESTART FAILED - new code is uploaded but the services are not running it.
echo Check:  plink %LOGIN% %HOST% "systemctl status weather_daq weather_web"
exit /b 1

:failed
echo.
echo UPLOAD FAILED - services left untouched.
exit /b 1
