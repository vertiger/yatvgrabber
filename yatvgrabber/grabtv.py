#!/usr/bin/env python
# -*- coding: utf-8 -*-

# standard libraries
import os
import re
import sys
import codecs
import signal
import string
import urllib
import datetime
import time
import subprocess
from random import choice
from multiprocessing import Pool
from xml.sax.saxutils import escape, quoteattr

# third party libraries
import argparse
from configobj import ConfigObj
import pytz


def main():

    # argument parsing
    ArgumentParser.parseArguments()

    # override the urllib useragent - to use the custom user agent
    urllib._urlopener = AppOpener()

    # run the pre grab step
    preGrabCleanUp()

    # read / set the grabber configuration file
    tmpConfigFile = ArgumentParser.args.configfile
    grabConf = ConfigObj(tmpConfigFile, raise_errors = True)
    if not os.path.isfile(tmpConfigFile):
        # write the default configuration
        grabConf['page'] = ['http://www.tvtv.ch',
                            'http://www.tvtv.de',
                            'http://www.tvtv.at']
        try:
            grabConf.write()
        except:
            print 'unable the write config file: %s' % \
                  ArgumentParser.args.configfile
            sys.exit(-1)

    # execute the configure mode
    tmpChannelFile = ArgumentParser.args.channelfile
    if ArgumentParser.args.configure:
        tmpChannelList = {}
        [tmpChannelList.update(parseChannelList(page)) for page in reversed(grabConf['page'])]
        try:
            tmpList = []
            [tmpList.append('%s#%s\n' % (channelid, tmpChannelList[channelid]))
                for channelid in sorted(tmpChannelList.keys())]
            codecs.open(tmpChannelFile, 'w', 'utf-8').write(string.joinfields(tmpList, ''))
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
    parseChannelData(grabConf['page'][0], ArgumentParser.args.weeks)

    # post grab cleanup - do not cleanup after process locally
    if not ArgumentParser.args.local:
        postGrabCleanUp()

    #normal exit
    sys.exit(0)


class DataStorage():
    channelList = {}
    xmlDataFile = None


class ArgumentParser():
    @staticmethod
    def parseArguments():
        parser = argparse.ArgumentParser(
                    description = 'YaTvGrabber, XMLTV grabbing script',
                    epilog = 'Copyright (C) [2013] [keller.eric, lars.schmohl]',
                    formatter_class = argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('--weeks', type = int, choices = range(1, 4),
                            default = 3,
                            help = 'weeks to grab')
        parser.add_argument('--outputfile', type = str,
                            default = 'tvtv.xml',
                            help = 'output file with the xmltv data')
        parser.add_argument('--configure', action = 'store_true',
                            default = False,
                            help = 'get all channels and create \
                            the channel file (normal grabbing is disabled)')
        parser.add_argument('--configfile', type = str,
                            default = '/etc/yatvgrabber/grab.conf',
                            help = 'configuration file for the grabber')
        parser.add_argument('--channelfile', type = str,
                            default = '/etc/yatvgrabber/channel.grab',
                            help = 'channel file for the grabber')
        parser.add_argument('--cachedir', type = str,
                            default = '/var/cache/yatvgrabber',
                            help = 'cache directory for the grabber')
        parser.add_argument('--local', action = 'store_true',
                            default = False,
                            help = 'process only the local stored cache files')

        # parse the arguments
        ArgumentParser.args = parser.parse_args()
        ArgumentParser.args.outputfile = \
            os.path.realpath(ArgumentParser.args.outputfile)
        ArgumentParser.args.configfile = \
            os.path.realpath(ArgumentParser.args.configfile)
        ArgumentParser.args.channelfile = \
            os.path.realpath(ArgumentParser.args.channelfile)
        ArgumentParser.args.cachedir = \
            os.path.realpath(ArgumentParser.args.cachedir)


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
        subprocess.call('find %s -type f -empty -not -name ".*" \
                         -exec rm -f \'{}\' +' % tmpCacheDir, shell = True)


def postGrabCleanUp():
    tmpCacheDir = ArgumentParser.args.cachedir
    # cleanup the grabbed files - just the empty files
    subprocess.call('find %s -type f -empty -not -name ".*" \
                     -exec rm -f \'{}\' +' % tmpCacheDir, shell = True)
    # cleanup the grabbed files - files which are not used anymore
    subprocess.call('find %s -type f -atime +1 -not -name ".*" \
                     -exec rm -f \'{}\' +' % tmpCacheDir, shell = True)


class AppOpener(urllib.FancyURLopener):
    user_agents = ['Mozilla/5.0 ;Windows NT 6.1; WOW64; AppleWebKit/537.36 ;KHTML, like Gecko; Chrome/36.0.1985.143 Safari/537.36',
                   'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Safari/537.36',
                   'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/600.3.18 (KHTML, like Gecko) Version/8.0.3 Safari/600.3.18',
                   'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
                   'Mozilla/5.0 ;Windows NT 6.2; WOW64; rv:27.0; Gecko/20100101 Firefox/27.0',
                   'Mozilla/5.0 ;Windows NT 6.3; WOW64; AppleWebKit/537.36 ;KHTML, like Gecko; Chrome/39.0.2171.95 Safari/537.36']
    version = choice(user_agents)


def getOverviewPage(base_url):
    filename = '%s/%s.html' % (ArgumentParser.args.cachedir,
                               (base_url.split('/')[-1]).strip())
    try:
        if not ArgumentParser.args.local:
            # always retrieve the overview page in none local mode
            urllib.urlretrieve(base_url, filename)
        if not os.path.isfile(filename):
            raise Warning(filename)
        else:
            if os.stat(filename).st_size == 0:
                os.remove(filename)
                raise Warning(filename)
    except:
        print 'error retrieve / open file: %s' % filename
        sys.exit(-1)
    return open(filename, 'r').read().decode('utf-8')


def getWeekDayPage(base_url, week, channelId):
    print 'grabbing %s week %s channel %s ' % (base_url, week, channelId)
    filename = '%s/week=%s-channel=%s.html' % (ArgumentParser.args.cachedir, week, channelId)
    # use channelWeek to get the hole week for one channel
    grabUrl = '%s/senderlistings_channel.php?channel=%s&woche=%s' % (base_url, channelId, week)
    try:
        # always retrieve the day page in none local mode
        if not ArgumentParser.args.local:
            urllib.urlretrieve(grabUrl, filename)
        if not os.path.isfile(filename):
            raise Warning(filename)
        else:
            if os.stat(filename).st_size == 0:
                os.remove(filename)
                raise Warning(filename)
    except:
        print 'error retrieve / open file: %s' % filename
        sys.exit(-1)
    return filename


def getProgramPage(base_url, programId):
    # use the page from cache if available
    filename = '%s/%s.html' % (ArgumentParser.args.cachedir, programId)
    try:
        # always use the cached program page if available
        if not ArgumentParser.args.local and not os.path.isfile(filename):
            urllib.urlretrieve('%s/detailansicht.php?sendungs_id=%s' % (base_url, programId), filename)
        if not os.path.isfile(filename):
            raise Warning(filename)
        else:
            if os.stat(filename).st_size == 0:
                os.remove(filename)
                raise Warning(filename)
    except:
        print 'error retrieve / open file: %s' % filename
        sys.exit(-1)
    return filename


def parseChannelList(pagename):
    channellist = {}

    # parse the main page
    for line in getOverviewPage(pagename).split('\n'):
        for programId in RegExStorage.regExChannelId1.findall(line):
            for programName in RegExStorage.regExChannelName.findall(line):
                channellist[programId] = '%s (%s)' % (programName, pagename)

    return channellist


def parseChannelData(pagename, weeks):

    # multiprocessing
    pool = Pool(processes = None, initializer = initializeProcess)

    resultsList = []
    for entry in range(0, weeks):
        for channelId in DataStorage.channelList.keys():
            pageFileName = getWeekDayPage(pagename, entry, channelId)
            resultsList.append(pool.apply_async(processChannelPage,
                                                (pageFileName,)))

    # open the output file
    try:
        DataStorage.xmlDataFile = codecs.open(
                            ArgumentParser.args.outputfile, 'w', 'utf-8')
    except:
        print 'error open outputfile, file: ' + ArgumentParser.args.outputfile
        sys.exit(-1)

    # write header
    tmpData = []
    tmpData.append('<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n')
    tmpData.append('<!DOCTYPE tv SYSTEM "xmltv.dtd">\n')
    tmpData.append('<tv source-info-url="%s" source-info-name="tvtv" generator-info-url="http://code.google.com/p/yatvgrabber/" generator-info-name="yatvgrabber">\n' % pagename)

    # list the channels
    for channelid in DataStorage.channelList.keys():
        tmpData.append('  <channel id="%s">\n' % channelid)
        tmpData.append('    <display-name>%s</display-name>\n' % \
                       DataStorage.channelList[channelid].decode('latin1'))
        tmpData.append('    <icon src="%s/images/senderlogos/%s.gif" />\n' % (pagename, channelid.lower()))
        tmpData.append('  </channel>\n')
    DataStorage.xmlDataFile.write(string.joinfields(tmpData, ''))

    # collect the results
    programIdList = []
    [programIdList.extend(tmpResults.get(timeout = 10))
        for tmpResults in resultsList]

    #program page getting loop
    totalProgrammeIds = len(programIdList)
    stepProgrammeIds = 0
    tmpTime1 = datetime.datetime(2012, 1, 1)
    for programId in programIdList:
        #debug output
        tmpTime2 = datetime.datetime.today()
        if (tmpTime2 > (tmpTime1 + datetime.timedelta(minutes = 5))):
            print "[%s] progress: %s of %s program pages" % \
                (tmpTime2.strftime('%Y-%m-%d %H:%M:%S'),
                 stepProgrammeIds,
                 totalProgrammeIds)
            tmpTime1 = tmpTime2

        # get the program page
        programFileName = getProgramPage(pagename, programId)

        # pass the filename to the process for parsing
        if programFileName != '':
            pool.apply_async(processProgramPage,
                             (programId, programFileName,),
                             callback = contentInjectCallback)
            #retValue = processProgramPage(programId, programFileName)
            #contentInjectCallback(retValue)
        stepProgrammeIds += 1

    pool.close()
    pool.join()

    DataStorage.xmlDataFile.write('</tv>\n')
    DataStorage.xmlDataFile.close()
    print 'xmltv file successfully written, file: %s' % \
            ArgumentParser.args.outputfile


def processChannelPage(filename):
    tmpData = ''
    programIds = []
    try:
        tmpData = open(filename, 'r').read().decode('utf-8')
    except:
        return programIds
    for foundId in RegExStorage.regExProgramId.findall(tmpData):
        if foundId not in programIds:
            programIds.append(foundId)
    return programIds


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
            print 'minimal required data is invalid of programid %s' % programid
            continue

        tmpData = []
        # concat the programme tag
        # timezone offset - the tvtv website always displays dates and times in the CET timezone
        tmpData.append('  <programme start="%s" ' % pytz.timezone('Europe/Zurich').localize(pdate['start']).strftime('%Y%m%d%H%M%S %z'))
        if 'finish' in pdata and pdata['finish'] != '':
            tmpData.append('stop="%s" ' % pytz.timezone('Europe/Zurich').localize(pdate['finish']).strftime('%Y%m%d%H%M%S %z'))
        tmpData.append('channel="%s">\n' % pdata['channel'])

        # write the title
        if 'title' in pdata:
            for tmpLang in pdata['title'].keys():
                if pdata['title'][tmpLang] != '':
                    tmpData.append('    <title lang="%s">%s</title>\n' % (tmpLang, escape(pdata['title'][tmpLang])))
        # write the sub-title
        if 'sub-title' in pdata:
            for tmpLang in pdata['sub-title'].keys():
                if pdata['sub-title'][tmpLang] != '':
                    tmpData.append('    <sub-title lang="%s">%s</sub-title>\n' % (tmpLang, escape(pdata['sub-title'][tmpLang])))
        # write the description
        if 'desc' in pdata:
            for tmpLang in pdata['desc'].keys():
                if pdata['desc'][tmpLang] != '':
                    tmpData.append('    <desc lang="%s">%s</desc>\n' % (tmpLang, escape(pdata['desc'][tmpLang])))

        tmpCredits = []
        # director
        if 'director' in pdata:
            for tmpDirector in pdata['director']:
                if tmpDirector != '':
                    tmpCredits.append('      <director>%s</director>\n' % escape(tmpDirector))
        # actors
        if 'actor' in pdata:
            for tmpActorData in pdata['actor']:
                for tmpActor in tmpActorData.keys():
                    if tmpActor != '':
                        if tmpActorData[tmpActor] == '':
                            tmpCredits.append('      <actor>%s</actor>\n' % escape(tmpActor))
                        else:
                            tmpCredits.append('      <actor role=%s>%s</actor>\n' % (quoteattr(tmpActorData[tmpActor]), escape(tmpActor)))
        # writer
        if 'writer' in pdata:
            for tmpWriter in pdata['writer']:
                if tmpWriter != '':
                    tmpCredits.append('      <writer>%s</writer>\n' % escape(tmpWriter))
        # adapter
        if 'adapter' in pdata:
            for tmpAdapter in pdata['adapter']:
                if tmpAdapter != '':
                    tmpCredits.append('      <adapter>%s</adapter>\n' % escape(tmpAdapter))
        # producer
        if 'producer' in pdata:
            for tmpProducer in pdata['producer']:
                if tmpProducer != '':
                    tmpCredits.append('      <producer>%s</producer>\n' % escape(tmpProducer))
        # composer
        if 'composer' in pdata:
            for tmpComposer in pdata['composer']:
                if tmpComposer != '':
                    tmpCredits.append('      <composer>%s</composer>\n' % escape(tmpComposer))
        # editor
        if 'editor' in pdata:
            for tmpEditor in pdata['editor']:
                if tmpEditor != '':
                    tmpCredits.append('      <editor>%s</editor>\n' % escape(tmpEditor))
        # presenter
        if 'presenter' in pdata:
            for tmpPresenter in pdata['presenter']:
                if tmpPresenter != '':
                    tmpCredits.append('      <presenter>%s</presenter>\n' % escape(tmpPresenter))
        # commentator
        if 'commentator' in pdata:
            for tmpCommentator in pdata['commentator']:
                if tmpCommentator != '':
                    tmpCredits.append('      <commentator>%s</commentator>\n' % escape(tmpCommentator))
        # guest
        if 'guest' in pdata:
            for tmpGuest in pdata['guest']:
                if tmpGuest != '':
                    tmpCredits.append('      <guest>%s</guest>\n' % escape(tmpGuest))

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
                        tmpData.append('    <category lang="%s">%s</category>\n' % (tmpLang, escape(tmpCategory)))
        # language
        if 'language' in pdata:
            for tmpLang in pdata['language']:
                for tmpLanguage in pdata['language'][tmpLang]:
                    if tmpLanguage != '':
                        tmpData.append('    <language lang="%s">%s</language>\n' % (tmpLang, escape(tmpLanguage)))
        # orig-language
        if 'orig-language' in pdata:
            for tmpLang in pdata['orig-language']:
                for tmpOrigLanguage in pdata['orig-language'][tmpLang]:
                    if tmpOrigLanguage != '':
                        tmpData.append('    <orig-language lang="%s">%s</orig-language>\n' % (tmpLang, escape(tmpOrigLanguage)))
        # length
        if 'length' in pdata:
            for tmpUnits in pdata['length']:
                for tmpValue in pdata['length'][tmpUnits]:
                    if tmpValue != '':
                        tmpData.append('    <length units="%s">%s</length>\n' % (tmpUnits, escape(tmpValue)))
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
                        tmpData.append('    <country lang="%s">%s</country>\n' % (tmpLang, escape(tmpCountry)))

        # episode numbers
        if 'episode-num' in pdata:
            for tmpSystem in pdata['episode-num']:
                if pdata['episode-num'][tmpSystem] != '':
                    tmpData.append('    <episode-num system="%s">%s</episode-num>\n' % (tmpSystem, pdata['episode-num'][tmpSystem]))
        # video quality
        if "HD" in DataStorage.channelList[pdata['channel']]:
            tmpData.append('    <video>\n')
            tmpData.append('      <quality>HDTV</quality>\n')
            tmpData.append('    </video>\n')
        # regExRating
        if 'rating' in pdata:
            for tmpSystem in pdata['rating']:
                if pdata['rating'][tmpSystem] != '':
                    tmpData.append('    <regExRating system=%s>\n' % quoteattr(tmpSystem))
                    tmpData.append('      <value>%s</value>\n' % escape(pdata['rating'][tmpSystem]))
                    tmpData.append('    </regExRating>\n')

        # end programme tag
        tmpData.append('  </programme>\n')
        DataStorage.xmlDataFile.write(string.joinfields(tmpData, ''))


def initializeProcess():
    # ignore sig int so the main process can be interrupted
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def processProgramPage(programId, filename):

    os.utime(filename, None)    # "touch" the file
    programPage = open(filename, 'r').read().decode('utf-8')
    programData = {programId: {}}

    # min data found?
    try:
        if not RegExStorage.regExChannelId3.search(programPage):
            raise Warning(programId)
        if not RegExStorage.regExDate.search(programPage):
            raise Warning(programId)
        if not RegExStorage.regExStart.search(programPage):
            raise Warning(programId)
        if not RegExStorage.regExTitle.search(programPage):
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
            programData[programId]['title'] = {'de': tempStr}
    # production year
    for foundStr in RegExStorage.regExProductionYear.findall(programPage):
        programData[programId]['date'] = CleanFromTags(foundStr)

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
            startdate = datetime.datetime(int(year), int(month), int(day),
                                          int(starthour), int(startminute))
            programData[programId]['start'] = startdate
        except:
            os.remove(filename)
            return {programId: {}}
    # stop date
    for foundStr in RegExStorage.regExStop.findall(programPage):
        try:
            (endhour, endminute) = foundStr.strip().split(':')
            enddate = datetime.datetime(int(year), int(month), int(day),
                                        int(endhour), int(endminute))
            if startdate > enddate:
                # program ends next day
                enddate = enddate + datetime.timedelta(days = 1)
            programData[programId]['finish'] = enddate
        except:
            pass  # optional data

    # original title
    for foundStr in RegExStorage.regExOrgTitle.findall(programPage):
        tmpTitle = CleanFromTags(foundStr)
        if tmpTitle not in programData[programId]['title']['de'] and \
            programData[programId]['title']['de'] not in tmpTitle:
            # org title in title not found - concat the titles
            tmpTitle = "%s - %s" % (tmpTitle, programData[programId]['title']['de'])
        programData[programId]['title']['de'] = tmpTitle

    # sub-title
    for foundStr in RegExStorage.regExSubtitle.findall(programPage):
        programData[programId]['sub-title'] = {'de': CleanFromTags(foundStr)}

    # description
    for foundStr in RegExStorage.regExDescription.findall(programPage):
        programData[programId]['desc'] = {'de': CleanFromTags(foundStr)}

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
        programData[programId]['category'] = {'de': []}
        for tmpCategory in CleanFromTags(foundStr).split(','):
            programData[programId]['category']['de'].append(tmpCategory.strip())
    # country
    for foundStr in RegExStorage.regExCountry.findall(programPage):
        programData[programId]['country'] = {'de': []}
        for tmpCountry in CleanFromTags(foundStr).split(','):
            programData[programId]['country']['de'].append(tmpCountry.strip())
    # episode
    episodeString = ''
    for foundStr in RegExStorage.regExEpisode.findall(programPage):
        episodeString = '%s %s' % (episodeString, foundStr.strip())
    episodeString = episodeString.strip()
    if episodeString != '':
        # episode in format xmltv_ns
        tempstr = ''
        for tmpSeason in RegExStorage.regExSeason.findall(episodeString):
            tempstr = str(int(tmpSeason) - 1)
        tempstr = '%s.' % tempstr
        for tmpEpisode in RegExStorage.regExEpisodeNum.findall(episodeString):
            tempstr = '%s%s' % (tempstr, int(tmpEpisode) - 1)
            for tmpEpisodeTotal in RegExStorage.regExEpisodeTotal.findall(episodeString):
                tempstr = '%s/%s' % (tempstr, tmpEpisodeTotal)
        if tempstr != ".":
            programData[programId]['episode-num'] = {'xmltv_ns': '%s.' % tempstr}
        # episode in format onscreen
        tempstr = ''
        for tmpSeason in RegExStorage.regExSeason.findall(episodeString):
            tempstr = "S%02d" % int(tmpSeason)
        for tmpEpisode in RegExStorage.regExEpisodeNum.findall(episodeString):
            tempstr = '%sE%02d' % (tempstr, int(tmpEpisode))
        if tempstr != "":
            programData[programId]['episode-num']['onscreen'] = tempstr
    # kid protection
    for foundStr in RegExStorage.regExRating.findall(programPage):
        programData[programId]['rating'] = {'FSK': CleanFromTags(foundStr)}

    return programData


class RegExStorage():
    # for the configuration workflow
    regExChannelId1 = re.compile(r'channel=([\w]+)">')
    regExChannelName = re.compile(r'">(.*)</a>')

    # for the grab workflow
    regExProgramId = re.compile(r'openDetailPopup\(\'[0-9]+\', \'([0-9]+)\', \'[\w]+\'\)')
    regExChannelId3 = re.compile(r'channel=([\w]+)\'')
    regExTitle = re.compile(r'<h2 class="DetailTitel">(.*?)</h2>')
    regExSubtitle = re.compile(r'<span class="DetailFolgeninfo">.*?<b>(.*?)</b></span>')
    regExEpisode = re.compile(r'<span class="DetailFolgeninfo">(.*?)</span>')
    regExProductionYear = re.compile(r'<span class="DetailJahr">([0-9]{4})</span>')
    regExDescription = re.compile(r'<span class="DetailText">(.*?)</span>')
    regExDate = re.compile(r'<span class="DetailblockDatum">[^<]+([0-9]{2}\.[0-9]{2}\.[0-9]{4})</span>')
    regExStart = re.compile(r'<span class="DetailblockZeit">Beginn: ([0-9]{2}:[0-9]{2}) Uhr</span>')
    regExStop = re.compile(r'<span class="DetailblockZeit">Ende: ([0-9]{2}:[0-9]{2}) Uhr</span>')
    regExActors = re.compile(r'<span class="DetailblockDarsteller">(.*?)</span>')
    regExProducer = re.compile(r'<span class="DetailblockProduktion">(.*?)</span>')
    regExDirector = re.compile(r'<span class="DetailblockRegie">(.*?)</span>')
    regExWriter = re.compile(r'<span class="DetailblockAutor">(.*?)</span>')
    regExRating = re.compile(r'<span class="DetailblockFSK">(.*?)</span>')
    regExCategory = re.compile(r'<span class="DetailblockKategorie">(.*?)</span>')
    regExCountry = re.compile(r'<span class="DetailblockLand">(.*?)</span>')
    regExSeason = re.compile(r'Staffel: ([0-9]+)')
    regExEpisodeNum = re.compile(r'Folge: ([0-9]+)')
    regExEpisodeTotal = re.compile(r'Folge: [0-9]+/([0-9]+)')
    regExOrgTitle = re.compile(r'<span class="DetailblockOrig">(.*?)</span>')
    regExPresenter = re.compile(r'<span class="DetailblockPresenter">(.*?)</span>')

    # treat special chars and words
    charSpecial = {3: [re.compile(r'\(Wiederholung\)'), r''],
                   4: [re.compile(r'^Reihe: .+'), r''],
                   95: [re.compile(r'c\<t'), r'c\'t'],
                   98: [re.compile(r'[\n\t ]+', re.DOTALL), r' '],
                   99: [re.compile(r',$'), r'']}


def CleanFromTags(inputStr):

    retStr = strip_html(inputStr)
    for key in sorted(RegExStorage.charSpecial.keys()):
        # clean all special characters
        retStr = RegExStorage.charSpecial[key][0].sub(
                        RegExStorage.charSpecial[key][1], retStr)

    return retStr.strip()


##
# Removes HTML markup from a text string.
#
# @param text The HTML source.
# @return The plain text.  If the HTML source contains non-ASCII
#     entities or character references, this is a Unicode string.
def strip_html(text):
    def fixup(m):
        text = m.group(0)
        if text[:1] == "<":
            return ""  # ignore tags
        if text[:2] == "&#":
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        elif text[:1] == "&":
            import htmlentitydefs
            entity = htmlentitydefs.entitydefs.get(text[1:-1])
            if entity:
                if entity[:2] == "&#":
                    try:
                        return unichr(int(entity[2:-1]))
                    except ValueError:
                        pass
                else:
                    return unicode(entity, "iso-8859-1")
        return text  # leave as is
    return re.sub("(?s)<[^>]*>|&#?\w+;", fixup, text)


# open the gui
if __name__ == "__main__":
    main()
