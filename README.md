# LocRes-Builder ver0.1.0
Building tool for localization resources of UE4 games

## Features
- No need UE4 and original locres files to cook locres files
- Eble to add .locres files for new languages.<br>
  (It will just add new resource files. It doesn't mean you can add support for the languages to your game.)

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
Locres data is used to translate stirngs uassets have.
So, english resources should have the same strings as the ones uassets have.
If you want to edit them, you need to flollow the steps below.

### 1. Copy en folder
Copy `en/*.locres` and paste as `dummy/*.locres`

### 2. Convert LocRes
Drop `.locmeta` on `convert.bat`.

### 3. Swap Main Langage
Open `./out/*.json`.
Then, set `dummy` to `locmeta/main_language`, and add `en` to `locmeta/local_languages`.

### 4. Done!
You can edit english resources!
It will work without data table editing.
