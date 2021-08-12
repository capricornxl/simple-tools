#!/bin/sh
export PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin
###############################
# 此脚本用来每日备份openldap
# 此文件名：openldapbackup.sh
#
# Author: Leven Xiang
# create: 2019/11/07
#
# Crontab 每天早上1点15分一次全量备份
# 15 1 * * * /bin/sh /opt/bin/openldapbackup.sh >> /dev/null 2>&1
###############################


# 企业微信小应用，发送通知消息的
CropID='ww123451234512345'
Secret='smYVVeWM9123451234512345123451234512345'
# 应用ID
AppID=1000003

#当天日期
today=$(date +%Y-%m-%d)
#只保留最近7天备份（其他删除）
old_date=`date +%Y-%m-%d -d '-7 days'`
#邮件通知程序
#mutt="/usr/bin/mutt -F /opt/bin/mutt-gitbackup-config"
#本地备份路径,rsync会严格区分本文件夹或本文件夹内
#如果只传输文件夹内的文件，切记要以/结束
src_dir=/opt/backup/openldap/
#脚本执行过程记录文件
openldap_backup_log=${src_dir}openldap_backup_log.log
#备份文件上传的目标主机
backup_host=192.168.100.12
#客户端rsync_password文件
rsync_pwd_file=/etc/rsync.password
#openldap_backup执行命令，修改/etc/openldap/openldap.rb中的openldap_rails['backup_path']
openldap_backup_run="/rk/app/openldap-2.4/sbin/slapcat -l ${src_dir}openldap.${today}.ldif"
#rsync执行参数
rsync_run="rsync -vzrtopg --delete ${src_dir} rsync@${backup_host}::openldap-113-229 --password-file=${rsync_pwd_file}"

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


# 对backup_dir进行判断
if [ ! -d "${src_dir}" ]
then
    echo "src_dir为空，脚本不予执行！！\n" >> ${openldap_backup_log}
    exit 1
fi
# 初始化日志文件
echo "" > ${openldap_backup_log} 
###### 开始执行  ##########################
# 先清理7天之前的旧备份文件
old_files=$(find ${src_dir} -maxdepth 1 -type f -mtime +7)
if [ $? -eq 0 ] && [ -n "${old_files}" ]
then
    echo -e $(date +"%Y-%m-%d %H:%M:%S")' - 清理旧备份文件：' >> ${openldap_backup_log}
    for old_file in ${old_files}
    do
        echo -e "${old_file}" >> ${openldap_backup_log}
        rm -f ${old_file}
    done
    echo -e "\n==========\n" >> ${openldap_backup_log}
else
    echo -e $(date +"%Y-%m-%d %H:%M:%S")' - 无旧文件清理，将继续执行备份操作...' >> ${openldap_backup_log}
    echo -e "\n==========\n" >> ${openldap_backup_log}
fi
# 开始备份openldap
echo -e $(date +"%Y-%m-%d %H:%M:%S")' - 开始备份openldap数据：' >> ${openldap_backup_log}
${openldap_backup_run}
if [ $? -eq 0 ]
then
    echo -e $(date +"%Y-%m-%d %H:%M:%S")' - openldap数据备份完成...' >> ${openldap_backup_log}
    echo -e "${src_dir}openldap.${today}.ldif" >> ${openldap_backup_log}
    echo -e "\n==========\n" >> ${openldap_backup_log}
else
    echo -e $(date +"%Y-%m-%d %H:%M:%S")' - openldap数据备份失败...' >> ${openldap_backup_log}
    echo -e "\n==========\n" >> ${openldap_backup_log}
fi

# # Rsync同步
# echo -e $(date +"%Y-%m-%d %H:%M:%S")' - 开始同步openldap备份到'${backup_host}'：' >> ${openldap_backup_log}
# ${rsync_run} >> ${openldap_backup_log}
# if [ $? -eq 0 ]
# then
#     echo -e "\n"$(date +"%Y-%m-%d %H:%M:%S")' - Rsync同步备份到'${backup_host}'完成...' >> ${openldap_backup_log}
# else
#     echo -e "\n"$(date +"%Y-%m-%d %H:%M:%S")' - Rsync同步备份到'${backup_host}'失败...'"\n" >> ${openldap_backup_log}
# fi

msgs=`cat ${openldap_backup_log}`
send_msg="openldap备份结果\n${msgs}"
#发送微个消息给用户
_sendMsgs 'Xiangle' "$send_msg"
# 邮件发送备份情况
#${mutt} -s "openldap备份情况" 97098414@qq.com,xiangle0109@outlook.com < ${openldap_backup_log}
