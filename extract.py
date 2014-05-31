#!/usr/bin/python
#
# usage: ./extract.py (dir containing texts) (output dir)

import collections
import datetime
from dateutil.parser import parse as parse_date
import os
import sys

INPUT_DIR = sys.argv[1]
OUTPUT_DIR = sys.argv[2]

class PartialMessage(object):
  def __init__(self, time, from_number, from_name, text):
    self.time = time
    assert isinstance(self.time, datetime.datetime)

    self.from_number = from_number
    assert self.from_number
    assert isinstance(self.from_number, basestring)

    self.from_name = from_name  # can be empty.
    assert isinstance(self.from_name, basestring)

    self.text = text
    assert self.text
    assert isinstance(self.text, basestring)

class MessagesFile(object):
  def __init__(self, with_name, messages):
    # empty if no name associated with this number.
    self.with_name = with_name

    self.messages = messages

def message_from_str(s):
  t = s[s.find('title="') + len('title="'):]
  t = t[:t.find('"')]
  time = parse_date(t)

  t = s[s.find('tel:+') + len('tel:+'):]
  t = t[:t.find('"')]
  from_number = t

  t = s[s.find('"fn"') + len('"fn"'):]
  t = t[t.find('>') + len('>'):t.find('<')]
  from_name = t

  t = s[s.find('<q>') + len('<q>'):s.find('</q>')]
  text = t

  m = PartialMessage(time, from_number, from_name, text)
  return m

def parse_messages_file(f):
  # print 'parse', f
  s = open(f).read()

  t = s[s.find('<title>') + len('<title>'):]
  t = t[:t.find('</title>')]
  if 'Me to' in t:
    t = t[6:]
  with_name = t

  ss = s.split('<div class="message">')[1:]
  mm = map(message_from_str, ss)

  return MessagesFile(with_name, mm)

class Message(object):
  def __init__(self, time, from_name, to_name, text):
    self.time = time
    self.from_name = from_name
    self.to_name = to_name
    self.text = text

def main():
  # list the files we want.
  ff = []
  for f in os.listdir(INPUT_DIR):
    if ' - Text - ' in f:
      ff.append(f)

  # extract from files.
  mfs = []  # list of MessagesFile.
  for f in ff:
    mf = parse_messages_file(os.path.join(INPUT_DIR, f))
    mfs.append(mf)
    # print len(mf.messages), '\t', f

  # get each message we can identify.
  mm = []  # list of Message.
  for mf in mfs:
    if not mf.with_name:
      continue
    for m in mf.messages:
      if m.from_name == 'Me':
        from_name = m.from_name
        to_name = mf.with_name
      else:
        from_name = m.from_name
        to_name = 'Me'
      new = Message(m.time, from_name, to_name, m.text)
      mm.append(new)

  # index the messages.
  name2xx = collections.defaultdict(list)  # name -> indexes into mm.
  for i, m in enumerate(mm):
    name2xx[m.from_name].append(i)
    name2xx[m.to_name].append(i)

  # dump files.
  os.makedirs(OUTPUT_DIR)
  for name in sorted(name2xx):
    if not name:
      continue
    # print 'name = (%s)' % name
    xx = name2xx[name]
    sub_mm = map(lambda x: mm[x], xx)
    sub_mm = sorted(sub_mm, key=lambda m: m.time)
    f = os.path.join(OUTPUT_DIR, name)
    f = open(f, 'w')
    prev_ymd = None
    for m in sub_mm:
      ymd = m.time.strftime('%Y-%b-%d')
      if ymd != prev_ymd:
        f.write('\n' + ymd + '\n\n')
      prev_ymd = ymd
      f.write('\t')
      if m.from_name == 'Me':
        f.write('\t')
      f.write(m.time.strftime('%H:%M') + ' ' + m.text + '\n')
    f.close()

main()
