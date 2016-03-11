from __future__ import division
from datetime import datetime
import json
import logging
import os
from time import sleep
import traceback
from types import GeneratorType
from flask import Flask, jsonify, request
from terminalone import T1
from terminalone.errors import (APIError, AuthRequiredError, ClientError, NotFoundError,
								ParserException, ValidationError, T1Error)
from terminalone.models import TargetValue
from .config import BASE_CONFIG, SINGULAR, SUPPLIES, STRATEGY_PROPERTIES, TARGET_DIMENSIONS

app = Flask(__name__)
app.config.from_object('template_library.config')


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
UP_ONE_DIR = os.path.dirname(CURRENT_DIR)
REQUEST_LOG = os.path.join(UP_ONE_DIR, 'log', 'request.log')
LOG_FILE = os.path.join(UP_ONE_DIR, 'log', 'api.log')

CLIENT_ERRORS = (AuthRequiredError, NotFoundError, ClientError, ParserException,
					ValidationError, ValueError)
ADAMA_ERRORS = (APIError, T1Error)

formatter = logging.Formatter('%(asctime)s|%(name)s|%(levelname)s|%(message)s')
request_logger = logging.getLogger('request_logger')
request_file_handler = logging.FileHandler(REQUEST_LOG)
request_file_handler.setFormatter(formatter)
request_logger.addHandler(request_file_handler)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
	format='%(asctime)s|%(name)s|%(levelname)s|%(message)s')

def empty_generator():
	return
	yield

def new_t1():
	session = request.cookies['adama_session']
	t1 = retry_return(5, T1,
					auth_method='cookie',
					session_id=session,
					api_base=BASE_CONFIG[request.headers['Host']][0])
	return t1

def return_status(content, code=200, data=None):
	response = {'message': content, 'code': code}
	if data:
		response['data'] = data
	response = jsonify(response)
	response.status_code = code
	return response

def log_request(_request):
	row = 'Cookies: {}\nData: {}'.format(str(_request.cookies), str(_request.data))
	request_logger.info(row)

def retry(attempts, method, *args, **kwargs):
	try:
		method(*args, **kwargs)
	except (CLIENT_ERRORS, ADAMA_ERRORS):
		if attempts > 1:
			sleep(2)
			retry(attempts-1, method, *args, **kwargs)
		else:
			raise

def retry_return(attempts, method, *args, **kwargs):
	try:
		return method(*args, **kwargs)
	except (CLIENT_ERRORS, ADAMA_ERRORS):
		if attempts > 1:
			sleep(2)
			return retry_return(attempts-1, method, *args, **kwargs)
		else:
			raise

def save_then_deserialize(strategy):
	if isinstance(strategy.pixel_target_expr, str):
		strategy._deserialize_target_expr()
	strategy.save()

def update_targeting(originals, changes, operation=None):
	if isinstance(changes, int):
		_changes = set([changes])
	elif isinstance(changes, list):
		_changes = set(changes)
	else:
		raise ValueError('Bad format')
	_originals = set(originals)

	if operation == 'add':
		return list(_originals.union(_changes))
	elif operation == 'remove':
		return list(_originals.difference(_changes))
	else:
		return originals


@app.route('/')
def hello():
    return '<html><body><script src="https://ajax.googleapis.com/ajax/libs/jquery/2.2.0/jquery.min.js"></script>Hello World!</body></html>'

@app.route('/strategies/create', methods=['POST'])
def edit_strategies():
	log_request(request)
	try:
		t1 = new_t1()
	except KeyError as e:
		logging.info('Error: {}\nCaused traceback: {}'.format(str(e),
									traceback.format_exc()))
		return return_status('No session passed', code=400)
	except CLIENT_ERRORS as e:
		logging.info('Error: {}\nCaused traceback: {}'.format(str(e),
						traceback.format_exc()))
		return return_status('Error\n{}'.format(str(e)), code=400)
	
	data = json.loads(request.data)

	if isinstance(data, dict):
		data = [data]
	
	# ONLY FOR PING PONG
	# print data
	# return return_status('PONG!', 200, data=data)
	#

	for template_strategy in data:
		properties = template_strategy.get('properties', {})
		pixel_targeting = template_strategy.get('pixel_targeting')
		child_entities = template_strategy.get('child_entities', {})

		try:
			strategy = t1.new('strategy')
		except CLIENT_ERRORS as e:
			logging.info('Error: {}\nCaused traceback: {}'.format(str(e),
							traceback.format_exc()))
			return return_status('Error\n{}'.format(str(e)), code=400)

		# Any properties that t1-python recognizes can be edited
		for _property, value in properties.iteritems():
			if (_property in strategy.properties or
				_property in STRATEGY_PROPERTIES):
				strategy.properties[str(_property)] = value

		# t1-python expects date objects
		if strategy.properties.get('start_date') and (
			type(strategy.properties.get('start_date')) != datetime):
			strategy.properties['start_date'] = datetime.strptime(
									strategy.start_date, "%Y-%m-%dT%H:%M:%S")
		if strategy.properties.get('end_date') and (
			type(strategy.properties.get('end_date')) != datetime):
			strategy.properties['end_date'] = datetime.strptime(
									strategy.end_date, "%Y-%m-%dT%H:%M:%S")

		# Pixel Targeting is a special case
		if isinstance(pixel_targeting, dict) and any(
			command in pixel_targeting for command in ('add', 'remove',
								'include_operator', 'exclude_operator')):
			additions = pixel_targeting.get('add', {})
			removals = pixel_targeting.get('remove', {})
			for targeting_group, _additions in additions.iteritems():
				try:
					pix = strategy.pixel_target_expr[targeting_group]['pixels'][:]
				except KeyError as e:
					logging.info('Error: {}\nCaused traceback: {}'.format(str(e),
									traceback.format_exc()))
					return return_status(
						'Invalid targeting group: {}'.format(targeting_group),
						code=400
					)
				try:
					pix = update_targeting(pix, _additions, 'add')
				except ValueError as e:
					logging.info('Error: {}\nCaused traceback: {}'.format(str(e),
									traceback.format_exc()))
					return return_status(
						'Invalid pixel data format: {}'.format(_additions),
						code=400
					)
				strategy.pixel_target_expr[targeting_group]['pixels'] = pix

			for targeting_group, _removals in removals.iteritems():
				try:
					pix = strategy.pixel_target_expr[targeting_group]['pixels'][:]
				except KeyError as e:
					logging.info('Error: {}\nCaused traceback: {}'.format(str(e),
									traceback.format_exc()))
					return return_status(
						'Invalid targeting group: {}'.format(targeting_group),
						code=400
					)
				try:
					pix = update_targeting(pix, _removals, 'remove')
				except ValueError as e:
					logging.info('Error: {}\nCaused traceback: {}'.format(str(e),
									traceback.format_exc()))
					return return_status(
						'Invalid pixel data format: {}'.format(_removals),
						code=400
					)
				strategy.pixel_target_expr[targeting_group]['pixels'] = pix

			include_op = pixel_targeting.get('include_operator')
			exclude_op = pixel_targeting.get('exclude_operator')
			if include_op in ('AND', 'OR'):
				strategy.pixel_target_expr['include']['operator'] = include_op
			if exclude_op in ('AND', 'OR'):
				strategy.pixel_target_expr['exclude']['operator'] = exclude_op

		strategy.properties['version'] = 0

		# POST Strategy edits & logging
		try:
			props_before_save = strategy.properties.copy()
			retry(5, save_then_deserialize, strategy)
		except CLIENT_ERRORS as e:
			logging.info('Error: {}\nCaused traceback: {}'.format(str(e),
							traceback.format_exc()))
			logging.info('Strategy properties before save: {}'.format(
														props_before_save))
			return return_status('Error\n{}'.format(str(e)), code=400)
		except Exception as e:
			logging.info('Error: {}\nCaused traceback: {}'.format(str(e),
							traceback.format_exc()))
			logging.info('Strategy properties before save: {}'.format(
														props_before_save))
			return return_status('Unexpected error occured', code=500)
		_id = strategy.id

		# All Target Dimensions are handled the same way
		# Iteration syntax works only in Python 3 and 2.7+
		for _type, _properties in {k: child_entities[k] for k in
			child_entities if k in TARGET_DIMENSIONS}.iteritems():
			try:
				child = retry_return(5, t1.get, 'strategies', _id, child=_type)
			except StopIteration as e:
				logging.info('Error: {}\nCaused traceback: {}'.format(str(e),
									traceback.format_exc()))
				return return_status(
					('Not possible to edit when '
						'entity does not exist: {}'.format(_type)),
					code=400
				)
			except ClientError as e:
				logging.info('Error: {}\nCaused traceback: {}'.format(str(e),
									traceback.format_exc()))
				return return_status(
					str(e),
					code=400
				)

			additions = _properties.get('add', {})
			removals = _properties.get('remove', {})
			if isinstance(_properties.get('include'), list):
				child.include = _properties['include']
			if isinstance(_properties.get('exclude'), list):
				child.exclude = _properties['exclude']
			for targeting_group, _additions in additions.iteritems():
				try:
					target_vals = [_val.id if isinstance(_val, TargetValue)
						else _val for _val in child.properties[targeting_group]]
				except KeyError as e:
					logging.info('Error: {}\nCaused traceback: {}'.format(str(e),
									traceback.format_exc()))
					return return_status(
						'Invalid targeting group: {}'.format(targeting_group),
						code=400
					)
				try:
					target_vals = update_targeting(target_vals, _additions, 'add')
				except ValueError as e:
					logging.info('Error: {}\nCaused traceback: {}'.format(str(e),
									traceback.format_exc()))
					return return_status(
						'Invalid target_values data format: {}'.format(_additions),
						code=400
					)
				child.properties[targeting_group] = target_vals

			for targeting_group, _removals in removals.iteritems():
				try:
					target_vals = [_val.id if isinstance(_val, TargetValue)
						else _val for _val in child.properties[targeting_group]]
				except KeyError as e:
					logging.info('Error: {}\nCaused traceback: {}'.format(str(e),
									traceback.format_exc()))
					return return_status(
						'Invalid targeting group: {}'.format(targeting_group),
						code=400
					)
				try:
					target_vals = update_targeting(target_vals, _removals, 'remove')
				except ValueError as e:
					logging.info('Error: {}\nCaused traceback: {}'.format(str(e),
									traceback.format_exc()))
					return return_status(
						'Invalid target_values data format: {}'.format(_removals),
						code=400
					)
				child.properties[targeting_group] = target_vals

			try:
				retry(5, child.save)
			except CLIENT_ERRORS as e:
				logging.info('Error: {}\nCaused traceback: {}'.format(str(e),
								traceback.format_exc()))
				return return_status('Error\n{}'.format(str(e)), code=400)


		# Day Parts are a special case
		# TODO: Removing day parts
		# TODO: Editing multiple day parts with different settings
		day_parts = child_entities.get('day_parts')
		if isinstance(day_parts, dict) and any(
			command in day_parts for command in ('properties', 'add', 'remove')):
			try:
				children = retry_return(5, t1.get, 'strategies', _id, child='day_parts')
			except StopIteration:
				children = empty_generator()
			if not isinstance(children, GeneratorType):
				children = iter([children])
			child_properties = day_parts.get('properties', {})
			additions = day_parts.get('add', [])
			removals = day_parts.get('remove', [])
			try:
				day_part = next(children)
			except StopIteration:
				day_part = False
			if day_part:
				for _property, value in child_properties.iteritems():
					if value != '' and _property in day_part.properties:
						day_part.properties[_property] = value
				try:
					# edited_dp = t1.new('strategy_day_part')
					# edited_dp.set(day_part.properties.copy())
					# del edited_dp.id, edited_dp.name
					# retry(5, edited_dp.save)
					retry(5, day_part.save)
				except CLIENT_ERRORS as e:
					logging.info('Error: {}\nCaused traceback: {}'.format(str(e),
									traceback.format_exc()))
					logging.info('Failed to save obj:\n{}'.format(
											str(day_part.properties))
					)
					return return_status('Error\n{}'.format(str(e)), code=400)

			for new_properties in additions:
				new_daypart = t1.new('strategy_day_part')
				new_daypart.properties = new_properties
				new_daypart.properties['strategy_id'] = _id
				try:
					retry(5, new_daypart.save)
				except CLIENT_ERRORS as e:
					logging.info('Error: {}\nCaused traceback: {}'.format(str(e),
									traceback.format_exc()))
					return return_status('Error\n{}'.format(str(e)), code=400)


		# Concepts are a special case
		concepts = child_entities.get('concepts')
		if isinstance(concepts, dict) and any(
			command in concepts for command in ('add', 'remove')):
			additions = concepts.get('add', [])
			removals = concepts.get('remove', [])
			for concept_id in additions:
				new_concept = t1.new('strategy_concept')
				new_concept.strategy_id = _id
				new_concept.concept_id = concept_id
				try:
					retry(5, new_concept.save)
				except CLIENT_ERRORS as e:
					logging.info('Error: {}\nCaused traceback: {}'.format(str(e),
									traceback.format_exc()))
					return return_status('Error\n{}'.format(str(e)), code=400)
			try:
				strategy_concepts = retry_return(5, t1.get, 'strategies', _id,
								include='strategy_concepts')
				strategy_concepts = strategy_concepts.strategy_concepts
			except (StopIteration, AttributeError):
				strategy_concepts = empty_generator()
			for strategy_concept in strategy_concepts:
				if strategy_concept.concept_id in removals:
					strategy_concept.remove()


		# Supplies are a special case
		supplies = child_entities.get('supplies')
		if isinstance(supplies, dict) and any(
			source in supplies for source in SUPPLIES):
			for _type, ids in supplies.iteritems():
				data = {}
				i = 0
				for _id in ids:
					i += 1
					new_source = '{}.{}.id'.format(SINGULAR[_type], str(i))
					data[new_source] = _id
				strategy.properties['pixel_target_expr'] = strategy._serialize_target_expr()
				try:
					retry(5, strategy.save_supplies, data)
				except CLIENT_ERRORS as e:
					logging.info('Error: {}\nCaused traceback: {}'.format(str(e),
									traceback.format_exc()))
					return return_status('Error\n{}'.format(str(e)), code=400)

	return return_status('Success!', code=200)
	

if __name__ == '__main__' and __package__ is None:
	__package__ = 'template_library'
