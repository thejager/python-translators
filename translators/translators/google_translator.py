# -*- coding: utf-8 -*-

import re

import HTMLParser
from googleapiclient.discovery import build
import xml.etree.ElementTree as ET
import cgi

from context_aware_translator import ContextAwareTranslator

re_opening_tag = re.compile(r"<[\s]*[sS]pan[\s]*>(.*)", flags=re.DOTALL)  # <span> tag
re_closing_tag = re.compile(r"(.*?)<[\s]*/[\s]*[sS]pan[\s]*>", flags=re.DOTALL)  # </span> tag


class GoogleTranslator(ContextAwareTranslator):

    gt_instance = None

    def __init__(self, source_language, target_language, key):
        super(GoogleTranslator, self).__init__(source_language, target_language)

        self.key = key
        self.translation_service = build('translate', 'v2', developerKey=key)

    def translate(self, query, max_translations=1):
        """
        Translate a query from source language to target language
        :param max_translations: 
        :param after_context: 
        :param before_context: 
        :param query:
        :return:
        """

        params = {
            'source': self.source_language,
            'target': self.target_language,
            'q': query,
            'format': 'html',
        }

        translations = self.translation_service.translations().list(**params).execute()
        translation = translations['translations'][0][u'translatedText']

        # Unescape HTML characters
        unescaped_translation = HTMLParser.HTMLParser().unescape(translation)

        return unescaped_translation

    def _ca_translate(self, query, before_context='', after_context='', max_translations=1):
        """
        Function to translate a query by taking into account the context
        :param max_translations: 
        :param query:
        :param before_context:
        :param after_context:
        :return:
        """

        # Escape HTML
        query = cgi.escape(query)
        before_context = cgi.escape(before_context)
        after_context = cgi.escape(after_context)

        query = u'%(before_context)s<span>%(query)s</span>%(after_context)s' % locals()  # enclose query in span tags

        print(query)

        translation = self.translate(query)

        translated_query = GoogleTranslator.parse_spanned_string(translation).strip()

        stripped_after_context = after_context.strip()

        if stripped_after_context and translated_query and stripped_after_context[0] in ",;'.\"-" \
                and translated_query[-1] == stripped_after_context[0]:
            translated_query = translated_query[:-1]

        return translated_query

    @staticmethod
    def parse_spanned_string(spanned_string):

        xml_object = ET.fromstring('<s>' + spanned_string.encode('utf-8') + '</s>')

        found_span = xml_object.find('span')

        if found_span is None:
            return spanned_string

        return found_span.text


if __name__ == '__main__':
    t = GoogleTranslator(source_language='en', target_language='nl', key='AIzaSyCaahQqG18a5ok1A6UE_XgpAXBGc7aI4KM')
    print(t.ca_translate(before_context='He', query='leaves', after_context='the building'))
