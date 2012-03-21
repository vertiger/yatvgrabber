-- phpMyAdmin SQL Dump
-- version 3.4.5deb1
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Mar 18, 2012 at 03:11 PM
-- Server version: 5.1.61
-- PHP Version: 5.3.6-13ubuntu3.6

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `mythconverg`
--

-- --------------------------------------------------------

--
-- Table structure for table `channel`
--

CREATE TABLE IF NOT EXISTS `channel` (
  `chanid` int(10) unsigned NOT NULL DEFAULT '0',
  `channum` varchar(10) NOT NULL DEFAULT '',
  `freqid` varchar(10) DEFAULT NULL,
  `sourceid` int(10) unsigned DEFAULT NULL,
  `callsign` varchar(20) NOT NULL DEFAULT '',
  `name` varchar(64) NOT NULL DEFAULT '',
  `icon` varchar(255) NOT NULL DEFAULT 'none',
  `finetune` int(11) DEFAULT NULL,
  `videofilters` varchar(255) NOT NULL DEFAULT '',
  `xmltvid` varchar(64) NOT NULL DEFAULT '',
  `recpriority` int(10) NOT NULL DEFAULT '0',
  `contrast` int(11) DEFAULT '32768',
  `brightness` int(11) DEFAULT '32768',
  `colour` int(11) DEFAULT '32768',
  `hue` int(11) DEFAULT '32768',
  `tvformat` varchar(10) NOT NULL DEFAULT 'Default',
  `visible` tinyint(1) NOT NULL DEFAULT '1',
  `outputfilters` varchar(255) NOT NULL DEFAULT '',
  `useonairguide` tinyint(1) DEFAULT '0',
  `mplexid` smallint(6) DEFAULT NULL,
  `serviceid` mediumint(8) unsigned DEFAULT NULL,
  `tmoffset` int(11) NOT NULL DEFAULT '0',
  `atsc_major_chan` int(10) unsigned NOT NULL DEFAULT '0',
  `atsc_minor_chan` int(10) unsigned NOT NULL DEFAULT '0',
  `last_record` datetime NOT NULL,
  `default_authority` varchar(32) NOT NULL DEFAULT '',
  `commmethod` int(11) NOT NULL DEFAULT '-1',
  PRIMARY KEY (`chanid`),
  KEY `channel_src` (`channum`,`sourceid`),
  KEY `sourceid` (`sourceid`,`xmltvid`,`chanid`),
  KEY `visible` (`visible`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Dumping data for table `channel`
--

INSERT INTO `channel` (`chanid`, `channum`, `freqid`, `sourceid`, `callsign`, `name`, `icon`, `finetune`, `videofilters`, `xmltvid`, `recpriority`, `contrast`, `brightness`, `colour`, `hue`, `tvformat`, `visible`, `outputfilters`, `useonairguide`, `mplexid`, `serviceid`, `tmoffset`, `atsc_major_chan`, `atsc_minor_chan`, `last_record`, `default_authority`, `commmethod`) VALUES
(29721, '28721', '40', 1, 'EinsExtra', 'EinsExtra', '', 0, '', '962', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 2, 28721, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29722, '28722', '40', 1, 'Einsfestival', 'Einsfestival', '', 0, '', '955', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 2, 28722, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29723, '28723', '40', 1, 'EinsPlus', 'EinsPlus', '', 0, '', '956', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 2, 28723, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29724, '28724', '40', 1, 'arte', 'arte', '', 0, '', '10', 0, 32768, 32768, 32768, 32768, '', 0, '', 0, 2, 28724, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29725, '28725', '40', 1, 'PHOENIX', 'PHOENIX', '', 0, '', '206', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 2, 28725, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(1901, '901', '22', 1, 'SF 1', 'SF 1', '', 0, '', '24', 0, 32768, 32768, 32768, 32768, '', 0, '', 0, 5, 901, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(1907, '907', '22', 1, 'SF zwei', 'SF zwei', '', 0, '', '900', 0, 32768, 32768, 32768, 32768, '', 0, '', 0, 5, 907, 0, 0, 0, '2012-03-04 01:51:01', '', -1),
(1911, '911', '22', 1, 'SF info', 'SF info', '', 0, '', '820', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 5, 911, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(1921, '921', '23', 1, 'SRG-DRS 1', 'SRG-DRS 1', '', 0, '', '', 0, 32768, 32768, 32768, 32768, '', 1, '', 1, 6, 921, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(1922, '922', '23', 1, 'SRG-DRS 2', 'SRG-DRS 2', '', 0, '', '', 0, 32768, 32768, 32768, 32768, '', 1, '', 1, 6, 922, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(1923, '923', '23', 1, 'SRG-DRS 3', 'SRG-DRS 3', '', 0, '', '', 0, 32768, 32768, 32768, 32768, '', 1, '', 1, 6, 923, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(1924, '924', '23', 1, 'SRG-DRS Virus', 'SRG-DRS Virus', '', 0, '', '', 0, 32768, 32768, 32768, 32768, '', 1, '', 1, 6, 924, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(1934, '934', '23', 1, 'SRG-Swiss Classic', 'SRG-Swiss Classic', '', 0, '', '', 0, 32768, 32768, 32768, 32768, '', 1, '', 1, 6, 934, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(1935, '935', '23', 1, 'SRG-Swiss Pop', 'SRG-Swiss Pop', '', 0, '', '', 0, 32768, 32768, 32768, 32768, '', 1, '', 1, 6, 935, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(1936, '936', '23', 1, 'SRG-Swiss Jazz', 'SRG-Swiss Jazz', '', 0, '', '', 0, 32768, 32768, 32768, 32768, '', 1, '', 1, 6, 936, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(1937, '937', '23', 1, 'SRG-DRS 4 News', 'SRG-DRS 4 News', '', 0, '', '', 0, 32768, 32768, 32768, 32768, '', 1, '', 1, 6, 937, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(2793, '1793', '23', 1, 'D VIERTE', 'DAS VIERTE', '', 0, '', '885', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 6, 1793, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(15039, '14039', '23', 1, 'SSR-CH-Classique', 'SSR-CH-Classique', '', 0, '', '', 0, 32768, 32768, 32768, 32768, '', 1, '', 1, 6, 14039, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(32200, '31200', '23', 1, 'Eurosport', 'Eurosport Deutschland', '', 0, '', '107', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 6, 31200, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(32220, '31220', '23', 1, 'EuroNews', 'EuroNews', '', 0, '', '13', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 6, 31220, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(1051, '51', '24', 1, 'TELE 5', 'TELE 5', '', 0, '', '105', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 7, 51, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(1063, '63', '24', 1, 'DMAX', 'DMAX', '', 0, '', '227', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 7, 63, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(1900, '900', '24', 1, 'SPORT1', 'SPORT1', '', 0, '', '12', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 7, 900, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(21001, '20001', '24', 1, 'ProSieben Schweiz', 'ProSieben Schweiz', '', 0, '', '855', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 7, 20001, 0, 0, 0, '2012-03-13 01:38:55', '', -1),
(21003, '20003', '24', 1, 'Kabel 1 Schweiz', 'Kabel 1 Schweiz', '', 0, '', '3838', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 7, 20003, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(21006, '20006', '24', 1, 'SAT.1 CH', 'SAT.1 CH', '', 0, '', '832', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 7, 20006, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(13503, '12503', '25', 1, 'Schweiz 5', 'Schweiz 5', '', 0, '', '1080', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 8, 12503, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29433, '28433', '25', 1, 'MDR SPUTNIK', 'MDR SPUTNIK', '', 0, '', '', 0, 32768, 32768, 32768, 32768, '', 1, '', 1, 8, 28433, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29440, '28440', '25', 1, 'N-JOY', 'N-JOY', '', 0, '', '', 0, 32768, 32768, 32768, 32768, '', 1, '', 1, 8, 28440, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29456, '28456', '25', 1, 'radioeins', 'radioeins', '', 0, '', '', 0, 32768, 32768, 32768, 32768, '', 1, '', 1, 8, 28456, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29457, '28457', '25', 1, 'Fritz', 'Fritz', '', 0, '', '', 0, 32768, 32768, 32768, 32768, '', 1, '', 1, 8, 28457, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(14001, '13001', '26', 1, 'ORF eins', 'ORF eins', '', 0, '', '14', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 9, 13001, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(14009, '13009', '26', 1, 'ORF 2', 'ORF 2', '', 0, '', '15', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 9, 13009, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29522, '28522', '26', 1, 'CNN Int.', 'CNN Int.', '', 0, '', '2025', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 9, 28522, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29106, '28106', '27', 1, 'Das Erste', 'Das Erste', '', 0, '', '1', 0, 32768, 32768, 32768, 32768, '', 0, '', 0, 10, 28106, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29108, '28108', '27', 1, 'hr-fernsehen', 'hr-fernsehen', '', 0, '', '26', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 10, 28108, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29111, '28111', '27', 1, 'WDR Köln', 'WDR Köln', '', 0, '', '17', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 10, 28111, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29112, '28112', '27', 1, 'BR-alpha', 'BR-alpha', '', 0, '', '57', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 10, 28112, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29113, '28113', '27', 1, 'SWR Fernsehen BW', 'SWR Fernsehen BW', '', 0, '', '29', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 10, 28113, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(13508, '12508', '28', 1, 'MTV Schweiz', 'MTV Schweiz', '', 0, '', '3968', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 11, 12508, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(1049, '49', '31', 1, 'M6 Suisse', 'M6 Suisse', '', 0, '', '2510', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 14, 49, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(7301, '6301', '32', 1, 'BBC 1 London', 'BBC 1 London', '', 0, '', '2008', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 15, 6301, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(7302, '6302', '32', 1, 'BBC 2 England', 'BBC 2 England', '', 0, '', '2009', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 15, 6302, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(7317, '6317', '32', 1, 'CBBC Channel', 'CBBC Channel', '', 0, '', '2182', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 15, 6317, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(7335, '6335', '32', 1, 'Channel 5', 'Channel 5', '', 0, '', '', 0, 32768, 32768, 32768, 32768, '', 1, '', 1, 15, 6335, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(1015, '15', '33', 1, '3+', '3+', '', 0, '', '710', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 16, 15, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29006, '28006', '33', 1, 'ZDF', 'ZDF', '', 0, '', '2', 0, 32768, 32768, 32768, 32768, '', 0, '', 0, 16, 28006, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29007, '28007', '33', 1, '3sat', '3sat', '', 0, '', '118', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 16, 28007, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29008, '28008', '33', 1, 'KiKA', 'KiKA', '', 0, '', '63', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 16, 28008, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29011, '28011', '33', 1, 'ZDFinfo', 'ZDFinfo', '', 0, '', '963', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 16, 28011, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29014, '28014', '33', 1, 'zdf_neo', 'zdf_neo', '', 0, '', '4130', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 16, 28014, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29016, '28016', '33', 1, 'zdf.kultur', 'zdf.kultur', '', 0, '', '', 0, 32768, 32768, 32768, 32768, '', 1, '', 1, 16, 28016, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29396, '28396', '34', 1, 'Einsfestival HD', 'Einsfestival HD', '', 0, '', '', 0, 32768, 32768, 32768, 32768, '', 1, '', 1, 17, 28396, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(13020, '12020', '35', 1, 'RTL2', 'RTL2', '', 0, '', '9', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 24, 12020, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(13041, '12041', '35', 1, 'SUPER RTL CH', 'SUPER RTL CH', '', 0, '', '179', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 24, 12041, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(13061, '12061', '35', 1, 'VOX CH', 'VOX CH', '', 0, '', '11', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 24, 12061, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(13080, '12080', '35', 1, 'Channel 21', 'Channel 21', '', 0, '', '', 0, 32768, 32768, 32768, 32768, '', 1, '', 1, 24, 12080, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(13090, '12090', '35', 1, 'n-tv', 'n-tv', '', 0, '', '7', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 24, 12090, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(12120, '11120', '36', 1, 'arte HD', 'arte HD', '', 0, '', '3832', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 18, 11120, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(34197, '33197', '36', 1, 'Sunshine', 'Sunshine', '', 0, '', '', 0, 32768, 32768, 32768, 32768, '', 1, '', 1, 18, 33197, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(7940, '6940', '37', 1, 'BBC HD', 'BBC HD', '', 0, '', '3793', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 19, 6940, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(13502, '12502', '37', 1, 'Nick Comedy Schweiz', 'Nick Comedy Schweiz', '', 0, '', '882', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 19, 12502, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(5913, '4913', '38', 1, 'ServusTV', 'ServusTV HD Oesterreich', '', 0, '', '4119', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 20, 4913, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(29206, '28206', '38', 1, 'rbb Berlin', 'rbb Berlin', '', 0, '', '3528', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 20, 28206, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(62202, '61202', '38', 1, 'ANIXE HD', 'ANIXE HD', '', 0, '', '', 0, 32768, 32768, 32768, 32768, '', 1, '', 1, 20, 61202, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(14101, '13101', '39', 1, 'ORF III', 'ORF III', '', 0, '', '', 0, 32768, 32768, 32768, 32768, '', 1, '', 1, 21, 13101, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(18503, '17503', '39', 1, 'N24', 'N24', '', 0, '', '953', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 21, 17503, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(12100, '11100', '40', 1, 'Das Erste HD', 'Das Erste HD', '', 0, '', '4162', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 22, 11100, 0, 0, 0, '2012-03-10 23:11:01', '', -1),
(12110, '11110', '40', 1, 'ZDF HD', 'ZDF HD', '', 0, '', '4163', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 22, 11110, 0, 0, 0, '2012-03-12 01:28:01', '', -1),
(18201, '17201', '48', 1, 'SF 1 HD', 'SF 1 HD', '', 0, '', '24', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 25, 17201, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(18202, '17202', '48', 1, 'SF zwei HD', 'SF zwei HD', '', 0, '', '900', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 25, 17202, 0, 0, 0, '2012-03-14 23:41:29', '', -1),
(11030, '10030', '31', 1, 'CNBC Europe', 'CNBC Europe', '', 0, '', '2024', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 14, 10030, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(11050, '10050', '31', 1, 'BBC World', 'BBC World', '', 0, '', '112', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 14, 10050, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(11060, '10060', '31', 1, 'TV5MONDE EUROPE', 'TV5MONDE EUROPE', '', 0, '', '2559', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 14, 10060, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(1001, '1', '36', 1, 'SSF', 'SSF', '', 0, '', '4106', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 18, 1, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(1002, '2', '40', 1, 'ITV1 London', 'ITV1 London', '', 0, '', '2017', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 22, 10060, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(11070, '10070', '40', 1, 'ITV2', 'ITV2', '', 0, '', '2035', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 22, 10070, 0, 0, 0, '0000-00-00 00:00:00', '', -1),
(13353, '35-12003', '35', 1, 'RTL Television', 'RTL Television', '', 0, '', '4', 0, 32768, 32768, 32768, 32768, '', 1, '', 0, 24, 12003, 0, 0, 0, '0000-00-00 00:00:00', '', -1);

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;