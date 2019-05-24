#!/usr/bin/env python
#-*- coding:utf-8 -*-

import re

content="ax0F23"

rule = r"^0x[0-9a-fA-F]+$"
ret = re.match(rule, content)

print(ret)