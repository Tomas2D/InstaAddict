"""IG 447 describes a carousel element as 'Photo 1 of 4 by ...', which the old
^Photo branch classified as a single photo.

Run: PYTHONPATH=. python test/test_detect_media_type.py
"""

from InstaAddict.core.views import MediaType, PostsViewList

detect = PostsViewList.detect_media_type


def test_carousel_new_format():
    assert detect("Photo 1 of 4 by Some Account, 2,280 likes") == (
        MediaType.CAROUSEL,
        4,
    )


def test_carousel_video_element():
    assert detect("Video 2 of 3 by Some Account") == (MediaType.CAROUSEL, 3)


def test_plain_photo_still_photo():
    assert detect("Photo by Dusty Pilgrim, 2 likes, 1 comment") == (
        MediaType.PHOTO,
        1,
    )


def test_plain_video_still_video():
    assert detect("Video by Someone, 5 likes") == (MediaType.VIDEO, 1)


def test_reel_still_reel():
    assert detect("Reel by Someone") == (MediaType.REEL, 1)


def test_empty_desc_unknown():
    assert detect("") == (MediaType.UNKNOWN, 1)


def test_none_desc():
    assert detect(None) == (None, None)


def main():
    test_carousel_new_format()
    test_carousel_video_element()
    test_plain_photo_still_photo()
    test_plain_video_still_video()
    test_reel_still_reel()
    test_empty_desc_unknown()
    test_none_desc()
    print("OK")


if __name__ == "__main__":
    main()
