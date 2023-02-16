#!/usr/bin/env python
import sys
import ipaddress
import http.client
import requests
import urllib3
import multiprocessing
from requests.adapters import HTTPAdapter

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class FrontingAdapter(HTTPAdapter):
    """"Transport adapter" that allows us to use SSLv3."""

    def __init__(self, fronted_domain=None, **kwargs):
        self.fronted_domain = fronted_domain
        super(FrontingAdapter, self).__init__(**kwargs)

    def send(self, request, **kwargs):
        connection_pool_kwargs = self.poolmanager.connection_pool_kw
        if self.fronted_domain:
            connection_pool_kwargs["assert_hostname"] = self.fronted_domain
        elif "assert_hostname" in connection_pool_kwargs:
            connection_pool_kwargs.pop("assert_hostname", None)
        return super(FrontingAdapter, self).send(request, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        server_hostname = None
        if self.fronted_domain:
            server_hostname = self.fronted_domain
        super(FrontingAdapter, self).init_poolmanager(server_hostname=server_hostname, *args, **kwargs)

def fncDomainCheck(subnets):
    for subnet in subnets:
        ipList = list(ipaddress.ip_network(subnet).subnets(new_prefix=32))
        for ip in ipList:
            realIP=str(ip).replace('/32', '')
            realUrl=f"https://{realIP}/"
            s = requests.Session()
            s.mount('https://', FrontingAdapter(fronted_domain="fronting.sudoer.net"))
            try:
                r = s.get(realUrl, headers={"Host": "fronting.sudoer.net"})
                if r.status_code == 200:
                    print(f"{bcolors.OKGREEN} OK {bcolors.OKBLUE} {realIP} {bcolors.ENDC}")
                else:
                    print(f"{bcolors.FAIL} NO {bcolors.WARNNING} {realIP} {bcolors.ENDC}")
            except:
                print(f"{bcolors.FAIL} NO {bcolors.FAIL} {realIP} {bcolors.ENDC}")

def split(listInput, chunk_size):
  for i in range(0, len(listInput), chunk_size):
    yield listInput[i:i + chunk_size]

if __name__ == "__main__":
    filePath=sys.argv[1]
    threadsCount=sys.argv[2]
    subnetFile = open(str(filePath), 'r')
    subnetList = subnetFile.readlines()
    jobs = []
    for subnet in subnetList:
        breakedSubnets = list(ipaddress.ip_network(subnet.strip()).subnets(new_prefix=24))
        chunkedList = list(split(breakedSubnets, int(threadsCount)))
        for chunkedSubnet in chunkedList:
            for subnet in chunkedSubnet:
                process = multiprocessing.Process(target=fncDomainCheck, args=(subnet,))
                jobs.append(process)
                process.start()
            for job in jobs:
                job.join()
