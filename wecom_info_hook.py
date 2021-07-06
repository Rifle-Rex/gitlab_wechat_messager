#!/usr/local/bin/python3
# coding=utf-8
from sys import stdin
import requests
import json
import copy
import sys

class Parser:

    text_template = {
        "msgtype": "text",
        "text": {
            "content": "",
            "mentioned_list": [],
            "mentioned_mobile_list": []
        }
    }

    markdown_template = {
        "msgtype": "markdown",
        "markdown": {"content":""}
    }

    @classmethod
    def _parseMergeRequest(cls, o):
        msg = cls.getTemplate('text')
        msgDict = {
            "项目名": o['project']['name'],
            '仓库': o['repository']['name'],
            '源分支': o['object_attributes']['source_branch'],
            '目标分支': o['object_attributes']['target_branch'],
            '合并状态': o['object_attributes']['merge_status'],
            '发起事件': o['object_attributes']['created_at'],
            '合并人': o['user']['name'] or o['user']['username'],
            'branch_title': o['object_attributes']['title'],
            'last_commit_id': o['object_attributes']['last_commit']['id'],
        }
        msgList = [ x+": "+y+';' for x,y in msgDict.items() ]
        msgText = "\n".join(msgList)
        msg['text']['content'] = msgText
        return msg

    @classmethod
    def _parseProjectUpdate(cls, o):
        msg = cls.getTemplate('text')
        return msg

    @classmethod
    def _parseRepositoryUpdate(cls, o):
        msg = cls.getTemplate('text')
        return msg

    @classmethod
    def _parsePush(cls, o):
        msg = cls.getTemplate('text')
        msgDict = {
            "项目名": o['project']['name'],
            'before_push' : o['before'],
            'after_push': o['after'],
            'user_name': o['user_name'],
            'message': o['message'],
            'ref': o['ref']
        }
        commit_info = ''
        for commit in o['commits']:
            commit_info += 'id: ' + commit['id'] + "\n"
            commit_info += 'title: ' + commit['title'] + "\n"
            commit_info += 'timestamp: ' + commit['timestamp'] + "\n---------------\n"
        msgList = [ x+": "+y+';' for x,y in msgDict.items() ]
        msgList.append(commit_info)
        msgText = "\n".join(msgList)
        msg['text']['content'] = msgText
        return msg

    @classmethod
    def getTemplate(cls, name):
        template = getattr(cls, name + '_template', None)
        if template is None:
            raise NameError("not such template '%s'" % name)
        else:
            return copy.deepcopy(template)

    @classmethod
    def parseRequest(cls, event_name, o):
        words = [ s[0].upper() + s[1:] for s in event_name.split("_") ]
        funcName = '_parse' + ''.join(words)
        func = getattr(cls, funcName)
        if func:
            return func(o)
        else:
            raise NameError("can't find a parse to handle event '%s'" % event_name)

def sendMessage(url, msg):
    response = requests.post(url, json=msg)
    if response.status_code != 200:
        response.raise_for_status()
    re_json = json.loads(response.text)
    if re_json['errcode'] != 0:
        raise RuntimeError(response.text)

if __name__ == "__main__":
    input_str = stdin.read()
    args = json.loads(input_str)
    # 触发发送消息的事件
    event_name = args['event_name'] or args['object_kind']
    sys.stderr.write(json.dumps(args))
    # event filter
    trigger_event = ['merge_request', 'push']
    if event_name not in trigger_event:
        sys.exit(0)
    msg = Parser.parseRequest(args['event_name'], args)
    # setup the wecom robot message api
    url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=blablablablabla" 
    sendMessage(url, msg)
    sys.exit(0)
