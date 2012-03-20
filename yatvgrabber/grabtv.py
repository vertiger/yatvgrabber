#! /usr/bin/env python

import os
import re
import sys
import urllib
#import logging
import argparse
import subprocess
from random import choice
from configobj import ConfigObj

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
    # get the program data
    # looping for the days
    for dayIndex in range(0, ArgumentParser.args.days+1):
        parseChannelData(grabConf['page'][0], dayIndex//7, dayIndex%7)
    
    # export the program data to xmltv file
    # debug output is here
    for program in DataStorage.programData.keys():
        print str(program)+': '+str(DataStorage.programData[program])
    
    # post grab cleanup
    postGrabCleanUp()

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
        parser.add_argument('--local', action="store_true", default=False,
                            help='process only the local stored cache files')
        #parser.add_argument('--verbose', type=int, default=0,
        #                    help='make it verbose')
        
        ## parse the arguments
        ArgumentParser.args = parser.parse_args()
        ArgumentParser.args.outputfile = os.path.realpath(ArgumentParser.args.outputfile)
        ArgumentParser.args.configfile = os.path.realpath(ArgumentParser.args.configfile)
        ArgumentParser.args.channelfile = os.path.realpath(ArgumentParser.args.channelfile)
        ArgumentParser.args.cachedir = os.path.realpath(ArgumentParser.args.cachedir)
        
        # verbose - print the arguments
        # somebody make an good advise for logging
        #logging.disable(logging.CRITICAL + 1 - (ArgumentParser.args.verbose * 10))

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

class DataStorage():
    channelList = dict()
    programData = dict()

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
            # use channelWeek to get the hole week for one channel
            #urllib.urlretrieve(base_url + "/tvtv/index.vm?weekId="+str(week)+"&dayId="+str(day)+"&channelWeek="+str(channelId), filename)
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
        os.utime(filename, None)    ## "touch" the file
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
    regExChannelId = re.compile(r's.prop16="[^\(]+\(([0-9]+)\)"')
    regExTitle = re.compile(r's.prop5="(.*)\[[0-9]+\]"')
    for channelId in DataStorage.channelList.keys():
        for dayLine in Parser.getDayPage(pagename, week, day, channelId).split('\n'):
            for programId in regExProgramId.findall(dayLine):
                # create the progam data container
                if not DataStorage.programData.has_key(programId):
                    DataStorage.programData[programId] = dict()
                programPage = Parser.getProgramPage(pagename, programId)
                
                # get the channel id from the page
                for foundChanId in regExChannelId.findall(programPage):
                    DataStorage.programData[programId]['channelid'] = foundChanId
                # get the title from the page
                for foundTitle in regExTitle.findall(programPage):
                    DataStorage.programData[programId]['title'] = foundTitle.strip()
                
                #cut down the content
                programPage = programPage.split(r'class="program-content"')[1]
                programPage = programPage.split(r'class="list_detail"')[0]
                
                # parse the page content
                for programLine in programPage.split('\n'):
                    pass

# open the gui
if __name__ == "__main__":
    main()
