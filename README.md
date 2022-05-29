# LocRes-Builder
Building tool for localization resources of UE4 games

## Features
- No need UE4 and original files to cook locres files
- Eble to add .locres files for new languages.
  (It will just add resource files. It doesn't mean you can add support for the languages to your game.)
- Eble to change main language.

## Getting Started

### 1. LocRes to Json
Drop `.locmeta` on `convert.bat`.
It will dump all LocRes data in a `.json` file.

### 2. Json to LocRes
Drop `.json` on `convert.bat`.
It will build LocRes files.