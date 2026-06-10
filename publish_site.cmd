@echo off
setlocal EnableExtensions

cd /d "%~dp0"
call tools\publish_ui_update.cmd "Update GameHub site UI"
exit /b %ERRORLEVEL%
