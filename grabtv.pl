#!/usr/bin/perl -w
#
#Copyright (C) [2008,2009] [keller.eric, lars.schmohl]
#
#This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 3 of the License, or (at your option) any later version.
#This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#You should have received a copy of the GNU General Public License along with this program; if not, see <http://www.gnu.org/licenses>.
#Additional permission under GNU GPL version 3 section 7
#

use strict;
use threads;
use threads::shared;
use Getopt::Long;
use File::Path;
use File::Copy;
use File::Basename;
use Time::Local;
use Sys::CPU; #install libsys-cpu-perl in ubuntu

#------------------------------------------------------------------------------#
# Globals
#------------------------------------------------------------------------------#
my $commonurl = "http://cablecom.tvtv.ch/tvtv";
my $tmpdir 		 = "/etc/yatvgrabber";
my $testdir 	 = "$tmpdir/tests";
my $configurefile = "$tmpdir/channel.grab";
my $tmpcache     = "/var/cache/yatvgrabber";
my $swap_file    = "$tmpcache/tempgrab";
#------------------------------------------------------------------------------#
# User agents
#------------------------------------------------------------------------------#
my @useragents   = (
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_5; fr-fr) AppleWebKit/525.18 (KHTML, like Gecko) Version/3.1.2 Safari/525.20.1',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.6) Gecko/2009020519 Ubuntu/9.04 (jaunty) Firefox/3.0.6',
'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)'
);
my $rand_agent_number = int(rand(@useragents));
my $language     = 'de';    # TODO support other languages / other tvtv-sites (tvtv.de, tvtv.fr, tvtv.co.uk))
my $wget_timeout = "15";

# using Tor!!!
my $enableproxy   = '';
my $http_proxy    = "http://127.0.0.1:8118";
my $cache_age_day = "+1";

# lists
my @idlist        = ();
my @mainpages     = ();
my @channellist   = ();
my @validchannels = ();
my @programmelist :shared = ();

# statistics
my $grabstats  = 0;
my $lineparsed :shared = 0;
my $fileparsed :shared = 0;

# error codes
my $success     = 0;
my $retparamerr = 1;
my $retsyserr   = 2;

# get option long
# use some of the standard option defined by xmltv
my $no_cleanup;
my $numberofthreads = Sys::CPU::cpu_count();
my $configure;
my $output;
my $update_only;
my $verbose = 0;
my $help;

# per default it gets the tv program from max days and groups.
# the number of days the grabber has to get
#
# As the cablecom site works with the followinf parameter in its address
#
#
my $nbr_of_days   = 20;
my $processlocal;
my $maketestonerror; # this option will make a test of a file which could not properly be parsed

# prototypes
sub script_prefix;
sub main;
sub script_sufix;

# this function is the first to be called...
script_prefix();

# program entry point
main();

# this function is the last to be called
script_sufix();

sub main() {

	# main programm switch
	if ($configure) {
		#
		# configure option
		#
		# configure (only get the channel info with one day)
		$nbr_of_days = 0;
		
	    get_groups();
	    write_channels();
	    
	} else {
		#
		# program parser option
		#
		# or program grabber
		generate_valid_channels();
		
		get_groups();
		xml_write();
	}

    return $success;
}

sub script_prefix() {
    if ( not -e $tmpcache ) {
        print "create temporary directory--> $tmpcache\n" if ($verbose > 1);
        mkpath("$tmpcache");
        chmod( 0777, "$tmpcache" );
    }
    if ( not -e $tmpdir ) {
        print "create conf directory--> $tmpdir\n" if ($verbose > 1);
        mkpath("$tmpdir");
        chmod( 0777, "$tmpdir" );
    }
    if ( not -e $testdir ) {
        print "create test directory--> $testdir\n" if ($verbose > 1);
        mkpath("$testdir");
        chmod( 0777, "$testdir" );
    }
    
    # delete all empty files - could confuse the parser / file getter
    system("find $tmpcache -empty -exec rm -f \'{}\' +") if (-e $tmpcache);

	# gets the options
	options();
	
	# checks the options
	check_options();
}

sub script_sufix() {
    # delete all empty files - could confuse the parser / file getter
    system("find $tmpcache -empty -exec rm -f \'{}\' +") if (-e $tmpcache);
    # delete old files which have not been touched - only if not grabbing for tomorrow
    system("find $tmpcache -atime $cache_age_day -exec rm -f \'{}\' +") if not $no_cleanup;

    print "
===============================================================================
= Grabber Stats...
===============================================================================
\t\t$grabstats cast program were downloaded...
\t\t$fileparsed files were parsed...
\t\t$lineparsed lines were parsed...
Goodbye\n
" if ($verbose > 1);
}

# parse the script options
sub options() {
    GetOptions(
        "d|days=i"          => \$nbr_of_days,
        "p|process-locally" => \$processlocal,
        "t|threads=i"       => \$numberofthreads,
        "c|configure"       => \$configure,
        "cf|configure-file" => \$configurefile,
        "v|verbose=i"       => \$verbose,
        "o|output-file=s"   => \$output,
        "e|enable-proxy"    => \$enableproxy,
        "nc|no-cleanup"		=> \$no_cleanup,
        "uo|update-only"	=> \$update_only,
        "tope|make-test-on-parse-error"    => \$maketestonerror,
        "h|?|help"          => \$help
    ) || die "try -h or --help for more details...";

    usage() if $help;
}

# this function checks the option given to the script
# with the given --days the check option calculate the number of weeks and the rest of the available days...
sub check_options() {

    # limit the number of days to grab
    $nbr_of_days = 20 if ($nbr_of_days > 20);
    $nbr_of_days = 0 if ($nbr_of_days < 0);
    
    # configure channel valid list
    warn "WARNING: the $configurefile channel configuration file already exits\n" if ($configure and -e "$configurefile" );

    # return an error if the config file is missing
    if ((not -e "$configurefile" ) and (not $configure)) {
        warn "the $configurefile channel configuration file is missing, please call the --configure option first.\n";
        exit $retsyserr;
    }
    
    # do not activate process local and update only at the same time
    if (($update_only) and ($processlocal)) {
    	warn "do not activate update-only and process-local at the same time - abort\n";
    	exit $retsyserr;
    }
}

sub generate_valid_channels() {
    print "loading the $configurefile configuration file...\n" if ($verbose > 1);
    foreach (read_from_file("$configurefile")) {
    	push ( @validchannels, $1) if (m/(\d+)/);
    }
    print "authorised channel list: @validchannels\n" if ($verbose > 1);
}

sub usage() {
    print "
this is the $0 usage

-- Official parameters:
o|output-file=s => define a output filename for the xml.
d|days=x => grab tv data for x days counting from now! [0..20]
c|configure => get the channel list, and save it to the $configurefile file. The user can remove as many channels he does not require. When calling the script, only the channel in this file will be grabbed.

-- NoN Official parameters
t|threads=i => define the number of threads are take to parse the html pages (default autoset, 0 = parse in main thread) [0..]
p|process-locally => only create the xmltv data without grabing any file (this work on the local files downloaded during a previous session)
tope|make-test-on-parse-error => generate a test if a filename fails to be parsed properly [default off]
nc|no-cleanup => do no cleanup after parsing [default off]
uo|update-only => only generate an update file (only adds new downloaded programs) [default off]
h|?|help => display this usage
v|verbose=i => make it verbose, [default 0]

Examples:
# first you have to grab a channel list
$0 --configure
# you can print out a listing of the channels 
$0 --channel-list
# this will grab every tv program for every channels (-g option set to 16) and stores the results in test.xml
$0 -d 6 -g 17 -o test.xml

AUTHORS:
* keller_e 
* schmoh_l
";
    exit 1;
}

# get the group pages
#   create the group page urls and pass them to the get programm function
sub get_groups() {
    my $dayid;
    my $weekid;
    my $groupid;
    my $url;
    my $file;
    my @lines = ();
    
    # get the group numbers from the main page - mind process-local
    
    
	# get the group pages
    for (0 .. $nbr_of_days) {
    	$dayid = $_ % 7;
    	$weekid = int($_ / 7);
    	
        for $groupid (0 .. 17) {
           	$url = "$commonurl/index.vm?dayId=${dayid}&weekId=${weekid}&groupid=${groupid}&lang=de&epgView=list";
            $file = "$tmpcache/group${groupid}-week${weekid}-day${dayid}.htm";
            print "URL:$url\n" if $verbose;
            
            if ($processlocal)
            {
            	# only parse the local available files
            	if (-e $file) {
            		# read the file
            		@lines = read_from_file( $file);
            		
	              	# parse the channel info
	              	if ($success == parse_channel( \@lines)) {
		              	# get the programs from that page
		              	get_tv_program( \@lines) if not $configure;
	              	}
            	} else {
            		warn "unable to find $file" if $verbose;
            	} 
            	           	
            } else {
	            unlink $file if (-e $file);                
            	
            	## get the group page from the web
	            if ($success == use_wget( $url, $file))
	            {
            		@lines = read_from_file( $file);
            		
	              	# parse the channel info
	              	if ($success == parse_channel( \@lines)) {
		              	# get the programs from that page
		              	get_tv_program( \@lines) if not $configure;
	              	}
	              	
	            } else {
	                warn "unable to get $url" if $verbose; 
	            }
            }
        }
    }
}

# TODO use wget for getting the main pages...
# get_tv_program($url)
# the url is generated by the combine_dates() function
# this function will grab in the defined tmpdir directory all the casts
# using the system call to wget --> much quicker than perl get!
sub get_tv_program($) {
    my @lines      = @{shift @_};
    my @greppedurl = grep { /programdetails.vm?/ } @lines;

	my $url;
    my $id;
    my $file;
    my @localidlist = ();
    #used for getting the localidlist array into equivalent slices
    
    foreach (@greppedurl) {
        if ( $_ =~ /.*programmeId=(\d+)&lang.*/ ) {
            $id = $1;
            $file = "$tmpcache/$id.htm";
            
            # deletion of file is not needed (content of programm is not changing, instead ids on the group page change)
            if ($processlocal or -e $file) {
                # check if the file is available
                next if (not -e $file);
                #   go to the next file, if the update-only flag is given
                if ($update_only) {
                	# update the access time --> for the clean up
                	utime( time(), time(), $file);
                	next;
                }
                	
                print "$id.htm already exists... Skip Grabbing!\n" if ($verbose > 1);
            } else {
            	# download the file
            	$url = "$commonurl/web/programdetails.vm?programmeId=${id}&lang=de&epgView=list";
                next if ($success != use_wget( $url, $file ));
		    }
		    push( @localidlist, $file );
    	}
        $grabstats++;
    }
    # only continue, if ids are available in the local list
    return if not (@localidlist > 0);

    # join the running threads list (from a previous run)
    foreach (threads->list())
    {
	    $_->join();
    }

    #use slice
    if ($numberofthreads < 1)
    {
    	# no threads just call the parser directly
    	thread_parser( @localidlist);
    }
    else
    {
	    my $localsize = (int (@localidlist / $numberofthreads) + 1);
	    for (1 .. $numberofthreads)
	    {
	    	if ($localsize < @localidlist)
	    	{
	    		# will splice the elements
		   		threads->create('thread_parser', splice @localidlist, 0, $localsize);
	    	}
	    	else
	    	{
		   		# will create a thread for the rest of the list
	    		threads->create('thread_parser', @localidlist);
	    	}	
	    }
    }
}

#
# this function contains the thread operation on each file...
# meaning the parser will be threaded here
# thread_parser(@ids_of_files_to_parse)
sub thread_parser()
{
    my @lines = ();
    
    foreach (@_)
    {
    	if (defined $_)
    	{
	    	print "$_\n" if ($verbose > 1);
	    	
	    	@lines = read_from_file($_);
	    	
		    ($maketestonerror) ? parse_lines(\@lines, $_) : parse_lines(\@lines, "");
		    $fileparsed += 1;
    	}
    }
    
}

#use_wget($url, $id)
sub use_wget($$) {
    my $url          = shift;
    my $file         = shift;
    my $wgetquiet    = ($verbose < 2) ? '--quiet' : '';
    my $wgetusragent = "--user-agent=\"$useragents[$rand_agent_number]\"";
    my $wgetoptions  = "-nc --random-wait --no-cache --timeout=$wget_timeout";
    my $proxycommand = "set http_proxy=\"$http_proxy\"";

    my $wgetcommand = "wget \"$url\" $wgetoptions $wgetusragent -O $file $wgetquiet";

    # use the Tor proxy
    $wgetcommand = "$proxycommand; $wgetcommand" if $enableproxy;
    print "wgetcommand: $wgetcommand\n" if ($verbose > 1);

    if ( 0 != system($wgetcommand) ) {
        warn("some problem occured when calling system\n") if ($verbose > 1);
    } else { 
        chmod( 0666, $file );
    }
    return $success;
}

# read_from_file($filename)
sub read_from_file($) {
    my $filename = shift;

	# reset time to refect access
	utime( time(), time(), $filename );
	
    open( FILE, "$filename" );
    my @lines = <FILE>;
    close FILE;

    return @lines;
}

# parse_lines($refonlines, $idfilename)
# depends on the language
sub parse_lines($$) {
    my @lines     = @{shift @_};
    my %programme :shared = ();
    
    my $idfilename = shift @_ if $maketestonerror;

    my $extractchan   = 0;
    my $category      = 0;
    my $land          = 0;
    my $producer      = 0;
    my $productor     = 0;
    my $presentator   = 0;
    my $originaltitle = 0;
    my $camera        = 0;
    my $music         = 0;
    my $script        = 0;
    my $production    = 0;
    my $filmeditor    = 0;
    my $actors        = 0;
    my $author        = 0;
    my $kidprotection = 0;
    my $musicleader   = 0;
    my $i             = 0;

    #print "LINES: @lines\n";
    foreach (@lines) {

        # extarct the channel id
        # hbx.pn="SF ZWEI (900)";//PAGE NAME(S)
        if ( $_ =~ /hbx.pn=".*\((.*)\)".*/ ) {
            print "CHANID: $1\n" if ( defined $1 and ($verbose > 1) );
            $programme{'channelid'} = "$1";
            
            # next file if this is no valid channel
            return if (not grep { $_ == $1} @validchannels);
        }

        # extract cast type
        if ( $_ =~ /Film/ ) {
            print "cast Type: Film\n" if ($verbose > 1);
            $programme{'programmetype'} = "Film";
        }
        if ( $_ =~ /Serie/ ) {
            print "cast Type: Serie\n" if ($verbose > 1);
            $programme{'programmetype'} = "Serie";
        }

        # extract title
        if ( $_ =~ /fb-b15">(.*)<\/span.*/ ) {
            print "TITLE: $1\n" if ( defined $1 and ($verbose > 1) );
            $programme{'title'} = filter_xml_content("$1");
        }

        # extract episode
        if ( $_ =~ /fn-b9">(.*)<\/span.*/ ) {
            print "FOLGE: $1\n" if ( defined $1 and ($verbose > 1) );
            $programme{'episode'} = filter_xml_content("$1");
        }

        # extraction of the description
        if ( $_ =~ /fn-b10">(.*)<\/span.*/ ) {
            print "DESC: $1\n" if ( defined $1 and ($verbose > 1) );
            $programme{'desc'} = filter_xml_content("$1");
        }

        # extraction of the date
        if ( $_ =~ /fn-w8".*>(.*),\s+(\d+.\d+.\d+)<\/t.*/ ) {
            print "Date: $1, $2\n" if ( defined $1 and defined $2 and ($verbose > 1) );
            $programme{'dayoftheweek'} = filter_xml_content("$1");
            $programme{'date'}         = filter_xml_content("$2");
        }

        # extraction of the begin end time
        if ( $_ =~ /fn-b8".*>Beginn:\s+(\d+:\d+).*<\/t.*/ ) {
            print "\tTime Start: $1\n" if ( defined $1 and ($verbose > 1) );
            $programme{'start'} = filter_xml_content("$1");
        }
        if ( $_ =~ /fn-b8".*>Ende:\s+(\d+:\d+).*<\/t.*/ ) {
            print "\tTime End: $1\n" if ( defined $1 and ($verbose > 1) );
            $programme{'stop'} = filter_xml_content("$1");
        }
        if ( $_ =~ /fn-b8".*>Länge:\s+(\d+).*<\/t.*/ ) {
            print "\tcast Time: $1 min.\n" if ( defined $1 and ($verbose > 1) );
            $programme{'timeduration'} = filter_xml_content("$1");
        }

        # extract actors
        if ( $_ =~ /fn-w8".*>Darsteller:.*/ ) {
            $actors = 1;
            next;
        }
        if ( $actors == 1 ) {
            if ( $_ =~ /.*fn-b8">(.*)<\/span.*/ ) {
                print "Staring: $1\n" if ( defined $1 and ($verbose > 1) );
                $programme{'actors'} = filter_xml_content("$1");
            }
            $actors = 0;
            next;
        }

        #extract Producers
        if ( $_ =~ /fn-w8".*>Regie:.*/ ) {
            $producer = 1;
            next;
        }
        if ( $producer == 1 ) {
            if ( $_ =~ /.*fn-b8">(.*)<\/span.*/ ) {
                print "Regie: $1\n" if ( defined $1 and ($verbose > 1) );

                $programme{'director'} = filter_xml_content("$1");
            }
            $producer = 0;
            next;
        }

        # Authors
        if ( $_ =~ /fn-w8".*>Autor:.*/ ) {
            $author = 1;
            next;
        }
        if ( $author == 1 ) {
            if ( $_ =~ /.*fn-b8">(.*)<\/span.*/ ) {
                print "Authors: $1\n" if ( defined $1 and ($verbose > 1) );
                $programme{'writer'} .= filter_xml_content("$1");
            }
            $author = 0;
            next;
        }

        # category
        if ( $_ =~ /fn-w8".*>Kategorie:.*/ ) {
            $category = 1;
            next;
        }
        if ( $category == 1 ) {
            if ( $_ =~ /.*fn-b8">(.*)<\/span.*/ ) {
                print "Category: $1\n" if ( defined $1 and ($verbose > 1) );
                $programme{'category'} = filter_xml_content("$1");
            }
            $category = 0;
            next;
        }

        # filming location
        if ( $_ =~ /fn-w8".*>Land:.*/ ) {
            $land = 1;
            next;
        }
        if ( $land == 1 ) {
            if ( $_ =~ /.*fn-b8">(.*)<.*/ ) {
                print "Land: $1\n" if ( defined $1 and ($verbose > 1) );
                $programme{'country'} = filter_xml_content("$1");
            }
            $land = 0;
            next;
        }

        # Kid Protection
        if ( $_ =~ /fn-w8".*>FSK:.*/ ) {
            $kidprotection = 1;
            next;
        }
        if ( $kidprotection == 1 ) {
            if ( $_ =~ /.*fn-b8">(.*)<\/span.*/ ) {
                print "Not Allowed for Kid under: $1\n" if ( defined $1 and ($verbose > 1) );
                $programme{'rating'} = filter_xml_content("$1");
            }
            $kidprotection = 0;
            next;
        }

        # Film Editor
        if ( $_ =~ /fn-w8".*>Film Editor:.*/ ) {
            $filmeditor = 1;
            next;
        }
        if ( $filmeditor == 1 ) {
            if ( $_ =~ /.*fn-b8">(.*)<\/span.*/ ) {
                print "Film Editor: $1\n" if ( defined $1 and ($verbose > 1) );
                $programme{'filmeditor'} = filter_xml_content("$1");
            }
            $filmeditor = 0;
            next;
        }

        # Produktion
        if ( $_ =~ /fn-w8".*>Produktion:.*/ ) {
            $production = 1;
            next;
        }
        if ( $production == 1 ) {
            if ( $_ =~ /.*fn-b8">(.*)<\/span.*/ ) {
                print "Studio Production: $1\n" if ( defined $1 and ($verbose > 1) );
                $programme{'studio'} = filter_xml_content("$1");
            }
            $production = 0;
            next;
        }

        # Produzent
        if ( $_ =~ /fn-w8".*>Produzent:.*/ ) {
            $productor = 1;
            next;
        }
        if ( $productor == 1 ) {
            if ( $_ =~ /.*fn-b8">(.*)<\/span.*/ ) {
                print "Producer: $1\n" if ( defined $1 and ($verbose > 1) );
                $programme{'producer'} = filter_xml_content("$1");
            }
            $productor = 0;
            next;
        }

        # Drehbuch
        if ( $_ =~ /fn-w8".*>Drehbuch:.*/ ) {
            $script = 1;
            next;
        }
        if ( $script == 1 ) {
            if ( $_ =~ /.*fn-b8">(.*)<\/span.*/ ) {
                print "script: $1\n" if ( defined $1 and ($verbose > 1) );
                $programme{'writer'} .= filter_xml_content("$1");
            }
            $script = 0;
            next;
        }

        # Musik
        if ( $_ =~ /fn-w8".*>Musik:.*/ ) {
            $music = 1;
            next;
        }
        if ( $music == 1 ) {
            if ( $_ =~ /.*fn-b8">(.*)<\/span.*/ ) {
                print "Music: $1\n" if ( defined $1 and ($verbose > 1) );
                $programme{'musicauthor'} = filter_xml_content("$1");
            }
            $music = 0;
            next;
        }

        # Kamera
        if ( $_ =~ /fn-w8".*>Kamera:.*/ ) {
            $camera = 1;
            next;
        }
        if ( $camera == 1 ) {
            if ( $_ =~ /.*fn-b8">(.*)<\/span.*/ ) {
                print "Camera: $1\n" if ( defined $1 and ($verbose > 1) );
                $programme{'camera'} = filter_xml_content("$1");
            }
            $camera = 0;
            next;
        }

        # Orginaltitel
        if ( $_ =~ /fn-w8".*>Orginaltitel:.*/ ) {
            $originaltitle = 1;
            next;
        }
        if ( $originaltitle == 1 ) {
            if ( $_ =~ /.*fn-b8">(.*)<\/span.*/ ) {
                print "Original Title: $1\n" if ( defined $1 and ($verbose > 1) );
                $programme{'sub-title'} = filter_xml_content("$1");
            }
            $originaltitle = 0;
            next;
        }

        # Präsentiert von
        if ( $_ =~ /fn-w8".*>Präsentiert von:.*/ ) {
            $presentator = 1;
            next;
        }
        if ( $presentator == 1 ) {
            if ( $_ =~ /.*fn-b8">(.*)<\/span.*/ ) {
                print "presented by: $1\n" if ( defined $1 and ($verbose > 1) );
                $programme{'presenter'} = filter_xml_content("$1");
            }
            $presentator = 0;
            next;
        }

        # Musikalische Leitung
        if ( $_ =~ /fn-w8".*>Musikalische Leitung:.*/ ) {
            $musicleader = 1;
            next;
        }
        if ( $musicleader == 1 ) {
            if ( $_ =~ /.*fn-b8">(.*)<\/span.*/ ) {
                print "Music chef: $1\n" if ( defined $1 and ($verbose > 1) );
                $programme{'musicchef'} = filter_xml_content("$1");
            }
            $musicleader = 0;
            next;
        }

        # audio, video types...
        # depends on the web language
        # this first implementation just use german :)
        if ( $_ =~ /Stereo/ ) {
            print "AUDIO=Stereo\n" if ($verbose > 1);
            $programme{'audio'} = "stereo";
        }
        if ( $_ =~ /16:9 video format/ ) {
            print "VIDEO=16:9 video format\n" if ($verbose > 1);
            $programme{'aspect'} = "16:9";
        }
        if ( $_ =~ /Mehrsprachig/ ) {
            print "Multilangue: Mehrsprachig\n" if ($verbose > 1);
            $programme{'languages'} = "multi";
        }
        if ( $_ =~ /High Definition Video/ ) {
            print "HDTV: High Definition Video\n" if ($verbose > 1);
            $programme{'quality'} = "HDTV";
        }
        if ( $_ =~ /Surround Sound/ ) {
            print "Audio: Surround Sound\n" if ($verbose > 1);
            $programme{'audiotype'} = "surround";
        }
    }
    $lineparsed += $i;

	# add the parsed programm to the programm list
	$programme{'idfilename'} = "$idfilename" if $maketestonerror;
   	push( @programmelist, \%programme );
}

# parse_channel($refonlines)
#   returns $success, if one channel of this group is in the valid channels list
sub parse_channel($) {
    my @lines        = @{shift @_};
    my $chanlogolink;
    my $channame;
    my %chaninfo     = ();
    my $channelid;
    my $returnCode = -1;

    foreach (@lines) {

#<td><img src="http://cablecom.tvtv.ch:80/tvtv/resource?channelLogo=118" border=0 height="21" vspace="1" width="40" alt="3sat"></td>
#<div class="fb-w10" style="padding-left:5px;">Das Erste</div>
#if ($_ =~ /fb-w10\" style=.*>(.*)<\/div>/)
        if ( $_ =~ /<td><img src="(.*channelLogo.*)"\s+border.*alt="(.*)".*/ ) {

			$chanlogolink = $1;
			$channame     = $2;
            $chanlogolink =~ m/.*channelLogo=(\d+)/;
            $channelid    = $1; 

			# only save channels which are in the config file
			next if ((not $configure) and (not grep { $_ == $channelid} @validchannels));
			
			# report found channel
			$returnCode = $success;
			
			# only save channels which are not already in the list
			next if (grep { ${$_}{'id'} == $channelid} @channellist);
            
            $chaninfo{'id'} = $1;
            $chaninfo{'name'} = filter_xml_content($channame);
            $chaninfo{'link'} = $chanlogolink;

			# this{%chaninfo} will create a unique pointer reference on the %chaninfo hash.
			# it is like pass the reference by copy...
            push( @channellist, {%chaninfo} );
            if ( $verbose > 1 ) {
                print "channel id  = $chaninfo{'id'}\n";
                print "channel name= $chaninfo{'name'}\n";
                print "channel link= $chaninfo{'link'}\n";
            }
        }
    }
    return $returnCode;
}

#sub copyfiletotest($filename)
sub copyfiletotest($)
{
	my $filename = shift;
 
	print("error parse in file> $filename\n");
 	copy("$filename", "$testdir/" . basename("$filename"));
}

# this function display all the channels available on the given website...
sub write_channels() {
    my $nbrchan      = @channellist;
    my $channelid    = '';
    my $channelname  = '';

    print "/------------------------------------------\\\n";
    print "| Channel List                             |\n";
    print "\------------------------------------------/\n";
    print "from: $commonurl...\nto: $configurefile\n";

    open( WF, ">$configurefile" ) or (warn "could not create the $configurefile file $!" and die);

    foreach (@channellist) {

        $channelid    = ${$_}{'id'};
        $channelname  = ${$_}{'name'};

        print "channel id=${channelid}\t\t\t$channelname\n";
        print WF "$channelid#$channelname\n";
    }

    print "/------------------------------------------\\\n";
    print "| Found $nbrchan Channels\n";
    print "\------------------------------------------/\n";
    print "from: $commonurl...\nto: $configurefile\n";
    close(WF);
}

# filter the content for insert in xml file
#  returns undef if parameter is undef
sub filter_xml_content($)
{
	my $line = shift;
	
	# look for undef
	return undef if not defined $line;
	
	# cut tailing newline
	chomp $line;
	
	# filter the content for unwanted chars
	$line =~ s/\<.*\>//g;
	$line =~ s/&/&amp;/g;
	$line =~ s/c\<t/c't/g;
	
	return $line;
}

# xml_print($aline)
# automatic \n at the end of the line
sub xml_print($) {
    my $line = shift;

    $output ? print XMLFILE "$line\n" : print "$line\n";
}

sub xml_init() {
    # write xml in a file...
    open( XMLFILE, ">$output" ) if ($output);
    xml_print( "<tv generator-info-name=\"yagraber\" source-info-url=\"$commonurl\">");
}

sub xml_close() {
    xml_print("</tv>");
    close(XMLFILE) if ($output);
}

# create the head of the xml file
#   containing the channels with icons
sub xml_print_channel($) {
    my %chaninfo      = %{shift @_};
    my $channelid    = $chaninfo{'id'};
    my $channelname  = $chaninfo{'name'};
    my $chanlogolink = $chaninfo{'link'};

    xml_print("\t\<channel id=\"${channelid}\"\>");
    xml_print("\t\t\<display-name lang=\"$language\"\>$channelname\<\/display-name\>");
    xml_print("\t\t\<icon src=\"${chanlogolink}\"\/\>");
    xml_print("\t\<\/channel\>");
}

# create bonus entries
# this function checks if there are more information contained in the programme hash table, like
# actors, description, subtitle, original title, producer, writer, audio format video format, ...
#
# sub xml_print_additional_materials($aProgrammeReference)
sub xml_print_additional_materials($) {
    my %programme      = %{shift @_};

    # locals
    my $description = '';
    my $credits     = 0;
    my $subtitle    = '';

    # non mandatory parameters... Bonus if it's existing
    # sub title, original title
    if ( defined $programme{'sub-title'} ) {
        $subtitle = $programme{'sub-title'};
        xml_print("\t\t\<sub-title lang=\"${language}\"\>${subtitle}\<\/sub-title\>");
    }

    # description
    if ( defined $programme{'desc'} ) {
        $description = $programme{'desc'};
        xml_print("\t\t\<desc lang=\"${language}\"\>${description}\t\t\<\/desc\>");
    }

    # credits authors, actors, regie, producer, ...
    if (   defined $programme{'actors'}
        or defined $programme{'director'}
        or defined $programme{'writer'}
        or defined $programme{'producer'}
        or defined $programme{'presenter'}
        or defined $programme{'commentator'}
        or defined $programme{'guest'} )
    {
        # any of the credits contents will write the credit xml tag
        xml_print("\t\t\<credits\>");
        # add the actors
        if ( defined $programme{'actors'} ) {
            foreach (split( ', ', $programme{'actors'} )) {
                xml_print("\t\t\t\<actor\>$_\<\/actor\>");
            }
        }
        xml_print("\t\t\t\<director\>$programme{'director'}\<\/director\>") if ( defined $programme{'director'} );
        xml_print("\t\t\t\<writer\>$programme{'writer'}\<\/writer\>") if ( defined $programme{'writer'} );
        xml_print("\t\t\t\<adapter\>$programme{'adapter'}\<\/adapter\>") if ( defined $programme{'adapter'} );
        xml_print("\t\t\t\<producer\>$programme{'producer'}\<\/producer\>") if ( defined $programme{'producer'} );
        xml_print("\t\t\t\<presenter\>$programme{'presenter'}\<\/presenter\>") if ( defined $programme{'presenter'} );
        xml_print("\t\t\t\<commentator\>$programme{'commentator'}\<\/commentator\>") if ( defined $programme{'commentator'} );
        xml_print("\t\t\t\<guest\>$programme{'guest'}\<\/guest\>") if ( defined $programme{'guest'} );
        xml_print("\t\t\<\/credits\>");
    }

    if ( defined $programme{'audio'} or defined $programme{'audiotype'} ) {
        xml_print("\t\t\<audio\>");
        xml_print("\t\t\t\<stereo\>$programme{'audio'}\<\/stereo\>") if defined $programme{'audio'};
        xml_print("\t\t\t\<stereo\>$programme{'audiotype'}\<\/stereo\>") if defined $programme{'audiotype'};
        xml_print("\t\t\<\/audio\>");
    }
    if ( defined $programme{'aspect'} or defined $programme{'quality'} ) {
        xml_print("\t\t\<video\>");
        xml_print("\t\t\t\<aspect\>$programme{'aspect'}\<\/aspect\>") if defined $programme{'aspect'};
        xml_print("\t\t\t\<quality\>$programme{'quality'}\<\/quality\>") if defined $programme{'quality'};
        xml_print("\t\t\<\/video\>");
    }

    # filming country
    xml_print("\t\t\<country lang=\"${language}\"\>$programme{'country'}\<\/country\>") if ( defined $programme{'country'} );
    if ( defined $programme{'rating'} ) {
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
sub xml_print_programme($) {
    my %programme      = %{shift @_};

    # locals
    my $date          = '';
    my $channelid     = $programme{'channelid'}; # channel id is always defined
    my $title         = '';
    my $start         = '';
    my $end           = '';
    my $category      = '';
    my $programmetype = '';
    my $warning       = 0;

    if ( defined $programme{'date'} ) {
        $date = $programme{'date'};
        $date =~ m/(\d+).(\d+).(\d+)/;
        $date = "$3$2$1" if defined $1 and defined $2 and defined $3;
    }
    else {
        print STDERR "missing date\n";
        $warning++;
    }
    if ( defined $programme{'title'} ) {
        $title = $programme{'title'};
    }
    else {
        print STDERR "missing title\n";
        $warning++;
    }

    if ( defined $programme{'start'} ) {
        $start = $programme{'start'};
        $start =~ s/://g;
        $start .= "00";
    }
    else {
        print STDERR "missing time start\n";
        $warning++;
    }
    if ( defined $programme{'stop'} ) {
        $end = $programme{'stop'};
        $end =~ s/://g;
        $end .= "00";
    }

    if ( defined $programme{'category'} ) {
        $category = $programme{'category'};
    }
    elsif ( defined $programme{'programmetype'} ) {
        $programmetype = $programme{'programmetype'};
        if ( "Serie" eq "$programmetype" ) {
            $category = $programmetype;
        }
    }

    if ( $warning == 0 ) {
        xml_print("\t\<programme start=\"${date}${start}\" stop=\"${date}${end}\" channel=\"${channelid}\"\>");
        xml_print("\t\t\<title lang=\"${language}\"\>${title}\<\/title\>");
        xml_print("\t\t\<date\>${date}\<\/date>");
        foreach (split( ', ', $category)) {
            xml_print("\t\t\<category lang=\"${language}\"\>$_\<\/category\>");
        }
        xml_print_additional_materials( \%programme );
        xml_print("\t\<\/programme\>");
    }
    else {
        warn("some mandatory keys are missing take a look to the following hash: warning nr: $warning\n");
        foreach ( keys(%programme) ) {
            print STDERR "key: $_ -> $programme{$_}\n";
        }
        copyfiletotest($programme{'idfilename'}) if ($maketestonerror);
    }
}

# main function to write the xml information
#   writes the header, channels info, programs to the 
#	xml file (at this order)
sub xml_write() {
	
	my $channelid;
	
	#join all threaded channel parsers
    foreach (threads->list())
    {
	    $_->join();
    }
	
    xml_init();
    
    foreach (@channellist) {
    	$channelid = ${$_}{'id'};
        xml_print_channel($_) if (defined $channelid);
    }
    foreach (@programmelist) {
    	$channelid = ${$_}{'channelid'};
        xml_print_programme($_) if (defined $channelid);
    }
    
    xml_close();
}
