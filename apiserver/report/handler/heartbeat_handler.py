#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:owefsad
# datetime:2020/10/23 11:56
# software: PyCharm
# project: webapi
import logging
import time

from dongtai.models.agent import IastAgent
from dongtai.models.heartbeat import IastHeartbeat
from dongtai.models.replay_queue import IastReplayQueue
from dongtai.models.vulnerablity import IastVulnerabilityModel
from dongtai.utils import const

from apiserver.report.handler.report_handler_interface import IReportHandler
from apiserver.report.report_handler_factory import ReportHandler

logger = logging.getLogger('dongtai.openapi')


@ReportHandler.register(const.REPORT_HEART_BEAT)
class HeartBeatHandler(IReportHandler):
    def __init__(self):
        super().__init__()
        self.req_count = None
        self.cpu = None
        self.memory = None
        self.network = None
        self.disk = None

    def parse(self):
        self.cpu = self.detail.get('cpu')
        self.memory = self.detail.get('memory')
        self.network = self.detail.get('network')
        self.disk = self.detail.get('disk')
        self.req_count = self.detail.get('req_count')
        self.report_queue = self.detail.get('report_queue')
        self.method_queue = self.detail.get('method_queue')
        self.replay_queue = self.detail.get('replay_queue')
    def save_heartbeat(self):
        # update agent state
        self.agent.is_running = 1
        self.agent.online = 1
        self.agent.save(update_fields=['is_running', 'online'])
        queryset = IastHeartbeat.objects.filter(agent=self.agent)
        heartbeat_count = queryset.values('id').count()
        logger.info("{},{}".format(self.agent, self.detail))
        if heartbeat_count == 1:
            heartbeat = queryset.first()
            heartbeat.memory = self.memory
            heartbeat.cpu = self.cpu
            heartbeat.disk = self.disk
            heartbeat.req_count = self.req_count
            heartbeat.report_queue = self.report_queue
            heartbeat.method_queue = self.method_queue
            heartbeat.replay_queue = self.replay_queue
            heartbeat.dt = int(time.time())
            heartbeat.save(update_fields=[
                'memory', 'cpu', 'disk', 'req_count', 'dt', 'report_queue',
                'method_queue', 'replay_queue'
            ])
        else:
            queryset.delete()
            IastHeartbeat.objects.create(memory=self.memory,
                                         cpu=self.cpu,
                                         disk=self.disk,
                                         req_count=self.req_count,
                                         report_queue=self.replay_queue,
                                         method_queue=self.method_queue,
                                         replay_queue=self.replay_queue,
                                         dt=int(time.time()),
                                         agent=self.agent)

    def get_result(self, msg=None):
        try:
            project_agents = IastAgent.objects.values('id').filter(bind_project_id=self.agent.bind_project_id)
            if project_agents is None:
                logger.info(f'项目下不存在探针')

            replay_queryset = IastReplayQueue.objects.values(
                'id', 'relation_id', 'uri', 'method', 'scheme', 'header', 'params', 'body', 'replay_type'
            ).filter(agent_id__in=project_agents, state=const.WAITING)[:10]
            if len(replay_queryset) == 0:
                logger.info(f'重放请求不存在')

            success_ids, success_vul_ids, failure_ids, failure_vul_ids, replay_requests = [], [], [], [], []
            for replay_request in replay_queryset:
                if replay_request['uri']:
                    replay_requests.append(replay_request)
                    success_ids.append(replay_request['id'])
                    if replay_request['replay_type'] == const.VUL_REPLAY:
                        success_vul_ids.append(replay_request['relation_id'])
                else:
                    failure_ids.append(replay_request['id'])
                    if replay_request['replay_type'] == const.VUL_REPLAY:
                        failure_vul_ids.append(replay_request['relation_id'])

            timestamp = int(time.time())
            IastReplayQueue.objects.filter(id__in=success_ids).update(update_time=timestamp, state=const.SOLVING)
            IastReplayQueue.objects.filter(id__in=failure_ids).update(update_time=timestamp, state=const.SOLVED)

            IastVulnerabilityModel.objects.filter(id__in=success_vul_ids).update(latest_time=timestamp, status='验证中')
            IastVulnerabilityModel.objects.filter(id__in=failure_vul_ids).update(latest_time=timestamp, status='验证失败')
            logger.info(f'重放请求下发成功')

            return replay_requests
        except Exception as e:
            logger.info(f'重放请求查询失败，原因：{e}')
        return list()

    def save(self):
        self.save_heartbeat()
