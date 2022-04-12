
# -*- coding: utf-8 -*-

# Copyright (C) 2011-2012 WikiTeam
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# DumpGenerator.py is a script to generate backups of MediaWiki wikis
# To learn more, read the documentation:
#        http://code.google.com/p/wikiteam/wiki/NewTutorial
import datetime
import pickle
import urllib
# import urlparse
import re
import wikipedia as pywikibot
import getopt

from hashlib import md5
import os
import re
import subprocess
import sys
import time
import urllib
import os
from shove import Shove

file_store = Shove('file://mystore')


def saveName(title):
    name = urllib.unquote(title)
    file_store[name] = title


def isNewTitle(name):
    name = urllib.unquote(name)
    try:
        if (file_store[name]):
            print
            "Skipping %s" % name
            return 0
        else:
            return 1
    except KeyError:
        print
        "not seen %s" % name
        return 1


#    except:
#       print "other except"
#        return 1


def truncateFilename(other={}, filename=''):
    """  """
    return filename[:other['filenamelimit']] + md5(filename).hexdigest() + '.' + filename.split('.')[-1]


def delay(config={}):
    """  """
    if config['delay'] > 0:
        print
        'Sleeping... %d seconds...' % (config['delay'])
        time.sleep(config['delay'])


def cleanHTML(raw=''):
    """  """
    # <!-- bodytext --> <!-- /bodytext -->
    # <!-- start content --> <!-- end content -->
    # <!-- Begin Content Area --> <!-- End Content Area -->
    # <!-- content --> <!-- mw_content -->
    if re.search('<!-- bodytext -->', raw):
        raw = raw.split('<!-- bodytext -->')[1].split('<!-- /bodytext -->')[0]
    elif re.search('<!-- start content -->', raw):
        raw = raw.split('<!-- start content -->')[1].split('<!-- end content -->')[0]
    elif re.search('<!-- Begin Content Area -->', raw):
        raw = raw.split('<!-- Begin Content Area -->')[1].split('<!-- End Content Area -->')[0]
    elif re.search('<!-- content -->', raw):
        raw = raw.split('<!-- content -->')[1].split('<!-- mw_content -->')[0]
    elif re.search('<article id="WikiaMainContent" class="WikiaMainContent">', raw):
        raw = raw.split('<article id="WikiaMainContent" class="WikiaMainContent">')[1].split('</article>')[0]
    else:
        print
        raw[:250]
        print
        'This wiki doesn\'t use marks to split content'
        sys.exit()
    return raw


def getNamespaces(config={}):
    """ Hackishly gets the list of namespaces names and ids from the dropdown in the HTML of Special:AllPages. Function called if no API is available. """
    namespaces = config['namespaces']
    namespacenames = {0: ''}  # main is 0, no prefix
    if namespaces:
        req = urllib.Request(url=config['index'], data=urllib.urlencode({'title': 'Special:Allpages', }),
                              headers={'User-Agent': getUserAgent()})
        f = urllib.urlopen(req)
        raw = f.read()
        f.close()

        m = re.compile(r'<option [^>]*?value="(?P<namespaceid>\d+)"[^>]*?>(?P<namespacename>[^<]+)</option>').finditer(
            raw)  # [^>]*? to include selected="selected"
        if 'all' in namespaces:
            namespaces = []
            for i in m:
                namespaces.append(int(i.group("namespaceid")))
                namespacenames[int(i.group("namespaceid"))] = i.group("namespacename")
        else:
            # check if those namespaces really exist in this wiki
            namespaces2 = []
            for i in m:
                if int(i.group("namespaceid")) in namespaces:
                    namespaces2.append(int(i.group("namespaceid")))
                    namespacenames[int(i.group("namespaceid"))] = i.group("namespacename")
            namespaces = namespaces2
    else:
        namespaces = [0]

    # retrieve all titles from Special:Allpages, if the wiki is big, perhaps there are sub-Allpages to explore
    namespaces = [i for i in set(namespaces)]  # uniques
    #    print '%d namespaces found' % (len(namespaces))
    return namespaces, namespacenames


def getPageTitlesAPI(config={}):
    """ Uses the API to get the list of page titles """
    titles = []
    site = pywikibot.getSite()
    # titles += getTitles(site, config)
    return titles


def getPageTitlesScrapper(config={}):
    """  """
    titles = []
    namespaces, namespacenames = getNamespaces(config=config)
    for namespace in namespaces:
        print
        '    Retrieving titles in the namespace', namespace
        url = '%s?title=Special:Allpages&namespace=%s' % (config['index'], namespace)
        raw = urllib.urlopen(url).read()
        raw = cleanHTML(raw)

        r_title = r'title="(?P<title>[^>]+)">'
        r_suballpages = ''
        r_suballpages1 = r'&amp;from=(?P<from>[^>]+)&amp;to=(?P<to>[^>]+)">'
        r_suballpages2 = r'Special:Allpages/(?P<from>[^>]+)">'
        if re.search(r_suballpages1, raw):
            r_suballpages = r_suballpages1
        elif re.search(r_suballpages2, raw):
            r_suballpages = r_suballpages2
        else:
            pass  # perhaps no subpages

        deep = 3  # 3 is the current deep of English Wikipedia for Special:Allpages, 3 levels
        c = 0
        checked_suballpages = []
        rawacum = raw
        while r_suballpages and re.search(r_suballpages, raw) and c < deep:
            # load sub-Allpages
            m = re.compile(r_suballpages).finditer(raw)
            for i in m:
                fr = i.group('from')

                if r_suballpages == r_suballpages1:
                    to = i.group('to')
                    name = '%s-%s' % (fr, to)
                    url = '%s?title=Special:Allpages&namespace=%s&from=%s&to=%s' % (
                    config['index'], namespace, fr, to)  # do not put urllib.quote in fr or to
                elif r_suballpages == r_suballpages2:  # fix, esta regexp no carga bien todas? o falla el r_title en este tipo de subpag? (wikiindex)
                    fr = fr.split('&amp;namespace=')[0]  # clean &amp;namespace=\d, sometimes happens
                    name = fr
                    url = '%s?title=Special:Allpages/%s&namespace=%s' % (config['index'], name, namespace)

                if not name in checked_suballpages:
                    checked_suballpages.append(name)  # to avoid reload dupe subpages links
                    raw2 = urllib.urlopen(url).read()
                    raw2 = cleanHTML(raw2)
                    rawacum += raw2  # merge it after removed junk
                    print
                    '    Reading', name, len(raw2), 'bytes', len(re.findall(r_suballpages, raw2)), 'subpages', len(
                        re.findall(r_title, raw2)), 'pages'
            c += 1

        c = 0
        m = re.compile(r_title).finditer(rawacum)
        for i in m:
            if not i.group('title').startswith('Special:'):
                if not i.group('title') in titles:
                    titles.append(undoHTMLEntities(text=i.group('title')))
                    c += 1
    #        print '    %d titles retrieved in the namespace %d' % (c, namespace)
    return titles


def getPageTitles(config={}):
    """  """

    print
    'Loading page titles from namespaces = %s' % (
                config['namespaces'] and ','.join([str(i) for i in config['namespaces']]) or 'None')
    print
    'Excluding titles from namespaces = %s' % (
                config['exnamespaces'] and ','.join([str(i) for i in config['exnamespaces']]) or 'None')

    titles = []
    if config['api']:
        titles = getPageTitlesAPI(config=config)
    elif config['index']:
        titles = getPageTitlesScrapper(config=config)

    titles = list(set(
        titles))  # removing dupes (e.g. in CZ appears Widget:AddThis two times (main namespace and widget namespace))
    titles.sort()  # sorting

    print
    '%d page titles loaded' % (len(titles))
    return titles


def getXMLHeader(config={}):
    """ Retrieve a random page to extract XML headers (namespace info, etc) """
    # get the header of a random page, to attach it in the complete XML backup
    # similar to: <mediawiki xmlns="http://www.mediawiki.org/xml/export-0.3/" xmlns:x....
    randomtitle = 'Main_Page'  # previously AMF5LKE43MNFGHKSDMRTJ
    xml = getXMLPage(config=config, title=randomtitle, verbose=False)
    header = xml.split('</mediawiki>')[0]
    if not xml:
        print
        'XML export on this wiki is broken, quitting.'
        sys.exit()
    return header


def getXMLFileDesc(config={}, title=''):
    """  """
    config['curonly'] = 1  # tricky to get only the most recent desc
    return getXMLPage(config=config, title=title, verbose=False)


def getUserAgent():
    """ Return a cool user-agent to hide Python user-agent """
    useragents = ['Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.0.4) Gecko/20060508 Firefox/1.5.0.4']
    return useragents[0]


def logerror(config={}, text=''):
    """  """
    if text:
        f = open('%s/errors.log' % (config['path']), 'a')
        f.write('%s: %s\n' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), text))
        f.close()


def getXMLPageCore(headers={}, params={}, config={}):
    """  """
    # returns a XML containing params['limit'] revisions (or current only), ending in </mediawiki>
    # if retrieving params['limit'] revisions fails, returns a current only version
    # if all fail, returns the empty string
    xml = ''
    c = 0
    maxseconds = 100  # max seconds to wait in a single sleeping
    maxretries = 5  # x retries and skip
    increment = 20  # increment every retry
    while not re.search(r'</mediawiki>', xml):
        if c > 0 and c < maxretries:
            wait = increment * c < maxseconds and increment * c or maxseconds  # incremental until maxseconds
            print
            '    XML for "%s" is wrong. Waiting %d seconds and reloading...' % (params['pages'], wait)
            time.sleep(wait)
            if params[
                'limit'] > 1:  # reducing server load requesting smallest chunks (if curonly then limit = 1 from mother function)
                params['limit'] = params['limit'] / 2  # half
        if c >= maxretries:
            print
            '    We have retried %d times' % (c)
            print
            '    MediaWiki error for "%s", network error or whatever...' % (params['pages'])
            # If it's not already what we tried: our last chance, preserve only the last revision...
            # config['curonly'] means that the whole dump is configured to save nonly the last
            # params['curonly'] means that we've already tried this fallback, because it's set by the following if and passed to getXMLPageCore
            if not config['curonly'] and not params['curonly']:
                print
                '    Trying to save only the last revision for this page...'
                params['curonly'] = 1
                logerror(config=config,
                         text='Error while retrieving the full history of "%s". Trying to save only the last revision for this page' % (
                         params['pages']))
                return getXMLPageCore(headers=headers, params=params, config=config)
            else:
                print
                '    Saving in the errors log, and skipping...'
                logerror(config=config,
                         text='Error while retrieving the last revision of "%s". Skipping.' % (params['pages']))
                return ''  # empty xml

        data = urllib.urlencode(params)
        req = urllib.Request(url=config['index'], data=data, headers=headers)
        try:
            f = urllib.urlopen(req)
        except:
            try:
                print
                'Server is slow... Waiting some seconds and retrying...'
                time.sleep(15)
                f = urllib.urlopen(req)
            except:
                print
                'An error have occurred while retrieving "%s"' % (params['pages'])
                print
                'Please, resume the dump, --resume'
                sys.exit()
                # The error is usually temporary, but we exit the dump altogether.
        xml = f.read()
        c += 1

    return xml


def getXMLPage(config={}, title='', verbose=True):
    """  """
    # return the full history (or current only) of a page
    # if server errors occurs while retrieving the full page history, it may return [oldest OK versions] + last version, excluding middle revisions, so it would be partialy truncated
    # http://www.mediawiki.org/wiki/Manual_talk:Parameters_to_Special:Export#Parameters_no_longer_in_use.3F

    limit = 1000
    truncated = False
    title_ = title
    title_ = re.sub(' ', '_', title_)
    title_ = urllib.unquote(title_)
    #    print "after check %s" % title_

    #    title_ = re.sub('%3A', ':', title_)

    # do not convert & into %26, title_ = re.sub('&', '%26', title_)
    headers = {'User-Agent': getUserAgent()}
    params = {'title': 'Special:Export', 'pages': title_, 'action': 'submit', }
    #    if config['curonly']:
    #       params['curonly'] = 1
    #       params['limit'] = 1
    #   else:
    params['offset'] = '1'  # 1 always < 2000s
    params['limit'] = limit
    params['curonly'] = 0  # we need this to be defined, in getXMLPageCore
    # if config.has_key('templates') and config['templates']: #in other case, do not set params['templates']
    params['templates'] = 1

    xml = getXMLPageCore(headers=headers, params=params, config=config)

    # if complete history, check if this page history has > limit edits, if so, retrieve all using offset if available
    # else, warning about Special:Export truncating large page histories
    r_timestamp = r'<timestamp>([^<]+)</timestamp>'
    if not config['curonly'] and re.search(r_timestamp,
                                           xml):  # search for timestamps in xml to avoid analysing empty pages like Special:Allpages and the random one
        while not truncated and params['offset']:  # next chunk
            params['offset'] = re.findall(r_timestamp, xml)[-1]  # get the last timestamp from the acum XML
            xml2 = getXMLPageCore(headers=headers, params=params, config=config)

            if re.findall(r_timestamp, xml2):  # are there more edits in this next XML chunk or no <page></page>?
                if re.findall(r_timestamp, xml2)[-1] == params['offset']:
                    # again the same XML, this wiki does not support params in Special:Export, offer complete XML up to X edits (usually 1000)
                    #                    print 'ATTENTION: This wiki does not allow some parameters in Special:Export, therefore pages with large histories may be truncated'
                    truncated = True
                    break
                else:
                    """    </namespaces>
                      </siteinfo>
                      <page>
                        <title>Main Page</title>
                        <id>15580374</id>
                        <restrictions>edit=sysop:move=sysop</restrictions> (?)
                        <revision>
                          <id>418009832</id>
                          <timestamp>2011-03-09T19:57:06Z</timestamp>
                          <contributor>
                    """
                    # offset is OK in this wiki, merge with the previous chunk of this page history and continue
                    xml = xml.split('</page>')[0] + '    <revision>' + ('<revision>'.join(xml2.split('<revision>')[1:]))
            else:
                params['offset'] = ''  # no more edits in this page history

    if verbose:
        print
        '    %s, %s edits' % (title, len(re.findall(r_timestamp, xml)))

    return xml


def cleanXML(xml=''):
    """  """
    # do not touch xml codification, as is
    if re.search(r'</siteinfo>\n', xml) and re.search(r'</mediawiki>', xml):
        xml = xml.split('</siteinfo>\n')[1]
        xml = xml.split('</mediawiki>')[0]
    return xml


def generateXMLDump(config={}, titles=[], start=''):
    """  """
    print
    'Retrieving the XML for every page from "%s"' % (start and start or 'start')
    header = getXMLHeader(config=config)
    footer = '</mediawiki>\n'  # new line at the end
    xmlfilename = '%s-%s-%s.xml' % (
    domain2prefix(config=config), config['date'], config['curonly'] and 'current' or 'history')
    xmlfile = ''
    lock = True
    if start:
        # remove the last chunk of xml dump (it is probably incomplete)
        xmlfile = open('%s/%s' % (config['path'], xmlfilename), 'r')
        xmlfile2 = open('%s/%s2' % (config['path'], xmlfilename), 'w')
        prev = ''
        c = 0
        for l in xmlfile:
            # removing <page>\n until end of file
            if c != 0:  # lock to avoid write an empty line at the begining of file
                if not re.search(r'<title>%s</title>' % (start), l):
                    xmlfile2.write(prev)
                else:
                    break
            c += 1
            prev = l
        xmlfile.close()
        xmlfile2.close()
        # subst xml with xml2
        os.remove('%s/%s' % (config['path'], xmlfilename))  # remove previous xml dump
        os.rename('%s/%s2' % (config['path'], xmlfilename),
                  '%s/%s' % (config['path'], xmlfilename))  # move correctly truncated dump to its real name
    else:
        # requested complete xml dump
        lock = False
        xmlfile = open('%s/%s' % (config['path'], xmlfilename), 'w')
        xmlfile.write(header)
        xmlfile.close()

    xmlfile = open('%s/%s' % (config['path'], xmlfilename), 'a')
    c = 1

    for title in titles:
        if not (isNewTitle(title)):
            continue

        if not title.strip():
            continue
        if title == start:  # start downloading from start, included
            lock = False
        if lock:
            continue
        delay(config=config)
        if c % 10 == 0:
            print
            'Downloaded %d pages' % (c)
        xml = getXMLPage(config=config, title=title)
        xml = cleanXML(xml=xml)
        if not xml:
            print
            'The page "%s" was missing in the wiki (probably deleted)' % (title)

        # here, XML is a correct <page> </page> chunk or
        # an empty string due to a deleted page (logged in errors log) or
        # an empty string due to an error while retrieving the page from server (logged in errors log)
        xmlfile.write(xml)
        c += 1

    xmlfile.write(footer)
    xmlfile.close()
    print
    'XML dump saved at...', xmlfilename

    for title in titles:
        saveName(title)


def saveTitles(config={}, titles=[]):
    """  """
    # save titles in a txt for resume if needed
    titlesfilename = '%s-%s-titles.txt' % (domain2prefix(config=config), config['date'])
    titlesfile = open('%s/%s' % (config['path'], titlesfilename), 'w')
    t = '\n'.join(titles)
    t = t.encode("ascii", "ignore")
    titlesfile.write('\n')
    titlesfile.write(t)
    titlesfile.write('\n--END--')
    titlesfile.close()
    print
    'Titles saved at...', titlesfilename


def undoHTMLEntities(text=''):
    """  """
    text = re.sub('&lt;', '<',
                  text)  # i guess only < > & " need conversion http://www.w3schools.com/html/html_entities.asp
    text = re.sub('&gt;', '>', text)
    text = re.sub('&amp;', '&', text)
    text = re.sub('&quot;', '"', text)
    text = re.sub('&#039;', '\'', text)
    return text


def domain2prefix(config={}):
    """  """
    domain = ''
    if config['api']:
        domain = config['api']
    elif config['index']:
        domain = config['index']
    domain = domain.lower()
    domain = re.sub(r'(https?://|www\.|/index\.php|/api\.php)', '', domain)
    domain = re.sub(r'/', '_', domain)
    domain = re.sub(r'..', '', domain)
    domain = re.sub(r'[^A-Za-z0-9]', '_', domain)
    return domain


def saveConfig(config={}, configfilename=''):
    """  """
    f = open('%s/%s' % (config['path'], configfilename), 'w')
    pickle.dump(config, f)
    f.close()


def welcome():
    """  """
    print
    "#" * 73
    print
    """# Welcome to DumpGenerator 0.1 by WikiTeam (GPL v3)                     #
# More info at: http://code.google.com/p/wikiteam/                      #"""
    print
    "#" * 73
    print
    ''
    print
    "#" * 73
    print
    """# Copyright (C) 2011-2012 WikiTeam                                      #
# This program is free software: you can redistribute it and/or modify  #
# it under the terms of the GNU General Public License as published by  #
# the Free Software Foundation, either version 3 of the License, or     #
# (at your option) any later version.                                   #
#                                                                       #
# This program is distributed in the hope that it will be useful,       #
# but WITHOUT ANY WARRANTY; without even the implied warranty of        #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
# GNU General Public License for more details.                          #
#                                                                       #
# You should have received a copy of the GNU General Public License     #
# along with this program.  If not, see <http://www.gnu.org/licenses/>. #"""
    print
    "#" * 73
    print
    ''


def usage():
    """  """
    print
    """Error. You forget mandatory parameters:
    --api or --index: URL to api.php or to index.php, one of them. If wiki has api.php, please, use --api instead of --index. Examples: --api=http://archiveteam.org/api.php or --index=http://archiveteam.org/index.php

And one of these at least:
    --xml: it generates a XML dump. It retrieves full history of pages located in namespace = 0 (articles)
           If you want more namespaces, use the parameter --namespaces=0,1,2,3... or --namespaces=all
           If you want only the current versions of articles (not the full history), use --curonly option too

You can resume previous incomplete dumps:
    --resume: it resumes previous incomplete dump. When using --resume, --path is mandatory (path to directory where incomplete dump is).

You can exclude namespaces:
    --exnamespaces: write the number of the namespaces you want to exclude, split by commas.

You can be nice with servers using a delay:
    --delay: it adds a time sleep (in seconds, adding 5 seconds between requests: --delay:5)

Write --help for help."""


def getParameters(params=[]):
    if not params:
        params = sys.argv[1:]
    config = {
        'curonly': False,
        'date': datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
        'api': "http://en.wikipedia.org/w/api.php",
        'index': '',
        'titles': 'titles.txt',
        'xml': True,
        'namespaces': ['all'],
        'exnamespaces': [],
        'path': '',
        'delay': 0,
    }
    other = {
        'resume': False,
        'filenamelimit': 100,  # do not change
        'force': False,
    }
    # console params
    try:
        opts, args = getopt.getopt(params, "",
                                   ["h", "help", "path=", "api=", "index=", "xml", "curonly", "resume", "delay=",
                                    "namespaces=", "titles=", "exnamespaces=", "force", ])
    except getopt.GetoptError as err:
        # print help information and exit:
        print
        str(err)  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("--path"):
            config["path"] = a
            while len(config["path"]) > 0:
                if config["path"][-1] == '/':  # dará problemas con rutas windows?
                    config["path"] = config["path"][:-1]
                else:
                    break

        elif o in ("--titles"):
            config["titles"] = a

        elif o in ("--api"):
            if not a.startswith('http://') and not a.startswith('https://'):
                print
                'api.php must start with http:// or https://'
                sys.exit()
            config['api'] = a
        elif o in ("--index"):
            if not a.startswith('http://') and not a.startswith('https://'):
                print
                'index.php must start with http:// or https://'
                sys.exit()
            config["index"] = a
        elif o in ("--xml"):
            config["xml"] = True
        elif o in ("--curonly"):
            if not config["xml"]:
                print
                "If you select --curonly, you must use --xml too"
                sys.exit()
            config["curonly"] = True
        elif o in ("--resume"):
            other["resume"] = True
        elif o in ("--delay"):
            config["delay"] = int(a)
        elif o in ("--namespaces"):
            if re.search(r'[^\d, \-]',
                         a) and a.lower() != 'all':  # fix, why - ?  and... --namespaces= all with a space works?
                print
                "Invalid namespaces values.\nValid format is integer(s) splitted by commas"
                sys.exit()
            a = re.sub(' ', '', a)
            if a.lower() == 'all':
                config["namespaces"] = ['all']
            else:
                config["namespaces"] = [int(i) for i in a.split(',')]
        elif o in ("--exnamespaces"):
            if re.search(r'[^\d, \-]', a):
                print
                "Invalid exnamespaces values.\nValid format is integer(s) splitted by commas"
                sys.exit()
            a = re.sub(' ', '', a)
            if a.lower() == 'all':
                print
                'You have excluded all namespaces. Error.'
                sys.exit()
            else:
                config["exnamespaces"] = [int(i) for i in a.split(',')]
        elif o in ("--force"):
            other["force"] = True
        else:
            assert False, "unhandled option"

    # missing mandatory params
    # (config['index'] and not re.search('/index\.php', config['index'])) or \ # in EditThis there is no index.php, it is empty editthis.info/mywiki/?title=...
    if (not config['api'] and not config['index']) or \
            (config['api'] and not re.search('/api\.php', config['api'])) or \
            not (config["xml"]) or \
            (other['resume'] and not config['path']):
        usage()
        sys.exit()

    # user chosen --api, --index it is neccesary for special:export, we generate it
    if config['api'] and not config['index']:
        config['index'] = config['api'].split('api.php')[0] + 'index.php'
        # print 'You didn\'t provide a path for index.php, trying to wonder one:', config['index']

    if config['index']:
        # check index.php
        if checkIndexphp(config['index']):
            print
            'index.php is OK'
        else:
            print
            'Error in index.php, please, provide a correct path to index.php'
            sys.exit()

    # calculating path, if not defined by user with --path=
    if not config['path']:
        config['path'] = './%s-%s-wikidump' % (domain2prefix(config=config), config['date'])

    return config, other


def checkAPI(api):
    f = urllib.urlopen(api)
    raw = f.read()
    f.close()
    print
    'Checking api.php...', api
    if re.search(r'action=query', raw):
        return True
    return False


def checkIndexphp(indexphp):
    req = urllib.Request(url=indexphp, data=urllib.urlencode({'title': 'Special:Version', }),
                          headers={'User-Agent': getUserAgent()})
    f = urllib.urlopen(req)
    raw = f.read()
    f.close()
    print
    'Checking index.php...', indexphp
    if re.search(r'(This wiki is powered by|<h2 id="mw-version-license">)', raw):
        return True
    return False


def removeIP(raw=''):
    """ Remove IP from HTML comments <!-- --> """
    raw = re.sub(r'\d+\.\d+\.\d+\.\d+', '0.0.0.0', raw)
    # http://www.juniper.net/techpubs/software/erx/erx50x/swconfig-routing-vol1/html/ipv6-config5.html
    # weird cases as :: are not included
    raw = re.sub(
        r'(?i)[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}',
        '0:0:0:0:0:0:0:0', raw)
    return raw


def percent_cb(complete, total):
    sys.stdout.write('..')
    sys.stdout.flush()


def postprocess(path):  # now lets post process  the outpu
    d = datetime.datetime.now()
    datestring = d.strftime("%d%m%y%H%M%S")
    zipfilename = "wtarchive%s.zip" % datestring
    os.system("zip %s %s/*" % (zipfilename, path))


def readTitles(filename):
    lines = tuple(open(filename, 'r'))
    return lines


def main(params=[]):
    """ Main function """
    welcome()
    configfilename = 'config.txt'
    config, other = getParameters(params=params)

    print
    'Analysing %s' % (config['api'] and config['api'] or config['index'])
    c = 2
    originalpath = config['path']  # to avoid concat blabla-2, blabla-2-3, and so on...

    os.mkdir(config['path'])
    saveConfig(config=config, configfilename=configfilename)

    titles = []

    print
    'Trying generating a new dump into a new directory...'

    titles += readTitles(config["titles"])
    print
    "read %s " % '\n'.join(titles)

    saveTitles(config=config, titles=titles)
    generateXMLDump(config=config, titles=titles)

    # save index.php as html, for license details at the bootom of the page
    if os.path.exists('%s/index.html' % (config['path'])):
        print
        'index.html exists, do not overwrite'
    else:
        print
        'Downloading index.php (Main Page)'
        req = urllib.Request(url=config['index'], data=urllib.urlencode({}), headers={'User-Agent': getUserAgent()})
        f = urllib.urlopen(req)
        raw = f.read()
        f.close()
        raw = removeIP(raw=raw)
        f = open('%s/index.html' % (config['path']), 'w')
        f.write(raw)
        f.close()

    # save special:Version as html, for extensions details
    if os.path.exists('%s/Special:Version.html' % (config['path'])):
        print
        'Special:Version.html exists, do not overwrite'
    else:
        print
        'Downloading Special:Version with extensions and other related info'
        req = urllib.Request(url=config['index'], data=urllib.urlencode({'title': 'Special:Version', }),
                              headers={'User-Agent': getUserAgent()})
        f = urllib.urlopen(req)
        raw = f.read()
        f.close()
        raw = removeIP(raw=raw)
        f = open('%s/Special:Version.html' % (config['path']), 'w')
        f.write(raw)
        f.close()

    postprocess(config['path']);  # now lets post process  the outpu


if __name__ == "__main__":
    main()
