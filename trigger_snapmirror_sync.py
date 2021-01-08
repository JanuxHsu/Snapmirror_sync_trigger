# ! /usr/bin/env python3
"""
Author: JanuxHsu
usage: python3 trigger_snapmirror_sync.py
    Args:
    parser.add_argument("-c", "--cluster", required=True, help="Target Cluster", dest="cluster")
    parser.add_argument("-u", "--api_user", required=True, help="API Username", dest="api_user")
    parser.add_argument("-p", "--api_password", required=True, help="API Password", dest="api_password")
    parser.add_argument("-o", "--api_port", required=False, help="API Port", default=443, dest="port")
    parser.add_argument("-i", "--uuid", required=True, help="Snapmirror uuid", dest="uuid")
    parser.add_argument("-m", "--mode", required=True, help="Snapmirror mode", choices=["snapmirrored"], dest="mode")
"""
import json

import base64

import os
import requests
from argparse import ArgumentParser
import logging

import urllib3

urllib3.disable_warnings()


def setup_default_logger(log_level=logging.INFO):
    logging.basicConfig(level=log_level,
                        format='%(levelname)-8s[%(asctime)s] %(name)-14s:  %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    console = logging.StreamHandler()
    console.setLevel(log_level)


class API_Handler(object):
    def __init__(self):
        self.port = 443
        self.auth_header = None
        self.cluster = ""
        self.api_user = ""
        self.api_password = ""
        self.mode = "snapmirrored"
        self.logger = logging.getLogger(self.__class__.__name__)

    def set_cluster(self, cluster=""):
        self.cluster = cluster

    def set_api_user(self, api_user=""):
        self.api_user = api_user

    def set_api_password(self, api_password=""):
        self.api_password = api_password

    def set_port(self, port=443):
        self.port = port

    def set_mode(self, mode="snapmirrored"):
        self.mode = mode

    def _get_url(self):
        return "https://{}:{}".format(self.cluster, self.port)

    def generate_auth_header(self):
        base64string = base64.encodebytes(('%s:%s' % (self.api_user, self.api_password)).encode()).decode().replace('\n', '')

        headers = {
            'authorization': "Basic %s" % base64string,
            'content-type': "application/json",
            'accept': "application/json"
        }

        self.auth_header = headers
        return headers

    def check_snapmirror_by_id(self, uuid=""):
        snap_api_url = "{}/api/snapmirror/relationships/{}".format(self._get_url(), uuid)

        response = requests.get(snap_api_url, headers=self.auth_header, verify=False)

        res_json = response.json()

        if response.status_code != 200:
            raise Exception(res_json)

        return res_json

    def trigger_snapmirror_sync(self, uuid=""):
        data_obj = dict()
        data_obj['state'] = self.mode

        url = "{}/api/snapmirror/relationships/{}".format(self._get_url(), uuid)

        response = requests.patch(url, headers=self.auth_header, json=data_obj, verify=False)
        res_json = response.json()

        if response.status_code != 200 and response.status_code != 202:
            raise Exception(res_json)
        return res_json


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-c", "--cluster", required=True, help="Target Cluster", dest="cluster")
    parser.add_argument("-u", "--api_user", required=True, help="API Username", dest="api_user")
    parser.add_argument("-p", "--api_password", required=True, help="API Password", dest="api_password")
    parser.add_argument("-o", "--api_port", required=False, help="API Port", default=443, dest="port")
    parser.add_argument("-i", "--uuid", required=True, help="Snapmirror uuid", dest="uuid")
    parser.add_argument("-m", "--mode", required=True, help="Snapmirror mode", choices=["snapmirrored"], dest="mode")
    args = parser.parse_args()

    setup_default_logger()

    main_logger = logging.getLogger(os.path.basename(__file__))

    try:
        api_handler = API_Handler()
        api_handler.set_cluster(cluster=args.cluster)
        api_handler.set_api_user(api_user=args.api_user)
        api_handler.set_api_password(api_password=args.api_password)
        api_handler.set_port(port=args.port)
        api_handler.set_mode(mode=args.mode)
        api_handler.generate_auth_header()

        sm_uuid = args.uuid
        check_res = api_handler.check_snapmirror_by_id(uuid=sm_uuid)
        main_logger.info("Snapmirror id: {} existed in the target cluster, move on to trigger sync.".format(sm_uuid))

        trigger_res = api_handler.trigger_snapmirror_sync(uuid=sm_uuid)
        main_logger.info("Snapmirror id: {} sync triggered.".format(sm_uuid))
        main_logger.info(json.dumps(check_res, indent=4, sort_keys=True))

    except Exception as error:
        main_logger.error(str(error))
        main_logger.error("Unhandled error occurred, program exited.")
