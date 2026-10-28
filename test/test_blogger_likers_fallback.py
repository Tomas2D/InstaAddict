from types import SimpleNamespace
from unittest.mock import patch

from InstaAddict.core import views
from InstaAddict.core.views import PostsViewList
from InstaAddict.core import handle_sources

APP_ID = "com.instagram.android"
views.ResourceID = views.resources(APP_ID)
views.configs = SimpleNamespace(args=SimpleNamespace(app_id=APP_ID))


def _node(resource_id="", text="", bounds="[0,0][10,10]"):
    return (
        f'<node package="{APP_ID}" visible-to-user="true" '
        f'resource-id="{resource_id}" text="{text}" bounds="{bounds}" />'
    )


def _hierarchy(extra_nodes):
    return (
        "<hierarchy>"
        + _node(views.ResourceID.ROW_FEED_VIEW_GROUP_BUTTONS, bounds="[0,564][900,656]")
        + _node(views.ResourceID.ROW_FEED_BUTTON_LIKE, bounds="[24,564][72,656]")
        + extra_nodes
        + "</hierarchy>"
    )


def _reader(xml):
    return PostsViewList(
        SimpleNamespace(deviceV2=SimpleNamespace(dump_hierarchy=lambda: xml))
    )


def test_finds_bare_like_count_button():
    xml = _hierarchy(_node(text="174", bounds="[80,564][122,656]"))
    result = _reader(xml)._get_current_likers_info()
    assert result["text"] == "174"
    assert result["bounds"] == {"left": 80, "top": 564, "right": 122, "bottom": 656}


def test_prefers_exact_like_button_count_over_social_proof_text():
    social_proof = _node(
        text="Liked by someone and 1.2K others",
        bounds="[138,675][537,709]",
    )
    numeric_button = _node(text="294", bounds="[80,564][122,656]")
    result = _reader(
        _hierarchy(social_proof + numeric_button)
    )._get_current_likers_info()
    assert result["text"] == "294"
    assert result["bounds"]["left"] == 80


def test_bare_count_requires_digit_aligned_with_like_button():
    no_count = _reader(_hierarchy(_node(text="Like", bounds="[80,564][122,656]")))
    assert no_count._get_current_likers_info() is None

    # The only digit is aligned with the comment button, not the like button.
    comment_only = _hierarchy(
        _node(
            views.ResourceID.ROW_FEED_BUTTON_COMMENT,
            bounds="[134,564][182,656]",
        )
        + _node(text="8", bounds="[190,564][212,656]")
        + _node(views.ResourceID.ROW_FEED_BUTTON_LIKE, bounds="[24,564][72,656]")
    )
    assert _reader(comment_only)._get_current_likers_info() is None


def test_parses_numeric_and_legacy_like_labels():
    parser = PostsViewList.__new__(PostsViewList)
    expected = {
        "174": 174,
        "1,234": 1234,
        "12.3K": 12300,
        "1.2M": 1200000,
        "Liked by x and 5 others": 5,
        "Liked by x and 1.2K others": 1200,
        "12.3K likes": 12300,
        "5 likes": 5,
        "1 view": -1,
        "Liked by x": 1,
    }
    for label, count in expected.items():
        assert parser._get_number_of_likers_from_text(label) == count, label


def test_captionless_repeat_guard_dumps_hierarchy_and_stops():
    class FakePostsViewList:
        def __init__(self, device):
            self.device = device

        def _check_if_last_post(self, *_):
            return False, "", "fake_author", False, False, False

        def _find_likers_container(self):
            return False, 0

        def swipe_to_fit_posts(self, *_):
            pass

    device = SimpleNamespace(dump_calls=[])
    device.dump_hierarchy = lambda path: device.dump_calls.append(path)

    with (
        patch.object(handle_sources, "PostsViewList", FakePostsViewList),
        patch.object(handle_sources, "nav_to_post_likers", return_value=True),
    ):
        handle_sources.handle_likers(
            None,
            device,
            SimpleNamespace(my_username="fake"),
            "fake_target",
            "blogger-post-likers",
            None,
            None,
            None,
            None,
            None,
            None,
        )

    assert device.dump_calls == ["stuck_post.xml"]


def _check_post_description(next_header_top=None, caption_after_swipe=False):
    class FakeView:
        def __init__(self, exists, bounds=None, count=None):
            self._exists = exists
            self._bounds = bounds or {"top": 0, "bottom": 0}
            self._count = int(exists) if count is None else count

        def exists(self, *_):
            return self._exists

        def count_items(self):
            return self._count

        def get_bounds(self):
            return self._bounds

        def is_above_this(self, *_):
            return None

    class FakeDevice:
        def find(self, **kwargs):
            if kwargs.get("resourceId") == views.ResourceID.ROW_FEED_VIEW_GROUP_BUTTONS:
                return FakeView(True, {"top": 500, "bottom": 560})
            if kwargs.get("resourceId") == views.ResourceID.ROW_FEED_PROFILE_HEADER:
                if kwargs.get("index") is not None and next_header_top is not None:
                    return FakeView(
                        True, {"top": next_header_top, "bottom": next_header_top + 40}
                    )
                return FakeView(
                    next_header_top is not None, count=int(next_header_top is not None)
                )
            return FakeView(False)

    post = PostsViewList(FakeDevice())
    post._has_tags = lambda: False
    swipe_count = [0]
    post._find_caption_text_in_current_post = lambda *_: (
        "fake_author caption" if caption_after_swipe and swipe_count[0] else None
    )

    with (
        patch.object(
            PostsViewList,
            "_post_owner",
            return_value=("fake_author", False, False),
        ),
        patch.object(
            views.UniversalActions,
            "_swipe_points",
            side_effect=lambda *args, **kwargs: swipe_count.__setitem__(
                0, swipe_count[0] + 1
            ),
        ) as swipe,
    ):
        result = post._check_if_last_post("", "blogger-post-likers")
    return result, swipe_count[0], swipe.call_count


def test_captionless_post_with_next_header_does_not_swipe():
    result, swipe_count, calls = _check_post_description(next_header_top=600)
    assert result == (False, "", "fake_author", False, False, False)
    assert swipe_count == calls == 0


def test_action_row_without_next_header_keeps_retrying():
    result, swipe_count, calls = _check_post_description()
    assert result == (False, "", "fake_author", False, False, False)
    assert swipe_count == calls == 8


def test_caption_below_fold_is_found_after_swipe():
    result, swipe_count, calls = _check_post_description(caption_after_swipe=True)
    assert result == (
        False,
        "FAKE_AUTHOR CAPTION",
        "fake_author",
        False,
        False,
        False,
    )
    assert swipe_count == calls == 1


def main():
    test_finds_bare_like_count_button()
    test_bare_count_requires_digit_aligned_with_like_button()
    test_parses_numeric_and_legacy_like_labels()
    test_captionless_repeat_guard_dumps_hierarchy_and_stops()
    test_captionless_post_with_next_header_does_not_swipe()
    test_action_row_without_next_header_keeps_retrying()
    test_caption_below_fold_is_found_after_swipe()
    print("OK")


if __name__ == "__main__":
    main()
