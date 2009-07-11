# this file contains the regular expression which is depending on the country
# the format for defining a regular expression is the following:
#
# [name_used_in_the_hash]=a_regula_expression
#
# for example:
# [presenter]=fn-w8".*>Präsentiert von:.*
#
# this file will be loaded and parsed in the grabtv.pl script, the result is a hash table containing the regular expression
# one advantage is the flexibility, everybody can extend the regular expression if the webpage changes, without having to 
# start modifying the graptv.pl script.

[baseurl]=http://cablecom.tvtv.ch

#
# Program parser regexp
#

[channelid]=s.prop16="[^\(]+\((\d+)\)".*
[programmetype]=(Film|Serie)
[title]=fb-b15">(.*)<\/span.*
[episode]=fn-b9">(.*)<\/span.*
[description]=fn-b10">(.*)<\/span.*
[date]=fn-w8".*>(.*),\s+(\d+.\d+.\d+)<\/t.*
[starts]=fn-b8".*>Beginn:\s+(\d+:\d+).*<\/t.*
[stops]=fn-b8".*>Ende:\s+(\d+:\d+).*<\/t.*
[duration]=fn-b8".*>Länge:\s+(\d+).*<\/t.*
[actors]=fn-w8".*>Darsteller:.*
[producers]=fn-w8".*>Regie:.* 
[authors]=fn-w8".*>Autor:.*
[category]=fn-w8".*>Kategorie:.*
[country]=fn-w8".*>Land:.*
[rating]=fn-w8".*>FSK:.*
[filmeditor]=fn-w8".*>Film Editor:.*
[studio]=fn-w8".*>Produktion:.*
[producer]=fn-w8".*>Produzent:.*
[writer]=fn-w8".*>Drehbuch:.*
[music]=fn-w8".*>Musik:.*
[camera]=fn-w8".*>Kamera:.*
[sub-title]=fn-w8".*>Orginaltitel:.*
[presenter]=fn-w8".*>Präsentiert von:.*
[musicchef]=fn-w8".*>Musikalische Leitung:.*
[audio]=Stereo
[aspect]=16:9 video format
[languages]=Mehrsprachig
[quality]=High Definition Video
[audiotype]=Surround Sound
# this regular expression is used for several multiline capture like actors, producers, authors, ...
[multiline]=.*fn-b8">(.*)<\/span.*


#
# Channels parser regexp
#
