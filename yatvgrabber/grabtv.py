#! /usr/bin/env python

import argparse
import sys
import os
import re
import urllib
from configobj import ConfigObj
from random import choice

def main():
    # argument parsing
    ArgumentParser.parseArguments()
    
    # override the urllib useragent - to get the custom user agent
    urllib._urlopener = AppOpener()

    # read / set the grabber configuration file
    grabConf = ConfigObj(ArgumentParser.args.configfile, raise_errors=True)
    if not os.path.isfile(ArgumentParser.args.configfile):
        # write the default configuration
        grabConf['page'] = ['http://www.tvtv.ch','http://www.tvtv.de','http://www.tvtv.at','http://www.tvtv.co.uk']
        grabConf.write()
    
    # execute the configure mode
    if ArgumentParser.args.configure:
        for page in reversed(grabConf['page']):
            DataStorage.channelList.update(parseChannelList(page))
        channelfile = open(ArgumentParser.args.channelfile, "w")
        for channelid in sorted(DataStorage.channelList.keys()):
            channelfile.write(str(channelid) +'#'+ DataStorage.channelList[channelid] +'\n')
        channelfile.close()
        sys.exit()
    
    # normal grabbing workflow
    # fill the channel list
    for line in open(ArgumentParser.args.channelfile, "r"):
        temp = line.split('#')
        DataStorage.channelList[temp[0]] = temp[1]
    # looping for the days
    for dayIndex in range(0, ArgumentParser.args.days+1):
        week = dayIndex//7
        day = dayIndex - week*7
        parseChannelData(grabConf['page'][0], week, day)

class ArgumentParser():
    @staticmethod
    def parseArguments():
        parser = argparse.ArgumentParser(description="YaTvGrabber, XMLTV grabbing script",
                                 epilog="Copyright (C) [2012] [keller.eric, lars.schmohl]",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('--days', type=int, choices=range(0, 21), default=20,
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
        parser.add_argument('--update-only', action="store_true", default=False,
                            help='only generate an update file (only adds new downloaded programs)')
        parser.add_argument('--local', action="store_true", default=False,
                            help='process only the local stored cache files')
        parser.add_argument('--disable-cleanup', action="store_true", default=False,
                            help='do no cleanup after parsing')
        parser.add_argument('--verbose', type=int, default=0,
                            help='make it verbose')
        
        ## parse the arguments
        ArgumentParser.args = parser.parse_args()
        
        # verbose - print the arguments
        if ArgumentParser.args.verbose > 0:
            print ArgumentParser.args

class DataStorage():
    channelList = dict()
    channelData = dict()

class AppOpener(urllib.FancyURLopener):
    user_agents = ['Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322)',
               'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0)',
               'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Sindup)',
               'Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
               'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.6) Gecko/2009011913 Firefox/3.0.6',
               'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
               'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)',
               'Mozilla/4.0 (compatible; MSIE 5.0; Windows 98; DigExt)',
               'Mozilla/4.0 (compatible; MSIE 6.0; Windows 98; Win 9x 4.90)',
               'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:11.0) Gecko/20100101 Firefox/11.0']
    version = choice(user_agents)

class Parser():
    @staticmethod
    def getOverviewPage(base_url):
        filename = ArgumentParser.args.cachedir +"/"+ (base_url.split('/')[-1]).strip() + ".html"
        if not ArgumentParser.args.local:
            # always retrieve the overview page in none local mode
            urllib.urlretrieve(base_url, filename)
        if  not os.path.isfile(filename):
            print sys.stderr, "unable to find file " +filename
            return str()
        return open(filename, 'r').read()
    
    @staticmethod
    def getAdditionalPage(base_url):
        filename = ArgumentParser.args.cachedir +"/"+ (base_url.split('/')[-1]).strip() + ".additional.html"
        if not ArgumentParser.args.local:
            # always retrieve the additional page in none local mode
            urllib.urlretrieve(base_url + "/tvtv/index.vm?mainTemplate=web%2FadditionalChannelsSelection.vm", filename)
        if  not os.path.isfile(filename):
            print sys.stderr, "unable to find file " +filename
            return str()
        return open(filename, 'r').read()
    
    @staticmethod
    def getDayPage(base_url, week, day, channelId):
        filename = ArgumentParser.args.cachedir +"/week="+str(week)+"-day="+str(day)+"-channel="+str(channelId)+".html"
        if not ArgumentParser.args.local:
            # always retrieve the day page in none local mode
            urllib.urlretrieve(base_url + "/tvtv/index.vm?weekId="+str(week)+"&dayId="+str(day)+"&chnl="+str(channelId), filename)
        if  not os.path.isfile(filename):
            print sys.stderr, "unable to find file " +filename
            return str()
        return open(filename, 'r').read()
    
    @staticmethod
    def getProgramPage(base_url, programId):
        # use the page from cache if available
        filename = ArgumentParser.args.cachedir +"/"+str(programId)+ ".html"
        # always cached the program page if available
        if not ArgumentParser.args.local and not os.path.isfile(filename):
            urllib.urlretrieve(base_url + "/tvtv/web/programdetails.vm?programmeId="+str(programId), filename)
        if  not os.path.isfile(filename):
            print sys.stderr, "unable to find file " +filename
            return str()
        return open(filename, 'r').read()

def parseChannelList(pagename):
    channellist = dict()
    # parse the main page
    regExChannelId = re.compile(r'weekChannel=([0-9]+)')
    regExChannelName = re.compile(r'class="">(.*)<')
    for line in Parser.getOverviewPage(pagename).split('\n'):
        for foundId in regExChannelId.findall(line):
            for foundName in regExChannelName.findall(line):
                channellist[foundId] = foundName + " (" + pagename + ")"
    # additional page page
    regExChannelId = re.compile(r'channelLogo=([0-9]+)"')
    for line in Parser.getAdditionalPage(pagename).split('\n'):
        for foundId in regExChannelId.findall(line):
            channellist[foundId] = (line.split('>')[-1]).strip() +" ("+ pagename +")"
    return channellist

def parseChannelData(pagename, week, day):
    regExProgramId = re.compile(r'programmeId=([0-9]+)')
    for channelId in DataStorage.channelList.keys():
        for dayLine in Parser.getDayPage(pagename, week, day, channelId).split('\n'):
            for programId in regExProgramId.findall(dayLine):
                for programLine in Parser.getProgramPage(pagename, programId):
                    pass

# open the gui
if __name__ == "__main__":
    main()
