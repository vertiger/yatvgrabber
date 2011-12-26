#!/usr/bin/perl -w
#
#Copyright (C) [2011] [keller.eric, lars.schmohl]
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
use Time::localtime;
use Sys::CPU;    #install libsys-cpu-perl in ubuntu

#------------------------------------------------------------------------------#
# Globals
#------------------------------------------------------------------------------#
my $baseurl       = "http://cablecom.tvtv.ch";
my $commonurl     = "$baseurl/cbc/program";
my $groupurl      = "$commonurl/group";
my $tmpdir        = "/etc/yatvgrabber";
my $testdir       = "$tmpdir/tests";
my $configurefile = "$tmpdir/channel.grab";
my $tmpcache      = "/var/cache/yatvgrabber";
my $swap_file     = "$tmpcache/tempgrab";

#------------------------------------------------------------------------------#
# User agents
#------------------------------------------------------------------------------#
my @useragents = (
'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.102011-10-16 20:23:50',
'Mozilla/5.0 (Linux; U; Android 2.3.3; en-au; GT-I9100 Build/GINGERBREAD) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.12011-10-16 20:22:55',
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.202 Safari/535.12011-10-16 20:21:13',
'Mozilla/5.0 (Ubuntu; X11; Linux x86_64; rv:8.0) Gecko/20100101 Firefox/8.0',
'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:7.0.1) Gecko/20100101 Firefox/7.0.12011-10-16 20:23:00'
);
my $rand_agent_number  = int( rand(@useragents) );
my $language           = 'de';
my $wget_timeout_local = "15";
my $current_year       = localtime->year() + 1900;

# using Tor!!!
my $enableproxy   = '';
my $http_proxy    = "http://127.0.0.1:8118";
my $cache_age_day = "+1";

# lists
my @idlist                 = ();
my @mainpages              = ();
my @channellist            = ();
my @validchannels          = ();
my @programmelist : shared = ();

# statistics
my $grabstats           = 0;
my $lineparsed : shared = 0;
my $fileparsed : shared = 0;

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
# As the cablecom site works with the following parameter in its address
#
#
my $nbr_of_days = 20;
my $processlocal;
my $maketestonerror
  ;  # this option will make a test of a file which could not properly be parsed

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
    }
    else {

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
        print "create temporary directory--> $tmpcache\n" if ( $verbose > 1 );
        mkpath("$tmpcache");
        chmod( 0777, "$tmpcache" );
    }
    if ( not -e $tmpdir ) {
        print "create conf directory--> $tmpdir\n" if ( $verbose > 1 );
        mkpath("$tmpdir");
        chmod( 0777, "$tmpdir" );
    }
    if ( not -e $testdir ) {
        print "create test directory--> $testdir\n" if ( $verbose > 1 );
        mkpath("$testdir");
        chmod( 0777, "$testdir" );
    }

    # delete all empty files - could confuse the parser / file getter
    system("find $tmpcache -type f -empty -exec rm -f \'{}\' +")
      if ( -e $tmpcache );

    # gets the options
    options();

    # checks the options
    check_options();
}

sub script_sufix() {

    # delete all empty files - could confuse the parser / file getter
    system("find $tmpcache -type f -empty -exec rm -f \'{}\' +")
      if ( -e $tmpcache );

# delete old files which have not been touched - only if not grabbing for tomorrow
    system("find $tmpcache -type f -atime $cache_age_day -exec rm -f \'{}\' +")
      if not $no_cleanup;

    print "
===============================================================================
= Grabber Stats...
===============================================================================
\t\t$grabstats cast program were downloaded...
\t\t$fileparsed files were parsed...
\t\t$lineparsed lines were parsed...
Goodbye\n
" if ( $verbose > 1 );
}

# parse the script options
sub options() {
    GetOptions(
        "d|days=i"                      => \$nbr_of_days,
        "p|process-locally"             => \$processlocal,
        "t|threads=i"                   => \$numberofthreads,
        "c|configure"                   => \$configure,
        "cf|configure-file"             => \$configurefile,
        "v|verbose=i"                   => \$verbose,
        "o|output-file=s"               => \$output,
        "e|enable-proxy"                => \$enableproxy,
        "nc|no-cleanup"                 => \$no_cleanup,
        "uo|update-only"                => \$update_only,
        "tope|make-test-on-parse-error" => \$maketestonerror,
        "h|?|help"                      => \$help
    ) || die "try -h or --help for more details...";

    usage() if $help;
}

# this function checks the option given to the script
# with the given --days the check option calculate the number of weeks and the rest of the available days...
sub check_options() {

    # limit the number of days to grab
    $nbr_of_days = 20 if ( $nbr_of_days > 20 );
    $nbr_of_days = 0  if ( $nbr_of_days < 0 );

    # configure channel valid list
    warn
      "WARNING: the $configurefile channel configuration file already exits\n"
      if ( $configure and -e "$configurefile" );

    # return an error if the config file is missing
    if ( ( not -e "$configurefile" ) and ( not $configure ) ) {
        warn
"the $configurefile channel configuration file is missing, please call the --configure option first.\n";
        exit $retsyserr;
    }

    # do not activate process local and update only at the same time
    if ( ($update_only) and ($processlocal) ) {
        warn
"do not activate update-only and process-local at the same time - abort\n";
        exit $retsyserr;
    }
}

sub generate_valid_channels() {
    print "loading the $configurefile configuration file...\n"
      if ( $verbose > 1 );
    foreach ( read_from_file("$configurefile") ) {
        push( @validchannels, $1 ) if (m/(\d+)/);
    }
    print "authorised channel list: @validchannels\n" if ( $verbose > 1 );
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
    my $url;
    my $file;
    my @lines = ();
    my @groupid =
      ( 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17 );

    # get the group numbers from the main page - mind process-local
    $file = "$tmpcache/group";
    $url  = "$groupurl";
    print "URL:$groupurl\n" if $verbose;

    if ($processlocal) {

        # local processing
        if ( -e $file ) {

            # read the file
            @lines = read_from_file($file);

            @groupid = (0);

            # parse the main file
            foreach (@lines) {
                if ( $_ =~ /&cg=(\d+)/ ) {
                    push @groupid, $1 if not grep { $_ == $1 } @groupid;
                }
            }
        }
    }
    else {

        # normal grabbing
        unlink $file if ( -e $file );

        # get the main page
        if ( $success == use_wget( $url, $file ) ) {

            # read the file
            @lines = read_from_file($file);

            @groupid = (0);

            # parse the main page
            foreach (@lines) {
                if ( $_ =~ /&cg=(\d+)/ ) {
                    push @groupid, $1 if not grep { $_ == $1 } @groupid;
                }
            }
        }
    }

    # get the group pages
    for ( 0 .. $nbr_of_days ) {
        $dayid = $_;

        foreach my $groupid (@groupid) {
            $url  = "$groupurl?day=${dayid}&cg=${groupid}";
            $file = "$tmpcache/cg${groupid}-day${dayid}.htm";
            print "URL:$url\n" if $verbose;

            if ($processlocal) {

                # only parse the local available files
                if ( -e $file ) {

                    # read the file
                    @lines = read_from_file($file);

                    # parse the channel info
                    if ( $success == parse_channel( \@lines ) ) {

                        # get the programs from that page
                        get_tv_program( \@lines ) if not $configure;
                    }
                }
                else {
                    warn "unable to find $file" if $verbose;
                }
            }
            else {
                unlink $file if ( -e $file );
                ## get the group page from the web
                if ( $success == use_wget( $url, $file ) ) {
                    @lines = read_from_file($file);

                    # parse the channel info
                    if ( $success == parse_channel( \@lines ) ) {

                        # get the programs from that page
                        get_tv_program( \@lines ) if not $configure;
                    }
                }
                else {
                    warn "unable to get $url" if $verbose;
                }
            }
        }
    }
}

# get_tv_program($url)
# this function will grab in the defined tmpdir directory all the casts
# using the system call to wget --> much quicker than perl get!
sub get_tv_program($) {
    my @lines = @{ shift @_ };
    my @greppedurl = grep { /\/cbc\/program\/detail\// } @lines;

    my $url;
    my $id;
    my $file;
    my @localidlist = ();

    #used for getting the localidlist array into equivalent slices

    foreach (@greppedurl) {
        if ( $_ =~ /.*\/cbc\/program\/detail\/(\d+).*/ ) {
            $id   = $1;
            $file = "$tmpcache/$id.htm";

            # deletion of file is not needed
            # (content of programm is not changing,
            #instead ids on the group page change)
            if ( $processlocal or -e $file ) {

                # check if the file is available
                next if ( not -e $file );

                #   go to the next file, if the update-only flag is given
                if ($update_only) {

                    # update the access time --> for the clean up
                    utime( time(), time(), $file );
                    next;
                }

        #print "$id.htm already exists... Skip Grabbing!\n" if ( $verbose > 1 );
            }
            else {

                # download the file
                $url = "$commonurl/detail/${id}?po=ct";
                next if ( $success != use_wget( $url, $file ) );
            }
            push( @localidlist, $file )
              if not grep { $_ eq $file } @localidlist;
        }
        $grabstats++;
    }

    # only continue, if ids are available in the local list
    return if not( @localidlist > 0 );

    # join the running threads list (from a previous run)
    foreach ( threads->list() ) {
        $_->join();
    }

    #use slice
    if ( $numberofthreads < 1 ) {

        # no threads just call the parser directly
        thread_parser(@localidlist);
    }
    else {
        my $localsize = ( int( @localidlist / $numberofthreads ) + 1 );
        for ( 1 .. $numberofthreads ) {
            if ( $localsize < @localidlist ) {

                # will splice the elements
                threads->create( 'thread_parser', splice @localidlist,
                    0, $localsize );
            }
            else {

                # will create a thread for the rest of the list
                threads->create( 'thread_parser', @localidlist );
            }
        }
    }
}

#
# this function contains the thread operation on each file...
# meaning the parser will be threaded here
# thread_parser(@ids_of_files_to_parse)
sub thread_parser() {
    my @lines = ();
    foreach (@_) {
        if ( defined $_ ) {
            print "$_\n" if ( $verbose > 1 );
            @lines = read_from_file($_);
            ($maketestonerror)
              ? parse_lines( \@lines, $_ )
              : parse_lines( \@lines, "" );
            $fileparsed += 1;
        }
    }
}

#use_wget($url, $id)
sub use_wget($$) {
    my $url          = shift;
    my $file         = shift;
    my $wgetquiet    = ( $verbose < 2 ) ? '--quiet' : '';
    my $wgetusragent = "--user-agent=\"$useragents[$rand_agent_number]\"";
    my $wgetoptions =
      "-nc --random-wait --no-cache --timeout=$wget_timeout_local";
    my $proxycommand = "set http_proxy=\"$http_proxy\"";
    my $wgetcommand =
      "wget \"$url\" $wgetoptions $wgetusragent -O $file $wgetquiet";

    # use the Tor proxy
    $wgetcommand = "$proxycommand; $wgetcommand" if $enableproxy;
    print "wgetcommand: $wgetcommand\n" if ( $verbose > 1 );

    if ( 0 != system($wgetcommand) ) {
        warn("some problem occured when calling system\n") if ( $verbose > 1 );
    }
    else {
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
    my @lines              = @{ shift @_ };
    my %programme : shared = ();
    my $idfilename         = shift @_ if $maketestonerror;

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
    my $content       = 0;
    my $description   = 0;
    my $epsiode       = 0;
    my $year          = 0;
    my $header        = 0;

    #print "LINES: @lines\n";
    foreach (@lines) {
        # grabber stats
        $lineparsed += 1;

        # extract the channel id
        # s.prop16="SF ZWEI (900)";//PAGE NAME(S)
        if ( $_ =~ /s.prop16="[^\(]+\((.*)\)"/ ) {
            $programme{'channelid'} = "$1";
            $programme{'channelid'} =~ s/,//g;
            print "CHANID: $programme{'channelid'}\n" if ( $verbose > 1 );

            # next file if this is no valid channel
            return if ( not grep { $_ == $programme{'channelid'} } @validchannels );
        }

        # extract header information
        if ( $_ =~ /<table id="header">/ ) {
            $header = 1;
            next;
        }
        if ( $header > 0 ) {

            # get the date information
            if ( $_ =~ /<td>.*([0-9]{2})\.([0-9]{2}).*<\/td>/ ) {
                my $day_temp   = 1;
                my $month_temp = 1;
                my $year_temp  = $current_year;
                $day_temp   = $1 if defined $1;
                $month_temp = $2 if defined $2;
                $year_temp++  if ($month_temp-1 < localtime->mon());
                
                $programme{'date'} = "$day_temp.$month_temp.$year_temp";
                print "DATE: $programme{'date'}\n" if ( $verbose > 1 );
                next;
            }

            # exit the content information
            if ( $_ =~ /<\/table>/ ) {
                $header = 0;
                next;
            }
        }

        # extract content information
        if ( $_ =~ /<table id="content">/ ) {
            $content = 1;
            $year    = 0;
            next;
        }
        if ( $content > 0 ) {

            # get the title information
            if ( $_ =~ /<span.*>(.*)<\/span/ ) {
                $programme{'title'} = filter_xml_content("$1");
                print "TITLE: $programme{'title'}\n" if ( $verbose > 1 );
                next;
            }
            if ( $_ =~ /<br\/>/ ) {
                $content = 2;
                next;
            }

            # get the episode information
            if ( $content == 2 ) {
                my $episode_temp = filter_xml_content("$_");
                $programme{'episode'} = $episode_temp
                  if ( $episode_temp ne "" );
                print "EPISODE: $programme{'episode'}\n"
                  if ( defined $programme{'episode'} and $verbose > 1 );
                $content = 3;
                next;
            }
            if ( $content == 3 and $_ =~ /<p>/ ) {
                $year = 1;
                next;
            }

            # get the date (year information)
            if ( $year == 1 and $_ =~ /([0-9]{4})/ ) {
                $programme{'year'} = filter_xml_content("$1");
                print "YEAR: $programme{'year'}\n" if ( $verbose > 1 );
                $year = 0;
                next;
            }

            # additional information search
            if ( $_ =~ /img title="Film/ ) {
                print "cast Type: Film\n" if ( $verbose > 1 );
                $programme{'programmetype'} = "Film";
                next;
            }
            if ( $_ =~ /img title="Serie/ ) {
                print "cast Type: Serie\n" if ( $verbose > 1 );
                $programme{'programmetype'} = "Serie";
            }
            if ( $_ =~ /img title="Live/ ) {
                print "cast Type: Live\n" if ( $verbose > 1 );
                $programme{'programmetype'} = "Live";
                next;
            }
            if ( $_ =~ /img title="Dokumentation/ ) {
                print "cast Type: Dokumentation\n" if ( $verbose > 1 );
                $programme{'programmetype'} = "Dokumentation";
                next;
            }
            if ( $_ =~ /img title="Stereo/ ) {
                print "AUDIO=Stereo\n" if ( $verbose > 1 );
                $programme{'audio'} = "stereo";
                next;
            }
            if ( $_ =~ /img tile="16:9 video format/ ) {
                print "VIDEO=16:9 video format\n" if ( $verbose > 1 );
                $programme{'aspect'} = "16:9";
                next;
            }
            if ( $_ =~ /img title="Mehrsprachig/ ) {
                print "Multilangue: Mehrsprachig\n" if ( $verbose > 1 );
                $programme{'languages'} = "multi";
                next;
            }
            if ( $_ =~ /img title="High Definition Video/ ) {
                print "HDTV: High Definition Video\n" if ( $verbose > 1 );
                $programme{'quality'} = "HDTV";
                next;
            }
            if ( $_ =~ /img title="Surround Sound/ ) {
                print "Audio: Surround Sound\n" if ( $verbose > 1 );
                $programme{'audiotype'} = "surround";
                next;
            }

            # exit the content information
            if ( $_ =~ /<\/table>/ ) {
                $content = 0;
                next;
            }
        }

        # extract description information
        if ( $_ =~ /.*<div id="description">.*/ ) {
            $description = 1;
            $actors      = 0;
            next;
        }
        if ( $description == 1 ) {

            # extraction of the description
            if ( $_ =~ /<p>(.*)<\/p>/ ) {
                my $desc_temp = filter_xml_content("$1");
                $programme{'desc'} = $desc_temp if ($desc_temp ne "");
                print "DESC: $programme{'desc'}\n" if (defined $programme{'desc'} and $verbose > 1 );
                next;
            }

            # extraction of the begin end time
            if ( $_ =~ /Beginn:.*([0-9]{2}:[0-9]{2})<\/td>/ ) {
                $programme{'start'} = filter_xml_content("$1");
                print "\tTime Start: $programme{'start'}\n" if ( $verbose > 1 );
                next;
            }
            if ( $_ =~ /Ende:.*([0-9]{2}:[0-9]{2})<\/td>/ ) {
                $programme{'stop'} = filter_xml_content("$1");
                print "\tTime End: $programme{'stop'}\n" if ( $verbose > 1 );
                next;
            }

            # original title - use as subtitle
            if ( $originaltitle == 1 and $_ =~ /<span/ ) {
                print "Original Title: $programme{'sub-title'}\n"
                  if ( defined $programme{'sub-title'} and $verbose > 1 );
                $originaltitle = 0;
            }
            if ( $originaltitle == 1 ) {
                my $title_temp = filter_xml_content("$_");
                if ( not defined $programme{'sub-title'} ) {
                    $programme{'sub-title'} = $title_temp
                      if ( $title_temp ne "" );
                }
                else {
                    $programme{'sub-title'} =
                      "$programme{'sub-title'} $title_temp"
                      if ( $title_temp ne "" );
                }
                next;
            }
            if ( $_ =~ /<span.*>Orginaltitel:/ ) {
                $originaltitle = 1;
            }

            # extract actors
            if ( $actors == 1 and $_ =~ /<span/ ) {
                print "ACTORS: $programme{'actors'}\n"
                  if ( defined $programme{'actors'} and $verbose > 1 );
                $actors = 0;
            }
            if ( $actors == 1 ) {
                my $actor_temp = filter_xml_content("$_");
                if ( not defined $programme{'actors'} ) {
                    $programme{'actors'} = $actor_temp if ( $actor_temp ne "" );
                }
                else {
                    $programme{'actors'} = "$programme{'actors'} $actor_temp"
                      if ( $actor_temp ne "" );
                }
                next;
            }
            if ( $_ =~ /<span .*>Darsteller:/ ) {
                $actors = 1;
            }

            # extract producers
            if ( $producer == 1 and $_ =~ /<span/ ) {
                print "DIRECTOR: $programme{'director'}\n"
                  if ( defined $programme{'director'} and $verbose > 1 );
                $producer = 0;
            }
            if ( $producer == 1 ) {
                my $director_temp = filter_xml_content("$_");
                if ( not defined $programme{'director'} ) {
                    $programme{'director'} = $director_temp
                      if ( $director_temp ne "" );
                }
                else {
                    $programme{'director'} =
                      "$programme{'director'} $director_temp"
                      if ( $director_temp ne "" );
                }
                next;
            }
            if ( $_ =~ /<span .*>Regie:/ ) {
                $producer = 1;
            }

            # extract writer
            if ( $author == 1 and $_ =~ /<span/ ) {
                print "AUTHORS: $programme{'writer'}\n"
                  if ( defined $programme{'writer'} and $verbose > 1 );
                $author = 0;
            }
            if ( $author == 1 ) {
                my $writer_temp = filter_xml_content("$_");
                if ( not defined $programme{'writer'} ) {
                    $programme{'writer'} = $writer_temp
                      if ( $writer_temp ne "" );
                }
                else {
                    $programme{'writer'} = "$programme{'writer'} $writer_temp"
                      if ( $writer_temp ne "" );
                }
                next;
            }
            if ( $_ =~ /<span .*>Autor:/ ) {
                $author = 1;
            }

            # category
            if ( $_ =~ /<span .*>Kategorie:.*<\/span>(.*)<br \/>/ ) {
                my $category_temp = filter_xml_content("$1");
                $programme{'category'} = $category_temp if $category_temp ne "";
                print "Category: $1\n"
                  if ( defined $programme{'category'} and ( $verbose > 1 ) );
                next;
            }

            # extract country
            if ( $land == 1 and $_ =~ /<span/ ) {
                print "LAND: $programme{'country'}\n"
                  if ( defined $programme{'country'} and $verbose > 1 );
                $land = 0;
            }
            if ( $land == 1 ) {
                my $country_temp = filter_xml_content("$_");
                if ( not defined $programme{'country'} ) {
                    $programme{'country'} = $country_temp
                      if ( $country_temp ne "" );
                }
                else {
                    $programme{'country'} =
                      "$programme{'country'} $country_temp"
                      if ( $country_temp ne "" );
                }
                next;
            }
            if ( $_ =~ /<span .*>Land:/ ) {
                $land = 1;
            }

            # Produzent
            if ( $productor == 1 and $_ =~ /<span/ ) {
                print "LAND: $programme{'producer'}\n"
                  if ( defined $programme{'producer'} and $verbose > 1 );
                $productor = 0;
            }
            if ( $productor == 1 ) {
                my $producer_temp = filter_xml_content("$_");
                if ( not defined $programme{'producer'} ) {
                    $programme{'producer'} = $producer_temp
                      if ( $producer_temp ne "" );
                }
                else {
                    $programme{'producer'} =
                      "$programme{'producer'} $producer_temp"
                      if ( $producer_temp ne "" );
                }
                next;
            }
            if ( $_ =~ /<span .*>Produzent:/ ) {
                $productor = 1;
            }

            # Drehbuch
            if ( $script == 1 and $_ =~ /<span/ ) {
                print "SCRIPT: $programme{'writer'}\n"
                  if ( defined $programme{'writer'} and $verbose > 1 );
                $script = 0;
            }
            if ( $script == 1 ) {
                my $writer_temp = filter_xml_content("$_");
                if ( not defined $programme{'writer'} ) {
                    $programme{'writer'} = $writer_temp
                      if ( $writer_temp ne "" );
                }
                else {
                    $programme{'writer'} = "$programme{'writer'} $writer_temp"
                      if ( $writer_temp ne "" );
                }
                next;
            }
            if ( $_ =~ /<span .*>Autor:/ ) {
                $script = 1;
            }

            # exit the description information
            if ( $_ =~ /.*<\/div>.*/ ) {
                $description = 0;
                next;
            }
        }
    }

    # add the parsed programm to the programm list
    $programme{'idfilename'} = "$idfilename" if $maketestonerror;
    push( @programmelist, \%programme );
}

# parse_channel($refonlines)
#   returns $success, if one channel of this group is in the valid channels list
sub parse_channel($) {
    my @lines = @{ shift @_ };
    my $channelid;
    my $channame;
    my $chanlogolink = "";
    my %chaninfo     = ();
    my $returnCode   = -1;

    foreach (@lines) {

#<a title="Zum Wochenprogramm für SF 1"
#href="/cbc/program/week/24">
#<span class="left"><img src="http://media.tvtv.de/mediaserver/resize?type=channellogo&format=boxed&size=40x21&imageName=24.jpg" /></span>
#<span class="header_text">SF 1</span>
#</a>
#first grab the link and id
        if ( $_ =~ /<img src="(.*channellogo.*)"/ ) {
            $chanlogolink = $1;
            $chanlogolink =~ m/.*imageName=(\d+)/;
            $channelid = $1;
        }

        #name name is next
        if ( $_ =~ /<span class="header_text">(.*)</ ) {
            $channame = $1;
        }

        #only save valid data
        if ( defined $channame && defined $channelid ) {
            $channame = $1;

            # only save channels which are in the config file
            next
              if (  ( not $configure )
                and ( not grep { $_ == $channelid } @validchannels ) );

            # report found channel
            $returnCode = $success;

            # only save channels which are not already in the list
            next if ( grep { ${$_}{'id'} == $channelid } @channellist );

            $chaninfo{'id'}   = $channelid;
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

            undef $channame;
            undef $channelid;
            $chanlogolink = "";
        }
    }
    return $returnCode;
}

#sub copyfiletotest($filename)
sub copyfiletotest($) {
    my $filename = shift;

    print("error parse in file> $filename\n");
    copy( "$filename", "$testdir/" . basename("$filename") );
}

# this function display all the channels available on the given website...
sub write_channels() {
    my $nbrchan     = @channellist;
    my $channelid   = '';
    my $channelname = '';

    print "/------------------------------------------\\\n";
    print "| Channel List                             |\n";
    print "\------------------------------------------/\n";
    print "from: $commonurl...\nto: $configurefile\n";

    open( WF, ">$configurefile" )
      or ( warn "could not create the $configurefile file $!" and die );

    foreach (@channellist) {

        $channelid   = ${$_}{'id'};
        $channelname = ${$_}{'name'};

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
sub filter_xml_content($) {
    my $line = shift;

    # look for undef
    return undef if not defined $line;

    # cut tailing newline
    chomp $line;

    # filter the content for unwanted chars
    $line =~ s/<.*?>//g;
    $line =~ s/>(.*)</$1/g;
    $line =~ s/&/&amp;/g;
    $line =~ s/c\<t/c't/g;
    $line =~ s/<//g;
    $line =~ s/>//g;

    #remove all tabs and spaces
    #$line =~ s/\t//g;
    $line =~ s/^\s+|\s+$//g;

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
    xml_print(
        "<tv generator-info-name=\"yatvgrabber\" source-info-url=\"$commonurl\">");
}

sub xml_close() {
    xml_print("</tv>");
    close(XMLFILE) if ($output);
}

# create the head of the xml file
#   containing the channels with icons
sub xml_print_channel($) {
    my %chaninfo     = %{ shift @_ };
    my $channelid    = $chaninfo{'id'};
    my $channelname  = $chaninfo{'name'};
    my $chanlogolink = $chaninfo{'link'};

    xml_print("\t\<channel id=\"${channelid}\"\>");
    xml_print(
        "\t\t\<display-name lang=\"$language\"\>$channelname\<\/display-name\>"
    );
    #xml_print("\t\t\<icon src=\"${chanlogolink}\"\/\>");
    xml_print("\t\<\/channel\>");
}

# create bonus entries
# this function checks if there are more information contained in the programme hash table, like
# actors, description, subtitle, original title, producer, writer, audio format video format, ...
#
# sub xml_print_additional_materials($aProgrammeReference)
sub xml_print_additional_materials($) {
    my %programme = %{ shift @_ };

    # non mandatory parameters... Bonus if it's existing
    # sub title, original title
    xml_print("\t\t\<sub-title lang=\"${language}\"\>$programme{'sub-title'}\<\/sub-title\>") if defined $programme{'sub-title'};

    # description
    xml_print("\t\t\<desc lang=\"${language}\"\>$programme{'desc'}\<\/desc\>") if defined $programme{'desc'};

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
            foreach ( split( ', ', $programme{'actors'} ) ) {
                xml_print("\t\t\t\<actor\>$_\<\/actor\>");
            }
        }
        xml_print("\t\t\t\<director\>$programme{'director'}\<\/director\>")
          if ( defined $programme{'director'} );
        xml_print("\t\t\t\<writer\>$programme{'writer'}\<\/writer\>")
          if ( defined $programme{'writer'} );
        xml_print("\t\t\t\<adapter\>$programme{'adapter'}\<\/adapter\>")
          if ( defined $programme{'adapter'} );
        xml_print("\t\t\t\<producer\>$programme{'producer'}\<\/producer\>")
          if ( defined $programme{'producer'} );
        xml_print("\t\t\t\<presenter\>$programme{'presenter'}\<\/presenter\>")
          if ( defined $programme{'presenter'} );
        xml_print(
            "\t\t\t\<commentator\>$programme{'commentator'}\<\/commentator\>")
          if ( defined $programme{'commentator'} );
        xml_print("\t\t\t\<guest\>$programme{'guest'}\<\/guest\>")
          if ( defined $programme{'guest'} );
        xml_print("\t\t\<\/credits\>");
    }

    if ( defined $programme{'audio'} or defined $programme{'audiotype'} ) {
        xml_print("\t\t\<audio\>");
        xml_print("\t\t\t\<stereo\>$programme{'audio'}\<\/stereo\>")
          if defined $programme{'audio'};
        xml_print("\t\t\t\<stereo\>$programme{'audiotype'}\<\/stereo\>")
          if defined $programme{'audiotype'};
        xml_print("\t\t\<\/audio\>");
    }
    if ( defined $programme{'aspect'} or defined $programme{'quality'} ) {
        xml_print("\t\t\<video\>");
        xml_print("\t\t\t\<aspect\>$programme{'aspect'}\<\/aspect\>")
          if defined $programme{'aspect'};
        xml_print("\t\t\t\<quality\>$programme{'quality'}\<\/quality\>")
          if defined $programme{'quality'};
        xml_print("\t\t\<\/video\>");
    }

    # filming country
    xml_print(
        "\t\t\<country lang=\"${language}\"\>$programme{'country'}\<\/country\>"
    ) if ( defined $programme{'country'} );
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
    my %programme = %{ shift @_ };

    # locals
    my $year          = 0;
    my $date          = '';
    my $channelid     = $programme{'channelid'};  # channel id is always defined
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
        xml_print(
"\t\<programme start=\"${date}${start}\" stop=\"${date}${end}\" channel=\"${channelid}\"\>"
        );
        xml_print("\t\t\<title lang=\"${language}\"\>${title}\<\/title\>");

        xml_print("\t\t\<date\>$programme{'year'}\<\/date>")
          if ( defined $programme{'year'} );
        foreach ( split( ', ', $category ) ) {
            xml_print("\t\t\<category lang=\"${language}\"\>$_\<\/category\>");
        }
        xml_print_additional_materials( \%programme );
        xml_print("\t\<\/programme\>");
    }
    else {
        warn(
"some mandatory keys are missing take a look to the following hash: warning nr: $warning\n"
        );
        foreach ( keys(%programme) ) {
            print STDERR "key: $_ -> $programme{$_}\n";
        }
        copyfiletotest( $programme{'idfilename'} ) if ($maketestonerror);
    }
}

# main function to write the xml information
#   writes the header, channels info, programs to the
#	xml file (at this order)
sub xml_write() {

    my $channelid;

    #join all threaded channel parsers
    foreach ( threads->list() ) {
        $_->join();
    }

    xml_init();

    foreach (@channellist) {
        $channelid = ${$_}{'id'};
        xml_print_channel($_) if ( defined $channelid );
    }
    foreach (@programmelist) {
        $channelid = ${$_}{'channelid'};
        xml_print_programme($_) if ( defined $channelid );
    }

    xml_close();
}
