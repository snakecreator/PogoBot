from unittest.mock import MagicMock, patch

import bot


def test_get_screen_resolution_parsing():
    """Checks whether the function correctly parses the result of the `adb shell wm size` command"""
    mock_completed_process = MagicMock()
    mock_completed_process.stdout = "Physical size: 1080x2400\n"

    with patch("subprocess.run", return_value=mock_completed_process):
        width, height = bot.get_screen_resolution()
        assert width == 1080
        assert height == 2400


def test_tap_ratio_calculation():
    """Checks whether the conversion of proportional coordinates to pixels works correctly"""
    bot.SCREEN_W = 1000
    bot.SCREEN_H = 2000

    with patch("bot.tap") as mock_tap:
        # 50% width = 500px, 80% height = 1600px
        bot.tap_ratio(0.5, 0.8)
        mock_tap.assert_called_once_with(500, 1600)