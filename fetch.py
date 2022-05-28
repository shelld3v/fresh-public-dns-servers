import re
import requests
import time
import json

from bs4 import BeautifulSoup

min_reliability = 80
ipv4_regex = '\\d{1,3}[.]\\d{1,3}[.]\\d{1,3}[.]\\d{1,3}'
ip_regex = '/^(?>(?>([a-f0-9]{1,4})(?>:(?1)){7}|(?!(?:.*[a-f0-9](?>:|$)){8,})((?1)(?>:(?1)){0,6})?::(?2)?)|(?>(?>(?1)(?>:(?1)){5}:|(?!(?:.*[a-f0-9]:){6,})(?3)?::(?>((?1)(?>:(?1)){0,4}):)?)?(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])(?>\.(?4)){3}))$/iD'


def scrape_addresses(text):
    return re.findall(ip_regex, text)


def scrape_ipv4_addresses(text):
    return re.findall(ipv4_regex, text)


def get(url):
    time.sleep(2)
    return requests.get(
        url, verify=False, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61/63 Safari/537.36'}
    ).content.decode(errors='ignore')


def is_reliable(reliability):
    return reliability >= min_reliability


def ipv4_public_dns_info():
    return get('https://raw.githubusercontent.com/BonJarber/fresh-resolvers/main/resolvers.txt').split('\n')


def ipv6_public_dns_info():
    return get('https://raw.githubusercontent.com/proabiral/Fresh-Resolvers/master/resolvers.ipv6').split('\n')


def opennic_project():
    return scrape_ipv4_addresses(get('https://servers.opennic.org/?show=PASS'))

def ipfire():
    return scrape_ipv4_addresses(get('https://wiki.ipfire.org/dns/public-servers'))

def publicdns_xyz():
    resolvers = scrape_ipv4_addresses(get('https://www.publicdns.xyz/'))
    all_cc = (
        'us', 'ru', 'id', 'jp', 'de', 'gb', 'fr', 'sg', 'pl', 'ph', 'kr',
        'tw', 'ca', 'br', 'in', 'se', 'th', 'hk', 'it', 'ua'
    )

    for cc in all_cc:
        url = 'https://www.publicdns.xyz/country/%s.html' % cc
        soup = BeautifulSoup(get(url), 'html.parser')
        server_attrs = soup.find_all(class_='server-ip')
        reliability_attrs = soup.find_all(class_='list-table-reliability')
        for server, reliability in zip(server_attrs, reliability_attrs):
            if is_reliable(float(reliability.string[:-1])):
                resolvers.append(server.string)

    return resolvers

def publicdnsserver_com():
    resolvers = []
    countries = (
        'china', 'denmark', 'germany', 'japan', 'poland', 'austria', 'hongkong',
        'italy', 'netherlands', 'singapore', 'switzerland', 'unitedstates',
        'canada', 'france', 'russia', 'southkorea', 'australia', 'taiwan',
        'spain', 'unitedkingdom', 'sweden'
    )

    for country in countries:
        url = 'https://publicdnsserver.com/%s' % country
        soup = BeautifulSoup(get(url), 'html.parser')
        attrs = soup.find_all(class_='tebal')
        it = iter(attrs)
        for server, _, reliability in zip(it, it, it):
            if is_reliable(float(reliability.string[:-2])):
                resolvers.append(server.string)

    return resolvers


def dnscrypt():
    resolvers = []
    for x in json.loads(get('https://download.dnscrypt.info/dnscrypt-resolvers/json/public-resolvers.json')):
        for server in x['addrs']:
            if not any(c.isalpha() for c in server):
                resolvers.append(server)
                break

    return resolvers


if __name__ == '__main__':
    resolvers = set(filter(
        ipv4_public_dns_info() +
        ipv6_public_dns_info() +
        opennic_project() +
        ipfire() +
        publicdns_xyz() +
        publicdnsserver_com() +
        dnscrypt()
    ))
    with open('tmp.txt', 'w') as f:
        f.write('\n'.join(resolvers))
