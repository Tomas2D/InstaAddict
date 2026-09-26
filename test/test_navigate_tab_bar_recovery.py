"""Regression check for issues #22/#23: _navigateTo must back out of screens
without a tab bar (e.g. the focused search-input screen) before looking for a tab.

Run: .venv/bin/python test/test_navigate_tab_bar_recovery.py
"""

from types import SimpleNamespace
from unittest.mock import patch

from InstaAddict.core import views
from InstaAddict.core.views import TabBarTabs, TabBarView


class FakeButton:
    def __init__(self, visible):
        self.visible = visible
        self.clicks = 0

    def exists(self, *_):
        return self.visible

    def click(self, *_, **__):
        self.clicks += 1


def _make_view(backs_needed):
    """Tab bar becomes visible only after `backs_needed` back() presses."""
    state = SimpleNamespace(backs=0)
    tab_bar = FakeButton(backs_needed == 0)
    tab_button = FakeButton(True)

    def back():
        state.backs += 1
        tab_bar.visible = state.backs >= backs_needed

    view = TabBarView.__new__(TabBarView)
    view.device = SimpleNamespace(back=back, find=lambda **kw: tab_button)
    view._getTabBar = lambda: tab_bar
    return view, state, tab_button


def _navigate(view):
    with (
        patch.object(views.UniversalActions, "close_keyboard"),
        patch.object(views, "random_sleep"),
    ):
        view._navigateTo(TabBarTabs.HOME)


def main():
    for backs_needed in (0, 2):
        view, state, tab_button = _make_view(backs_needed)
        _navigate(view)
        assert state.backs == backs_needed, (backs_needed, state.backs)
        assert tab_button.clicks == 2, tab_button.clicks  # two clicks reset the tab

    # never recovers -> bounded retries, no infinite loop
    view, state, _ = _make_view(99)
    _navigate(view)
    assert state.backs == 5, state.backs

    print("OK")


if __name__ == "__main__":
    main()
