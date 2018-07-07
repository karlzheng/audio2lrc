#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
import codecs
from aip import AipSpeech
from pydub import AudioSegment
from pydub.silence import split_on_silence

reload(sys)
sys.setdefaultencoding('utf-8')

APP_ID = '10843115'
API_KEY = ''
SECRET_KEY = ''
from baidusecet import *

aipSpeech = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
try:
        script, fileFullName = sys.argv
except:
	print("参数 文件名 未指定!")
	exit()
if not os.path.isfile(fileFullName):
	print("参数 %s 不是一个文件名" %fileFullName)
	exit()
if not os.path.exists(fileFullName):
	print("参数 %s 指定的文件不存在" %fileFullName)
	exit()

fileSufix = os.path.splitext(fileFullName)[1]
fileBaseName = os.path.splitext(fileFullName)[0]
#sys.exit()
if fileSufix.lower() == ".mp3":
    record = AudioSegment.from_mp3(fileFullName)
else:
    record = AudioSegment.from_wav(fileFullName)

def sec2LrcTime(t):
    msec = int ((t * 1000) % 1000)
    t = int(t)
    m = t / 60
    h = m / 60
    s = t % 60
    m %= 60
    h %= 60
    minsec = '[' + ("%02d"%m) + ':' + ("%02d"%s) + '.' + ("%03d"%msec) + ']'

    return minsec

bitrate = 16000
record = record.set_frame_rate(bitrate).set_channels(1)
#chunks = split_on_silence(record, min_silence_len=300, silence_thresh=-45)
#chunks = split_on_silence(record, min_silence_len=250, silence_thresh=-40, seek_step=1)

min_silence_len=250
silence_thresh=-40
seek_step=10

chunks = split_on_silence(record, min_silence_len=min_silence_len, silence_thresh=silence_thresh, seek_step=seek_step)

new_chunks = []
max_len = 5000
for i, chunk in enumerate(chunks):
    if (len(chunk) < max_len):
        new_chunks.append(chunk)
    else:
        min_silence_len=40
        silence_thresh=-20
        seek_step=1
        mini_chunks = split_on_silence(chunk, min_silence_len=min_silence_len, silence_thresh=silence_thresh, seek_step=seek_step)
        new_chunks.extend(mini_chunks)

chunks = []
if (len(new_chunks) > 0):
    tc = new_chunks[0]
    for i, c in enumerate(new_chunks):
        if (len(tc) > 3000 or len(tc + c) > 5000):
            chunks.append(tc)
            tc = c
        else:
            tc += c

    chunks.append(tc)

#for i, c in enumerate(chunks):
    #print(len(c))
#sys.exit()

lrcFile = codecs.open(fileBaseName + ".lrc", 'w', 'utf-8')
lrcFile.write(('[ti:' + fileBaseName + "]\n").decode('utf-8'))
total_sec = 0

def write_chunk(chunk):
    ofn = "tmpchunk{0}_{1}.wav".format(total_sec).format(len(chunk));
    chunk.export(ofn, format="wav") #chunk.export(sio, format="s16le")
    #sio = StringIO.StringIO()
    #sio.getvalue()   #Raw PCM

for i, chunk in enumerate(chunks):
    lrc = sec2LrcTime(total_sec)
    result = aipSpeech.asr(chunk.raw_data, 'pcm', bitrate, {'lan': 'zh'})
    if result and result['err_no'] == 0:
        lrc = (lrc + result['result'][0] + '\n').encode("utf-8")
        #print(lrc)
        lrcFile.write(lrc.decode('utf-8'))
    else:
        print("aipSpeech.asr error at:", i, chunk)
        #pass
    total_sec += chunk.frame_count() / chunk.frame_rate
    #print(total_sec)

lrcFile.close()
