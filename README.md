[![discord](https://badgen.net/badge/icon/discord?icon=discord&label)](https://discord.gg/Qx2Ff3MByF)
![packaging](https://github.com/matyalatte/LocRes-Builder/actions/workflows/main.yml/badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# LocRes-Builder ver0.1.1
Building tool for localization resources of UE4 games

## Features
- No need UE4 and original locres files to cook locres files
- Eble to add .locres files for new languages.<br>
  (It will just add new resource files. It doesn't mean you can add support for the languages to your game.)
- Eble to edit English resources without data table editing.
- Eble to add new keys and namespaces.

## Supported Versions
- .locres: 3
- .locmeta: 0 and 1

If you got `Unsupported locres (or locmeta) version.` error, you can't mod the locres files with the tool.<br>
But I'll add support for the version if you can share the resource files.<br>
Please DM me with [discord](https://discord.gg/Qx2Ff3MByF) or Twitter (@MatyaModding).

## Getting Started

### 1. Download
Download `LocRes-Builder*.zip` from [here](https://github.com/matyalatte/LocRes-Builder/releases)

### 2. LocRes to Json
Drop `.locmeta` on `convert.bat`.<br>
It will dump all LocRes data in `./out/*.json`.

### 3. Edit Json
Edit the `.json` file as you like.

### 4. Json to LocRes
Drop `.json` on `convert.bat`.<br>
It will build LocRes files in `./out`.


## How to Mod English Text
Locres data is a dictionary for translating strings uassets have.<br>
So, english resources should have the same strings as the ones uassets have.<br>
If you want to edit them, you need to flollow the steps below.

### 1. Copy en folder
Copy `en/*.locres` and paste as `dummy/*.locres`

### 2. Convert LocRes
Drop `.locmeta` on `convert.bat`.

### 3. Swap Main Langage
Open `./out/*.json`.<br>
Then, set `dummy` to `locmeta/main_language`, add `en` to `locmeta/local_languages`, and remove `dummy` from `locmeta/local_languages`.

### 4. Done!
You can edit english resources!<br>
It will work without data table editing.
