#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
import codecs
import argparse

from aip import AipSpeech
from pydub import AudioSegment
from pydub.silence import split_on_silence

reload(sys)
sys.setdefaultencoding('utf-8')

APP_ID = '10843115'
API_KEY = ''
SECRET_KEY = ''
from baidusecet import *

language = "zh"

def get_parser():
    parser = argparse.ArgumentParser(description='audio2lrc arg parser')
    parser.add_argument('-f', '--filename', required=True,  action='store', type=str, help='audio filename')
    parser.add_argument('-l', '--language', action='store', type=str, default="zh", help='language of the Audio: "zh" for Chinese or "en" for English')
    return parser

def parse_args():
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

def main():
    parser = get_parser()
    args = parser.parse_args()

    fileFullName = args.filename
    language = args.language
    print(args)
    print(fileFullName)
    #sys.exit()

    if not os.path.isfile(fileFullName):
            print("参数 %s 不是一个文件名" %fileFullName)
            exit()
    if not os.path.exists(fileFullName):
            print("参数 %s 指定的文件不存在" %fileFullName)
            exit()

    aipSpeech = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
    fileSufix = os.path.splitext(fileFullName)[1]
    fileBaseName = os.path.splitext(fileFullName)[0]

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

#原始PCM的录音参数必须符合8k/16k采样率、16bit 位深、单声道
    bitrate = 16000
    record = record.set_sample_width(2)
    record = record.set_frame_rate(bitrate).set_channels(1)
#chunks = split_on_silence(record, min_silence_len=300, silence_thresh=-45)
#chunks = split_on_silence(record, min_silence_len=250, silence_thresh=-40, seek_step=1)

    min_silence_len=250
    silence_thresh=-40
    seek_step=10

    chunks = split_on_silence(record, min_silence_len=min_silence_len, silence_thresh=silence_thresh, seek_step=seek_step)

    splited_chunks = []
    max_len = 10000
    for i, chunk in enumerate(chunks):
        if (len(chunk) < max_len):
            splited_chunks.append(chunk)
        else:
            min_silence_len=40
            silence_thresh=-20
            seek_step=1
            mini_chunks = split_on_silence(chunk, min_silence_len=min_silence_len, silence_thresh=silence_thresh, seek_step=seek_step)
            splited_chunks.extend(mini_chunks)

    combined_chunks = []
    if (len(splited_chunks) > 0):
        tc = splited_chunks[0]
        for i, c in enumerate(splited_chunks[1:]):
            if (len(tc) > 8000 or len(tc + c) > 20000):
                combined_chunks.append(tc)
                tc = c
            else:
                tc += c
        combined_chunks.append(tc)


    for i, c in enumerate(combined_chunks):
        print(len(c))

#sys.exit()

    lrcFile = codecs.open(fileBaseName + ".lrc", 'w', 'utf-8')
    lrcFile.write(('[ti:' + fileBaseName + "]\n").decode('utf-8'))
    total_sec = 0

    def write_chunk(chunk):
        ofn = "tmpchunk{0}_{1}.wav".format(total_sec, len(chunk))
        chunk.export(ofn, format="wav") #chunk.export(sio, format="s16le")
        #sio = StringIO.StringIO()
        #sio.getvalue()   #Raw PCM

    for i, chunk in enumerate(combined_chunks):
        #write_chunk(chunk)
        lrc = sec2LrcTime(total_sec)
        result = aipSpeech.asr(chunk.raw_data, 'pcm', bitrate, {'lan': language})
        if result and result['err_no'] == 0:
            lrc = (lrc + result['result'][0] + '\n').encode("utf-8")
            #print(lrc)
            lrcFile.write(lrc.decode('utf-8'))
        else:
            print("aipSpeech.asr error at:", i, chunk, "err_no:", result['err_no'])
            #pass
        total_sec += chunk.frame_count() / chunk.frame_rate
        #print(total_sec)

    lrcFile.close()

if __name__ == "__main__":
    main()
