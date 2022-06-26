[![discord](https://badgen.net/badge/icon/discord?icon=discord&label)](https://discord.gg/Qx2Ff3MByF)
![packaging](https://github.com/matyalatte/LocRes-Builder/actions/workflows/main.yml/badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# LocRes-Builder ver0.1.2
Building tool for localization resources of UE4 games

## Features
- No need UE4 and the original resources to cook locres files
- Eble to add .locres files for new languages.<br>
  (It will just add new resource files. It doesn't mean you can add support for the languages to your game.)
- Eble to edit English resources without data table editing.
- Eble to add new keys and namespaces.

## Supported File Versions
- .locres: 3
- .locmeta: 0 and 1

You will get `Unsupported version.` error for other versions.

## Getting Started

### 1. Download
Download `LocRes-Builder*.zip` from [here](https://github.com/matyalatte/LocRes-Builder/releases)

### 2. LocRes to Json
Drop `.locmeta` on `convert.bat`.<br>
It will dump all LocRes data in `./out/*/*.json`.

### 3. Edit Json
Edit the `.json` file as you like.

### 4. Json to LocRes
Drop `locmeta.json` on `convert.bat`.<br>
It will build LocRes files in `./out/*`.

## CSV Support
Open `convert.bat`, and rewrite `-f=json` to `-f=csv`.
You can use csv instead of json.<br>
But please note that the followings.
- Encoding should be utf-8.
- Use `<LF>` instead of line feed (`\n`)

## How to Mod English Text
Locres data is a dictionary for translating strings uassets have.<br>
So, english resources should have the same strings as the ones uassets have.<br>
If you want to edit them, you need to flollow the steps below.

### 1. Convert LocRes
Drop `.locmeta` on `convert.bat`.

### 2. Copy English File
Copy `en.json` and paste as `dummy.json`

### 3. Swap Main Langage
Open `./out/*/locmeta.json`.<br>
Then, set `dummy` to `main_language`, and add `en` to `local_languages`.

### 4. Done!
You can edit english resources!<br>
It will work without data table editing.
