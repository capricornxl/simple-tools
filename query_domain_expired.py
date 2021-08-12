#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @FileName：     query_domain_expired.py
# @Software:      
# @Author:         Leven Xiang
# @Mail:           xiangle0109@outlook.com
# @Date：          2021/4/27 17:03

import json
import time

import datetime
import requests
from Tea.core import TeaCore
from alibabacloud_domain20180129 import models as domain_20180129_models
from alibabacloud_domain20180129.client import Client as Domain20180129Client
from alibabacloud_tea_openapi import models as open_api_models


class QueryDomain:
    def __init__(self, access_key_id, access_key_secret):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret

    @property
    def create_client(self):
        config = open_api_models.Config(
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret
        )
        config.endpoint = 'domain.aliyuncs.com'
        return Domain20180129Client(config)

    @property
    def get_domain_list(self):
        client = self.create_client
        query_domain_list_request = domain_20180129_models.QueryDomainListRequest(
            page_num=1,
            page_size=100
        )
        return TeaCore.to_map(client.query_domain_list(query_domain_list_request))


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


if __name__ == '__main__':
    AccessKey_ID = 'LTAI4FzWzgdf6112312312312'
    AccessKey_Secret = 'QALcNPAkqX7JUV12312312312312'

    wx = WeChat(corpid='112312312', agentid='12312312312312', corpsecret='32kdhxcvjkp23uijhdfsda')
    # 单位天
    expired_thread = 60
    # 微信消息接收人
    # send_user = r'XiangLe'
    send_user = r'XiangLe'

    # 当前日期 格式化
    # 域名的过期时间格式是 "ExpirationDate": "2025-05-29 10:17:02",
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    domain_result = QueryDomain(access_key_id=AccessKey_ID, access_key_secret=AccessKey_Secret).get_domain_list

    # print(domain_result)
    domain_msg_list = []
    if 'body' in domain_result.keys():
        domain_list = domain_result['body']['Data']['Domain']
        for domain in domain_list:
            expired_time = int(calc_time(now, domain['ExpirationDate'], '%Y-%m-%d %H:%M:%S').days)
            if expired_time < expired_thread:
                domain_msg_list.append("域名[{}]，还有{}天到期，到期日期[{}]".format(domain['DomainName'], expired_time,
                                                                        datetime.datetime.strptime(domain['ExpirationDate'], "%Y-%m-%d %H:%M:%S").date()))
        if len(domain_msg_list) > 0:
            domain_msg = '\n'.join(domain_msg_list)
            wx.send(send_user, '', '【发现即将到期的域名】', domain_msg)
        else:
            wx.send(send_user, '', '【域名到期时间检查】', "域名可用时间均正常")
