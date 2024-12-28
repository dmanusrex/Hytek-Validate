@echo off

setlocal EnableDelayedExpansion

::: Build and Sign the exe
python build.py

::: Signing needs to be more dynamic...
signtool sign /a /s MY /n "NGN Management Inc."  /tr http://timestamp.sectigo.com /fd SHA256 /td SHA256 /v dist\Hytek-Validate\Hytek-Validate.exe

::: Build the installer

makensis Hytek-Validate.nsi

::: Clean up build artifacts
rmdir /q/s build
