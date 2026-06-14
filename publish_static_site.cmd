@echo off
setlocal EnableExtensions

cd /d "%~dp0"
call tools\publish_ui_update.cmd "Deploy GameHub static site"
exit /b %ERRORLEVEL%
