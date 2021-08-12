#!/bin/bash
export PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin
###############################
# Elasticsearch索引自动备份及清理指定时间外的旧索引备份
#
# Author: Leven Xiang
# create: 2019/11/07
#
# Crontab 每天早上1点15分一次备份
# 15 1 * * * /bin/sh /opt/bin/elasticsearch_index_backup.sh >> /dev/null 2>&1
##############################################################

# 企业微信小应用，发送通知消息的
CropID='ww123451234512345'
Secret='smYVVeWM9123451234512345123451234512345'
# 应用ID
AppID=1000003

DateTime=$(date +%F.%H.%M.%S)
# ElasicSearch的访问地址
Url=http://192.168.100.11:9200
# 用于存放快照的Repo名称
DataRepo=elastic_storerepo
# DaysAgo=$(date +%s)
DaysAgo=$(date +%s -d "-7 days")
Msg=''

# 微信消息实体
_msgBodys()
{
local int AppID=${AppID}
local UserID=$1
local Msg="$2"
cat << EOF
{
"touser": "${UserID}",
"msgtype": "text",
"agentid": "${AppID}",
"text": {
"content": "${Msg}"
},
"safe": "0"
}
EOF
}

#发送消息
_sendMsgs()
{
CropID=${CropID}
Secret=${Secret}
GURL="https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=${CropID}&corpsecret=${Secret}"
Gtoken=$(/usr/bin/curl -s -G $GURL | grep -Po "(?<=access_token\W{3})[\w-]+")
PURL="https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=${Gtoken}"
/usr/bin/curl -s -k --data-ascii "$(_msgBodys "$1" "$2")" $PURL
}


BackupReuslt=$(echo `curl -s -H "Content-Type:application/json" -XPUT ${Url}/_snapshot/${DataRepo}/index_backup_${DateTime}` | jq .accepted)
if [[ $? -eq 0 ]];then
    Msg="BackupReuslt: \nindex_backup_${DateTime}--${BackupReuslt}\n"
fi
Length=$(expr $(curl -s -XGET ${Url}/_snapshot/${DataRepo}/index_backup_* |jq '.snapshots |length') - 1)
BackupIndex=$(curl -s -XGET ${Url}/_snapshot/${DataRepo}/index_backup_* |jq '[.snapshots[] | {snapshot:.snapshot, start_time:.start_time}]')
Msg="${Msg} \nDeleteResult: "
for i in $(seq 0 ${Length});do
    StartTime=$(echo $BackupIndex | jq .[$i].start_time |sed 's@"@@g' |awk -F "T" '{print $1}')
    if [[ $(date -d "$StartTime" +%s) -lt ${DaysAgo} ]]; then
        IndexName=$(echo $BackupIndex | jq .[$i].snapshot |sed 's@"@@g')
        DeleteResult=$(curl -s -XDELETE ${Url}/_snapshot/${DataRepo}/${IndexName})
        IndexName="\n${IndexName}"
    fi
done
if [[ -z "${IndexName}" ]];then
    Msg="${Msg}\n无旧索引备份需要删除"
else
    Msg="${Msg}\n${IndexName}"
fi

send_msg="ES备份结果\n${Msg}"
#发送微个消息给用户
_sendMsgs 'Xiangle' "$send_msg"
