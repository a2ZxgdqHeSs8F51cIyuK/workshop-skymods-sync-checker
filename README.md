A Python script to check if mods from Steam Workshop collections are available and up-to-date on SkyMods.

## Features

- Scans Steam Workshop collections for mods
- Checks SkyMods for corresponding mods
- Compares update dates to identify outdated mods
- Generates a summary

## Quick Setup Guide

### Step 1: Save the Files
1. Create a new folder called `steam-mod-checker` (or whatever you prefer)
2. Save the Python script as `mod_checker.py` in this folder
3. Save the requirements as `requirements.txt` in the same folder

### Step 2: Install Requirements (One-time Setup)
1. Open **Windows PowerShell**
2. Navigate to your folder:
   ```powershell
   cd C:\path\to\your\steam-mod-checker
   ```
3. Install the required packages:
   ```powershell
   pip install -r requirements.txt
   ```

### Step 3: Run the Script
1. In the same PowerShell window, run:
   ```powershell
   python mod_checker.py
   ```
2. When prompted, paste your Steam Workshop collection URL
3. The script will scan and show you which mods are outdated or missing on SkyMods

### Example PowerShell Session:
```powershell
PS C:\Users\YourName> cd C:\tools\steam-mod-checker
PS C:\tools\steam-mod-checker> pip install -r requirements.txt
PS C:\tools\steam-mod-checker> python mod_checker.py
```

That's it! The script will guide you through the rest. You only need to run the `pip install` command once - after that, you can just run `python mod_checker.py` whenever you want to check your mod collections.
