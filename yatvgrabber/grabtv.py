#!/usr/bin/env python
# -*- coding: utf-8 -*-

# standart libraries
import os
import re
import sys
import codecs
import signal
import string
import urllib
#import logging
import datetime
import subprocess
from random import choice
from multiprocessing import Pool

# third party libraries
import argparse
from configobj import ConfigObj

def main():
    # argument parsing
    ArgumentParser.parseArguments()

    # override the urllib useragent - to get the custom user agent
    urllib._urlopener = AppOpener()

    # run the pre grab step
    preGrabCleanUp()

    # read / set the grabber configuration file
    tmpConfigFile = ArgumentParser.args.configfile
    grabConf = ConfigObj(tmpConfigFile, raise_errors=True)
    if not os.path.isfile(tmpConfigFile):
        # write the default configuration
        grabConf['page'] = ['http://www.tvtv.ch','http://www.tvtv.de','http://www.tvtv.at','http://www.tvtv.co.uk','http://www.tvtv.fr','http://www.tvtv.it']
        try:
            grabConf.write()
        except:
            print 'unable the write config file: %s' % ArgumentParser.args.configfile
            sys.exit(-1)

    # execute the configure mode
    tmpChannelFile = ArgumentParser.args.channelfile
    if ArgumentParser.args.configure:
        tmpChannelList = {}
        [ tmpChannelList.update(parseChannelList(page)) for page in reversed(grabConf['page']) ]
        try:
            channelfile = open(tmpChannelFile, 'w')
            tmpList = []
            [ tmpList.append('%s#%s\n' % (channelid, tmpChannelList[channelid])) for channelid in sorted(tmpChannelList.keys()) ]
            channelfile.write(string.joinfields(tmpList, ''))
            channelfile.close()
        except:
            print 'error the writing channel file: %s' % tmpChannelFile
            sys.exit(-1)
        print 'channel file successfully written, file: %s' % tmpChannelFile
        sys.exit(0)

    # normal grabbing workflow
    # fill the channel list
    tmpChanList = {}
    lstrip = string.strip
    lsplit = string.split
    for line in open(tmpChannelFile, 'r'):
        if lstrip(line) == '':
            continue
        try:
            (chanid, name) = lsplit(line, '#')
            tmpChanList[chanid] = lstrip(name)
        except:
            print 'error reading channel configuration, line: %s' % line
    DataStorage.channelList = tmpChanList

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
    tmpConfigFile = ArgumentParser.args.configfile
    if not os.path.isfile(tmpConfigFile):
        configdir = os.path.dirname(tmpConfigFile)
        if not os.path.isdir(configdir) and configdir != '':
            os.makedirs(configdir)
    # create the channel dir if needed
    tmpChannelFile = ArgumentParser.args.channelfile
    if not os.path.isfile(tmpChannelFile):
        channeldir = os.path.dirname(tmpChannelFile)
        if not os.path.isdir(channeldir) and channeldir != '':
            os.makedirs(channeldir)

    tmpCacheDir = ArgumentParser.args.cachedir
    if not os.path.isdir(tmpCacheDir) and tmpCacheDir != '':
        # create the cache dir if needed
        os.makedirs(tmpCacheDir)
    else:
        # cleanup the grabbed files - just the empty files
        subprocess.call('find %s -type f -empty -not -name ".*" -exec rm -f \'{}\' +' % tmpCacheDir, shell=True)

def postGrabCleanUp():
    tmpCacheDir = ArgumentParser.args.cachedir
    # cleanup the grabbed files - just the empty files
    subprocess.call('find %s -type f -empty -not -name ".*" -exec rm -f \'{}\' +' % tmpCacheDir, shell=True)
    # cleanup the grabbed files - files which are not used anymore
    subprocess.call('find %s -type f -atime +1 -not -name ".*" -exec rm -f \'{}\' +' % tmpCacheDir, shell=True)

class AppOpener(urllib.FancyURLopener):
    user_agents = ['Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0)',
                   'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)',
                   'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:10.0.2) Gecko/20100101 Firefox/10.0.2',
                   'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:11.0) Gecko/20100101 Firefox/11.0']
    version = choice(user_agents)

def getOverviewPage(base_url):
    filename = '%s/%s.html' % (ArgumentParser.args.cachedir, (base_url.split('/')[-1]).strip())
    try:
        if not ArgumentParser.args.local:
            # always retrieve the overview page in none local mode
            urllib.urlretrieve(base_url, filename)
        if not os.path.isfile(filename):
            raise Warning(filename)
    except:
        print 'error retrieve / open file: %s' % filename
        return ''
    return open(filename, 'r').read().decode('utf-8')

def getAdditionalPage(base_url):
    filename = '%s/%s.additional.html' % (ArgumentParser.args.cachedir, (base_url.split('/')[-1]).strip())
    try:
        if not ArgumentParser.args.local:
            # always retrieve the additional page in none local mode
            urllib.urlretrieve('%s/tvtv/index.vm?mainTemplate=web%%2FadditionalChannelsSelection.vm' % base_url, filename)
        if not os.path.isfile(filename):
            raise Warning(filename)
    except:
        print 'error retrieve / open file: %s' % filename
        return ''
    return open(filename, 'r').read().decode('utf-8')

def getWeekDayPage(base_url, week, day, channelId):
    print 'grabbing %s week %s day %s channelid %s ' % (base_url, week, day, channelId)
    filename = '%s/week=%s-day=%s-channel=%s.html' % (ArgumentParser.args.cachedir, week, day, channelId)
    if day > -1:
        # always retrieve the day page in none local mode
        grabUrl  = '%s/tvtv/index.vm?weekId=%s&dayId=%s&chnl=%s' % (base_url, week, day, channelId)
    else:
        # use channelWeek to get the hole week for one channel
        grabUrl  = '%s/tvtv/index.vm?weekId=%s&dayId=0&weekChannel=%s' % (base_url, week, channelId)
    try:
        if not ArgumentParser.args.local:
            urllib.urlretrieve(grabUrl, filename)
        if not os.path.isfile(filename):
            raise Warning(filename)
    except:
        print 'error retrieve / open file: %s' % filename
        return ''
    return filename

def getProgramPage(base_url, programId):
    # use the page from cache if available
    filename = '%s/%s.html' % (ArgumentParser.args.cachedir, programId)
    try:
        # always cached the program page if available
        if not ArgumentParser.args.local and not os.path.isfile(filename):
            urllib.urlretrieve('%s/tvtv/web/programdetails.vm?programmeId=%s' % (base_url, programId), filename)
        if not os.path.isfile(filename):
            raise Warning(filename)
    except:
        print 'error retrieve / open file: %s' % filename
        return ''
    return filename

def parseChannelList(pagename):
    channellist = {}

    # parse the main page
    for line in getOverviewPage(pagename).split('\n'):
        for foundId in RegExStorage.regExChannelId1.findall(line):
            for foundName in RegExStorage.regExChannelName.findall(line):
                channellist[foundId] = '%s (%s)' % (foundName, pagename)

    # additional page page
    for line in getAdditionalPage(pagename).split('\n'):
        for foundId in RegExStorage.regExChannelId2.findall(line):
            channellist[foundId] = '%s (%s)' % ((line.split('>')[-1]).strip(), pagename)

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

    # multiprocessing
    pool = Pool(processes=None, initializer=initializeProcess)

    resultsList = []
    for entry in grabPlan:
        for channelId in DataStorage.channelList.keys():
            pageFileName = getWeekDayPage(pagename, entry[0], entry[1], channelId)
            resultsList.append(pool.apply_async(processChannelPage, (pageFileName, )))

    # open the output file
    try:
        DataStorage.xmlDataFile = codecs.open(ArgumentParser.args.outputfile, 'w', 'utf-8')
    except:
        print 'error open outputfile, file: ' +ArgumentParser.args.outputfile
        sys.exit(-1)

    # write header
    tmpData = []
    tmpData.append('<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n')
    tmpData.append('<!DOCTYPE tv SYSTEM "xmltv.dtd">\n')
    tmpData.append('<tv source-info-url="%s" source-info-name="tvtv" generator-info-url="http://code.google.com/p/yatvgrabber/" generator-info-name="yatvgrabber">\n' % pagename)

    # list the channels
    for channelid in DataStorage.channelList.keys():
        tmpData.append('  <channel id="%s">\n' % channelid)
        tmpData.append('    <display-name>%s</display-name>\n' % DataStorage.channelList[channelid].decode('latin1'))
        tmpData.append('  </channel>\n')
    DataStorage.xmlDataFile.write(string.joinfields(tmpData, ''))

    # collect the results
    programIdList = []
    [ programIdList.extend(tmpResults.get(timeout=10)) for tmpResults in resultsList ]

    #program page getting loop
    totalProgrammeIds = len(programIdList)
    stepProgrammeIds = 0
    tmpTime1 = datetime.datetime(2012, 1, 1)
    for programId in programIdList:
        #debug output
        tmpTime2 = datetime.datetime.today()
        if (tmpTime2 > (tmpTime1 + datetime.timedelta(minutes=5))):
            print "[%s] progress: %s of %s program pages" % (tmpTime2.strftime('%Y-%m-%d %H:%M:%S'), stepProgrammeIds, totalProgrammeIds)
            tmpTime1 = tmpTime2

        # get the program page
        programFileName = getProgramPage(pagename, programId)

        # pass the filename to the process for parsing
        if programFileName != '':
            pool.apply_async(processProgramPage, (programId, programFileName,), callback=contentInjectCallback)
            #retValue = processProgramPage(programId, programFileName)
            #contentInjectCallback(retValue)
        stepProgrammeIds += 1

    pool.close()
    pool.join()

    DataStorage.xmlDataFile.write('</tv>\n')
    DataStorage.xmlDataFile.close()
    print 'xmltv file successfully written, file: %s' % ArgumentParser.args.outputfile

def processChannelPage(filename):
    tmpData = ''
    try:
        tmpData = open(filename, 'r').read().decode('utf-8')
    except:
        return []
    return RegExStorage.regExProgramId.findall(tmpData)

def contentInjectCallback(programEntry):

    llen = len
    for programid in programEntry.keys():
        if 0 == llen(programEntry[programid]):
            print 'parsing error of programid %s' % programid
            continue

        # get the programme data
        pdata = programEntry[programid]

        # check min requirements
        if 'start' not in pdata or 'channel' not in pdata or 'title' not in pdata:
            print 'minimal required data not available of programid %s' % programid
            continue
        if pdata['start'] == '' or pdata['channel'] == '' or pdata['title'] == '':
            print 'minimal required data not available of programid %s' % programid
            continue

        tmpData = []
        # concat the programme tag
        tmpData.append('  <programme start="%s" ' % pdata['start'])
        if 'finish' in pdata and pdata['finish'] != '':
            tmpData.append('finish="%s" ' % pdata['finish'])
        tmpData.append('channel="%s">\n' % pdata['channel'])

        # write the title
        if 'title' in pdata:
            for tmpLang in pdata['title'].keys():
                if pdata['title'][tmpLang] != '':
                    tmpData.append('    <title lang="%s">%s</title>\n' % (tmpLang, pdata['title'][tmpLang]))
        # write the sub-title
        if 'sub-title' in pdata:
            for tmpLang in pdata['sub-title'].keys():
                if pdata['sub-title'][tmpLang] != '':
                    tmpData.append('    <sub-title lang="%s">%s</sub-title>\n' % (tmpLang, pdata['sub-title'][tmpLang]))
        # write the description
        if 'desc' in pdata:
            for tmpLang in pdata['desc'].keys():
                if pdata['desc'][tmpLang] != '':
                    tmpData.append('    <desc lang="%s">%s</desc>\n' % (tmpLang, pdata['desc'][tmpLang]))

        tmpCredits = []
        # director
        if 'director' in pdata:
            for tmpDirector in pdata['director']:
                if tmpDirector != '':
                    tmpCredits.append('      <director>%s</director>\n' % tmpDirector)
        # actors
        if 'actor' in pdata:
            for tmpActorData in pdata['actor']:
                for tmpActor in tmpActorData.keys():
                    if tmpActor != '':
                        if tmpActorData[tmpActor] == '':
                            tmpCredits.append('      <actor>%s</actor>\n' % tmpActor)
                        else:
                            tmpCredits.append('      <actor role="%s">%s</actor>\n' % (tmpActorData[tmpActor], tmpActor))
        # writer
        if 'writer' in pdata:
            for tmpWriter in pdata['writer']:
                if tmpWriter != '':
                    tmpCredits.append('      <writer>%s</writer>\n' % tmpWriter)
        # adapter
        if 'adapter' in pdata:
            for tmpAdapter in pdata['adapter']:
                if tmpAdapter != '':
                    tmpCredits.append('      <adapter>%s</adapter>\n' % tmpAdapter)
        # producer
        if 'producer' in pdata:
            for tmpProducer in pdata['producer']:
                if tmpProducer != '':
                    tmpCredits.append('      <producer>%s</producer>\n' % tmpProducer)
        # composer
        if 'composer' in pdata:
            for tmpComposer in pdata['composer']:
                if tmpComposer != '':
                    tmpCredits.append('      <composer>%s</composer>\n' % tmpComposer)
        # editor
        if 'editor' in pdata:
            for tmpEditor in pdata['editor']:
                if tmpEditor != '':
                    tmpCredits.append('      <editor>%s</editor>\n' % tmpEditor)
        # presenter
        if 'presenter' in pdata:
            for tmpPresenter in pdata['presenter']:
                if tmpPresenter != '':
                    tmpCredits.append('      <presenter>%s</presenter>\n' % tmpPresenter)
        # commentator
        if 'commentator' in pdata:
            for tmpCommentator in pdata['commentator']:
                if tmpCommentator != '':
                    tmpCredits.append('      <commentator>%s</commentator>\n' % tmpCommentator)
        # guest
        if 'guest' in pdata:
            for tmpGuest in pdata['guest']:
                if tmpGuest != '':
                    tmpCredits.append('      <guest>%s</guest>\n' % tmpGuest)

        # write the credits
        if llen(tmpCredits) > 0:
            tmpData.append('    <credits>\n')
            tmpData.extend(tmpCredits)
            tmpData.append('    </credits>\n')

        # production date
        if 'date' in pdata and pdata['date'] != '':
            tmpData.append('    <date>%s</date>\n' % pdata['date'])

        # category
        if 'category' in pdata:
            for tmpLang in pdata['category']:
                for tmpCategory in pdata['category'][tmpLang]:
                    if tmpCategory != '':
                        tmpData.append('    <category lang="%s">%s</category>\n' % (tmpLang, tmpCategory))
        # language
        if 'language' in pdata:
            for tmpLang in pdata['language']:
                for tmpLanguage in pdata['language'][tmpLang]:
                    if tmpLanguage != '':
                        tmpData.append('    <language lang="%s">%s</language>\n' % (tmpLang, tmpLanguage))
        # orig-language
        if 'orig-language' in pdata:
            for tmpLang in pdata['orig-language']:
                for tmpOrigLanguage in pdata['orig-language'][tmpLang]:
                    if tmpOrigLanguage != '':
                        tmpData.append('    <orig-language lang="%s">%s</orig-language>\n' % (tmpLang, tmpOrigLanguage))
        # length
        if 'length' in pdata:
            for tmpUnits in pdata['length']:
                for tmpValue in pdata['length'][tmpUnits]:
                    if tmpValue != '':
                        tmpData.append('    <length units="%s">%s</length>\n' % (tmpUnits, tmpValue))
        # icon
        if 'icon' in pdata and llen(pdata['icon']) > 0:
            tmpIcon = []
            if 'src' in pdata['icon'] and pdata['icon']['src'] != '':
                tmpIcon = ['    <icon src="%s"' % pdata['icon']['src']]
                if 'width' in pdata['icon'] and pdata['icon']['width'] != '':
                    tmpIcon.append(' width="%s"' % pdata['icon']['width'])
                if 'height' in pdata['icon'] and pdata['icon']['height'] != '':
                    tmpIcon.append(' height="%s"' % pdata['icon']['height'])
                tmpIcon.append(' />\n')
            if llen(tmpIcon) > 0:
                tmpData.extend(tmpIcon)
        # country
        if 'country' in pdata:
            for tmpLang in pdata['country']:
                for tmpCountry in pdata['country'][tmpLang]:
                    if tmpCountry != '':
                        tmpData.append('    <country lang="%s">%s</country>\n' % (tmpLang, tmpCountry))

        # episode numbers
        if 'episode-num' in pdata:
            for tmpSystem in pdata['episode-num']:
                if pdata['episode-num'][tmpSystem] != '':
                    tmpData.append('    <episode-num system="%s">%s</episode-num>\n' % (tmpSystem, pdata['episode-num'][tmpSystem]))
        # regExRating
        if 'rating' in pdata:
            for tmpSystem in pdata['rating']:
                if pdata['rating'][tmpSystem] != '':
                    tmpData.append('    <regExRating system="%s">\n' % tmpSystem)
                    tmpData.append('      <value>%s</value>\n' % pdata['rating'][tmpSystem])
                    tmpData.append('    </regExRating>\n')

        # end programme tag
        tmpData.append('  </programme>\n')
        DataStorage.xmlDataFile.write(string.joinfields(tmpData, ''))

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
        if 'title' in programData[programId] and programData[programId]['title']['de'] != '':
            if tmpTitle['de'] in programData[programId]['title']['de']:
                # org tile found, just use the title
                tmpTitle['de'] = programData[programId]['title']['de']
            else:
                # org title in title not found - concat the titles
                tmpTitle['de'] = "%s - %s" % (tmpTitle['de'], programData[programId]['title']['de'])
        programData[programId]['title'] = tmpTitle
    if 'title' not in programData[programId] or programData[programId]['title']['de'] == '':
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
                (fActor, fRole) = tmpActor.strip().split('(', 1)
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
        episodeString = '%s %s' % (episodeString, foundStr.strip())
    episodeString = episodeString.strip()
    if episodeString != '':
        tempstr = ''
        for tmpSeason in RegExStorage.regExSeason.findall(episodeString):
            tempstr = str(int(tmpSeason) - 1)
        tempstr = '%s.' % tempstr
        for tmpEpisode in RegExStorage.regExEpisodeNum.findall(episodeString):
            tempstr = '%s%s' % (tempstr, int(tmpEpisode) - 1)
            for tmpEpisodeTotal in RegExStorage.regExEpisodeTotal.findall(episodeString):
                tempstr ='%s/%s' % (tempstr, tmpEpisodeTotal)
        if tempstr != ".":
            programData[programId]['episode-num'] = {'xmltv_ns': '%s.' % tempstr }
    # kid protection
    for foundStr in RegExStorage.regExRating.findall(programPage):
        programData[programId]['rating'] = { 'FSK': CleanFromTags(foundStr) }

    return programData

class RegExStorage():
    # for the configuration workflow
    regExChannelId1 = re.compile(r'weekChannel=([0-9]+)"')
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
        # clean all special characters
        retStr = RegExStorage.charSpecial[key][0].sub(RegExStorage.charSpecial[key][1], retStr)

    return retStr.strip()

# open the gui
if __name__ == "__main__":
    main()
