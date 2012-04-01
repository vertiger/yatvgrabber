#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import codecs
import signal
import urllib
#import logging
import argparse
import datetime
import subprocess
from random import choice
from configobj import ConfigObj
from multiprocessing import Pool

def main():
    # argument parsing
    ArgumentParser.parseArguments()

    # override the urllib useragent - to get the custom user agent
    urllib._urlopener = AppOpener()

    # run the pre grab step
    preGrabCleanUp()

    # read / set the grabber configuration file
    grabConf = ConfigObj(ArgumentParser.args.configfile, raise_errors=True)
    if not os.path.isfile(ArgumentParser.args.configfile):
        # write the default configuration
        grabConf['page'] = ['http://www.tvtv.ch','http://www.tvtv.de','http://www.tvtv.at','http://www.tvtv.co.uk','http://www.tvtv.fr','http://www.tvtv.it']
        try:
            grabConf.write()
        except:
            print 'unable the write config file: ' +ArgumentParser.args.configfile
            sys.exit(-1)

    # execute the configure mode
    if ArgumentParser.args.configure:
        for page in reversed(grabConf['page']):
            DataStorage.channelList.update(parseChannelList(page))
        try:
            channelfile = open(ArgumentParser.args.channelfile, 'w')
            for channelid in sorted(DataStorage.channelList.keys()):
                channelfile.write(str(channelid) +'#'+ DataStorage.channelList[channelid] +'\n')
            channelfile.close()
        except:
            print 'error the writing channel file: ' +ArgumentParser.args.channelfile
            sys.exit(-1)
        print 'channel file successfully written, file: ' +ArgumentParser.args.channelfile
        sys.exit(0)

    # normal grabbing workflow
    # fill the channel list
    for line in open(ArgumentParser.args.channelfile, 'r'):
        if line.strip() == '':
            continue
        try:
            (chanid, name) = line.split('#')
            DataStorage.channelList[chanid] = name.strip()
        except:
            print 'error reading channel configuration, line: ' +line

    # get the program data
    parseChannelData(grabConf['page'][0], ArgumentParser.args.days)

    # post grab cleanup - do not cleanup after process locally
    if not ArgumentParser.args.local:
        postGrabCleanUp()

class DataStorage():
    channelList = {}
    xmlDataFile = None

class ArgumentParser():
    @staticmethod
    def parseArguments():
        parser = argparse.ArgumentParser(description='YaTvGrabber, XMLTV grabbing script',
                                 epilog='Copyright (C) [2012] [keller.eric, lars.schmohl]',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('--days', type=int, choices=range(1, 22), default=21,
                            help='days to grab')
        parser.add_argument('--outputfile', type=str, default='tvtv.xml',
                            help='output file with the xmltv data')
        parser.add_argument('--configure', action='store_true', default=False,
                            help='get all channels and create the channel file (normal grabbing is disabled)')
        parser.add_argument('--configfile', type=str, default='/etc/yatvgrabber/grab.conf',
                            help='configuration file for the grabber')
        parser.add_argument('--channelfile', type=str,
                            default='/etc/yatvgrabber/channel.grab', help='channel file for the grabber')
        parser.add_argument('--cachedir', type=str, default='/var/cache/yatvgrabber',
                            help='cache directory for the grabber')
        parser.add_argument('--local', action='store_true', default=False,
                            help='process only the local stored cache files')

        # parse the arguments
        ArgumentParser.args = parser.parse_args()
        ArgumentParser.args.outputfile  = os.path.realpath(ArgumentParser.args.outputfile)
        ArgumentParser.args.configfile  = os.path.realpath(ArgumentParser.args.configfile)
        ArgumentParser.args.channelfile = os.path.realpath(ArgumentParser.args.channelfile)
        ArgumentParser.args.cachedir    = os.path.realpath(ArgumentParser.args.cachedir)

def preGrabCleanUp():
    # create the config dir if needed
    if not os.path.isfile(ArgumentParser.args.configfile):
        configdir = os.path.dirname(ArgumentParser.args.configfile)
        if not os.path.isdir(configdir) and configdir != '':
            os.makedirs(configdir)
    # create the channel dir if needed
    if not os.path.isfile(ArgumentParser.args.channelfile):
        channeldir = os.path.dirname(ArgumentParser.args.channelfile)
        if not os.path.isdir(channeldir) and channeldir != '':
            os.makedirs(channeldir)

    if ArgumentParser.args.cachedir != '' and not os.path.isdir(ArgumentParser.args.cachedir):
        # create the cache dir if needed
        os.makedirs(ArgumentParser.args.cachedir)
    else:
        # cleanup the grabbed files - just the empty files
        subprocess.call('find '+ ArgumentParser.args.cachedir +' -type f -empty -not -name ".*" -exec rm -f \'{}\' +', shell=True)

def postGrabCleanUp():
    # cleanup the grabbed files - just the empty files
    subprocess.call('find '+ ArgumentParser.args.cachedir +' -type f -empty -not -name ".*" -exec rm -f \'{}\' +', shell=True)
    # cleanup the grabbed files - files which are not used anymore
    subprocess.call('find '+ ArgumentParser.args.cachedir +' -type f -atime +1 -not -name ".*" -exec rm -f \'{}\' +', shell=True)

class AppOpener(urllib.FancyURLopener):
    user_agents = ['Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0)',
                   'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)',
                   'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:10.0.2) Gecko/20100101 Firefox/10.0.2',
                   'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:11.0) Gecko/20100101 Firefox/11.0']
    version = choice(user_agents)

def getOverviewPage(base_url):
    filename = ArgumentParser.args.cachedir +'/'+ (base_url.split('/')[-1]).strip() + '.html'
    try:
        if not ArgumentParser.args.local:
            # always retrieve the overview page in none local mode
            urllib.urlretrieve(base_url, filename)
        if  not os.path.isfile(filename):
            raise Warning(filename)
    except:
        print 'error retrieve / open file: ' +filename
        return ''
    return open(filename, 'r').read().decode('utf-8')

def getAdditionalPage(base_url):
    filename = ArgumentParser.args.cachedir +'/'+ (base_url.split('/')[-1]).strip() + '.additional.html'
    try:
        if not ArgumentParser.args.local:
            # always retrieve the additional page in none local mode
            urllib.urlretrieve(base_url + '/tvtv/index.vm?mainTemplate=web%2FadditionalChannelsSelection.vm', filename)
        if  not os.path.isfile(filename):
            raise Warning(filename)
    except:
        print 'error retrieve / open file: ' +filename
        return ''
    return open(filename, 'r').read().decode("utf-8")

def getDayPage(base_url, week, day, channelId):
    print 'grabbing ' +base_url+ ' week ' +str(week)+ ' day ' +str(day)+ ' channelid ' +str(channelId)
    if (day > -1):
        # always retrieve the day page in none local mode
        filename = ArgumentParser.args.cachedir +'/week='+str(week)+'-day='+str(day)+'-channel='+str(channelId)+'.html'
        grabUrl = base_url + '/tvtv/index.vm?weekId='+str(week)+'&dayId='+str(day)+'&chnl='+str(channelId)
    else:
        # use channelWeek to get the hole week for one channel
        filename = ArgumentParser.args.cachedir +'/week='+str(week)+'-channel='+str(channelId)+'.html'
        grabUrl = base_url + '/tvtv/index.vm?weekId='+str(week)+'&dayId=0&weekChannel='+str(channelId)
    try:
        if not ArgumentParser.args.local:
            urllib.urlretrieve(grabUrl, filename)
        if  not os.path.isfile(filename):
            raise Warning(filename)
    except:
        print 'error retrieve / open file: ' +filename
        return ''
    return open(filename, 'r').read().decode('utf-8')

def getProgramPage(base_url, programId):
    # use the page from cache if available
    filename = ArgumentParser.args.cachedir +'/'+str(programId)+ '.html'
    try:
        # always cached the program page if available
        if not ArgumentParser.args.local and not os.path.isfile(filename):
            urllib.urlretrieve(base_url + '/tvtv/web/programdetails.vm?programmeId='+str(programId), filename)
        if  not os.path.isfile(filename):
            raise Warning(filename)
    except:
        print 'error retrieve / open file: ' +filename
        return ''
    return filename

def parseChannelList(pagename):
    channellist = {}

    # parse the main page
    for line in getOverviewPage(pagename).split('\n'):
        for foundId in RegExStorage.regExChannelId1.findall(line):
            for foundName in RegExStorage.regExChannelName.findall(line):
                channellist[foundId] = foundName + ' (' + pagename + ')'

    # additional page page
    for line in getAdditionalPage(pagename).split('\n'):
        for foundId in RegExStorage.regExChannelId2.findall(line):
            channellist[foundId] = (line.split('>')[-1]).strip() +' ('+ pagename +')'

    return channellist

def parseChannelData(pagename, days):
    grabPlan = []
    weeksToGrab = days // 7
    leftoverDaysToGrab = days % 7
    if weeksToGrab > 0:
        for weekno in range(0, weeksToGrab):
            grabPlan.append([weekno, -1])
    if leftoverDaysToGrab > 0:
        for dayno in range(0, leftoverDaysToGrab):
            grabPlan.append([weeksToGrab, dayno])

    # open the output file
    try:
        DataStorage.xmlDataFile = codecs.open(ArgumentParser.args.outputfile, 'w', 'utf-8')
    except:
        print 'error open outputfile, file: ' +ArgumentParser.args.outputfile
        sys.exit(-1)
    dataBuffer = []

    # write header
    dataBuffer.append('<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n')
    dataBuffer.append('<!DOCTYPE tv SYSTEM "xmltv.dtd">\n')
    dataBuffer.extend(['<tv source-info-url="', pagename, '" source-info-name="tvtv" generator-info-url="http://code.google.com/p/yatvgrabber/" generator-info-name="yatvgrabber">\n'])

    # list the channels
    for channelid in sorted(DataStorage.channelList.keys()):
        dataBuffer.extend(['  <channel id="', channelid, '">\n'])
        dataBuffer.extend(['    <display-name>', DataStorage.channelList[channelid].decode('latin1'), '</display-name>\n'])
        dataBuffer.append('  </channel>\n')
    DataStorage.xmlDataFile.write(''.join(dataBuffer))
    dataBuffer = []

    # multiprocessing
    pool = Pool(processes=None, initializer=initializeProcess)

    for entry in grabPlan:
        for channelId in DataStorage.channelList.keys():
            channelPage = getDayPage(pagename, entry[0], entry[1], channelId)
            for programId in RegExStorage.regExProgramId.findall(channelPage):
                # get the program page
                programFileName = getProgramPage(pagename, programId)

                # pass the filename to the process for parsing
                if programFileName != '':
                    pool.apply_async(processProgramPage, (programId, programFileName,), callback=contentInjectCallback)
                    #retValue = processProgramPage(programId, programFileName)
                    #contentInjectCallback(retValue)

    pool.close()
    pool.join()

    DataStorage.xmlDataFile.write('</tv>\n')
    DataStorage.xmlDataFile.close()
    print "xmltv file successfully written, file: " +ArgumentParser.args.outputfile

def contentInjectCallback(programEntry):

    dataBuffer = []
    for programid in programEntry.keys():
        if 0 == len(programEntry[programid]):
            print 'parsing error of programid ' +programid
            continue

        # get the programme data
        pdata = programEntry[programid]

        # check min requirements
        if not pdata.has_key('start') or not pdata.has_key('channel')  or not pdata.has_key('title'):
            print 'minimal required data not available of programid ' +programid
            continue
        if pdata['start'] == '' or pdata['channel'] == '' or pdata['title'] == '':
            print 'minimal required data not available of programid ' +programid
            continue

        # concat the programme tag
        dataBuffer.extend(['  <programme start="', pdata['start'], '" '])
        if pdata.has_key('finish') and pdata['finish'] != '':
            dataBuffer.extend(['finish="', pdata['finish'], '" '])
        dataBuffer.extend(['channel="', pdata['channel'], '">\n'])

        # write the title
        if pdata.has_key('title'):
            for tmpLang in pdata['title'].keys():
                if pdata['title'][tmpLang] != '':
                    dataBuffer.extend(['    <title lang="', tmpLang, '">', pdata['title'][tmpLang], '</title>\n'])
        # write the sub-title
        if pdata.has_key('sub-title'):
            for tmpLang in pdata['sub-title'].keys():
                if pdata['sub-title'][tmpLang] != '':
                    dataBuffer.extend(['    <sub-title lang="', tmpLang, '">', pdata['sub-title'][tmpLang], '</sub-title>\n'])
        # write the description
        if pdata.has_key('desc'):
            for tmpLang in pdata['desc'].keys():
                if pdata['desc'][tmpLang] != '':
                    dataBuffer.extend(['    <desc lang="', tmpLang, '">', pdata['desc'][tmpLang], '</desc>\n'])

        tmpCredits = []
        # director
        if pdata.has_key('director'):
            for tmpDirector in pdata['director']:
                if tmpDirector != '':
                    tmpCredits.extend(['      <director>', tmpDirector, '</director>\n'])
        # actors
        if pdata.has_key('actor'):
            for tmpActorData in pdata['actor']:
                for tmpActor in tmpActorData.keys():
                    if tmpActor != '':
                        if tmpActorData[tmpActor] == '':
                            tmpCredits.extend(['      <actor>', tmpActor, '</actor>\n'])
                        else:
                            tmpCredits.extend(['      <actor role="', tmpActorData[tmpActor], '">', tmpActor, '</actor>\n'])
        # writer
        if pdata.has_key('writer'):
            for tmpWriter in pdata['writer']:
                if tmpWriter != '':
                    tmpCredits.extend(['      <writer>', tmpWriter, '</writer>\n'])
        # adapter
        if pdata.has_key('adapter'):
            for tmpAdapter in pdata['adapter']:
                if tmpAdapter != '':
                    tmpCredits.extend(['      <adapter>', tmpAdapter, '</adapter>\n'])
        # producer
        if pdata.has_key('producer'):
            for tmpProducer in pdata['producer']:
                if tmpProducer != '':
                    tmpCredits.extend(['      <producer>', tmpProducer, '</producer>\n'])
        # composer
        if pdata.has_key('composer'):
            for tmpComposer in pdata['composer']:
                if tmpComposer != '':
                    tmpCredits.extend(['      <composer>', tmpComposer, '</composer>\n'])
        # editor
        if pdata.has_key('editor'):
            for tmpEditor in pdata['editor']:
                if tmpEditor != '':
                    tmpCredits.extend(['      <editor>', tmpEditor, '</editor>\n'])
        # presenter
        if pdata.has_key('presenter'):
            for tmpPresenter in pdata['presenter']:
                if tmpPresenter != '':
                    tmpCredits.extend(['      <presenter>', tmpPresenter, '</presenter>\n'])
        # commentator
        if pdata.has_key('commentator'):
            for tmpCommentator in pdata['commentator']:
                if tmpCommentator != '':
                    tmpCredits.extend(['      <commentator>', tmpCommentator, '</commentator>\n'])
        # guest
        if pdata.has_key('guest'):
            for tmpGuest in pdata['guest']:
                if tmpGuest != '':
                    tmpCredits.extend(['      <guest>', tmpGuest, '</guest>\n'])

        # write the credits
        if len(tmpCredits) > 0:
            dataBuffer.append('    <credits>\n')
            dataBuffer.extend(tmpCredits)
            dataBuffer.append('    </credits>\n')

        # production date
        if pdata.has_key('date') and pdata['date'] != '':
            dataBuffer.extend(['    <date>', pdata['date'], '</date>\n'])

        # category
        if pdata.has_key('category'):
            for tmpLang in pdata['category']:
                for tmpCategory in pdata['category'][tmpLang]:
                    if tmpCategory != '':
                        dataBuffer.extend(['    <category lang="', tmpLang, '">', tmpCategory, '</category>\n'])
        # language
        if pdata.has_key('language'):
            for tmpLang in pdata['language']:
                for tmpLanguage in pdata['language'][tmpLang]:
                    if tmpLanguage != '':
                        dataBuffer.extend(['    <language lang="', tmpLang, '">', tmpLanguage, '</language>\n'])
        # orig-language
        if pdata.has_key('orig-language'):
            for tmpLang in pdata['orig-language']:
                for tmpOrigLanguage in pdata['orig-language'][tmpLang]:
                    if tmpOrigLanguage != '':
                        dataBuffer.extend(['    <orig-language lang="', tmpLang, '">', tmpOrigLanguage, '</orig-language>\n'])
        # length
        if pdata.has_key('length'):
            for tmpUnits in pdata['length']:
                for tmpValue in pdata['length'][tmpUnits]:
                    if tmpValue != '':
                        dataBuffer.extend(['    <length units="', tmpUnits, '">', tmpValue, '</length>\n'])
        # icon
        if pdata.has_key('icon') and len(pdata['icon']) > 0:
            tmpIcon = []
            if pdata['icon'].has_key('src') and pdata['icon']['src'] != '':
                tmpIcon = ['    <icon src="', pdata['icon']['src'], '"']
                if pdata['icon'].has_key('width') and pdata['icon']['width'] != '':
                    tmpIcon.extend([' width="', pdata['icon']['width'], '"'])
                if pdata['icon'].has_key('height') and pdata['icon']['height'] != '':
                    tmpIcon.extend([' height="', pdata['icon']['height'], '"'])
            if len(tmpIcon) > 0:
                tmpIcon.append(' />')
                dataBuffer.extend(tmpIcon)
        # country
        if pdata.has_key('country'):
            for tmpLang in pdata['country']:
                for tmpCountry in pdata['country'][tmpLang]:
                    if tmpCountry != '':
                        dataBuffer.extend(['    <country lang="', tmpLang, '">', tmpCountry, '</country>\n'])

        # episode numbers
        if pdata.has_key('episode-num'):
            for tmpSystem in pdata['episode-num']:
                if pdata['episode-num'][tmpSystem] != '':
                    dataBuffer.extend(['    <episode-num system="', tmpSystem, '">', pdata['episode-num'][tmpSystem], '</episode-num>\n'])
        # regExRating
        if pdata.has_key('rating'):
            for tmpSystem in pdata['rating']:
                if pdata['rating'][tmpSystem] != '':
                    dataBuffer.extend(['    <regExRating system="', tmpSystem, '">'])
                    dataBuffer.extend(['      <value>', pdata['rating'][tmpSystem], '</value>\n'])
                    dataBuffer.append('    </regExRating>\n')

        # end programme tag
        dataBuffer.append('  </programme>\n')

    # write all collected programme
    if len(dataBuffer) > 0:
        DataStorage.xmlDataFile.write(''.join(dataBuffer))

def initializeProcess():
    # ignore sig int so the main process can be interrupted
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def processProgramPage(programId, filename):

    os.utime(filename, None)    ## "touch" the file
    programPage = open(filename, 'r').read().decode('utf-8')
    programData = { programId: {} }

    # min data found?
    try:
        if RegExStorage.regExChannelId3.search(programPage) == None:
            raise Warning(programId)
        if RegExStorage.regExDate.search(programPage) == None:
            raise Warning(programId)
        if RegExStorage.regExStart.search(programPage) == None:
            raise Warning(programId)
    except:
        os.remove(filename)
        return programData

    # get the channel id from the page
    for foundStr in RegExStorage.regExChannelId3.findall(programPage):
        tempStr = CleanFromTags(foundStr)
        if tempStr != '':
            programData[programId]['channel'] = tempStr
    # get the title from the page
    for foundStr in RegExStorage.regExTitle.findall(programPage):
        tempStr = CleanFromTags(foundStr)
        if tempStr != '':
            programData[programId]['title'] = { 'de': tempStr }
    # production year
    for foundStr in RegExStorage.regExProductionYear.findall(programPage):
        programData[programId]['date'] = CleanFromTags(foundStr)

    #cut down the content
    try:
        programPage = programPage.split(r'class="program-content"')[1]
        programPage = programPage.split(r'class="list_detail"')[0]
    except:
        os.remove(filename)
        return { programId: {} }

    # date
    date = ''
    for foundStr in RegExStorage.regExDate.findall(programPage):
        date = foundStr.strip()
    # start date
    startdate = datetime.datetime(2012, 1, 1)
    for foundStr in RegExStorage.regExStart.findall(programPage):
        try:
            (day, month, year) = date.split('.')
            (starthour, startminute) = foundStr.strip().split(':')
            startdate = datetime.datetime(int(year), int(month), int(day), int(starthour), int(startminute))
            programData[programId]['start'] = startdate.strftime('%Y%m%d%H%M')
        except:
            os.remove(filename)
            return { programId: {} }
    # stop date
    for foundStr in RegExStorage.regExStop.findall(programPage):
        try:
            (endhour, endminute) = foundStr.strip().split(':')
            enddate = datetime.datetime(int(year), int(month), int(day), int(endhour), int(endminute))
            if startdate > enddate:
                enddate = enddate + datetime.timedelta(days=1)  # program ends next day
            programData[programId]['finish'] =  enddate.strftime('%Y%m%d%H%M')
        except:
            pass # optional data

    # original title
    for foundStr in RegExStorage.regExOrgTitle.findall(programPage):
        tmpTitle = { 'de': CleanFromTags(foundStr) }
        if programData[programId].has_key('title') and programData[programId]['title']['de'] != '':
            if tmpTitle['de'] in programData[programId]['title']['de']:
                # org tile found, just use the title
                tmpTitle['de'] = programData[programId]['title']['de']
            else:
                # org title in title not found - concat the titles
                tmpTitle['de'] += " - "+ programData[programId]['title']['de']
        programData[programId]['title'] = tmpTitle
    if not programData[programId].has_key('title') or programData[programId]['title']['de'] == '':
        os.remove(filename)
        return { programId: {} }

    # sub-title
    for foundStr in RegExStorage.regExSubtitle.findall(programPage):
        programData[programId]['sub-title'] = { 'de': CleanFromTags(foundStr) }

    # description
    for foundStr in RegExStorage.regExDescription.findall(programPage):
        programData[programId]['desc'] = { 'de': CleanFromTags(foundStr) }

    # director
    for foundStr in RegExStorage.regExDirector.findall(programPage):
        programData[programId]['director'] = []
        for tmpDirector in CleanFromTags(foundStr).split(','):
            programData[programId]['director'].append(tmpDirector.strip())
    # actors
    for foundStr in RegExStorage.regExActors.findall(programPage):
        programData[programId]['actor'] = []
        for tmpActor in CleanFromTags(foundStr).split(','):
            try:
                (fActor, fRole) = tmpActor.strip().split('(')
                programData[programId]['actor'].append({fActor.strip(): fRole.strip(') ')})
            except:
                programData[programId]['actor'].append({tmpActor.strip(): ''})
    # producer
    for foundStr in RegExStorage.regExProducer.findall(programPage):
        programData[programId]['producer'] = []
        for tmpProducer in CleanFromTags(foundStr).split(','):
            programData[programId]['producer'].append(tmpProducer.strip())
    # writer
    for foundStr in RegExStorage.regExWriter.findall(programPage):
        programData[programId]['writer'] = []
        for tmpAuthor in CleanFromTags(foundStr).split(','):
            programData[programId]['writer'].append(tmpAuthor.strip())
    # presenter
    for foundStr in RegExStorage.regExPresenter.findall(programPage):
        programData[programId]['presenter'] = []
        for tmpPresenter in CleanFromTags(foundStr).split(','):
            programData[programId]['presenter'].append(tmpPresenter.strip())
    # category
    for foundStr in RegExStorage.regExCategory.findall(programPage):
        programData[programId]['category'] = { 'de': [] }
        for tmpCategory in CleanFromTags(foundStr).split(','):
            programData[programId]['category']['de'].append(tmpCategory.strip())
    # country
    for foundStr in RegExStorage.regExCountry.findall(programPage):
        programData[programId]['country'] = { 'de': [] }
        for tmpCountry in CleanFromTags(foundStr).split(','):
            programData[programId]['country']['de'].append(tmpCountry.strip())
    # episode in format xmltv_ns
    episodeString = ''
    for foundStr in RegExStorage.regExEpisode.findall(programPage):
        episodeString = episodeString +' '+ foundStr.strip()
    episodeString = episodeString.strip()
    if episodeString != '':
        tempstr = ''
        for tmpSeason in RegExStorage.regExSeason.findall(episodeString):
            tempstr = str(int(tmpSeason) - 1)
        tempstr += '.'
        for tmpEpisode in RegExStorage.regExEpisodeNum.findall(episodeString):
            tempstr += str(int(tmpEpisode) - 1)
            for tmpEpisodeTotal in RegExStorage.regExEpisodeTotal.findall(episodeString):
                tempstr +='/' + tmpEpisodeTotal
        if tempstr != ".":
            programData[programId]['episode-num'] = {'xmltv_ns': tempstr + '.' }
    # kid protection
    for foundStr in RegExStorage.regExRating.findall(programPage):
        programData[programId]['rating'] = { 'FSK': CleanFromTags(foundStr) }

    return programData

class RegExStorage():
    # for the configuration workflow
    regExChannelId1 = re.compile(r'weekChannel=([0-9]+)')
    regExChannelName = re.compile(r'class="">(.*)<')
    regExChannelId2 = re.compile(r'channelLogo=([0-9]+)"')

    # for the grab workflow
    regExProgramId = re.compile(r'programmeId=([0-9]+)')
    regExChannelId3 = re.compile(r's.prop16="[^\(]+\(([0-9]+)\)"')
    regExTitle = re.compile(r's.prop5="(.*)\[[0-9]+\]"')
    regExSubtitle = re.compile(r'<span class="fb-b9">(.*?)</span>')
    regExEpisode = re.compile(r'<span class="fn-b9">(.*?)</span>')
    regExProductionYear = re.compile(r'<td class="fb-b9 trailing">.*?([0-9]{4}).*?</td>', re.DOTALL)
    regExDescription = re.compile(r'<span class="fn-b10">(.*?)</span>', re.DOTALL)
    regExDate = re.compile(r'>[^<]+([0-9]{2}\.[0-9]{2}\.[0-9]{4})<')
    regExStart = re.compile(r'>Beginn: ([0-9]{2}:[0-9]{2}) Uhr<')
    regExStop = re.compile(r'>Ende: ([0-9]{2}:[0-9]{2}) Uhr<')
    regExActors = re.compile(r'>Darsteller:</td>(.+?)</tr>', re.DOTALL)
    regExProducer = re.compile(r'>Produktion:</td>(.+?)</tr>', re.DOTALL)
    regExDirector = re.compile(r'>Regie:</td>(.+?)</tr>', re.DOTALL)
    regExWriter = re.compile(r'>Autor:</td>(.+?)</tr>', re.DOTALL)
    regExRating = re.compile(r'>FSK:</td>.*: ([0-9]+).*</tr>', re.DOTALL)
    regExCategory = re.compile(r'>Kategorie:</td>(.+?)</tr>', re.DOTALL)
    regExCountry = re.compile(r'>Land:</td>(.+?)</tr>', re.DOTALL)
    regExSeason = re.compile(r'Staffel ([0-9]+)')
    regExEpisodeNum = re.compile(r'Folge ([0-9]+)')
    regExEpisodeTotal = re.compile(r'Folge [0-9]+/([0-9]+)')
    regExOrgTitle = re.compile(r'>Orginaltitel:</td>(.+?)</tr>', re.DOTALL)
    regExPresenter = re.compile(r'sentiert von:</td>(.+?)</tr>', re.DOTALL)

    # treat special chars and words
    charSpecial = {1 : [re.compile(r'<[^>]*>'), r' '],
                   2 : [re.compile(r'&nbsp;'), r' '],
                   3 : [re.compile(r'\(Wiederholung\)'), r''],
                   4 : [re.compile(r'^Reihe: .+'), r''],
                   5 : [re.compile(r'&'), r'&amp;'],
                   6 : [re.compile(r'"'), r'&quot;'],
                   97: [re.compile(r'c\<t'), r'c\'t'],
                   98: [re.compile(r'[\n\t ]+', re.DOTALL), r' '],
                   99: [re.compile(r',$'), r'']}

def CleanFromTags(inputStr):

    retStr = inputStr
    for key in sorted(RegExStorage.charSpecial.keys()):
        retStr = RegExStorage.charSpecial[key][0].sub(RegExStorage.charSpecial[key][1], retStr)   # clean all special characters

    return retStr.strip()

# open the gui
if __name__ == "__main__":
    main()
