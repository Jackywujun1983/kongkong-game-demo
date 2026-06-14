@echo off
setlocal EnableExtensions

chcp 65001 >nul
cd /d "%~dp0.."

set "COMMIT_MESSAGE=%~1"
if "%COMMIT_MESSAGE%"=="" set "COMMIT_MESSAGE=Update GameHub UI design"

echo Current repository:
git remote -v
if errorlevel 1 goto fail

set "PYTHON_EXE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE="
if not defined PYTHON_EXE (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_EXE=python"
)
if not defined PYTHON_EXE (
  where py >nul 2>nul
  if not errorlevel 1 set "PYTHON_EXE=py"
)
if not defined PYTHON_EXE (
  echo Python runtime was not found. Please install Python or run this from Codex workspace.
  goto fail
)

echo.
echo Exporting static game data...
"%PYTHON_EXE%" tools\export_static_game_data.py
if errorlevel 1 goto fail

echo.
echo Staging tracked project changes...
git add -u -- .
if errorlevel 1 goto fail

echo.
echo Staging static deployment files...
git add -- .github/workflows/github-pages.yml ^
  .gitignore ^
  publish_static_site.cmd ^
  publish_site.cmd ^
  README.md ^
  backend/README.md ^
  backend/gamehub.sqlite3 ^
  docs ^
  frontend/README.md ^
  frontend/index.html ^
  frontend/detail.html ^
  frontend/preview.html ^
  frontend/public/assets/covers/default-game-cover.jpg ^
  frontend/public/assets/covers/default-game-cover.png ^
  frontend/public/game-data.js ^
  frontend/public/site.css ^
  frontend/src/App.tsx ^
  frontend/src/features/games/*.tsx ^
  frontend/src/styles/global.css ^
  frontend/src/types/domain.ts ^
  tools/export_static_game_data.py ^
  tools/import_fufu_quark_games.py ^
  tools/publish_ui_update.cmd
if errorlevel 1 goto fail

echo.
echo Staged files:
git diff --cached --name-only
if errorlevel 1 goto fail

git diff --cached --quiet
set "DIFF_STATUS=%ERRORLEVEL%"
if "%DIFF_STATUS%"=="0" (
  echo.
  echo No staged changes. Trying to push existing commits...
) else if "%DIFF_STATUS%"=="1" (
  echo.
  echo Creating commit: %COMMIT_MESSAGE%
  git commit -m "%COMMIT_MESSAGE%"
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
