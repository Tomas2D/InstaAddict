from types import SimpleNamespace
from unittest.mock import patch

from InstaAddict.core import views

views.ResourceID = views.resources("com.instagram.android")


class FakeView:
    def __init__(self, exists):
        self._exists = exists

    def exists(self, *_):
        return self._exists


def _make(like_button_exists, liked_marker_exists=False):
    """find() returns the like button by resourceIdMatches, the marker by desc."""
    state = SimpleNamespace(swipes=0)

    def find(**kw):
        if "resourceIdMatches" in kw:
            return FakeView(like_button_exists)
        return FakeView(liked_marker_exists)

    obj = views.PostsViewList.__new__(views.PostsViewList)
    obj.device = SimpleNamespace(find=find)
    return obj, state


def _run(obj, state):
    def swipe(self, *a, **kw):
        state.swipes += 1

    with patch.object(views.UniversalActions, "_swipe_points", swipe):
        return obj._check_if_liked()


def test_no_like_button_gives_up_instead_of_hanging():
    obj, state = _make(like_button_exists=False)
    assert _run(obj, state) is False
    assert state.swipes == 3, state.swipes  # capped, not endless


def test_like_detected():
    obj, state = _make(like_button_exists=True, liked_marker_exists=True)
    assert _run(obj, state) is True
    assert state.swipes == 0, state.swipes


def test_like_missing_reported_without_scrolling():
    obj, state = _make(like_button_exists=True, liked_marker_exists=False)
    assert _run(obj, state) is False
    assert state.swipes == 0, state.swipes


def main():
    test_no_like_button_gives_up_instead_of_hanging()
    test_like_detected()
    test_like_missing_reported_without_scrolling()
    print("OK")


if __name__ == "__main__":
    main()
