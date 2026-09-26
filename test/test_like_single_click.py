from types import SimpleNamespace

from InstaAddict.core import views
from InstaAddict.core.views import LikeMode, PostsViewList

views.ResourceID = views.resources("com.instagram.android")

LIKE_ID = views.ResourceID.ROW_FEED_BUTTON_LIKE


class FakeButton:
    def __init__(self, top, exists=True):
        self._top = top
        self._exists = exists
        self.clicks = 0

    def exists(self, *_):
        return self._exists

    def get_bounds(self):
        return {"top": self._top, "bottom": self._top + 127, "left": 33, "right": 99}

    def click(self, *_, **__):
        self.clicks += 1


class FakeMedia:
    def __init__(self, bottom):
        self._bottom = bottom

    def get_bounds(self):
        return {"top": 565, "bottom": self._bottom, "left": 0, "right": 1080}


def _make(buttons, media_bottom=1645, buttons_after_scroll=None):
    state = SimpleNamespace(scrolls=0, buttons=buttons)

    def find(**kw):
        if kw.get("resourceIdMatches") != LIKE_ID:
            return FakeButton(0, exists=False)
        index = kw.get("index")
        if index is not None:
            return state.buttons[index]
        holder = FakeButton(0, exists=bool(state.buttons))
        holder.count_items = lambda: len(state.buttons)
        return holder

    def find_likers_container():
        state.scrolls += 1
        if buttons_after_scroll is not None:
            state.buttons = buttons_after_scroll
        return (bool(state.buttons), 0)

    obj = PostsViewList.__new__(PostsViewList)
    obj.device = SimpleNamespace(find=find)
    obj._find_likers_container = find_likers_container
    obj._get_media_container = lambda: (
        FakeMedia(media_bottom),
        "Photo by someone, 2 likes",
    )
    return obj, state


def _run(obj):
    obj._like_in_post_view(LikeMode.SINGLE_CLICK, already_watched=True)


def test_presses_the_heart_of_this_post_not_the_one_above():
    above = FakeButton(top=147)  # post already scrolled past
    mine = FakeButton(top=1645)  # starts exactly where the media ends
    obj, state = _make([above, mine])
    _run(obj)
    assert mine.clicks == 1, mine.clicks
    assert above.clicks == 0, "pressed the neighbouring post"
    assert state.scrolls == 0, state.scrolls


def test_picks_the_nearest_heart_below_the_media():
    mine = FakeButton(top=1645)
    further = FakeButton(top=2400)
    obj, _ = _make([further, mine])
    _run(obj)
    assert mine.clicks == 1, mine.clicks
    assert further.clicks == 0, further.clicks


def test_scrolls_when_every_heart_is_above_the_media():
    above = FakeButton(top=147)
    mine = FakeButton(top=1645)
    obj, state = _make([above], buttons_after_scroll=[above, mine])
    _run(obj)
    assert state.scrolls == 1, state.scrolls
    assert mine.clicks == 1, mine.clicks


def test_gives_up_when_there_is_no_heart_at_all():
    obj, state = _make([], buttons_after_scroll=[])
    _run(obj)
    assert state.scrolls == 1, state.scrolls


def main():
    test_presses_the_heart_of_this_post_not_the_one_above()
    test_picks_the_nearest_heart_below_the_media()
    test_scrolls_when_every_heart_is_above_the_media()
    test_gives_up_when_there_is_no_heart_at_all()
    print("OK")


if __name__ == "__main__":
    main()
