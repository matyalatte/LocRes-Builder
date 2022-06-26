@echo off

REM Drop .locmeta or .json. It can convert the text resources

@if "%~1"=="" goto skip

@pushd %~dp0
python\python.exe src\main.py "%~1" -o=out -f=json
@popd

pause