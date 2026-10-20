import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")


def test_config_file_exists():
    """Checks whether the config.json file even exists"""
    assert os.path.exists(CONFIG_PATH), "The config.json file does not exist!"


def test_config_json_structure():
    """Checks if the file is a valid JSON file and contains the required fields"""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    required_keys = [
        "timeout_seconds",
        "click_interval_seconds",
        "battle_duration_seconds",
        "opencv_threshold",
        "ratio_attack",
        "ratio_switch_slot2",
    ]

    for key in required_keys:
        assert key in config, f"Missing key in config.json: {key}"


def test_config_ratios_validation():
    """Checks if the screen ratios are two-element arrays within the range [0.0, 1.0] 
    (0% screen resolution, 100% screen resolution)"""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    for key in ["ratio_attack", "ratio_switch_slot2"]:
        coords = config[key]
        assert isinstance(coords, list), f"{key}  must be a list"
        assert len(coords) == 2, f"{key} must contain exactly two elements [X, Y]"
        assert 0.0 <= coords[0] <= 1.0, f"{key}[0] must be in range of 0.0-1.0"
        assert 0.0 <= coords[1] <= 1.0, f"{key}[1] must be in range of 0.0-1.0"


def test_templates_directory():
    """Checks if the templates/ directory exists and contains all the necessary images"""
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    
    assert os.path.exists(templates_dir), "The templates/ does not exist!"
    assert os.path.isdir(templates_dir), "templates is not a directory!"
    
    # List of templates required for bot.py 
    required_templates = [
        "candela_icon.png",
        "battle_btn.png",
        "great_league.png",
        "use_this_party.png",
        "you_win.png",
        "checkmark.png",
        "training.png"
    ]
    
    existing_files = os.listdir(templates_dir)
    assert len(existing_files) > 0, "The templates/ directory is empty!"
    
    for template in required_templates:
        assert template in existing_files, f"Missing template file: {template}"