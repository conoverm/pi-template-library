# -*- coding: utf-8 -*-
"""Parses XML output from T1 and returns a (relatively) sane Python object."""

from __future__ import absolute_import

try:
    from itertools import imap

    map = imap
    import xml.etree.cElementTree as ET
except ImportError:  # Python 3
    import xml.etree.ElementTree as ET
from .errors import (T1Error, ValidationError, ParserException, STATUS_CODES)

ParseError = ET.ParseError


class XMLParser(object):
    """Parses XML response"""

    def __init__(self, xml):
        try:
            result = ET.fromstring(xml)
        except ParseError as e:
            raise ParserException(e)

        self.get_status(result, xml)

        def xfind(haystack, needle):
            return haystack.find(needle) is not None

        if xfind(result, 'entities'):
            self._parse_collection(result)

        elif xfind(result, 'entity'):
            self.entity_count = 1
            self.entities = self._parse_entities(result)

        elif any(xfind(result, x) for x in ['include, exclude', 'enabled']):
            self._parse_target_dimensions(result)

        elif xfind(result, 'permissions'):
            self._parse_permissions(result)

        elif xfind(result, 'log_entries'):
            self.entity_count = 1
            self.entities = map(self.dictify_history_entry,
                                result.iterfind('log_entries/entry'))

    def get_status(self, xmlresult, xml):
        """Gets the status code of T1 XML.

        If code is valid, returns None; otherwise raises the appropriate Error.
        """
        status = xmlresult.find('status')
        if status is None:
            raise T1Error(None, xml)
        status_code = status.attrib['code']
        message = status.text

        try:
            exc = STATUS_CODES[status_code]
        except KeyError:
            self.status_code = False
            raise T1Error(status_code, message)

        if exc is None:
            self.status_code = True
            return

        self.status_code = False
        if exc is True:
            message = self._parse_field_error(xmlresult)
            exc = ValidationError

        raise exc(status_code, message)

    def _parse_entities(self, ent_root):
        """Iterate over entities and parse them into dictionaries"""
        return map(self.dictify_entity, ent_root.iterfind('entity'))

    def _parse_collection(self, result):
        """Iterate over collection (i.e. "entities" tag) and parse into dicts"""
        root = result.find('entities')
        self.entity_count = int(root.get('count') or 0)
        self.entities = self._parse_entities(root)

    def _parse_target_dimensions(self, result):
        """Iterate over target dimensions and parse into dicts"""
        exclude = map(self.dictify_entity,
                      result.iterfind('exclude/entities/entity'))
        include = map(self.dictify_entity,
                      result.iterfind('include/entities/entity'))
        self.entity_count = 1
        self.entities = [{
            '_type': 'target_dimension',
            'exclude': exclude,
            'include': include,
        }]

    def _parse_permissions(self, result):
        """Iterate over permissions and parse into dicts"""
        root = result.find('permissions/entities')
        organization, agency, advertiser = None, None, None
        if root:
            advertiser = self.dictify_permission(root.find('advertiser'))
            agency = self.dictify_permission(root.find('agency'))
            organization = self.dictify_permission(root.find('organization'))

        flags = self.dictify_permission(result.find('permissions/flags'))
        flags.update({
            '_type': 'permission',
            'advertiser': advertiser,
            'agency': agency,
            'organization': organization,
        })

        # There will only be one instance here.
        # But the caller expects an iterator, so make a list of it
        self.entities, self.entity_count = [flags, ], 1

    @staticmethod
    def _parse_field_error(xml):
        """Iterate over field errors and parse into dicts"""
        errors = {}
        for error in xml.iter('field-error'):
            attribs = error.attrib
            errors[attribs['name']] = {'code': attribs['code'],
                                       'error': attribs['error']}
        return errors

    def dictify_entity(self, entity):
        """Turn XML entity into a dictionary"""
        output = entity.attrib
        # Hold relation objects in specific dict. T1Service instantiates the
        # correct classes.
        relations = {}
        if 'type' in output:
            output['_type'] = output['type']
            del output['type']
        for prop in entity:
            if prop.tag == 'entity':  # Get parent entities recursively
                ent = self.dictify_entity(prop)
                if prop.attrib['rel'] == ent.get('_type'):
                    relations[prop.attrib['rel']] = ent
                else:
                    relations.setdefault(prop.attrib['rel'], []).append(ent)
            else:
                output[prop.attrib['name']] = prop.attrib['value']
        if relations:
            output['relations'] = relations
        return output

    @staticmethod
    def dictify_permission(entity):
        """Turn XML permission into a dictionary"""
        if not entity:
            return
        output = {}
        if entity.tag == 'flags':
            for prop in entity:
                output[prop.attrib['type']] = prop.attrib['value']
        else:
            for prop in entity:
                output[int(prop.attrib['id'])] = prop.attrib['name']
        return output

    @staticmethod
    def dictify_history_entry(entry):
        """Turn XML history into a dictionary"""
        output = entry.attrib
        fields = {}
        for field in entry:
            kind = field.attrib['name']
            if kind != 'last_modified':
                fields[kind] = {'old_value': field.attrib['old_value'],
                                'new_value': field.attrib['new_value']}
        output['fields'] = fields
        return output
