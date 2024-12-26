@echo off

setlocal EnableDelayedExpansion

::: Build and Sign the exe
python build.py

::: Signing needs to be more dynamic...
signtool sign /a /s MY /n "NGN Management Inc."  /tr http://timestamp.sectigo.com /fd SHA256 /td SHA256 /v dist\HytekValidate\HytekValidate.exe

::: Build the installer

makensis HytekValidate.nsi

::: Sign the installer

::: signtool sign /a /s MY /n "Open Source Developer, Darren Richer" /fd SHA256 /t http://time.certum.pl /v swon-install.exe

::: Clean up build artifacts
rmdir /q/s build
