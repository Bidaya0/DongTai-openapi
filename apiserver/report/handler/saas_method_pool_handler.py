#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:owefsad
# datetime:2021/1/5 下午12:36
# software: PyCharm
# project: lingzhi-webapi
import json
import logging
import time
from hashlib import sha1

import requests
from dongtai.models.agent_method_pool import MethodPool
from dongtai.models.replay_method_pool import IastAgentMethodPoolReplay
from dongtai.models.replay_queue import IastReplayQueue
from dongtai.utils import const

from AgentServer import settings
from apiserver import utils
from apiserver.report.handler.report_handler_interface import IReportHandler
from apiserver.report.report_handler_factory import ReportHandler

logger = logging.getLogger('dongtai.openapi')


@ReportHandler.register(const.REPORT_VULN_SAAS_POOL)
class SaasMethodPoolHandler(IReportHandler):

    @staticmethod
    def parse_headers(headers_raw):
        headers = dict()
        import base64
        header_raw = base64.b64decode(headers_raw).decode('utf-8').split('\n')
        item_length = len(header_raw)
        for index in range(item_length):
            _header_list = header_raw[index].split(':')
            _header_name = _header_list[0]
            headers[_header_name] = ':'.join(_header_list[1:])
        return headers

    def parse(self):
        self.http_uri = self.detail.get('http_uri')
        self.http_url = self.detail.get('http_url')
        self.http_query_string = self.detail.get('http_query_string')
        self.http_req_data = self.detail.get('http_body')
        self.http_req_header = self.detail.get('http_req_header')
        self.http_method = self.detail.get('http_method')
        self.http_scheme = self.detail.get('http_scheme')
        self.http_secure = self.detail.get('http_secure')
        self.http_protocol = self.detail.get('http_protocol')
        self.http_replay = self.detail.get('http_replay_request')
        self.http_res_header = self.detail.get('http_res_header')
        self.http_res_body = self.detail.get('http_res_body')
        self.context_path = self.detail.get('context_path')
        self.vuln_type = self.detail.get('vuln_type')
        self.taint_value = self.detail.get('taint_value')
        self.taint_position = self.detail.get('taint_position')
        self.client_ip = self.detail.get('http_client_ip')
        self.param_name = self.detail.get('param_name')
        self.method_pool = self.report.get('detail', {}).get('pool', None)
        if self.method_pool:
            self.method_pool = sorted(self.method_pool, key=lambda e: e.__getitem__('invokeId'), reverse=True)

    def save(self):
        """
        如果agent存在，保存数据
        :return:
        """
        if self.http_replay:
            # 保存数据至重放请求池
            headers = SaasMethodPoolHandler.parse_headers(self.http_req_header)
            replay_id = headers.get('dongtai-replay-id')
            replay_type = headers.get('dongtai-replay-type')
            relation_id = headers.get('dongtai-relation-id')
            timestamp = int(time.time())

            # fixme 直接查询replay_id是否存在，如果存在，直接覆盖
            query_set = IastAgentMethodPoolReplay.objects.values("id").filter(replay_id=replay_id)
            if query_set.exists():
                # 更新
                replay_model = query_set.first()
                replay_model.update(
                    url=self.http_url,
                    uri=self.http_uri,
                    req_header=self.http_req_header,
                    req_params=self.http_query_string,
                    req_data=self.http_req_data,
                    res_header=self.http_res_header,
                    res_body=self.http_res_body,
                    context_path=self.context_path,
                    method_pool=json.dumps(self.method_pool),
                    clent_ip=self.client_ip,
                    update_time=timestamp
                )
                method_pool_id = replay_model['id']
            else:
                # 新增
                replay_model = IastAgentMethodPoolReplay.objects.create(
                    agent=self.agent,
                    url=self.http_url,
                    uri=self.http_uri,
                    http_method=self.http_method,
                    http_scheme=self.http_scheme,
                    http_protocol=self.http_protocol,
                    req_header=self.http_req_header,
                    req_params=self.http_query_string,
                    req_data=self.http_req_data,
                    res_header=self.http_res_header,
                    res_body=self.http_res_body,
                    context_path=self.context_path,
                    method_pool=json.dumps(self.method_pool),
                    clent_ip=self.client_ip,
                    replay_id=replay_id,
                    replay_type=replay_type,
                    relation_id=relation_id,
                    create_time=timestamp,
                    update_time=timestamp
                )
                method_pool_id = replay_model.id
            IastReplayQueue.objects.filter(id=replay_id).update(state=const.SOLVED)
            if method_pool_id:
                self.send_to_engine(method_pool_id=method_pool_id, model='replay')
        else:
            pool_sign = self.calc_hash()
            current_version_agents = self.get_project_agents(self.agent)
            update_record, method_pool = self.save_method_call(pool_sign, current_version_agents)
            self.send_to_engine(method_pool_id=method_pool.id, update_record=update_record)

    def save_method_call(self, pool_sign, current_version_agents):
        """
        保存方法池数据
        :param pool_sign:
        :param current_version_agents:
        :return:
        """
        method_pool = MethodPool.objects.filter(pool_sign=pool_sign, agent__in=current_version_agents).first()
        update_record = True
        if method_pool:
            method_pool.update_time = int(time.time())
            method_pool.method_pool = json.dumps(self.method_pool)
            method_pool.uri = self.http_uri
            method_pool.url = self.http_url
            method_pool.http_method = self.http_method
            method_pool.req_header = self.http_req_header
            method_pool.req_params = self.http_query_string
            method_pool.req_data = self.http_req_data
            method_pool.req_header_for_search = utils.build_request_header(
                req_method=self.http_method,
                raw_req_header=self.http_req_header,
                uri=self.http_uri,
                query_params=self.http_query_string,
                http_protocol=self.http_protocol
            )
            method_pool.res_header = utils.base64_decode(self.http_res_header)
            method_pool.res_body = self.http_res_body
            method_pool.save(update_fields=[
                'update_time', 'method_pool', 'uri', 'url', 'http_method', 'req_header', 'req_params', 'req_data',
                'req_header_for_search', 'res_header', 'res_body'
            ])
        else:
            # 获取agent
            update_record = False
            timestamp = int(time.time())
            method_pool = MethodPool.objects.create(
                agent=self.agent,
                url=self.http_url,
                uri=self.http_uri,
                http_method=self.http_method,
                http_scheme=self.http_scheme,
                http_protocol=self.http_protocol,
                req_header=self.http_req_header,
                req_params=self.http_query_string,
                req_data=self.http_req_data,
                req_header_for_search=utils.build_request_header(
                    req_method=self.http_method,
                    raw_req_header=self.http_req_header,
                    uri=self.http_uri,
                    query_params=self.http_query_string,
                    http_protocol=self.http_protocol
                ),
                res_header=utils.base64_decode(self.http_res_header),
                res_body=self.http_res_body,
                context_path=self.context_path,
                method_pool=json.dumps(self.method_pool),
                pool_sign=pool_sign,
                clent_ip=self.client_ip,
                create_time=timestamp,
                update_time=timestamp
            )
        return update_record, method_pool

    @staticmethod
    def send_to_engine(method_pool_id, update_record=False, model=None):
        try:
            if update_record:
                logger.info(
                    f'[+] send method_pool [{method_pool_id}] to engine for {"update" if update_record else "new record"}')
                requests.get(url=settings.BASE_ENGINE_URL.format(id=method_pool_id))
            if model:
                logger.info(
                    f'[+] send method_pool [{method_pool_id}] to engine for {model if model else ""}')
                requests.get(url=settings.REPLAY_ENGINE_URL.format(id=method_pool_id))
        except Exception as e:
            logger.info(f'[-] Failure: send method_pool [{method_pool_id}], Error: {e}')

    def calc_hash(self):
        sign_raw = self.http_uri
        for method in self.method_pool:
            sign_raw += f"{method.get('className')}.{method.get('methodName')}()->"
        sign_sha1 = self.sha1(sign_raw)
        return sign_sha1

    @staticmethod
    def sha1(raw):
        h = sha1()
        h.update(raw.encode('utf-8'))
        return h.hexdigest()
