import json
import urlparse

import CloudFlare
from structlog import get_logger

from . import common


class CloudFlareDns(common.BaseDns):
    """
    """

    def __init__(self):

        self.cfapi = CloudFlare.CloudFlare()
        self.dns_provider_name = 'cloudflare'

        self.logger = get_logger(__name__).bind(
            dns_provider_name=self.dns_provider_name)

    def create_dns_record(self, domain_name, base64_of_acme_keyauthorization):
        self.logger.info('create_dns_record', domain=domain_name)

        # delete any prior existing DNS authorizations that may exist already
        self.delete_dns_record(
            domain_name=domain_name,
            base64_of_acme_keyauthorization=base64_of_acme_keyauthorization)

        zone_id = self.get_zone_id(domain_name)

        body = {
            "type": "TXT",
            "name": '_acme-challenge' + '.' + domain_name + '.',
            "content": "{0}".format(base64_of_acme_keyauthorization)
        }
        try:
            create_cloudflare_dns_record_response = self.cfapi.zones.dns_records.post(zone_id, data=body)
            self.logger.info('create_cloudflare_dns_record_response')
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            self.logger.error('create_dns_record error', err=int(e), response=str(e))

    def delete_dns_record(self, domain_name, base64_of_acme_keyauthorization):
        self.logger.info('delete_dns_record', domain=domain_name)

        zone_id = self.get_zone_id(domain_name)
        dns_name = '_acme-challenge' + '.' + domain_name
        list_dns_payload = {'type': 'TXT', 'name': dns_name}

        list_dns_response = self.cfapi.zones.dns_records.get(zone_id,
            params=list_dns_payload)

        for record in list_dns_response:
            dns_record_id = record['id']
            try:
                delete_dns_record_response = self.cfapi.zones.dns_records.delete(zone_id, dns_record_id)
                self.logger.info('delete_dns_record success')
            except CloudFlare.exceptions.CloudFlareAPIError as e:
                self.logger.error('delete_dns_record error', err=int(e), response=str(e))

    def get_zone_id(self, domain_name):
        try:
            zone = self.cfapi.zones.get(params={'name': domain_name})[0]
            return zone['id']
        except IndexError:
            zones = self.cfapi.zones.get()
            for zone in zones:
                if zone['name'] in domain_name:
                    return zone['id']
