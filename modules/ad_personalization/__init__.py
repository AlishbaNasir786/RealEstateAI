"""
__init__.py for ad_personalization module
"""
from .segments import SEGMENTS, get_segment, get_all_segments
from .ad_generator import generate_ad_campaign
from .cache import get_cached_ads, set_cached_ads
