"""InstaAddict - Human-like Instagram bot powered by UIAutomator2"""

__version__ = "1.0.3"
__tested_ig_version__ = "451.0.0.53.80"

from InstaAddict.core.bot_flow import start_bot


def run(**kwargs):
    start_bot(**kwargs)
