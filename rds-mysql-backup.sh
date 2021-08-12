#!/bin/sh


# 企业微信小应用，发送通知消息的
CropID='ww123451234512345'
Secret='smYVVeWM9123451234512345123451234512345'
# 应用ID
AppID=1000003


mysql_user="sql_admin"
mysql_password="aA99t6rj12312312"
mysql_addr=rm-do21a123123123123123123.mysql.zhangbei.rds.aliyuncs.com
#mysqlclient路径
mysql_bin=/usr/bin/mysql
mysqldump_bin=/usr/bin/mysqldump
today=$(date +%Y-%m-%d)
#备份日志文件
log_file=backup.log
#只保留最近7天备份（其他删除）
old_date=`date +%Y-%m-%d -d '-7 days'`
#备份主目录
backup_dir=/opt/nasfolder/rds_backup
full_backup_dir=${backup_dir}/full_backup_dir
# 生成当天目录
[ -d "${backup_dir}/${today}" ] || mkdir -p ${backup_dir}/${today}
# 初始化日志文件
echo "" > ${backup_dir}/${today}/${log_file}


# 微信消息实体
_msgBodys(){
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
_sendMsgs(){
CropID=${CropID}
Secret=${Secret}
GET_URL="https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=${CropID}&corpsecret=${Secret}"
Gtoken=$(/usr/bin/curl -s -G $GET_URL| grep -Po "(?<=access_token\W{3})[\w-]+")
POST_URL="https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=${Gtoken}"
/usr/bin/curl -s -k --data-ascii "$(_msgBodys "$1" "$2")" $POST_URL
}

###### 开始执行  ##########################
# 先清理7天之前的旧备份目录
old_folders=$(find ${backup_dir} -maxdepth 1 -type d -mtime +7 | grep -v "^${backup_dir}$")
if [ $? -eq 0 ]
then
    for old_folder in `find ${backup_dir} -maxdepth 1 -type d -mtime +7 | grep -v "^${backup_dir}$"`
    do
        echo -e '['$(date +"%Y-%m-%d %H:%M:%S")'] - '"清理旧目录：" >> ${backup_dir}/${today}/${log_file}
        echo -e "${old_folder}" >> ${backup_dir}/${today}/${log_file}
        rm -rf ${old_folder}
    done
else
    echo -e '['$(date +"%Y-%m-%d %H:%M:%S")'] - '"无旧目录可清理" >> ${backup_dir}/${today}/${log_file}
fi

cd ${backup_dir}/${today}
# 需要备份的数据库列表文件，一行一个
mysql_databases=$(cat /opt/data/rds_db_list/db_list)
# 开始备份
for database in ${mysql_databases}
do
    #开始备份,记录备份开始时间 并压缩备份文件
    echo -e '['$(date +"%Y-%m-%d %H:%M:%S")'] - '${database}' - '"备份开始" >> ${backup_dir}/${today}/${log_file}
    #备份数据库
    ${mysqldump_bin} -u${mysql_user} -p${mysql_password} -h${mysql_addr} --quick --single-transaction --routines --add-drop-database --log-error=log.err ${database} | gzip > ${backup_dir}/${today}/${database}.backup.sql.gz
    [ $? -eq 0 ] && echo -e '['$(date +"%Y-%m-%d %H:%M:%S")'] - '"备份${database}并压缩备份文件 OK" >> ${backup_dir}/${today}/${log_file}
    sleep 5
done
echo -e '['$(date +"%Y-%m-%d %H:%M:%S")'] - 'ALL DB' - '"备份完成" >> ${backup_dir}/${today}/${log_file}


msgs=`ls ${backup_dir}/${today}/ |grep '.sql.gz'`
send_msg="RDS备份结果:\n${msgs}"
#发送微个消息给用户，多个用户用|分隔
_sendMsgs 'Xiangle' "$send_msg"