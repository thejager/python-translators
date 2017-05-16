from .context_aware_translator import ContextAwareTranslator
import urllib.request, urllib.parse, urllib.error
import requests
import time
import xml.etree.ElementTree as ET

from typing import Dict
from .config_parsing import get_key_from_config

TOKEN_SERVICE_URL = 'https://api.cognitive.microsoft.com/sts/v1.0/issueToken'
TRANSLATION_SERVICE_URL = 'https://api.microsofttranslator.com/V2/Http.svc/Translate'


class MicrosoftTranslator(ContextAwareTranslator):
    gt_instance = None

    def __init__(self, source_language: str, target_language: str, key: str = None) -> None:
        super(MicrosoftTranslator, self).__init__(source_language, target_language)

        if not key:
            key = get_key_from_config('MICROSOFT_TRANSLATE_API_KEY')

        self.key = key
        self.token = self.request_token()

    def _ca_translate(self, query: str, before_context: str, after_context: str, max_translations: int = 1) -> [str]:

        query = '%(before_context)s<span>%(query)s</span>%(after_context)s' % locals()  # enclose query in span tags

        translation = self.send_translation_request(query, 'text/html')

        # enclose in <s> tag to make it valid XML
        xml_object = ET.fromstring('<s>' + translation + '</s>')

        return [xml_object.find('span').text]

    def translate(self, query: str, max_translations: int = 1) -> [str]:
        return [self.send_translation_request(query, 'text/plain')]

    def send_translation_request(self, query: str, content_type: str) -> str:
        """
        Sends a translation request to the Microsoft Translation service, query parameters are 
        
        :param query: 
        :param content_type: 
        :return: 
        """

        # Refresh token if necessary
        if time.time() <= self.token['expiresAt']:
            self.refresh_token()

        # Build query parameters
        query_params = {
            'text': query.encode('utf-8'),
            'from': self.source_language,
            'to': self.target_language,
            'contentType': content_type,
        }

        # Build headers
        headers = {
            'Accept': 'application/xml',
            'Authorization': 'Bearer ' + self.token['token'],
        }

        # Send request to API
        response = requests.get(TRANSLATION_SERVICE_URL + '?' + urllib.parse.urlencode(query_params), headers=headers)

        xml_object = ET.fromstring(response.text.encode('utf-8'))

        return xml_object.text

    def refresh_token(self) -> None:
        self.token = self.request_token()

    def request_token(self) -> Dict:
        headers = {
            "Ocp-Apim-Subscription-Key": self.key,
            "Accept": 'application/jwt',
            'Content-Type': 'application/json',
        }

        response = requests.post('https://api.cognitive.microsoft.com/sts/v1.0/issueToken', headers=headers)

        if response.status_code == 401:
            raise Exception('Access denied due to invalid subscription key. Make sure to provide a valid key for an '
                            'active subscription.')

        if response.status_code != 200:
            raise Exception('Something went wrong when requesting a new token.')

        return {
            'expiresAt': time.time() + (60 * 8),  # expire after 8 minutes
            'token': response.text,
        }