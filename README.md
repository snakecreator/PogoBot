# PogoBot - Pokémon GO Auto Battle Bot
An automated Python-based bot that battles Candela in the Great League in Pokémon GO using Android Debug Bridge (ADB) and OpenCV template matching.

## Features

* **Fully Automated Battles:** Seamlessly navigates through battle selection menus, initiates the battle and performs attacks.
* **Smart Team Switching:** Automatically swaps to the 2nd party slot at the start of the battle (configured for Vaporeon).
* **Computer Vision:** Utilizes OpenCV template matching for reliable UI detection across different devices.
* **Flexible Execution:** Supports running for a specific number of fights, a defined duration in minutes, or indefinitely.
* **Cross-Platform:** Works on Windows, macOS and Linux.

---

Before running the bot, ensure you have the following installed and configured:
1. **Python 3.8+**
2. **Android Device:**
* Enable **Developer Options** and **USB Debugging** on your Android phone.
* Connect your device via USB (or set up ADB over Wi-Fi).
3. **ADB (Android Debug Bridge):**
* Must be installed and accessible via system PATH.
*Note for Windows users:* You can run `adb` directly via **Git Bash** or the integrated VS Code terminal without manually configuring Windows PATH variables, as long as ADB is detected by your shell environment.
* Verify your connection by running `adb devices` in your terminal.
   
## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/snakecreator/PogoBot.git
cd PogoBot.git
```

Create and activate a virtual environment (venv):

*Linux/macOS:*
```bash
python3 -m venv venv
source venv/bin/activate
```

*Windows:*
```PowerShell
python -m venv venv
.\venv\Scripts\activate.ps1
```

Install required packages:
```bash
pip install -r requirements.txt
```

## Usage:

1. Open Pokémon GO on your phone and navigate to the Battle tab (where Candela's icon is visible under Training).
2. Connect your phone to the computer with USB and enable USB debbuging. 
3. Run the script using one of the following modes:

*Run indefinitely:*
```bash
python bot.py
```

*Run for a specific number of battles (e.g., 50 fights):*
```bash
python bot.py --fights 50
```

*Run for a specific duration (e.g., 120 minutes):*
```bash
python bot.py --minutes 120
```

## Configuration

Project parameters are managed via config.json. You can tweak the following values:

```JSON
{
  "timeout_seconds": 30, 
  "click_interval_seconds": 0.04,
  "battle_duration_seconds": 55,
  "opencv_threshold": 0.80,
  "ratio_attack": [0.501, 0.805],
  "ratio_switch_slot2": [0.898, 0.607]
}
```

## Project structure
```text
├── bot.py             # Main execution script 
├── config.json        # Configuration file for timeouts and click ratios 
├── requirements.txt   # Python package dependencies 
├── .gitignore         # Files excluded from version control 
└── templates/         # Reference images for OpenCV template matching 
	├── candela_icon.png
	├── battle_btn.png 
	├── great_league.png 
	├── use_this_party.png 
	├── you_win.png 
	├── checkmark.png 
	└── training.png
```
## Troubleshooting & Custom Templates

If the bot struggles to recognize UI elements or fails to switch Pokémon on your device:
1. **Resolution & Language Differences:** The provided templates were captured on a specific screen resolution. If your device has a different aspect ratio, OpenCV template matching might fail.
2. **Replacing Template Images:** 
* Take a screenshot of your own phone screen during the relevant battle step.   
* Crop the specific UI element (e.g., Candela icon, Battle button, or your specific 2nd slot Pokémon/Vaporeon) using an image editor   
* Save the cropped image into the `templates/` folder using the exact same file name, replacing the default template.
## Disclaimer

This project is intended strictly for educational and personal research purposes. Automated actions may violate Pokémon GO's Terms of Service. Use at your own risk.