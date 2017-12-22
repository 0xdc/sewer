import json

try:
    import urlparse
except ImportError:
    from urllib.parse import urlparse

import os_client_config
from structlog import get_logger

from . import common


class RackspaceDns(common.BaseDns):
    """
    """

    def __init__(self):

        self.dns_provider_name = 'rackspace'

        self.logger = get_logger(__name__).bind(
            dns_provider_name=self.dns_provider_name)

    def create_dns_record(self, domain_name, base64_of_acme_keyauthorization):
        self.logger.info('create_dns_record', domain=domain_name)

        # delete any prior existing DNS authorizations that may exist already
        self.delete_dns_record(
            domain_name=domain_name,
            base64_of_acme_keyauthorization=base64_of_acme_keyauthorization)

        body = {
            "type": "TXT",
            "name": '_acme-challenge' + '.' + domain_name + '.',
            "content": "{0}".format(base64_of_acme_keyauthorization)
        }
        # XXX: TODO

    def delete_dns_record(self, domain_name, base64_of_acme_keyauthorization):
        self.logger.info('delete_dns_record', domain=domain_name)

        dns_name = '_acme-challenge' + '.' + domain_name
        list_dns_payload = {'type': 'TXT', 'name': dns_name}

        list_dns_response = []
        # XXX: TODO

        for record in list_dns_response:
            dns_record_id = record['id']
            # XXX: TODO

    def get_zone_id(self, domain_name):
        # XXX: TODO
        pass
