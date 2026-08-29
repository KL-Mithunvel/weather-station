@echo off
REM Release: push the current branch, then have the Pi pull it and restart.
REM
REM For quick dev iteration use upload.bat instead - it pscp's the working tree
REM straight onto the Pi without going through git.
REM
REM Pass --force to discard uncommitted changes on the Pi (typically leftovers
REM from upload.bat).
setlocal
call "%~dp0secrets.bat"

set HOST=rpi4b-weather
set LOGIN=-l klm -pw %passwd%

for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set BRANCH=%%b
if not defined BRANCH goto notrepo
if "%BRANCH%"=="HEAD" goto detached

REM Uncommitted work is not in the commit being pushed, so it would not deploy.
git diff --quiet HEAD
if errorlevel 1 goto dirty

echo Pushing %BRANCH% to origin...
git push origin %BRANCH%
if errorlevel 1 goto pushfailed

echo.
echo Deploying to %HOST%...
plink -batch %LOGIN% %HOST% "bash weather/spanner/deploy.sh %BRANCH% %1"
if errorlevel 1 goto deployfailed

echo.
echo Release complete.
exit /b 0

:notrepo
echo ERROR: not a git repository - run this from inside the checkout.
exit /b 1

:detached
echo ERROR: detached HEAD. Check out a branch before releasing.
exit /b 1

:dirty
echo ERROR: you have uncommitted changes to tracked files.
echo Commit them first, or use upload.bat to test them without committing.
echo.
git status --short
exit /b 1

:pushfailed
echo.
echo PUSH FAILED - nothing was deployed.
exit /b 1

:deployfailed
echo.
echo DEPLOY FAILED - see the output above.
echo The commit is pushed, but the Pi may not be running it.
echo Check:  plink %LOGIN% %HOST% "systemctl status weather_daq weather_web --no-pager"
exit /b 1
