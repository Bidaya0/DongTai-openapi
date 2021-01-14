#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:owefsad
# datetime:2020/5/21 15:56
# software: PyCharm
# project: webapi
import json
import logging

from django.http import JsonResponse
from rest_framework.request import Request

from AgentServer.base import R
from apiserver.base.openapi import OpenApiEndPoint
from apiserver.models.agent import IastAgent
from apiserver.models.agent_properties import IastAgentProperties
from apiserver.serializers.agent_properties import AgentPropertiesSerialize

logger = logging.getLogger("django")


class PropertiesEndPoint(OpenApiEndPoint):
    """
    当前用户详情
    """
    name = "api-v1-properties"
    description = "获取属性配置"

    def get(self, request: Request):
        """
        IAST下载 agent接口
        :param request:
        :return:{
            "status": 201,
            "data":{
                "hook_type": 0,
                "dump_class": 0
            },
            "msg": "success"
        }
        """
        agent_token = request.query_params.get('agentName', None)
        agent = IastAgent.objects.filter(token=agent_token).first()
        if agent:
            queryset = IastAgentProperties.objects.filter(agent=agent).first()
            if queryset:
                return JsonResponse(R.success(AgentPropertiesSerialize(queryset).data))
        return JsonResponse(R.failure(data=None))
