#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import urllib
#import logging
import argparse
import datetime
import subprocess
from lxml import etree
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
        grabConf['page'] = ['http://www.tvtv.ch','http://www.tvtv.de','http://www.tvtv.at','http://www.tvtv.co.uk']
        try:
            grabConf.write()
        except:
            print "unable the write config file: " +ArgumentParser.args.configfile
            sys.exit(-1)
    
    # execute the configure mode
    if ArgumentParser.args.configure:
        for page in reversed(grabConf['page']):
            DataStorage.channelList.update(parseChannelList(page))
        try:
            channelfile = open(ArgumentParser.args.channelfile, "w")
            for channelid in sorted(DataStorage.channelList.keys()):
                channelfile.write(str(channelid) +'#'+ DataStorage.channelList[channelid] +'\n')
            channelfile.close()
        except:
            print "error the writing channel file: " +ArgumentParser.args.channelfile
            sys.exit(-1)
        print "channel file successfully written, file: " +ArgumentParser.args.channelfile
        sys.exit(0)
    
    # normal grabbing workflow
    # fill the channel list
    for line in open(ArgumentParser.args.channelfile, "r"):
        if (line.strip() == ""):
            continue
        try:
            (chanid, name) = line.split('#')
            DataStorage.channelList[chanid] = name.strip().decode("latin1")
        except:
            print "error reading channel configuration, line: " + line
    
    # get the program data
    parseChannelData(grabConf['page'][0], ArgumentParser.args.days)
    
    # export the program data to xmltv file
    WriteXmlTvFile(grabConf['page'][0])
    
    # post grab cleanup - do not cleanup after process locally
    if not ArgumentParser.args.local:
        postGrabCleanUp()

class DataStorage():
    channelList = dict()
    programData = dict()

class ArgumentParser():
    @staticmethod
    def parseArguments():
        parser = argparse.ArgumentParser(description="YaTvGrabber, XMLTV grabbing script",
                                 epilog="Copyright (C) [2012] [keller.eric, lars.schmohl]",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('--days', type=int, choices=range(1, 22), default=21,
                            help='days to grab')
        parser.add_argument('--outputfile', type=str, default="tvtv.xml",
                            help='output file with the xmltv data')
        parser.add_argument('--configure', action="store_true", default=False,
                            help='get all channels and create the channel file (normal grabbing is disabled)')
        parser.add_argument('--configfile', type=str, default="/etc/yatvgrabber/grab.conf",
                            help='configuration file for the grabber')
        parser.add_argument('--channelfile', type=str,
                            default="/etc/yatvgrabber/channel.grab", help='channel file for the grabber')
        parser.add_argument('--cachedir', type=str, default="/var/cache/yatvgrabber",
                            help='cache directory for the grabber')
        parser.add_argument('--local', action="store_true", default=False,
                            help='process only the local stored cache files')
        
        ## parse the arguments
        ArgumentParser.args = parser.parse_args()
        ArgumentParser.args.outputfile = os.path.realpath(ArgumentParser.args.outputfile)
        ArgumentParser.args.configfile = os.path.realpath(ArgumentParser.args.configfile)
        ArgumentParser.args.channelfile = os.path.realpath(ArgumentParser.args.channelfile)
        ArgumentParser.args.cachedir = os.path.realpath(ArgumentParser.args.cachedir)

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
        subprocess.call('find '+ ArgumentParser.args.cachedir +' -type f -empty -exec rm -f \'{}\' +', shell=True)

def postGrabCleanUp():
    # cleanup the grabbed files - just the empty files
    subprocess.call('find '+ ArgumentParser.args.cachedir +' -type f -empty -exec rm -f \'{}\' +', shell=True)
    # cleanup the grabbed files - files which are not used anymore
    subprocess.call('find '+ ArgumentParser.args.cachedir +' -type f -atime +1 -exec rm -f \'{}\' +', shell=True)

class AppOpener(urllib.FancyURLopener):
    user_agents = ['Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0)',
                   'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)',
                   'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:10.0.2) Gecko/20100101 Firefox/10.0.2',
                   'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:11.0) Gecko/20100101 Firefox/11.0']
    version = choice(user_agents)

class Parser():
    @staticmethod
    def getOverviewPage(base_url):
        filename = ArgumentParser.args.cachedir +"/"+ (base_url.split('/')[-1]).strip() + ".html"
        try:
            if not ArgumentParser.args.local:
                # always retrieve the overview page in none local mode
                urllib.urlretrieve(base_url, filename)
            if  not os.path.isfile(filename):
                raise Warning(filename)
        except:
            print "error retrieve / open file: " +filename
            return str()
        return open(filename, 'r').read().decode("utf-8")
    
    @staticmethod
    def getAdditionalPage(base_url):
        filename = ArgumentParser.args.cachedir +"/"+ (base_url.split('/')[-1]).strip() + ".additional.html"
        try:
            if not ArgumentParser.args.local:
                # always retrieve the additional page in none local mode
                urllib.urlretrieve(base_url + "/tvtv/index.vm?mainTemplate=web%2FadditionalChannelsSelection.vm", filename)
            if  not os.path.isfile(filename):
                raise Warning(filename)
        except:
            print "error retrieve / open file: " +filename
            return str()
        return open(filename, 'r').read().decode("utf-8")
    
    @staticmethod
    def getDayPage(base_url, week, day, channelId):
        print "grabbing " +base_url+ " week " +str(week)+ " day " +str(day)+ " channelid " +str(channelId)
        if (day > -1):
            # always retrieve the day page in none local mode
            filename = ArgumentParser.args.cachedir +"/week="+str(week)+"-day="+str(day)+"-channel="+str(channelId)+".html"
            grabUrl = base_url + "/tvtv/index.vm?weekId="+str(week)+"&dayId="+str(day)+"&chnl="+str(channelId)
        else:
            # use channelWeek to get the hole week for one channel
            filename = ArgumentParser.args.cachedir +"/week="+str(week)+"-channel="+str(channelId)+".html"
            grabUrl = base_url + "/tvtv/index.vm?weekId="+str(week)+"&dayId=0&weekChannel="+str(channelId)
        try:
            if not ArgumentParser.args.local:
                urllib.urlretrieve(grabUrl, filename)
            if  not os.path.isfile(filename):
                raise Warning(filename)
        except:
            print "error retrieve / open file: " +filename
            return str()
        return open(filename, 'r').read().decode("utf-8")
    
    @staticmethod
    def getProgramPage(base_url, programId):
        # use the page from cache if available
        filename = ArgumentParser.args.cachedir +"/"+str(programId)+ ".html"
        try:
            # always cached the program page if available
            if not ArgumentParser.args.local and not os.path.isfile(filename):
                urllib.urlretrieve(base_url + "/tvtv/web/programdetails.vm?programmeId="+str(programId), filename)
            if  not os.path.isfile(filename):
                raise Warning(filename)
        except:
            print "error retrieve / open file: " +filename
            return str()
        os.utime(filename, None)    ## "touch" the file
        return open(filename, 'r').read().decode("utf-8")

def parseChannelList(pagename):
    """parse the overview and additional pages for channel ids"""
    
    channellist = dict()
    
    # parse the main page
    for line in Parser.getOverviewPage(pagename).split('\n'):
        for foundId in RegExStorage.regExChannelId1.findall(line):
            for foundName in RegExStorage.regExChannelName.findall(line):
                channellist[foundId] = foundName + " (" + pagename + ")"
    
    # additional page page
    for line in Parser.getAdditionalPage(pagename).split('\n'):
        for foundId in RegExStorage.regExChannelId2.findall(line):
            channellist[foundId] = (line.split('>')[-1]).strip() +" ("+ pagename +")"
    
    return channellist

def parseChannelData(pagename, days):
    grabPlan = []
    weeksToGrab = days // 7
    leftoverDaysToGrab = days % 7
    lastWeek = 0
    if weeksToGrab > 0:
        for weekno in range(0, weeksToGrab):
            grabPlan.append([weekno, -1])
            lastWeek = weekno + 1
    if leftoverDaysToGrab > 0:
        for dayno in range(0, leftoverDaysToGrab):
            grabPlan.append([lastWeek, dayno])
    
    # multiprocessing
    pool = Pool(processes=None)
    
    for entry in grabPlan:
        for channelId in DataStorage.channelList.keys():
            channelPage = Parser.getDayPage(pagename, entry[0], entry[1], channelId)
            for programId in RegExStorage.regExProgramId.findall(channelPage):
                # get the program page
                programPage = Parser.getProgramPage(pagename, programId)
                
                pool.apply_async(processProgramPage, (programId, programPage,), callback=contentInjectCallback)
    
    pool.close()
    pool.join()

def contentInjectCallback(programEntry):
    for programid in programEntry.keys():
        if len(programEntry[programid]) == 0:
            os.remove(ArgumentParser.args.cachedir+"/"+str(programid)+".html")
        else:
            DataStorage.programData[programid] = programEntry[programid]

def processProgramPage(programId, programPage):
    programData = { programId: dict() }
    
    # min data found?
    try:
        if RegExStorage.regExChannelId3.search(programPage) == None:
            raise Warning(programId)
        if RegExStorage.regExDate.search(programPage) == None:
            raise Warning(programId)
        if RegExStorage.regExStart.search(programPage) == None:
            raise Warning(programId)
    except:
        print "error finding the channel id, date, start time of programid " +programId
        return programData
    
    # get the channel id from the page
    for foundStr in RegExStorage.regExChannelId3.findall(programPage):
        tempStr = FilterStringForTags(foundStr)
        if tempStr != "":
            programData[programId]['channelid'] = tempStr
    # get the title from the page
    for foundStr in RegExStorage.regExTitle.findall(programPage):
        tempStr = FilterStringForTags(foundStr)
        if tempStr != "":
            programData[programId]['title'] = tempStr
    # year
    for foundStr in RegExStorage.regExYear.findall(programPage):
        programData[programId]['year'] = FilterStringForTags(foundStr)
    
    #cut down the content
    try:
        programPage = programPage.split(r'class="program-content"')[1]
        programPage = programPage.split(r'class="list_detail"')[0]
    except:
        print "parsing exception of programid " +programId
        # no right content - delete the file for another run
        return { programId: dict() }
    
    # sub-title
    for foundStr in RegExStorage.regExSubtitle.findall(programPage):
        programData[programId]['sub-title'] = FilterStringForTags(foundStr)
    # episode
    episodeString = ""
    for foundStr in RegExStorage.regExEpisode.findall(programPage):
        episodeString = episodeString +' '+ foundStr.strip()
    episodeString = episodeString.strip()
    if episodeString != "":
        for tmpStr in RegExStorage.regExEpisodeNum.findall(episodeString):
            programData[programId]['episode'] = tmpStr
        for tmpStr in RegExStorage.regExEpisodeTotal.findall(episodeString):
            programData[programId]['episode-total'] = tmpStr
        for tmpStr in RegExStorage.regExSeason.findall(episodeString):
            programData[programId]['season'] = tmpStr
    
    # description
    for foundStr in RegExStorage.regExDescription.findall(programPage):
        programData[programId]['description'] = FilterStringForTags(foundStr)
    
    # date
    for foundStr in RegExStorage.regExDate.findall(programPage):
        programData[programId]['date'] = foundStr.strip()
    # start date
    for foundStr in RegExStorage.regExStart.findall(programPage):
        programData[programId]['start'] = foundStr.strip()
    # finish date
    for foundStr in RegExStorage.regExFinish.findall(programPage):
        programData[programId]['finish'] = foundStr.strip()
    
    # actors
    for foundStr in RegExStorage.regExActors.findall(programPage):
        programData[programId]['actors'] = FilterStringForTags(foundStr)
    # production
    for foundStr in RegExStorage.regExProducer.findall(programPage):
        programData[programId]['producer'] = FilterStringForTags(foundStr)
    # direction
    for foundStr in RegExStorage.regExDirector.findall(programPage):
        programData[programId]['director'] = FilterStringForTags(foundStr)
    # author
    for foundStr in RegExStorage.regExAuthor.findall(programPage):
        programData[programId]['author'] = FilterStringForTags(foundStr)
    # camera
    #for foundStr in RegExStorage.regExCamera.findall(programPage):
    #    DataStorage.programData[programId]['camera'] = FilterStringForTags(foundStr)
    # kid protection
    for foundStr in RegExStorage.regExKidProtection.findall(programPage):
        programData[programId]['kidprotection'] = FilterStringForTags(foundStr)
    # category
    for foundStr in RegExStorage.regExCategory.findall(programPage):
        programData[programId]['category'] = FilterStringForTags(foundStr)
    # country
    for foundStr in RegExStorage.regExCountry.findall(programPage):
        programData[programId]['country'] = FilterStringForTags(foundStr)
    # stage setting
    #for foundStr in RegExStorage.regExStageSetting.findall(programPage):
    #    DataStorage.programData[programId]['stagesetting'] = FilterStringForTags(foundStr)
    # music
    #for foundStr in RegExStorage.regExMusic.findall(programPage):
    #    DataStorage.programData[programId]['music'] = FilterStringForTags(foundStr)
    # original title
    for foundStr in RegExStorage.regExOrgTitle.findall(programPage):
        programData[programId]['orgtitle'] = FilterStringForTags(foundStr)
    # presenter
    for foundStr in RegExStorage.regExPresenter.findall(programPage):
        programData[programId]['presenter'] = FilterStringForTags(foundStr)
    # press
    #for foundStr in RegExStorage.regExPress.findall(programPage):
    #    DataStorage.programData[programId]['reporter'] = FilterStringForTags(foundStr)
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
    regExYear = re.compile(r'<td class="fb-b9 trailing">.*?([0-9]{4}).*?</td>', re.DOTALL)
    regExDescription = re.compile(r'<span class="fn-b10">(.*?)</span>', re.DOTALL)
    regExDate = re.compile(r'>[^<]+([0-9]{2}\.[0-9]{2}\.[0-9]{4})<')
    regExStart = re.compile(r'>Beginn: ([0-9]{2}:[0-9]{2}) Uhr<')
    regExFinish = re.compile(r'>Ende: ([0-9]{2}:[0-9]{2}) Uhr<')
    regExActors = re.compile(r'>Darsteller:</td>(.+?)</tr>', re.DOTALL)
    regExProducer = re.compile(r'>Produktion:</td>(.+?)</tr>', re.DOTALL)
    regExDirector = re.compile(r'>Regie:</td>(.+?)</tr>', re.DOTALL)
    regExAuthor = re.compile(r'>Autor:</td>(.+?)</tr>', re.DOTALL)
    #regExCamera = re.compile(r'>Kamera:</td>(.+?)</tr>', re.DOTALL)
    regExKidProtection = re.compile(r'>FSK:</td>.*: ([0-9]+).*</tr>', re.DOTALL)
    regExCategory = re.compile(r'>Kategorie:</td>(.+?)</tr>', re.DOTALL)
    regExCountry = re.compile(r'>Land:</td>(.+?)</tr>', re.DOTALL)
    regExSeason = re.compile(r'Staffel ([0-9]+)')
    regExEpisodeNum = re.compile(r'Folge ([0-9]+)')
    regExEpisodeTotal = re.compile(r'Folge [0-9]+/([0-9]+)')
    #regExStageSetting = re.compile(r'Bühnenbild:</td>(.+?)</tr>', re.DOTALL)
    #regExMusic = re.compile(r'>Musik:</td>(.+?)</tr>', re.DOTALL)
    regExOrgTitle = re.compile(r'>Orginaltitel:</td>(.+?)</tr>', re.DOTALL)
    regExPresenter = re.compile(r'sentiert von:</td>(.+?)</tr>', re.DOTALL)
    #regExPress = re.compile(r'>Presse:</td>(.+?)</tr>', re.DOTALL)
    
    # special chars
    charSpecial = {1:  [re.compile(r'<[^>]*>'), r' '],
                   2:  [re.compile(r'&nbsp;'), r' '],
                   3:  [re.compile(r'\(Wiederholung\)'), r''],
                   97: [re.compile(r'c\<t'), r'c\'t'],
                   98: [re.compile(r'[\n\t ]+', re.DOTALL), r' '],
                   99: [re.compile(r',$'), r'']}

def FilterStringForTags(inputStr):
    
    retStr = inputStr
    for key in sorted(RegExStorage.charSpecial.keys()):
        retStr = RegExStorage.charSpecial[key][0].sub(RegExStorage.charSpecial[key][1], retStr)   # clean all special characters
    
    return retStr.strip()

def WriteXmlTvFile(base_url):
    
    root = etree.Element("tv")
    root.set("source-info-url", base_url)
    root.set("source-info-name", "tvtv")
    root.set("generator-info-url", "http://code.google.com/p/yatvgrabber/")
    root.set("generator-info-name", "yatvgrabber")
    
    # list the channels
    for channelid in sorted(DataStorage.channelList.keys()):
        try:
            channel = etree.SubElement(root, "channel", id=channelid)
            name = etree.SubElement(channel, "display-name")
            name.text = unicode(DataStorage.channelList[channelid])
        except:
            print "error create xmltv tags for channelid " + channelid
    
    # list the program
    for programid in sorted(DataStorage.programData.keys()):
        try:
            pdata = DataStorage.programData[programid]
            # create the main tag
            program = etree.Element("programme")
            # set the start datetime - required
            try:
                (day, month, year) = pdata["date"].split('.')
                (starthour, startminute) = pdata["start"].split(':')
                startdate = datetime.datetime(int(year), int(month), int(day), int(starthour), int(startminute))
                program.set("start", startdate.strftime("%Y%m%d%H%M"))
            except:
                print "error setting start time of programid " +programid
                continue
            # set the end datetime
            if pdata.has_key("finish") and pdata["finish"] != "":
                try:
                    (endhour, endminute) = pdata["finish"].split(':')
                    enddate = datetime.datetime(int(year), int(month), int(day), int(endhour), int(endminute))
                    if startdate > enddate:
                        enddate = enddate + datetime.timedelta(days=1)  # program ends next day
                    program.set("stop", enddate.strftime("%Y%m%d%H%M"))
                except:
                    print "error setting the end datetime of programid " +programid
            # set the channelid - required
            program.set("channel", pdata["channelid"])
            
            # got all required fields, add element to root element
            root.append(program)
            
            # create the title subtag
            tempstr = str()
            if pdata.has_key("title") and pdata["title"] != "":
                tempstr = pdata["title"]
            if pdata.has_key("orgtitle") and pdata["orgtitle"] != "":
                if tempstr.find(pdata["orgtitle"]) == -1:
                    tempstr = pdata["orgtitle"] +" - "+ tempstr
            if tempstr != "":
                title = etree.SubElement(program, "title")
                title.text = unicode(tempstr)
            # create the sub-title
            if pdata.has_key("sub-title") and pdata["sub-title"] != "":
                subtitle = etree.SubElement(program, "sub-title")
                subtitle.text = unicode(pdata["sub-title"])
            
            # create the description subtag
            if pdata.has_key("description") and pdata["description"] != "":
                desc = etree.SubElement(program, "desc")
                desc.text = unicode(pdata["description"])
            
            # create the creditstag subtag
            creditstag = etree.SubElement(program, "credits")
            # director
            if pdata.has_key("director") and pdata["director"] != "":
                for foundStr in pdata["director"].split(','):
                    director = etree.SubElement(creditstag, "director")
                    director.text = unicode(foundStr.strip())
            # actor
            if pdata.has_key("actors") and pdata["actors"] != "":
                for foundStr in pdata["actors"].split(','):
                    actor = etree.SubElement(creditstag, "actor")
                    try:
                        (fActor, fRole) = foundStr.strip().split('(')
                        actor.text = unicode(fActor.strip())
                        actor.set("role", unicode(fRole.strip(') ')))
                    except:
                        actor.text = unicode(foundStr.strip())
            # writer
            if pdata.has_key("author") and pdata["author"] != "":
                for foundStr in pdata["author"].split(','):
                    writer = etree.SubElement(creditstag, "writer")
                    writer.text = unicode(foundStr.strip())
            # producer
            if pdata.has_key("producer") and pdata["producer"] != "":
                for foundStr in pdata["producer"].split(','):
                    producer = etree.SubElement(creditstag, "producer")
                    producer.text = unicode(foundStr.strip())
            # presenter
            if pdata.has_key("presenter") and pdata["presenter"] != "":
                for foundStr in pdata["presenter"].split(','):
                    presenter = etree.SubElement(creditstag, "presenter")
                    presenter.text = unicode(foundStr.strip())
            
            # date - production year
            if pdata.has_key("year") and pdata["year"] != "":
                productionDate = etree.SubElement(program, "date")
                productionDate.text = unicode(pdata["year"])
            
            # category
            if pdata.has_key("category") and pdata["category"] != "":
                for foundStr in pdata["category"].split(','):
                    category = etree.SubElement(program, "category", lang="de")
                    category.text = unicode(foundStr.strip())
            
            # country
            if pdata.has_key("country") and pdata["country"] != "":
                for foundStr in pdata["country"].split(','):
                    country = etree.SubElement(program, "country")
                    country.text = unicode(foundStr.strip())
            
            # episode
            tempstr = str()
            if pdata.has_key("season") and pdata["season"] != "":
                tempstr = str(int(pdata["season"]) - 1)
            tempstr += '.'
            if pdata.has_key("episode") and pdata["episode"] != "":
                tempstr += str(int(pdata["episode"]) - 1)
                if pdata.has_key("episode-total") and pdata["episode-total"] != "":
                    tempstr +='/' + pdata["episode-total"]
            if tempstr != ".":
                episodenum = etree.SubElement(program, "episode-num", system="xmltv_ns")
                episodenum.text = tempstr + '.'
            
            # kid protection
            if pdata.has_key("kidprotection") and pdata["kidprotection"] != "":
                kidprotection = etree.SubElement(program, "rating", system="FSK")
                kidprotsubtag = etree.SubElement(kidprotection, "value")
                kidprotsubtag.text = unicode(pdata["kidprotection"].strip())
            
        except:
            print "error create xmltv tags for programid " + programid
    
    # open the output file
    try:
        outfile = open(ArgumentParser.args.outputfile, 'w')
    except:
        print "error writing outputfile, file: " +ArgumentParser.args.outputfile
        sys.exit(-1)
    
    # write the header and content
    outfile.write(etree.tostring(root, encoding="UTF-8", xml_declaration=True, pretty_print=True))
    #                                   doctype="<!DOCTYPE tv SYSTEM \"xmltv.dtd\">"))
    #for program in DataStorage.programData.keys():
    #    outfile.write( str(program)+': '+str(DataStorage.programData[program])+'\n')
    outfile.close()
    print "xmltv file successfully written, file: " +ArgumentParser.args.outputfile

# open the gui
if __name__ == "__main__":
    main()
