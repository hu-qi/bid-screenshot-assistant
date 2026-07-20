from bid_screenshot_assistant.adapters import DESCRIPTORS
from bid_screenshot_assistant.domain.models import PlatformId


def test_catalog_has_exactly_nine_unique_platforms():
    ids = [item.platform_id for item in DESCRIPTORS]
    assert len(ids) == 9
    assert len(set(ids)) == 9
    assert set(ids) == set(PlatformId)
