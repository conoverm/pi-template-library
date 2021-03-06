# -*- coding: utf-8 -*-
"""Provides creative object."""

from __future__ import absolute_import
from ..entity import Entity


class Creative(Entity):
    """Provides creative entity."""
    collection = 'creatives'
    resource = 'creative'
    _relations = {
        'atomic_creative',
        'creative_assets',
        'tmt_creative_scan',
        'tmt_creative_scan_event',
        'vendor_pixels',
    }
    _pull = {
        'atomic_creative_id': int,
        'created_on': Entity._strpt,
        'id': int,
        'last_modified': Entity._strpt,
        'tag': None,
        'tag_type': None,
        'version': int,
    }
    _push = _pull

    def __init__(self, session, properties=None, **kwargs):
        super(Creative, self).__init__(session, properties, **kwargs)
