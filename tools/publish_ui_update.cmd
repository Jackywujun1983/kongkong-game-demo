@echo off
setlocal EnableExtensions

chcp 65001 >nul
cd /d "%~dp0.."

set "COMMIT_MESSAGE=%~1"
if "%COMMIT_MESSAGE%"=="" set "COMMIT_MESSAGE=Update GameHub UI design"

echo Current repository:
git remote -v
if errorlevel 1 goto fail

echo.
echo Staging confirmed UI files...
git add -- .gitignore ^
  publish_site.cmd ^
  docs/*.md ^
  frontend/detail.html ^
  frontend/preview.html ^
  frontend/public/assets/covers/default-game-cover.jpg ^
  frontend/public/assets/covers/default-game-cover.png ^
  frontend/public/site.css ^
  frontend/src/App.tsx ^
  frontend/src/features/games/GameCard.tsx ^
  frontend/src/styles/global.css ^
  tools/publish_ui_update.cmd
if errorlevel 1 goto fail

echo.
echo Staged files:
git diff --cached --name-only -- .gitignore ^
  publish_site.cmd ^
  docs/*.md ^
  frontend/detail.html ^
  frontend/preview.html ^
  frontend/public/assets/covers/default-game-cover.jpg ^
  frontend/public/assets/covers/default-game-cover.png ^
  frontend/public/site.css ^
  frontend/src/App.tsx ^
  frontend/src/features/games/GameCard.tsx ^
  frontend/src/styles/global.css ^
  tools/publish_ui_update.cmd
if errorlevel 1 goto fail

git diff --cached --quiet -- .gitignore ^
  publish_site.cmd ^
  docs/*.md ^
  frontend/detail.html ^
  frontend/preview.html ^
  frontend/public/assets/covers/default-game-cover.jpg ^
  frontend/public/assets/covers/default-game-cover.png ^
  frontend/public/site.css ^
  frontend/src/App.tsx ^
  frontend/src/features/games/GameCard.tsx ^
  frontend/src/styles/global.css ^
  tools/publish_ui_update.cmd
set "DIFF_STATUS=%ERRORLEVEL%"
if "%DIFF_STATUS%"=="0" (
  echo.
  echo No staged changes. Trying to push existing commits...
) else if "%DIFF_STATUS%"=="1" (
  echo.
  echo Creating commit: %COMMIT_MESSAGE%
  git commit -m "%COMMIT_MESSAGE%" -- .gitignore ^
    publish_site.cmd ^
    docs/*.md ^
    frontend/detail.html ^
    frontend/preview.html ^
    frontend/public/assets/covers/default-game-cover.jpg ^
    frontend/public/assets/covers/default-game-cover.png ^
    frontend/public/site.css ^
    frontend/src/App.tsx ^
    frontend/src/features/games/GameCard.tsx ^
    frontend/src/styles/global.css ^
    tools/publish_ui_update.cmd
  if errorlevel 1 goto fail
) else (
  goto fail
)

echo.
echo Pushing to origin main...
git push origin main
if errorlevel 1 goto fail

echo.
echo Done.
echo If GitHub Pages still shows the old page, check Actions and make sure the latest deployment is green.
exit /b 0

:fail
echo.
echo Publish failed. Please check the error above.
exit /b 1
