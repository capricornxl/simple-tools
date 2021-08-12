#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @FileName：     queyr_ecs_expired.py
# @Software:      
# @Author:         Leven Xiang
# @Mail:           xiangle0109@outlook.com
# @Date：          2021/4/26 16:26

import json
import time

import datetime
import requests
from Tea.core import TeaCore
from alibabacloud_ecs20140526 import models as ecs_20140526_models
from alibabacloud_ecs20140526.client import Client as Ecs20140526Client
from alibabacloud_rds20140815 import models as rds_20140815_models
from alibabacloud_rds20140815.client import Client as Rds20140815Client
from alibabacloud_tea_openapi import models as open_api_models


class WeChat(object):
    def __init__(self, corpid, agentid, corpsecret):
        self.url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
        # 企业ID
        self.corpid = corpid
        # 应用AgentID
        self.agentid = agentid
        # 应用Secret
        self.corpsecret = corpsecret

    @property
    def __auth(self):
        params = {'corpid': self.corpid, 'corpsecret': self.corpsecret}
        try:
            rs = requests.get(self.url, params=params)
            return rs.json()['access_token']
        except Exception as auth_error:
            return 'get access_token error: {}'.format(auth_error)

    @property
    def __get_token(self):
        token = self.__auth
        return token.strip()

    def __message(self, touser, toparty, subject, content):
        data = json.dumps({
            'touser': touser,
            'toparty': toparty,
            'msgtype': 'text',
            'agentid': self.agentid,
            'text': {
                'content': '{}\n{}'.format(subject, content)},
            'safe': '0'
        }, ensure_ascii=False).encode('utf-8')
        return data

    def send(self, touser, toparty, subject, content):
        """
        :param touser:  用户名，多用户名用|分隔
        :param toparty: 部门，指定部门ID,或为空
        :param subject: 标题
        :param content: 消息内容
        :return:
        """
        try:
            url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=' + self.__get_token
            send = requests.post(url, data=self.__message(touser, toparty, subject, content))
            return json.loads(send.text)
        except Exception as send_error:
            return 'send error: {}'.format(send_error)


# 计算两个日期相差天数，自定义函数名，和两个日期的变量名。
def calc_time(date1, date2, time_format):
    """
    time_format: %Y-%m-%dT%H:%MZ %Y-%m-%d %H:%M:%SZ
    :param date1:
    :param date2:
    :param time_format:
    :return:
    """
    # %Y-%m-%d为日期格式，其中的-可以用其他代替或者不写，但是要统一，同理后面的时分秒也一样；可以只计算日期，不计算时间。
    # %Y-%m-%dT%H:%MZ %Y-%m-%d %H:%M:%SZ
    date1 = time.strptime(date1, time_format)
    date2 = time.strptime(date2, time_format)

    # 根据上面需要计算日期还是日期时间，来确定需要几个数组段。下标0表示年，小标1表示月，依次类推...
    # date1=datetime.datetime(date1[0],date1[1],date1[2],date1[3],date1[4],date1[5])
    # date2=datetime.datetime(date2[0],date2[1],date2[2],date2[3],date2[4],date2[5])
    date1 = datetime.datetime(date1[0], date1[1], date1[2])
    date2 = datetime.datetime(date2[0], date2[1], date2[2])
    # 返回两个变量相差的值，就是相差天数
    return date2 - date1


class QueryEcs(object):
    def __init__(self, access_key_id, access_key_secret):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret

    @property
    def create_client(self):
        config = open_api_models.Config(
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret
        )
        config.endpoint = 'ecs.cn-zhangjiakou.aliyuncs.com'
        return Ecs20140526Client(config)

    @property
    def get_ecs_list(self):
        client = self.create_client
        describe_instances_request = ecs_20140526_models.DescribeInstancesRequest(
            region_id='cn-zhangjiakou',
            instance_charge_type='PrePaid',
            page_size=20
        )
        return TeaCore.to_map(client.describe_instances(describe_instances_request))


class QueryRds:
    def __init__(self, access_key_id, access_key_secret):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret

    @property
    def create_client(self):
        config = open_api_models.Config(
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret
        )
        config.endpoint = 'rds.aliyuncs.com'
        return Rds20140815Client(config)

    @property
    def get_rds_list(self):
        client = self.create_client
        describe_dbinstance_attribute_request = rds_20140815_models.DescribeDBInstanceAttributeRequest(
            # 实例ID。可以一次输入最多30个，以英文逗号（,）分隔
            dbinstance_id='rm-do21a86n667hx8rdl'
        )
        return TeaCore.to_map(client.describe_dbinstance_attribute(describe_dbinstance_attribute_request))


if __name__ == '__main__':

    AccessKey_ID = 'LTAI4FzwuJfH12312312'
    AccessKey_Secret = 'EEAydPb4123123123123123123'

    wx = WeChat(corpid='112312312', agentid='12312312312312', corpsecret='32kdhxcvjkp23uijhdfsda')
    # 单位天
    expired_thread = 30
    # 微信消息接收人
    # 多用户用|分隔
    send_user = r'XiangLe'
    #  ECS check
    # 当前日期 格式化
    now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%MZ')
    ecs_result = QueryEcs(access_key_id=AccessKey_ID, access_key_secret=AccessKey_Secret).get_ecs_list

    # now = '2021-09-26T17:46Z'
    ecs_msg_list = []
    if 'body' in ecs_result.keys():
        ecs_list = ecs_result['body']['Instances']['Instance']
        for ecs in ecs_list:
            expired_time = int(calc_time(now, ecs['ExpiredTime'], '%Y-%m-%dT%H:%MZ').days)
            if expired_time < expired_thread:
                ecs_msg_list.append("主机[{}]-实例[{}]，还有{}天到期，到期时间：{}".format(ecs['InstanceName'], ecs['InstanceId'], expired_time,
                                                                           datetime.datetime.strptime(ecs['ExpiredTime'], "%Y-%m-%dT%H:%MZ").date()))
        if len(ecs_msg_list) > 0:
            rds_msg = '\n'.join(ecs_msg_list)
            wx.send(send_user, '', '【发现即将到期的ECS】', rds_msg)
        else:
            wx.send(send_user, '', '【ECS到期时间检查】', "ECS过期时间均正常")

    now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    rds_result = QueryRds(access_key_id=AccessKey_ID, access_key_secret=AccessKey_Secret).get_rds_list
    rds_msg_list = []

    if 'body' in rds_result.keys():
        rds_list = rds_result['body']['Items']['DBInstanceAttribute']
        for rds in rds_list:
            rds_expired_time = int(calc_time(now, rds['ExpireTime'], '%Y-%m-%dT%H:%M:%SZ').days)
            if rds_expired_time < expired_thread:
                rds_msg_list.append("RDS[{}]-实例ID[{}]，还有{}天到期，到期日期[{}]".format(rds['DBInstanceDescription'], rds['DBInstanceId'], rds_expired_time,
                                                                               datetime.datetime.strptime(rds['ExpireTime'], "%Y-%m-%dT%H:%M:%SZ").date()))
        if len(rds_msg_list) > 0:
            rds_msg = '\n'.join(rds_msg_list)
            # wx.send(send_user, '', '【测试消息】', rds_msg)
            wx.send(send_user, '', '【发现即将到期的RDS】', rds_msg)
        else:
            # print("不存在临近过期时间的RDS")
            wx.send(send_user, '', '【RDS到期检查】', "RDS过期时间均正常")
