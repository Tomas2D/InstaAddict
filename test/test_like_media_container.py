"""Regression checks for IG 447 feed layout.

Two problems, both caused by device.find() returning the first match in tree order:

1. The feed keeps thin slivers of already scrolled posts at the top and bottom of
   the list. They carry the same ids as real media but describe nothing, and being
   first they used to win - the double tap then landed on a 54px strip in the
   header and no like was registered.
2. The post description moved from media_group to the nested
   row_feed_photo_imageview / carousel_image.

Run: PYTHONPATH=. python test/test_like_media_container.py
"""

from types import SimpleNamespace

from InstaAddict.core import views

views.ResourceID = views.resources("com.instagram.android")

MEDIA_ID = views.ResourceID.CAROUSEL_AND_MEDIA_GROUP


class FakeView:
    """Minimal stand-in for DeviceFacade.View."""

    def __init__(self, desc=None, exists=True, children=None, bounds=None):
        self.desc = desc
        self._exists = exists
        self.children = children or {}
        self._bounds = bounds or {"top": 0, "bottom": 0, "left": 0, "right": 0}

    def exists(self, *_):
        return self._exists

    def get_desc(self):
        return self.desc

    def get_bounds(self):
        return self._bounds

    def child(self, **kwargs):
        pattern = kwargs.get("resourceIdMatches", "")
        for key, view in self.children.items():
            if key in pattern:
                return view
        return FakeView(exists=False)


def _view_with(matches):
    """matches: the list device.find() would iterate over, in tree order."""
    holder = FakeView(exists=bool(matches))
    holder.count_items = lambda: len(matches)

    def find(**kw):
        if kw.get("resourceIdMatches") != MEDIA_ID:
            return FakeView(exists=False)
        index = kw.get("index")
        return holder if index is None else matches[index]

    obj = views.PostsViewList.__new__(views.PostsViewList)
    obj.device = SimpleNamespace(find=find)
    return obj, holder


def test_sliver_is_skipped_in_favour_of_the_real_post():
    sliver = FakeView(desc=None, bounds={"top": 93, "bottom": 147})
    real = FakeView(desc="Video 2 of 3 by someone, 31 likes")
    obj, _ = _view_with([sliver, real])
    container, desc = obj._get_media_container()
    assert container is real, "picked the sliver instead of the post"
    assert desc == "Video 2 of 3 by someone, 31 likes", desc


def test_first_match_wins_when_it_describes_a_post():
    real = FakeView(desc="Photo by someone, 2 likes")
    other = FakeView(desc="Photo by another, 9 likes")
    obj, _ = _view_with([real, other])
    container, desc = obj._get_media_container()
    assert container is real, "took a later post"
    assert desc == "Photo by someone, 2 likes", desc


def test_description_taken_from_inner_image_view():
    inner = FakeView(desc="Photo by someone, 2 likes, 1 comment")
    outer = FakeView(desc=None, children={"row_feed_photo_imageview": inner})
    obj, _ = _view_with([outer])
    container, desc = obj._get_media_container()
    assert container is outer, container
    assert desc == "Photo by someone, 2 likes, 1 comment", desc


def test_description_taken_from_inner_carousel_image():
    inner = FakeView(desc="Photo 1 of 4 by someone, 2,280 likes")
    outer = FakeView(desc=None, children={"carousel_image": inner})
    obj, _ = _view_with([outer])
    _, desc = obj._get_media_container()
    assert desc == "Photo 1 of 4 by someone, 2,280 likes", desc


def test_nothing_on_screen():
    obj, holder = _view_with([])
    container, desc = obj._get_media_container()
    assert container is holder, container
    assert desc is None, desc


def test_only_slivers_means_no_post():
    obj, holder = _view_with([FakeView(desc=None), FakeView(desc="")])
    container, desc = obj._get_media_container()
    assert container is holder, container
    assert desc is None, desc


def main():
    test_sliver_is_skipped_in_favour_of_the_real_post()
    test_first_match_wins_when_it_describes_a_post()
    test_description_taken_from_inner_image_view()
    test_description_taken_from_inner_carousel_image()
    test_nothing_on_screen()
    test_only_slivers_means_no_post()
    print("OK")


if __name__ == "__main__":
    main()
