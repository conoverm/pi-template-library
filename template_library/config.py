from datetime import date
import os

VERSION = (0, 1, 0)

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

RUN_LEVEL = os.environ.get('RUN_LEVEL', 'dev')

if RUN_LEVEL != 'prod':
	DEBUG = True
else:
	DEBUG = False

SECRET_KEY = os.environ.get('SECRET_KEY', 'DEVELOPMENT_KEY')

SINGULAR = {
	'supply_sources': 'supply_source',
	'deals': 'deal',
	'site_placements': 'site_placement',
}
SUPPLIES = set(['supply_sources', 'deals', 'site_placements'])
STRATEGY_PROPERTIES = set([
	'audience_segment_exclude_op',
	'audience_segment_include_op',
	'bid_aggressiveness',
	'bid_price_is_media_only',
	'budget',
	'campaign_id',
	'concept_id',
	'description',
	'end_date',
	'frequency_amount',
	'frequency_interval',
	'frequency_type',
	'goal_type',
	'goal_value',
	'id',
	'impression_cap',
	'max_bid',
	'name',
	'pacing_amount',
	'pacing_interval',
	'pacing_type',
	'pixel_target_expr',
	'roi_target',
	'run_on_all_exchanges',
	'run_on_all_pmp',
	'run_on_display',
	'run_on_mobile',
	'run_on_streaming',
	'site_restriction_transparent_urls',
	'site_selectiveness',
	'start_date',
	'status',
	'strategy_id',
	'supply_source_id',
	'type',
	'use_campaign_end',
	'use_campaign_start',
	'use_mm_freq',
	'use_optimization',
	'version',
])
TARGET_DIMENSIONS = set([
	'audio',
	'browser',
	'channels',
	'connection speed',
	'content initiation',
	'country',
	'device',
	'dma',
	'fold position',
	'isp',
	'linear format',
	'mathselect250',
	'os',
	'player size',
	'region',
	'safety',
])
