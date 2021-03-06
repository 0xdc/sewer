import os
import argparse

from structlog import get_logger

from . import Client
from . import __version__ as sewer_version


def main():
    """
    Usage:
        1. To get a new certificate:
        CLOUDFLARE_EMAIL=example@example.com \
        CLOUDFLARE_DNS_ZONE_ID=some-zone \
        CLOUDFLARE_API_KEY=api-key \
        sewer \
        --dns cloudflare \
        --domain example.com \
    """
    # TODO: enable people to specify the location where they want certificate and keys to be stored.
    # currently, we store them in the directory from which sewer is ran
    parser = argparse.ArgumentParser(
        prog='sewer', description="Sewer is a Let's Encrypt(ACME) client.")
    parser.add_argument(
        "--version",
        action='version',
        version='%(prog)s {version}'.format(version=sewer_version.__version__),
        help="The currently installed sewer version.")
    parser.add_argument(
        "--account_key",
        type=argparse.FileType('r'),
        required=False,
        help="The path to your letsencrypt/acme account key. \
        eg: --account_key /home/myaccount.key")
    parser.add_argument(
        "--dns",
        type=str,
        required=True,
        choices=['cloudflare', 'aurora'],
        help="The name of the dns provider that you want to use.")
    parser.add_argument(
        "--domain",
        type=str,
        required=True,
        help="The domain/subdomain name for which \
        you want to get/renew certificate for. \
        eg: --domain example.com")
    parser.add_argument(
        "--alt_domains",
        type=str,
        required=False,
        default=[],
        nargs='*',
        help="A list of alternative domain/subdomain name/s(if any) for which \
        you want to get/renew certificate for. \
        eg: --alt_domains www.example.com blog.example.com")
    parser.add_argument(
        "--bundle_name",
        type=str,
        required=False,
        help="The name to use for certificate \
        certificate key and account key. Default is value of domain.")
    parser.add_argument(
        "--email",
        type=str,
        required=False,
        help="Email to be used for registration and recovery. \
        eg: --email me@example.com")

    args = parser.parse_args()
    logger = get_logger(__name__)

    dns_provider = args.dns
    domain = args.domain
    alt_domains = args.alt_domains
    account_key = args.account_key
    bundle_name = args.bundle_name
    email = args.email

    if bundle_name:
        file_name = bundle_name
    else:
        file_name = '{0}'.format(domain)

    if account_key:
        account_key = account_key.read()
    else:
        try:
            with open('{0}.account.key'.format(file_name), 'r') as account_file:
                account_key = account_file.read().encode()
        except IOError:
            account_key = None

    if email:
        # TODO: move this to a config.py file.
        # the cli and the client would both read this urls from that config file
        GET_NONCE_URL = "https://acme-v01.api.letsencrypt.org/directory"
        ACME_CERTIFICATE_AUTHORITY_URL = "https://acme-v01.api.letsencrypt.org"
    else:
        GET_NONCE_URL = "https://acme-staging.api.letsencrypt.org/directory"
        ACME_CERTIFICATE_AUTHORITY_URL = "https://acme-staging.api.letsencrypt.org"

    if dns_provider == 'cloudflare':
        from . import CloudFlareDns
        dns_class = CloudFlareDns()
        logger.info(
            'chosen_dns_provider',
            message='Using {0} as dns provider.'.format(dns_provider))

    elif dns_provider == 'aurora':
        from . import AuroraDns
        try:
            AURORA_API_KEY = os.environ['AURORA_API_KEY']
            AURORA_SECRET_KEY = os.environ['AURORA_SECRET_KEY']

            dns_class = AuroraDns(
                AURORA_API_KEY=AURORA_API_KEY,
                AURORA_SECRET_KEY=AURORA_SECRET_KEY)
            logger.info(
                'chosen_dns_provider',
                message='Using {0} as dns provider.'.format(dns_provider))
        except KeyError as e:
            logger.info("ERROR:: Please supply {0} as an environment variable.".
                        format(str(e)))
            raise
    elif dns_provider == 'rackspace':
        from . import RackspaceDns
        dns_class = RackspaceDns()
        logger.info(
            'chosen_dns_provider',
            message='Using {0} as dns provider.'.format(dns_provider))
    else:
        raise ValueError(
            'The dns provider {0} is not recognised.'.format(dns_provider))

    client = Client(
        domain_name=domain,
        dns_class=dns_class,
        domain_alt_names=alt_domains,
        registration_recovery_email=email,
        account_key=account_key,
        GET_NONCE_URL=GET_NONCE_URL,
        ACME_CERTIFICATE_AUTHORITY_URL=ACME_CERTIFICATE_AUTHORITY_URL)
    certificate_key = client.certificate_key
    account_key = client.account_key

    # write out account_key in current directory
    if not client.PRIOR_REGISTERED:
        with open('{0}.account.key'.format(file_name), 'wb') as account_file:
            account_file.write(account_key)
        logger.info(
            "write_account_key",
            message='account key succesfully written to current directory.')

    message = 'Certificate Succesfully issued. The certificate, certificate key and account key have been saved in the current directory'
    certificate = client.cert()

    # write out certificate and certificate key in current directory
    with open('{0}.crt'.format(file_name), 'wt') as certificate_file:
        certificate_file.write(certificate)
    with open('{0}.key'.format(file_name), 'wb') as certificate_key_file:
        certificate_key_file.write(certificate_key)

    logger.info("the_end", message=message)
