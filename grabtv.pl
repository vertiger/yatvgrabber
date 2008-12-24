#!/usr/bin/perl -w
#
#Copyright (C) [2008] [keller.eric, lars.schmohl]
#
#This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 3 of the License, or (at your option) any later version.
#This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#You should have received a copy of the GNU General Public License along with this program; if not, see <http://www.gnu.org/licenses>.
#Additional permission under GNU GPL version 3 section 7
#
#------------------------------------------------------------------------------#
# TODO
#------------------------------------------------------------------------------#
# * use some user-agents more popular than wget :) DONE
# * parse the results and create the xmltv format DONE
# * use the -nc wget option like caching...  DONE
# * maybe use the -N option for the timestamp version...
#------------------------------------------------------------------------------#
# User agents
#------------------------------------------------------------------------------#
#

use strict;
use Getopt::Long;
require LWP::UserAgent;
use File::Path; 
use Time::Local;

#------------------------------------------------------------------------------#
# Globals
#------------------------------------------------------------------------------#
my $commonurl = "http://cablecom.tvtv.ch/tvtv";
my $ua;
#my $tmpdir = "/tmp/tvgrab";
my $tmpdir = "/home/$ENV{'USER'}/.tvgrab";
my $tmpcache = "$tmpdir/cache";
my $chanconffile = "$tmpdir/channel.grab";
my $swap_file = "$tmpdir/tempgrab";
my @useragents = ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_5; fr-fr) AppleWebKit/525.18 (KHTML, like Gecko) Version/3.1.2 Safari/525.20.1','Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.3) Gecko/2008092510 Ubuntu/8.04 (hardy) Firefox/3.0.3','Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)');
my $language = 'de'; # TODO support other languages
my $wget_timeout = "15";

# using Tor!!!
my $enableproxy = '';
my $http_proxy = "http://127.0.0.1:8118";
my $cache_age_day = "+1";

# lists
my @idlist = ();
my @mainpages = ();
my @channellist = ();
my @validchannels = ();
my @programmelist = ();

# statistics
my $grabstats = 0;
my $lineparsed = 0;
my $fileparsed = 0;

# error codes
my $success = 0;
my $retparamerr = 1;
my $retsyserr = 2;

# get option long
# use some of the standard option defined by xmltv
my $mute;
my $threads = 0;
my $configure;
my $configurefile;
my $output;
my $verbose;
my $help;

# per default it just gets the tv program from the actual day on the main chan.
# the number of days the grabber has to get
#
# As the cablecom site works with the followinf parameter in its address
#
#
my $nbr_of_days;
my $nbr_of_weeks = 0;
my $nbr_of_groups = 0;
my $dayoffset = 0; # default value = 0 when no offset is defined...
my $chanlist;
my $processlocal;
my $capabilities;
my $offset;


sub options()
{
    GetOptions("q|quiet"=> \$mute,
	       "d|days=i"=> \$nbr_of_days,
	       "w|week=i"=> \$nbr_of_weeks,
	       "g|channel-group=i"=> \$nbr_of_groups,
	       "l|channel-list"=> \$chanlist,
	       "p|process-locally"=> \$processlocal,
	       "t|threads=i"=> \$threads,
	       "ca|capabilities"=> \$capabilities,
	       "c|configure"=> \$configure,
	       "cf|configure-file"=> \$configurefile,
	       "v|verbose"=> \$verbose,
	       "o|output-file=s"=> \$output,
	       "off|offset=i"=> \$offset,
	       "e|enable-proxy"=> \$enableproxy,
	       "h|?|help"=> \$help) || die "try -h or --help for more details...";
    
    usage() if $help;
}

sub calculate_date($)
{
    my @results = ();
    my $ndays = shift;

    $ndays = $ndays > 21 ? 21 : $ndays;
    @results = (($ndays > 6) and (($ndays % 7) == 0)) ? (6, (($ndays/7)-1)) : ((($ndays % 7) - 1), int ($ndays/7));
    
    return \@results;
}

# this function checks the option given to the script
# with the given --days the check option calculate the number of weeks and the rest of the available days...
sub check_options()
{
    my $tmpdays = 0;
    my $refonresults = 0;
    my @results = ();

    # print capabilities
    if ($capabilities)
    {
	print "baseline\n";
	return $success;
    }
    # display the channel list
    if ($chanlist)
    {
	list_of_channels();
	exit $success;
    }

    # configure channel valid list
    if ($configure)
    {
	if (not -e "$chanconffile")
	{
	    list_of_channels();
	}
	else
	{
	    warn "Generation FAILED, the $chanconffile channel configuration file already exits (delete the file, and launch the script again, this will regenerate the channel listing $chanconffile)\n";
	}
	exit $success;
    }

    # return an error if the --days parameter is missing
    if (not defined $nbr_of_days and not defined $chanlist and not defined $configure)
    {
	print STDERR "one of the following parameters are mandatory: --days X --configure --channel-list\n";	
	exit $retparamerr;
    }
    elsif(not -e "$chanconffile")
    {
	warn "the $chanconffile channel configuration file is missing, please call the --configure option first.\n";
	exit $retsyserr;
    }
    elsif(defined $nbr_of_days)
    {
	# gen the channel list the user wants to grab
	generate_valid_channels();
	# set temp days
	$tmpdays = $nbr_of_days;
	# set the offset if the option is used otherwise the dayoffset is 0 initial value
	if (defined $offset)
	{
	    $dayoffset = $offset;
	    $nbr_of_days += $offset;
	}

	# convert the number of days to days and week
	if ($nbr_of_days > 0)
	{
	    $nbr_of_days = $nbr_of_days > 21 ? 21 : $nbr_of_days;
	    $refonresults = calculate_date($nbr_of_days);
	    @results = @{$refonresults};
	    $nbr_of_days = $results[0];
	    $nbr_of_weeks = $results[1];
	    print "days=$nbr_of_days, weeks=$nbr_of_weeks\n" if not $mute;	    
	}
	else
	{
	    print STDERR "the following parameter --days should have an int value > 0\n";
	    exit $retparamerr;
	}

	if (defined $offset)
	{

	    if ($dayoffset > 0)
	    {
		if (($dayoffset + $tmpdays) > 21)
		{
		    print STDERR "the $dayoffset offset and the $nbr_of_days days to grab are exceading the maximum grab value (21)... the script tries to reduce the offset\n";
		    $dayoffset = 21 - $tmpdays;
		}
		$refonresults = calculate_date($dayoffset);
		@results = @{$refonresults};
		$dayoffset = $results[0] + 1;
		$nbr_of_weeks = $results[1];
		print "OFFSET odays=$dayoffset weeks=$nbr_of_weeks gdays=$nbr_of_days\n";
		#exit 82;
	    }
	    else
	    {
		print STDERR "the following parameter --offset should have an int value > 0\n";
		exit $retparamerr;
	    }
	}
    }
}

sub generate_valid_channels()
{
    print "loading the $chanconffile configuration file...\n" if not $mute;
    @validchannels = read_from_file("$chanconffile");
    chop(@validchannels);
    print "authorised channel list: @validchannels\n" if not $mute;
}

sub list_of_channels()
{
    get_main_pages();
    get_channels();
    display_channels();
}

sub usage()
{
print "
this is the $0 usage

-- Official parameters:
o|output-file=s => define a output filename for the xml.
ca|capabilities => displays the grabber capabilities {baseline, manualconfig, apiconfig}
q|quiet => make it quiet, only display error messages on STDERR
d|days=x => grab tv data for x days counting from now! (x > 0)
off|offset=X => grab tv data setting the begin period to X days (X > 0)
c|configure => get the channel list, and save it to the $chanconffile file. The user can remove as many channels he does not require. When calling the script, only the channel in this file will be grabbed.

-- NoN Official parameters
g|channel-group=i => gets the program for number of groups i E [0..16]
l|channel-list => gives a list of every tv channel available
p|process-locally => only create the xmltv data without grabing any file (this work on the local files downloaded during a previous session)
h|?|help => display this usage
------------------------------------------------------------------------
NOT YET IMPLEMENTED
------------------------------------------------------------------------
t|threads=i => define the number of threads are take to generate the xml
v|verbose => make it verbose

Examples:
# first you have to grab a channel list
$0 --configure
# you can print out a listing of the channels 
$0 --channel-list
# this will grab every tv program for every channels (-g option set to 16) and stores the results in test.xml
$0 -d 6 -g 16 -o test.xml
# this will grab the tv data for every channel for 3 weeks (-w 2) an stores the results in test.xml
$0 -d 6 -w 2 -g 16 -o test.xml

AUTHORS:
* keller_e 
* schmoh_l
";
exit 1;
}

sub init_ua_file
{
    $ua = LWP::UserAgent->new(); # the user agent does http request
    $ua->timeout(60);
    $ua->env_proxy;
}


#dayid 0..6
#weekid 0..2
#groupid 0..16 # attention 11 adult content --babslouloute
# the maximum days in advance to grab is 21 :)
# so if the days are < 7 0..6 and the week is = 0
# if  8 < days < 14 the day is mod 7 and the week = 1
# if 15 < days <= 21 day is mod 7 and week is 2
sub combine_dates()
{
    my $dayid = 0;
    my $weekid = 0;
    my $groupid = 0;
    my $url = 'none';
    

    if ($nbr_of_weeks == 1)
    {	
	print "in the week = 1 case\n";
	for $groupid (0..$nbr_of_groups)
	{
	    if (not defined $offset)
	    {
		$weekid = 0;
		# the first week do all the 6 days
		for $dayid (0..6)
		{
		    $url = "$commonurl/index.vm?dayId=${dayid}&weekId=${weekid}&groupid=${groupid}&lang=de&epgView=list";
		    print "URL:$url\n";
		    get_tv_program($url, "group${groupid}-week${weekid}-day${dayid}");
		}
	    }
	    $weekid = 1;
	    # the second week = 1 just get the rest of the days
	    for $dayid ($dayoffset..$nbr_of_days)
	    {
		$url = "$commonurl/index.vm?dayId=${dayid}&weekId=${weekid}&groupid=${groupid}&lang=de&epgView=list";
		print "URL:$url\n";
		get_tv_program($url, "group${groupid}-week${weekid}-day${dayid}");
	    }
	}
    }
    elsif ($nbr_of_weeks == 2)
    {
	print "in the week = 2 case\n";
	for $groupid (0..$nbr_of_groups)
	{
	    if (not defined $offset)
	    {
		for $weekid (0..1)
		{
		    # the first week do all the 6 days
		    for $dayid (0..6)
		    {
			$url = "$commonurl/index.vm?dayId=${dayid}&weekId=${weekid}&groupid=${groupid}&lang=de&epgView=list";
			print "URL:$url\n";
			get_tv_program($url, "group${groupid}-week${weekid}-day${dayid}");
		    }
		}
	    }
	    $weekid = 2;
	    # the second week = 1 just get the rest of the days
	    for $dayid ($dayoffset..$nbr_of_days)
	    {
		$url = "$commonurl/index.vm?dayId=${dayid}&weekId=${weekid}&groupid=${groupid}&lang=de&epgView=list";
		print "URL:$url\n";
		get_tv_program($url, "group${groupid}-week${weekid}-day${dayid}");
	    }
	}
    }
    elsif ($nbr_of_weeks == 0)
    {
	print "in the week = 0 case\n";
	for $groupid (0..$nbr_of_groups)
	{
	    $weekid = 0;
	    for $dayid ($dayoffset..$nbr_of_days)
	    {
		$url = "$commonurl/index.vm?dayId=${dayid}&weekId=${weekid}&groupid=${groupid}&lang=de&epgView=list";
		print "URL:$url\n";
		get_tv_program($url, "group${groupid}-week${weekid}-day${dayid}");
	    }
	}
    }
    else
    {
	print STDERR "something did horribly go wront with the given parameter days...\n";
	exit $retparamerr;
    }
}

# TODO use wget for getting the main pages...
# get_tv_program($url)
# the url is generated by the combine_dates() function
# this function will grab in the defined tmpdir directory all the casts
# using the system call to wget --> much quicker than perl get!
sub get_tv_program($$)
{
    my $url = shift;
    my $destinationfile = shift;
    my $response;
    my @greppedurl = ();
    my @lines = ();
    my $id = 0;

    print "getting $url save it to $destinationfile\n" if not $mute;

    #$response = $ua->get($url);
    #if ($response->is_success) 
    if($success == use_wget($url, $destinationfile))
    {
	#print MYOUTFILE $response->content;  # or whatever
	#@lines = split /\s+/, $response->content;
	@lines = read_from_file("$tmpcache/${destinationfile}.htm");
	#print "LINES: @lines\n";
	@greppedurl = grep(/programdetails.vm?/, @lines);
	
	foreach (@greppedurl)
	{
	    if ($_ =~ /.*programmeId=(\d+)&lang.*/)
	    {
		$id = $1;
		if (defined $id)
		{
		    $url = "$commonurl/web/programdetails.vm?programmeId=${id}&lang=de&epgView=list&groupid=0";
		    print "now getting --> $url\n" if not $mute;
		    if (-e "$tmpcache/$id.htm")
		    {
			utime( time(), time(), "$tmpcache/$id.htm");
			print "$id.htm already exists... Skip Grabbing!\n" if not $mute;
		    }
		    else
		    {
			use_wget($url, $id);
		    }
		    @idlist = (@idlist, $id);
		}
		else
		{
		    warn("some problems with $_ line\nABORT the local operation...\n");
		}
	    }
	    $grabstats++;
	    #last if $grabstats > 5; # DEBUG
	}

	#print "URLS: @greppedurl\n";
    }
    else 
    {
	warn $response->status_line;
    }
}

#use_wget($url, $id)
sub use_wget($$)
{
    my $url = shift;
    my $id = shift;
    my $wgetquiet = '';
    my $wgetusragent = "--user-agent=\"$useragents[2]\"";
    my $wgetoptions = "-nc --random-wait --no-cache --timeout=$wget_timeout";
    my $wgetcommand = '';
    my $proxycommand = "set http_proxy=\"$http_proxy\"";
    
    $wgetquiet = $mute ? '--quiet':'';
    $wgetcommand = "wget \"$url\" $wgetoptions $wgetusragent -O $tmpcache/$id.htm $wgetquiet";
    # use the Tor proxy 
    $wgetcommand = "$proxycommand; $wgetcommand" if $enableproxy;
    print "wgetcommand: $wgetcommand\n" if not $mute;
    
    if (0 != system($wgetcommand))
    {
	warn("some problem occured when calling system\n");
	#return $retsyserr;
    }
    else
    {
	chmod( 0666, "$tmpcache/$id.htm");
    }
    return $success;
}

# read_from_file($filename)
sub read_from_file($)
{
    my $filename = shift;
    my @lines = ();

    open(FILE, "$filename");
    @lines = <FILE>;

    return @lines;
}

# parse_lines($refonlines)
# depends on the language 
sub parse_lines($)
{
    my $linesref = shift;
    my @lines = @{$linesref};
    my %programme = ();

    my $extractchan = 0;
    my $category = 0;
    my $land = 0;
    my $producer = 0;
    my $productor = 0;
    my $presentator = 0;
    my $originaltitle = 0;
    my $camera = 0;
    my $music = 0;
    my $script = 0;
    my $production = 0;
    my $filmeditor = 0;
    my $actors = 0;
    my $author = 0;
    my $kidprotection = 0;
    my $musicleader = 0;
    my $i = 0;

    #print "LINES: @lines\n";
    foreach (@lines)
    {
	$i++;
	# extract the channel name
	if ($_ =~ /.*fb-b10.*>(.*)<.*/ and not $1 =~ m/\./ )
	{
	    print "CHAN: $1\n" if (defined $1 and not $mute);
	    $programme{'channel'} = "$1" if defined $1;
	    $extractchan = 0;
	    next;
	}
	# extarct the channel id
	# hbx.pn="SF ZWEI (900)";//PAGE NAME(S)
	if ($_ =~ /hbx.pn=".*\((.*)\)".*/)
	{
	    print "CHANID: $1\n" if (defined $1 and not $mute);
	    $programme{'channelid'} = "$1" if defined $1;
	}

	# extract cast type
	if ($_ =~ /Film/)
	{
	    print "cast Type: Film\n" if not $mute;
	    $programme{'programmetype'} = "Film";
	    next;
	}
	if ($_ =~ /Serie/)
	{
	    print "cast Type: Serie\n" if not $mute;
	    $programme{'programmetype'} = "Serie";
	    next;
	}
	# extract title
	if ($_ =~ /fb-b15">(.*)<\/span.*/)
	{
	    print "TITLE: $1\n" if (defined $1 and not $mute);
	    $programme{'title'} = "$1" if defined $1;
	    next;
	}
	# extract episode
	if ($_ =~ /fn-b9">(.*)<\/span.*/)
	{
	    print "FOLGE: $1\n" if (defined $1 and not $mute);
	    $programme{'episode'} = "$1" if defined $1;
	    next;
	}
	# extraction of the description
	if ($_ =~ /fn-b10">(.*)<\/span.*/)
	{
	    print "DESC: $1\n" if (defined $1 and not $mute);
	    $programme{'desc'} = "$1" if defined $1;
	    # FIXME: remove <br/> tag in description...
	    #$programme{'desc'} =~ s/\<br\/\>//g;
	    next;
	}
	# extraction of the date
	if ($_ =~ /fn-w8".*>(.*),\s+(\d+.\d+.\d+)<\/t.*/)
	{
	    print "Date: $1, $2\n" if (defined $1 and defined $2 and not $mute);
	    $programme{'dayoftheweek'} = "$1" if defined $1;
	    $programme{'date'} = "$2" if defined $2;
	    next;
	}
	# extraction of the begin end time
	if ($_ =~ /fn-b8".*>Beginn:\s+(\d+:\d+).*<\/t.*/)
	{
	    print "\tTime Start: $1\n" if (defined $1 and not $mute);
	    $programme{'start'} = "$1" if defined $1;
	    next;
	}
	if ($_ =~ /fn-b8".*>Ende:\s+(\d+:\d+).*<\/t.*/)
	{
	    print "\tTime End: $1\n" if (defined $1 and not $mute);
	    $programme{'stop'} = "$1" if defined $1;
	    next;
	}
	if ($_ =~ /fn-b8".*>Länge:\s+(\d+).*<\/t.*/)
	{
	    print "\tcast Time: $1 min.\n" if (defined $1 and not $mute);
	    $programme{'timeduration'} = "$1" if defined $1;
	    next;
	}
	# extract actors
	if ($_ =~ /fn-w8".*>Darsteller:.*/)
	{
	    $actors = 1;
	    next;
	}
	if ($actors == 1)
	{
	    if ($_ =~ /.*fn-b8">(.*)<\/span.*/)
	    {
		print "Staring: $1\n" if (defined $1 and not $mute);
		$programme{'actors'} = "$1" if defined $1;
	    }
	    $actors = 0;
	    next;
	}
	#extract Producers
        if ($_ =~ /fn-w8".*>Regie:.*/)
        {
            $producer = 1;
            next;
        }
        if ($producer == 1)
        {
            if ($_ =~ /.*fn-b8">(.*)<\/span.*/)
            {
		print "Regie: $1\n" if (defined $1 and not $mute);
	 
		$programme{'director'} = "$1" if defined $1;
		$programme{'director'} =~ s/\<show_pers\.php3\?cle=\d+\>//g;
		$programme{'director'} =~ s/\<\/show_pers\.php3\?cle=\d+\>//g;
            }
            $producer = 0;
	    next;
        }
	# Authors
	if ($_ =~ /fn-w8".*>Autor:.*/)
        {
            $author = 1;
            next;
        }
        if ($author == 1)
        {
            if ($_ =~ /.*fn-b8">(.*)<\/span.*/)
            {
		print "Authors: $1\n" if (defined $1 and not $mute);
		$programme{'writer'} .= "$1" if defined $1;
            }
            $author = 0;
	    next;
        }
	# category
	if ($_ =~ /fn-w8".*>Kategorie:.*/)
        {
            $category = 1;
            next;
        }
        if ($category == 1)
        {
            if ($_ =~ /.*fn-b8">(.*)<\/span.*/)
            {
                print "Category: $1\n" if (defined $1 and not $mute);
		$programme{'category'} = "$1" if defined $1;
            }
             $category = 0;
	    next;
        }
	# filming location
	if ($_ =~ /fn-w8".*>Land:.*/)
        {
            $land = 1;
            next;
        }
        if ($land == 1)
        {
            if ($_ =~ /.*fn-b8">(.*)<.*/)
            {
                print "Land: $1\n" if (defined $1 and not $mute);
		$programme{'country'} = "$1" if defined $1;
            }
	    $land = 0;
	    next;
        }
	# Kid Protection
	if ($_ =~ /fn-w8".*>FSK:.*/)
        {
            $kidprotection = 1;
            next;
        }
        if ($kidprotection == 1)
        {
            if ($_ =~ /.*fn-b8">(.*)<\/span.*/)
            {
                print "Not Allowed for Kid under: $1\n" if (defined $1 and not $mute);
		$programme{'rating'} = "$1" if defined $1;
            }
	    $kidprotection = 0;
	    next;
        }

	# Film Editor
	if ($_ =~ /fn-w8".*>Film Editor:.*/)
        {
            $filmeditor = 1;
            next;
        }
        if ($filmeditor == 1)
        {
            if ($_ =~ /.*fn-b8">(.*)<\/span.*/)
            {
                print "Film Editor: $1\n" if (defined $1 and not $mute);
		$programme{'filmeditor'} = "$1" if defined $1;
            }
	    $filmeditor = 0;
	    next;
        }
	# Produktion
	if ($_ =~ /fn-w8".*>Produktion:.*/)
        {
            $production = 1;
            next;
        }
        if ($production == 1)
        {
            if ($_ =~ /.*fn-b8">(.*)<\/span.*/)
            {
                print "Studio Production: $1\n" if (defined $1 and not $mute);
		$programme{'studio'} = "$1" if defined $1;
            }
	    $production = 0;
	    next;
        }
	# Produzent
	if ($_ =~ /fn-w8".*>Produzent:.*/)
        {
            $productor = 1;
            next;
        }
        if ($productor == 1)
        {
            if ($_ =~ /.*fn-b8">(.*)<\/span.*/)
            {
                print "Producer: $1\n" if (defined $1 and not $mute);
		$programme{'producer'} = "$1" if defined $1;
            }
	    $productor = 0;
	    next;
        }
	# Drehbuch
	if ($_ =~ /fn-w8".*>Drehbuch:.*/)
        {
            $script = 1;
            next;
        }
        if ($script == 1)
        {
            if ($_ =~ /.*fn-b8">(.*)<\/span.*/)
            {
                print "script: $1\n" if (defined $1 and not $mute);
		$programme{'writer'} .= "$1" if defined $1;
            }
	    $script = 0;
	    next;
        }
	# Musik
	if ($_ =~ /fn-w8".*>Musik:.*/)
        {
            $music = 1;
            next;
        }
        if ($music == 1)
        {
            if ($_ =~ /.*fn-b8">(.*)<\/span.*/)
            {
                print "Music: $1\n" if (defined $1 and not $mute);
		$programme{'musicauthor'} = "$1" if defined $1;
            }
	    $music = 0;
	    next;
        }
	# Kamera
	if ($_ =~ /fn-w8".*>Kamera:.*/)
        {
            $camera = 1;
            next;
        }
        if ($camera == 1)
        {
            if ($_ =~ /.*fn-b8">(.*)<\/span.*/)
            {
                print "Camera: $1\n" if (defined $1 and not $mute);
		$programme{'camera'} = "$1" if defined $1;
            }
	    $camera = 0;
	    next;
        }
	# Orginaltitel
	if ($_ =~ /fn-w8".*>Orginaltitel:.*/)
        {
            $originaltitle = 1;
            next;
        }
        if ($originaltitle == 1)
        {
            if ($_ =~ /.*fn-b8">(.*)<\/span.*/)
            {
                print "Original Title: $1\n" if (defined $1 and not $mute);
		$programme{'sub-title'} = "$1" if defined $1;
            }
	    $originaltitle = 0;
	    next;
        }
	# Präsentiert von
	if ($_ =~ /fn-w8".*>Präsentiert von:.*/)
        {
            $presentator = 1;
            next;
        }
        if ($presentator == 1)
        {
            if ($_ =~ /.*fn-b8">(.*)<\/span.*/)
            {
                print "presented by: $1\n" if (defined $1 and not $mute);
		$programme{'presenter'} = "$1" if defined $1;
            }
	    $presentator = 0;
	    next;
        }
	# Musikalische Leitung
	if ($_ =~ /fn-w8".*>Musikalische Leitung:.*/)
        {
            $musicleader = 1;
            next;
        }
        if ($musicleader == 1)
        {
            if ($_ =~ /.*fn-b8">(.*)<\/span.*/)
            {
                print "Music chef: $1\n" if (defined $1 and not $mute);
		$programme{'musicchef'} = "$1" if defined $1;
            }
	    $musicleader = 0;
	    next;
        }

	# audio, video types...
	# depends on the web language
	# this first implementation just use german :)
	if ($_ =~ /Stereo/)
	{
	    print "AUDIO=Stereo\n" if not $mute;
	    $programme{'audio'} = "stereo";
	    next;
	}
	if ($_ =~ /16:9 video format/)
	{
	    print "VIDEO=16:9 video format\n" if not $mute;
	    $programme{'aspect'} = "16:9";
	    next;
	}
	if ($_ =~ /Mehrsprachig/)
	{
	    print "Multilangue: Mehrsprachig\n" if not $mute;
	    $programme{'languages'} = "multi";
	    next;
	}
	if ($_ =~ /High Definition Video/)
	{
	    print "HDTV: High Definition Video\n" if not $mute;
	    $programme{'quality'} = "HDTV";
	    next;
	}
	if ($_ =~ /Surround Sound/)
	{
	    print "Audio: Surround Sound\n" if not $mute;
	    $programme{'audiotype'} = "surround";
	    next;
	}
    }
    $lineparsed += $i;
    @programmelist = (@programmelist, \%programme);
}

sub extract_info()
{
    my @lines = ();
    
    print "ID LIST: @idlist\n" if $verbose and not $mute;
    foreach (@idlist)
    {
	@lines = read_from_file("$tmpcache/$_.htm");
	#print "LINES: @lines\n";
	parse_lines(\@lines);
	$fileparsed += 1;
    }
}

sub local_parse_info()
{
    my @infolist = ();
    my $i;
    my @lines = ();

    @infolist = glob("$tmpcache/[0-9]*.htm");
    
    #print "INFO IDS: @infolist\n";
    foreach $i (@infolist)
    {
	@lines = read_from_file($i);
	#print "LINES: @lines\n";
	print "---> parsing file $i------------------------------------\n" if not $mute;
	parse_lines(\@lines);
	$fileparsed += 1;
    }
}

# get a list of the available channels...
sub get_main_pages()
{
    my $groupid;
    my $url;

    foreach $groupid (0..16)
    {
	$url = "$commonurl/index.vm?dayId=0&weekId=0&groupid=${groupid}&lang=de&epgView=list";
	if (not -e "$tmpcache/changroup$groupid.htm")
	{
	    use_wget($url, "changroup$groupid");
	}
	else
	{
	    utime( time(), time(),  "$tmpcache/changroup$groupid.htm");
	    print "$tmpcache/changroup$groupid.htm already exists...\n" if not $mute;
	}
	@mainpages = (@mainpages, "$tmpcache/changroup$groupid.htm");
    } 
}

sub get_channels()
{
    my @lines = ();

    foreach (@mainpages)
    {
	print "opening $_\n" if not $mute;
	@lines = read_from_file("$_");
	parse_channel(\@lines);
    }
}
# parse_channel($refonlines)
sub parse_channel($)
{
    my $refonlines = shift;
    my @lines = @{$refonlines};
    my $chanlogolink = '';
    my %chaninfo = ();

    foreach (@lines)
    {
	#<td><img src="http://cablecom.tvtv.ch:80/tvtv/resource?channelLogo=118" border=0 height="21" vspace="1" width="40" alt="3sat"></td>
	#<div class="fb-w10" style="padding-left:5px;">Das Erste</div>
        #if ($_ =~ /fb-w10\" style=.*>(.*)<\/div>/)
	if ($_ =~ /<td><img src="(.*channelLogo.*)"\s+border.*alt="(.*)".*/)
	{

	    $chanlogolink = $1 if defined $1;
	    $chaninfo{'link'} = $chanlogolink;
	    $chaninfo{'name'} = $2 if defined $2;
	    $chanlogolink =~ m/.*channelLogo=(\d+)/;
	    $chaninfo{'id'} = $1 if defined $1;
	    # this{%chaninfo} will create a unique pointer reference on the %chaninfo hash.
	    # it is like pass the reference by copy...
	    @channellist = (@channellist, {%chaninfo}); 
	    if ($verbose and not $mute)
	    {
		print "channel Logolink= $chaninfo{'id'}\n";
		print "channel Logolink= $chaninfo{'link'}\n";
		print "channel Logolink= $chaninfo{'name'}\n";
	    }
	}
    }
}

# this function display all the channels available on the given website...
sub display_channels()
{
    my $nbrchan = @channellist;
    my %chaninfo = ();
    my $channelid = '';
    my $channelname = '';
    my $chanlogolink = '';

    print "/------------------------------------------\\\n";
    print "| Channel List                             |\n";
    print "\------------------------------------------/\n";
    print "from: $commonurl...\nto: $chanconffile\n";
    
    if ($configure)
    {
	open (WF, ">$chanconffile") or warn "could not create the $chanconffile file $!";
    }
    
    foreach (@channellist)
    {
 
	%chaninfo = %{$_};
	$channelid = $chaninfo{'id'};
	$channelname = $chaninfo{'name'};
	$chanlogolink = $chaninfo{'link'};
	
	$channelname =~ s/&/&amp;/g;
	
	print "channel id=${channelid}\t\t\t$channelname\n";
	print WF "$channelid#$channelname\n" if ($configure);	
    }

    print "/------------------------------------------\\\n";
    print "| Found $nbrchan Channels\n";
    print "\------------------------------------------/\n";
    print "from: $commonurl...\nto: $chanconffile\n";
    close(WF) if $configure;
}
# xml_print($aline)
# automatic \n at the end of the line
sub xml_print($)
{
    my $line = shift;

    # removing unwanted html tags...
    $line =~ s/\<br\/?\>//g;
    $line =~ s/&/&amp;/g;
    # temporary... because cablecom.tvtv.ch has a problem with c't magazin
    $line =~ s/c\<t/c't/g;

    if ($output)
    {
	print XMLFILE "$line\n"; 
    }
    else
    {
	print "$line\n"; 
    }
}

sub xml_init()
{
    # write xml in a file...
    if($output)
    {
	open(XMLFILE, ">$output");
    }
    xml_print("<tv generator-info-name=\"yagraber\" source-info-url=\"$commonurl\">");
}

sub xml_close()
{
    xml_print("</tv>");
    if ($output)
    {
	close(XMLFILE);
    }
    
}

sub xml_print_channel($)
{
    my $refonchaninfo = shift;
    my %chaninfo = %{$refonchaninfo};
    #my %chaninfo = shift(@_);
    my $channelid = $chaninfo{'id'};
    my $channelname = $chaninfo{'name'};
    my $chanlogolink = $chaninfo{'link'};
    my @grepped = ();

    $channelname =~ s/&/&amp;/g;
    @grepped = grep(/${channelname}/, @validchannels);
    if (defined $grepped[0])
    {
	xml_print("\t\<channel id=\"channel.${channelid}\"\>");
	xml_print("\t\t\<display-name lang=\"$language\"\>$channelname\<\/display-name\>");
	xml_print("\t\t\<icon src=\"${chanlogolink}\"\/\>");
	xml_print("\t\<\/channel\>");
    }
}

# create bonnus entries
# this function checks if there are more information contained in the programme hash table, like 
# actors, description, subtitle, original title, producer, writer, audio format video format, ...
#
# sub xml_print_additional_materials($aProgrammeReference)
sub xml_print_additional_materials($)
{
    my $refonprogramme = shift;
    my %programme = %{$refonprogramme};
    # locals
    my $description = '';
    my @actors = ();
    my $credits = 0;
    my $subtitle = '';

    # non mandatory parameters... Bonus if it's existing
    # sub title, original title
    if(defined $programme{'sub-title'})
    {
	$subtitle = $programme{'sub-title'};
	$subtitle =~ s/&/&amp;/g;
	xml_print("\t\<sub-title lang=\"${language}\"\>${subtitle}\<\/sub-title\>");
    }

    # description
    if (defined $programme{'desc'})
    {
	$description = $programme{'desc'};
	$description =~ s/&/&amp;/g;
	xml_print("\t\t\<desc lang=\"${language}\"\>\n${description}\n\t\t\<\/desc\>");
    }
    # credits authors, actors, regie, producer, ...
    if (defined $programme{'actors'} or 
	defined $programme{'director'} or 
	defined $programme{'writer'} or
	defined $programme{'producer'} or
	defined $programme{'presenter'} or
	defined $programme{'commentator'} or
	defined $programme{'guest'}
	)
    {
	# any of the credits contents will write the credit xml tag
	xml_print("\t\t\<credits\>");

	if (defined $programme{'director'})
	{
	    xml_print("\t\t\t\<director\>$programme{'director'}\<\/director\>");
	}

	# add the actors
	if (defined $programme{'actors'})
	{
	    @actors = split(', ', $programme{'actors'});
	    foreach (@actors)
	    {
		xml_print("\t\t\t\<actor\>$_\<\/actor\>");
	    }
	}

	if (defined $programme{'writer'})
	{
	    xml_print("\t\t\t\<writer\>$programme{'writer'}\<\/writer\>");
	}
	if (defined $programme{'adapter'})
	{
	    xml_print("\t\t\t\<adapter\>$programme{'adapter'}\<\/adapter\>");
	}
	if (defined $programme{'producer'})
	{
	    xml_print("\t\t\t\<producer\>$programme{'producer'}\<\/producer\>");
	}
	if (defined $programme{'presenter'})
	{
	    xml_print("\t\t\t\<presenter\>$programme{'presenter'}\<\/presenter\>");
	}
	if (defined $programme{'commentator'})
	{
	    xml_print("\t\t\t\<commentator\>$programme{'commentator'}\<\/commentator\>");
	}
	if (defined $programme{'guest'})
	{
	    xml_print("\t\t\t\<guest\>$programme{'guest'}\<\/guest\>");
	}
	#$credits++;
	xml_print("\t\t\<\/credits\>");
    }

    if(defined $programme{'audio'} or defined $programme{'audiotype'})
    {
	xml_print("\t\t\<audio\>");
	xml_print("\t\t\t\<stereo\>$programme{'audio'}\<\/stereo\>") if defined $programme{'audio'};
	xml_print("\t\t\t\<stereo\>$programme{'audiotype'}\<\/stereo\>") if defined $programme{'audiotype'};
	xml_print("\t\t\<\/audio\>");
    }
    if(defined $programme{'aspect'} or defined $programme{'quality'})
    {
	xml_print("\t\t\<video\>");
	xml_print("\t\t\t\<aspect\>$programme{'aspect'}\<\/aspect\>") if defined $programme{'aspect'};
	xml_print("\t\t\t\<quality\>$programme{'quality'}\<\/quality\>") if defined $programme{'quality'};
	xml_print("\t\t\<\/video\>");
    }
    # filming country
    if(defined $programme{'country'})
    {
	xml_print("\t\t\<country lang=\"${language}\"\>$programme{'country'}\<\/country\>");
    }
    if(defined $programme{'rating'})
    {
	xml_print("\t\t\<rating system=\"VCHIP\"\>");
	xml_print("\t\t\t\<value\>$programme{'rating'}\<\/value\>");
	xml_print("\t\t\<\/rating\>");
    }

    
}

# create mandatory programme
# this function create the xml for all basic entries, like date, tittle, category, start, stop
# if one of this mandatory parameter is missing the script warns the user but continues...
#
# sub xml_print_programme($aProgrammeReference)
sub xml_print_programme($)
{
    my $refonprogramme = shift;
    my %programme = %{$refonprogramme};
    # locals
    my $date = '';
    my $channelid = '';
    my $channelname = '';
    my $title = '';
    my $start = '';
    my $end = '';
    my $category = '';
    my @categories = ();
    my $programmetype = '';
    my $warning = 0;
    my @grepped = ();

    if (defined $programme{'date'})
    {
	$date = $programme{'date'};
	$date =~ m/(\d+).(\d+).(\d+)/;
	$date = "$3$2$1" if defined $1 and defined $2 and defined $3;
    }
    else
    {
	print STDERR "missing date\n";
	$warning++;
    }
    if (defined $programme{'channel'})
    {
	$channelname = $programme{'channel'};
	$channelname =~ s/&/&amp;/g;
    }
    else
    {
	print STDERR "missing channelname\n";
	$warning++;
    }
    if (defined $programme{'channelid'})
    {
	$channelid = $programme{'channelid'};
    }
    else
    {
	print STDERR "missing channelid\n";
	$warning++;
    }
    if (defined $programme{'title'})
    {
	$title = $programme{'title'};
	$title =~ s/&/&amp;/g;
    }
    else
    {
	print STDERR "missing title\n";
	$warning++;
    }

    if (defined $programme{'start'})
    {
	$start = $programme{'start'};
	$start =~ s/://g;
	$start .= "00";
    }
    else
    {
	print STDERR "missing time start\n";
	$warning++;
    }
    if (defined $programme{'stop'})
    {
	$end = $programme{'stop'};
	$end =~ s/://g;
	$end .= "00";
    }
    else
    {
	print STDERR "missing time stop\n";
	$warning++;
    }

    if (defined $programme{'category'})
    {
	$category = $programme{'category'};
    }
    elsif (defined $programme{'programmetype'})
    {
	$programmetype = $programme{'programmetype'};
	if ("Serie" eq "$programmetype")
	{
	    $category = $programmetype;
	}
    }
    else
    {
	print STDERR "missing category\n";
	$warning++;
    }

    @grepped = grep(/${channelid}/, @validchannels);
    if (defined $grepped[0])
    {

	if ($warning == 0)
	{
	    xml_print("\t\<programme start=\"${date}${start}\" stop=\"${date}${end}\" channel=\"channel.${channelid}\"\>");
	    xml_print("\t\t\<title lang=\"${language}\"\>${title}\<\/title\>");
	    xml_print("\t\t\<date\>${date}\<\/date>");
	    @categories = split(', ', $category);
	    foreach (@categories)
	    {
		xml_print("\t\t\<category lang=\"${language}\"\>$_\<\/category\>");
	    }
	    xml_print_additional_materials(\%programme);
	    xml_print("\t\<\/programme\>");
	}
	else
	{
	    warn("some mandatory keys are missing take a look to the following hash: warning nr: $warning\n");
	    foreach (keys(%programme))
	    {
		print STDERR "key: $_ -> $programme{$_}\n";
	    }
	}
    }
}

sub xml_create_channels()
{
    foreach (@channellist)
    {
	xml_print_channel($_);
    }
}

sub xml_create_programmes()
{
    foreach (@programmelist)
    {
	xml_print_programme($_);
    }
}

sub xml_write()
{
    xml_init();
    xml_create_channels();
    xml_create_programmes();
    xml_close();
}

#cache clean up function
sub cleanup_cache()
{
    system("find $tmpcache -atime $cache_age_day -exec rm -f \'{}\' +");
    system("find $tmpcache -empty -exec rm -f \'{}\' +");
    system("rm -f $tmpcache/group*");
    system("rm -f $tmpcache/chan*");
}

sub main()
{
    # grab the main pages containing the channels
    get_main_pages();
    get_channels();

    if ($processlocal)
    {
	print "just parse the files located in the $tmpcache\n" if not $mute;
	local_parse_info();
	xml_write();
    }
    else
    {
	print "initialise the grabber...\n" if not $mute;
	init_ua_file();
	print "let's grab some tv info...\n" if not $mute;
	combine_dates();
	extract_info();
	xml_write();
    }
    
    print "
===============================================================================
= Grabber Stats...
===============================================================================
\t\t$grabstats cast program were downloaded...
\t\t$fileparsed files were parsed...
\t\t$lineparsed lines were parsed...

" if not $mute;
    return $success;
}

sub script_prefix()
{
    if (not -e $tmpcache)
    {
	print "create temporary directory--> $tmpcache\n" if not $mute;
	mkpath("$tmpcache");
	chmod(0777, "$tmpcache");
    }
}

sub script_sufix()
{
    cleanup_cache();
    print "Goodbye\n" if not $mute;
}

# this function is the first to be called...
script_prefix();
# gets the options
options();
# checks the options
check_options();
# program entry point
main();
# this function is the last to be called
script_sufix();

# function tests
#combine_dates();
#my @resu = read_from_file("$tmpcache/16409305.htm");
#print "RESU: @resu\n"; 

#xml_create_programmes();

#get_main_pages();
#get_channels();

#my $size = @channellist;
#print "Parsed $size channels\n@channellist\n";
#xml_write();
