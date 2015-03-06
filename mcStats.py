#!/usr/bin/python -tt

"""
    mcStats is a little tool to create statistics for a minecraft server.
    The projet is housed at <https://github.com/85pando/mcStats>. The
    Source can also be found there.

    Copyright (C) 2014 Stephan Heidinger

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>
"""

# import modules used here
import sys
import os
import gzip
import re
#import copy
import datetime
from pystache import Renderer

# global variables (ugh)
global verbose
verbose = False

_NAME = "mcStats"
layout_template = "templates/layout.mustache"

def set_verbose(boolean=True):
  global verbose
  verbose = boolean
  return


class Regex:
  """
  The Regex class includes the regexes used to find certain things in the logs.
  """
  def __init__(self):
    pass

  # this regex finds chat messages
  # ex: [17:42:42] [Server thread/INFO]: <herobrine> I really like this game.
  chat = re.compile(r'^\[\d{2}:\d{2}:\d{2}\] \[Server thread/INFO\]: \* (\S+)')
  # this regex finds connections losses
  # ex: [10:42:23] [Server thread/INFO]: herobrine lost connection: TextComponent...
  con_lost = re.compile(r'^\[\d{2}:\d{2}:\d{2}\] \[Server thread/INFO\]: (\S+) lost connection:')
  # this regex finds emotes
  # ex: [17:42:23] [Server thread/INFO]: * herobrine nice game
  emote = re.compile(r'^\[\d{2}:\d{2}:\d{2}\] \[Server thread/INFO\]: <(\S+)>')
  # this regex is used to extract the date from the filename
  # ex: 2014-28-03
  file_date = re.compile(r'(\d{4}-\d{2}-\d{2})')
  # this regex finds kick events
  # ex: [10:42:23] [Server thread/INFO]: Kicked herobrine from the game: 'herobrine is not wanted'
  kick = re.compile(r'^\[\d{2}:\d{2}:\d{2}\] \[Server thread/INFO\]: Kicked (\S+) from the game')
  # this regex finds a login
  # ex: [10:42:23] [Server thread/INFO]: herobrine joined the game
  login = re.compile(r'^\[\d{2}:\d{2}:\d{2}\] \[Server thread/INFO\]: (\S+) joined the game')
  # this regex finds a logout
  # ex: [10:42:23] [Server thread/INFO]: herobrine left the game
  logout = re.compile(r'^\[\d{2}:\d{2}:\d{2}\] \[Server thread/INFO\]: (\S+) left the game')
  # this regex finds the user name of a line where a user does something
  # ex: [23:42:00] [Server thread/INFO]: herobrine drowned
  name = re.compile(r'^\[\d{2}:\d{2}:\d{2}\] \[Server thread/INFO\]: (\S+)')
  # this regex finds the start of the server
  # ex: [17:28:14] [Server thread/INFO]: Starting minecraft server version 1.7.2
  # ex: [17:28:15] [Server thread/INFO]: Starting Minecraft server on 192.169.0.1:25566
  # ex: [15:35:24] [Server thread/INFO]: Starting minecraft server version 14w11a
  start = re.compile(r'\[\d{2}:\d{2}:\d{2}\] \[[\w\s]+/[A-Z]+\]: Starting [Mm]inecraft server (on \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}|version (\d+\.\d+\.\d+|\d{2}w\d{2}[a-z]*))')
  # this regex finds a server stop
  # ex: [10:42:23] [Server thread/INFO]: Stopping the server
  # ex: [10:42:23] [Server thread/INFO]: Stopping server
  stop = re.compile(r'^\[\d{2}:\d{2}:\d{2}\] \[Server thread/INFO\]: Stopping( the)* server')
  # this regex is supposed to find the date
  # ex: [10:42:23] [<thread>/<INFO|WARN|...>]: <message>
  time = re.compile(r'^\[(\d{2}:\d{2}:\d{2})\]')



class FontStyle:
  """
  The FontStyle class includes some shortcuts to format the output.
  """

  def __init__(self):
    pass

  normal = '\033[0m'
  bold = '\033[1m'
  underline = '\033[4m'
  red = '\033[31m'
  blue = '\033[34m'
  yellow = '\033[33m'
  green = '\033[32m'
  magenta = '\033[35m'
  cyan = '\033[36m'


# >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-<

def read_logfiles(filenames):
  """
  Give a list of valid minecraft logfiles in either gzipped (.gz) or plaintext (.log) format, read_logfiles extract the text from all logfiles as a list.
  filenames - a list of logfiles to process
  """
  # logfiles will include one logfile for each entry as a string
  logfiles = []
  for singlefile in filenames:
    # singlefile will be a single logfile as string
    if os.path.exists(os.path.abspath(singlefile)):
      # only try to add logfiles, when they exist
      logfiles.append(read_single_file(singlefile))
    else:
      if verbose:
      print singlefile, 'is not a file'
  return logfiles


# >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-<

def read_single_file(filename):
  """
  Given either a .gz or .log file, read_single_file will extract the content of the file and give it back as a string.
  filename - a single logfile
  """
  # unpack file_name and file_extension to be able to distinguish different file types
  file_name, file_extension = os.path.splitext(filename)
  if file_extension == '.gz':
    # .gz files are zipped, open accordingly
    if verbose:
      print 'open gzipped file', filename
    f = gzip.open(filename, 'rb')
  else:
    # .log are plaintext files, just open
    if verbose:
      print 'open file', filename
    f = open(filename, 'rU')
  # text will contain the content of filename as a string
  text = ''
  if file_extension == '.gz' or file_extension == '.log':
    # file is in one of the known formats, process
    if verbose:
      print 'processing', filename
    # include filename into text, s.t. date can be extracted if needed
    text = 'date: ' + file_name + '\n'
    text += f.read()
  else:
    # file is not in a known format, don't use
    if verbose:
      print 'not a logfile'
  f.close()
  return text


# >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-<

def purge_chat(raw_data):
  """
  purge_chat will split the logfiles into one file containing everything but chat/emotes and one file containing only chat/emotes.
  raw_data - a list of logfiles, each logfile is a string containing the whole file
  """
  chatless = []
  chatfull = []
  for logfile in raw_data:
    chatlines = []
    loglines = []
    # logfile is the content of a single log file
    lines = logfile.split('\n')
    for line in lines:
      # search for chat and emotes
      chat = re.search(Regex.chat, line)
      emote = re.search(Regex.emote, line)
      # the line is either a chat/emote line, or not, put it into the according structure
      if chat or emote:
        chatlines.append(line)
      else:
        loglines.append(line)
    loglines = '\n'.join(loglines)
    chatlines = '\n'.join(chatlines)
    chatless.append(loglines)
    chatfull.append(chatlines)
  return chatless, chatfull


# >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-<

def process_online_time(raw_data):
  """
  Given a list of the content of valid minecraft logfiles, process_online_time will calculate the online time for each player.
  raw_data - a list of logfiles, each logfile is a string containing the whole file
  """
  online_time = {}
  online = {}
  last_time = None
  for logfile in raw_data:
    # logfile is the content of a single log file
    lines = logfile.split('\n')
    # extract date from file
    file_date = re.search(Regex.file_date, lines[0])
    if file_date:
      file_date = file_date.group()
    else:
      # if the regex is not found in the first line, it is assumed to be latest.log or test.log
      if verbose:
        print 'assuming the filename is latest or test:', lines[0]
      #file_date = 'date', datetime.datetime.now().date()
      file_date = datetime.datetime.now().date()
    # check if the server did a clean shutdown (i.e. there are no users still online when the server starts)
    for line in lines[1:10]:
      search_result = re.search(Regex.login, line)
      if search_result:
        # this is a fresh server log, no users should be online
        if online:
          # there are sill users online, logging them out at the last point, where the server was known to run
          if verbose:
            print 'unclean shutdown, parting users at last known time the server was running'
          online_list = []
          for user in online:
            online_list.append(user)
          for user in online:
            from_time = online[user]
            if user in online_list:
              online_time[user] += last_time - from_time
            else:
              online_time[user] = last_time - from_time
          for user in online_list:
            del online[user]
    # lines is a list of all lines from the logfile
    if not re.search(Regex.time,lines[0]):
      # first line may contain date inserted by this script, ignore this
      del lines[0]
    for line in lines:
      if line == '':
        continue
      search_date = re.search(Regex.time, line)
      if not search_date:
        sys.stderr.write(FontStyle.bold +
                         'process_online_time:\n\t'
                         + FontStyle.normal +
                         'line contains no date:\n\t'
                         + line + '\n')
        continue
      else:
        #timestamp = file_date + ' ' + search_date.group(1)
        time = datetime.datetime.strptime(str(file_date) + " " + search_date.group(1), '%Y-%m-%d %H:%M:%S')
        # store time in case the server does an unclean shutdown (i.e. crash)
        last_time = time
      # search for login
      search_result = re.search(Regex.login, line)
      if search_result:
        user = search_result.group(1)
        # user logged in
        if user in online:
          # this should not happen
          online[user] = time
          sys.stderr.write(FontStyle.bold +
                           'process_online_time:\n\t'
                           + FontStyle.normal +
                           'user logs in, although he is already online:\n\t'
                           + line + '\n')
        else:
          # user is not online, comes online
          online[user] = time
      else:
        # search for disconnects
        for cur_reg in [Regex.logout, Regex.kick, Regex.con_lost]:
          # looking for any of the part messages
          search_result = re.search(cur_reg, line)
          if search_result:
            break  # we found a msg in this line
        if search_result:
          user = search_result.group(1)
          # user has a part message
          if user in online:
            from_time = online[user]
            del online[user]
            # user was online, is now parting
            if user in online_time:
              # user has been online before
              online_time[user] += time - from_time  # join-part
            else:
              # this was the first time, the user was online
              online_time[user] = time - from_time  # join-part
          else:
            if verbose:
              print 'redundant part message', line
        else:
          # we found no part message, look for server stop
          search_result = re.search(Regex.stop, line)
          if search_result:
            user_list = []
            for user in online:
              from_time = online[user]
              user_list.append(user)
              if user in online_time:
                online_time[user] += time - from_time
              else:
                online_time[user] = time - from_time
            for user in user_list:
              del online[user]
          else:
            if verbose:
              print 'line contained no join/part/stop message\n\t', line

  return online_time


# >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-<

def process_logins(raw_data):
  """
  Given a list of the content of valid minecraft logfiles, process_online_time will calculate the number of logins for this player.
  raw_data - a list of logfiles, each logfile is a string containing the whole file
  """
  # logins will be the dictionary which contains the number of logins for each player
  logins = {}
  # raw_data is a list of strings, each string is one logfile
  for logfile in raw_data:
    # split logfile into a list of lines
    lines = logfile.split('\n')
    for line in lines:
      search_result = re.search(Regex.login, line)
      if search_result:
        search_result = search_result.group(1)
        # now search result contains just the name of the user login in
        if search_result in logins:
          # user already in dictionary, increment
          logins[search_result] += 1
        else:
          # user not yet in dictionary, insert
          logins[search_result] = 1
  return logins


# >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-<

def process_deaths(raw_data):
  """
  Given a list of the content of valid minecraft logfiles, process_deaths will calculate the number of deaths for each player.
  raw_data - a list of logfiles, each logfile is a string containing the whole file
  """
  # deaths will be the dictionary which contains the number of deaths
  deaths = {}
  # read list of possible death causes
  deathlist_file = open(os.path.join(sys.path[0], 'deathlist'), 'r')
  deathlist = deathlist_file.read().split('\n')
  deathlist_file.close()
  # raw_data is a list of strings, each string is one logfile
  for logfile in raw_data:
    # split logfile into a list of lines
    lines = logfile.split('\n')
    #don't need first line, as this will only contain the death
    for line in lines:
      death_found = False
      # lines may contain empty strings
      for deathline in deathlist:
        if not deathline:
          continue
        if deathline in line:
          # we have found a line where a death has taken place
          death_found = True
          break
      if death_found:
        # extract name of user
        search_result = re.search(Regex.name, line)
        if search_result:
          user = search_result.group(1)
          if '*' in user:
            print lines[0]
            print line
          if user in deaths:
            # user has already died once
            deaths[user] += 1
          else:
            # user never died before
            deaths[user] = 1
        else:
          sys.stderr.write(FontStyle.bold +
                           'process_deaths:\n\t'
                           + FontStyle.normal +
                           'found a line with a death, but no username:\n\t'
                           + line + '\n')
  return deaths



# >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-<

def process_chats(raw_data):
  """
  Given a list of the content of valid minecraft logfiles, process_chats will calculate the number of times each player used the chat or emotes.
  raw_data - a list of logfiles, each logfile is a string containing the whole file
  """
  # chats will be the dictionary which contains the numer of chats/emotes for each player
  chats = {}
  # raw_data is a list of strings, each string is one logfile
  for logfile in raw_data:
    # split logfile into a list of lines
    lines = logfile.split('\n')
    for line in lines:
      # look if this line contains chat
      if line == '':
        # this may happen sometimes
        continue
      search_result = re.search(Regex.chat, line)
      if not search_result:
        # if not, this line should contain an emote
        search_result = re.search(Regex.emote, line)
        if not search_result:
          # this should not happen
          sys.stderr.write('chat-line processed, but neither chat nor emote found\n')
          sys.stderr.write(FontStyle.bold +
                           'process_chats:\n\t'
                           + FontStyle.normal +
                           'chat-line-processed, but neither chat nor emote found:\n\t'
                           + line + '\n')
          # skip this line
          continue
      # we have either a chat or an emote
      user = search_result.group(1)
      if user in chats:
        # user has already chatted once
        chats[user] += 1
      else:
        chats[user] = 1
  return chats


# >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-<

def process_by_login(data_dictionary, login_dictionary):
  by_logins = {}
  for user in data_dictionary:
    if user in login_dictionary:
      by_logins[user] = data_dictionary[user] / float(login_dictionary[user])
  return by_logins


# >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-<

def process_by_time(data_dictionary, online_dictionary):
  by_time = {}
  for user in data_dictionary:
    if user in online_dictionary:
      by_time[user] =  datetime.timedelta(seconds=online_dictionary[user].total_seconds() / float(data_dictionary[user]))
      #by_time = online_dictionary[user] / data_dictionary[user]
  return by_time


# >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-<

def test_regexes():
  """
  text_regexes is used to test the regexes used to find stuff in the logfiles. This is written for the included test.log but in theory should work on any valid logfile. For the test.log you should get output for every Regex.
  """
  logfile = read_logfiles(['test.log'])[0].split('\n')
  print 'testing chat regex'
  for line in logfile:
    user = re.search(Regex.chat, line)
    if user:
      print '\tchat', user.group(1) + '\n\t' + line
  print 'testing emote regex'
  for line in logfile:
    user = re.search(Regex.emote, line)
    if user:
      print '\temote', user.group(1) + '\n\t' + line
  print 'testing time regex'
  for line in logfile:
    time = re.search(Regex.time, line)
    if time:
      print '\ttime:', time.group(1) + '\n\t' + line
      break
  print 'testing login regex'
  for line in logfile:
    user = re.search(Regex.login, line)
    if user:
      print '\tlogin:', user.group(1) + '\n\t' + line

      break
  print 'testing logout regex'
  for line in logfile:
    user = re.search(Regex.logout, line)
    if user:
      print '\tlogout:', user.group(1) + '\n\t' + line

      break
  print 'testing kick regex'
  for line in logfile:
    user = re.search(Regex.kick, line)
    if user:
      print '\tkick:', user.group(1) + '\n\t' + line

      break
  print 'testing connection lost regex'
  for line in logfile:
    user = re.search(Regex.con_lost, line)
    if user:
      print '\tlost connection:', user.group(1) + '\n\t' + line

      break
  print 'testing name regex'
  for line in logfile:
    user = re.search(Regex.name, line)
    if user:
      print '\tname', user.group(1)
      break
  print 'testing serverstop regex (should be two results)'
  for line in logfile:
    serverstop = re.search(Regex.stop, line)
    if serverstop:
      print '\tserverstop:', True
  print 'testing serverstart regex (should be five results)'
  logfile = read_logfiles(['serverstart.log'])[0].split('\n')
  for line in logfile:
    serverstart = re.search(Regex.start, line)
    if serverstart:
      print'\tserverstart:', True


# >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-<

def print_dict(dictionary, heading=None, description=None, sorted_by_value=True):
  """
  print_dict prints a dictionary in a nicely readable manner. string will be printed as a header, if given. The sort_list can be used to sort the dictionary differently. By default it will be sorted naturally after the key. This can be used to sort by the value or similar.
  dictionary - a python dictionary containing some printable stuff
  string - print something in front of the output, if nothing is supplied 'Output:' will be used
  sorted_by_value - When this is True, the printout will be sorted by the value with the highest value first. Otherwise it will be sorted alphabetically.
  """
  if heading:
    # print something before the dictionary
    print FontStyle.bold + heading + FontStyle.normal
  else:
    # just print the default
    print FontStyle.bold + 'Output:' + FontStyle.normal
  if sorted_by_value:
    sort_list = sorted(dictionary, key=lambda x: dictionary[x], reverse=True)
  else:
    sort_list = sorted(dictionary)
  if description:
    print '\t' + description
  for name in sort_list:
    # print each entry from the sorted_list
    print '\t', name + ':', dictionary[name]
  return


def print_dict_html(dictionary, description=None, heading=None, sorted_by_value=True):
  body = '<table border="1px" cellspacing="0" cellpadding=3>'
  if heading:
    body += '<tr><th colspan="2">' + heading + '</th></tr>\n'
  if not sorted_by_value:
    sort_list = sorted(dictionary)
  else:
    sort_list = sorted(dictionary, key=lambda x: dictionary[x], reverse=True)
  if description:
    body += '<p>' + description + '</p>'
  for name in sort_list:
    body += '<tr><td>' + name + '</td><td>' + str(dictionary[name]) + '</td>\n'
  body += '</tr></table>'
  return body

# >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-<

def print_help():
  """
  print_help will display usage instructions for mcStats. It will stop the program after printing.
  """
  print 'Minecraft Statistics - Usage'
  print FontStyle.bold + 'mcStats' + FontStyle.normal, '[--help] [--write outputfile] [--online-time] [--logins] [--deaths] [--verbose]', FontStyle.bold + 'file [file ...]' + FontStyle.normal
  print FontStyle.bold + '\t--help' + FontStyle.normal
  print '\t\tPrint the help text. If this option is given, all other options will be ignored.'
  print FontStyle.bold + '\t--write outputfile' + FontStyle.normal
  print '\t\tDon\'t write the output to stdout but to the outputfile.', FontStyle.bold + FontStyle.red + 'not yet implemented' + FontStyle.normal
  print FontStyle.bold + '\t--chat' + FontStyle.normal
  print '\t\tCalculate number of times each player has used chat or emotes.'
  print FontStyle.bold + '\t--online-time' + FontStyle.normal
  print '\t\tCalculate the overall time each player has been online.'
  print FontStyle.bold + '\t--logins' + FontStyle.normal
  print '\t\tGive the number of times each player has logged in.'
  print FontStyle.bold + '\t--deaths' + FontStyle.normal
  print '\t\tGive the number of deaths for each player.'
  print FontStyle.bold + '\t--by-login' + FontStyle.normal
  print '\t\tCalculate values for the other flags by login.'
  print FontStyle.bold + '\t--by-time' + FontStyle.normal
  print '\t\tCalculate values for the other flags by online time.'
  print FontStyle.bold + '\t--verbose' + FontStyle.normal
  print '\t\tPrint more stuff. Depending on the number of logfiles, this will be a mess. You have been warned.'
  print '\nAt the moment, the css for the outputfile will ' + FontStyle.underline + 'not' + FontStyle.normal + ' not be copied along, you have to do this manually.'

  exit(0)


# >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-<

def dict_to_arr(result_dictionary, sorted_by_value=True):
  res = []
  for k,v in result_dictionary.items():
    res.append({"name" : k, "value" : v})
  if not sorted_by_value:
    res = sorted(res)
  else:
    res = sorted(res, key=lambda k: k['value'], reverse=True)
  return res

def render_html(content):
  tplFile = open(os.path.join(sys.path[0], layout_template),"r")
  rendered = Renderer().render(tplFile.read(), content)
  return rendered

def new_section(title, description, entries_dictionary):
  return { "title": title, "description": description, "entries" : dict_to_arr(entries_dictionary) }

# >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-<

def main():
  # variables for flags
  chat        = False
  by_time     = False
  by_logins   = False
  deaths      = False
  logins      = False
  online_time = False
  write       = False
  outname     = ''
  # input arguments
  args = sys.argv[1:]
  if not args:
    # no arguments supplied, print warning and help
    print FontStyle.red + FontStyle.bold + 'no files or options given\n' + FontStyle.normal
    print_help()

  if '-h' in args:
    print_help()
  if '--help' in args:
    print_help()

  if '--write' in args:
    write = True
    index = args.index('--write')
    outname = os.path.abspath(args[index + 1])
    if os.path.isfile(outname) & verbose:
      print outname, 'exists, overwriting'
    del args[index+1] # outname
    del args[index] # --write

  if '--verbose' in args:
    set_verbose(True)
    del args[args.index('--verbose')]

  if '--chat' in args:
    chat = True
    del args[args.index('--chat')]

  if '--online-time' in args:
    online_time = True
    del args[args.index('--online-time')]

  if '--logins' in args:
    logins = True
    del args[args.index('--logins')]

  if '--deaths' in args:
    deaths = True
    del args[args.index('--deaths')]

  if '--by-logins' in args:
    by_logins = True
    logins    = True
    del args[args.index('--by-logins')]

  if '--by-time' in args:
    by_time    = True
    online_time = True
    del args[args.index('--by-time')]

  # this is just to test the regexes against a logfile
  if '--test' in args:
    test_regexes()
    exit(0)

  if not args:
    print FontStyle.red + 'no files given\n' + FontStyle.normal
    print_help()

  filenames = args
  raw_data = read_logfiles(filenames)

  # the chat data is not really needed in the normal log file, split chat into separate file
  (chatless_data, chat_data) = purge_chat(raw_data)

  if chat:
    chat_result = process_chats(chat_data)
    if not write:
      print_dict(chat_result, 'Chats:', 'Number of times each user used the chat', True)

  if deaths:
    death_result = process_deaths(chatless_data)
    if not write:
      print_dict(death_result, 'Deaths:', 'Number of Deaths for each user', True)

  if logins:
    login_result = process_logins(chatless_data)
    if not write:
      print_dict(login_result, 'Logins:', 'Number of Logins of each user', True)

  if online_time:
    online_time_result = process_online_time(chatless_data)
    if not write:
      print_dict(online_time_result, 'Online-Time:', 'Time each user was online.', True)

  if by_logins:
    if chat:
      # chats by login
      chat_by_logins = process_by_login(chat_result, login_result)
      print_dict(chat_by_logins, 'Chats by Logins:', 'Number of times each user used the chat by number of logins.', sorted_by_value=True)
    if deaths:
      # deaths by login
      deaths_by_logins = process_by_login(death_result, login_result)
      print_dict(deaths_by_logins, 'Deaths by Logins:', 'Number of times each user died by number of logins.', sorted_by_value=True)

  if by_time:
    if chat:
      # time by chat
      time_by_chat = process_by_time(chat_result, online_time_result)
      print_dict(time_by_chat, 'Time by Chat', 'Time each user was online by chat message.', sorted_by_value=True)
    if deaths:
      # time by death
      time_by_death = process_by_time(death_result, online_time_result)
      print_dict(time_by_death, 'Time by Death', 'Time each user was online by Death.', sorted_by_value=True)
    if logins:
      # time by login
      time_by_login = process_by_time(login_result, online_time_result)
      print_dict(time_by_login, 'Time by Login', 'Time each user was online by login.', sorted_by_value=True)

  if write:
    sections = []
    content = { "title": _NAME, "generator": _NAME, "generated_at" : datetime.datetime.now().ctime(),"sections" : sections }

    if chat:
      sections.append(new_section('Chat', 'Number of times each user used the chat.', chat_result))
    if deaths:
      sections.append(new_section('Deaths', 'Number of times each user died.', death_result))
    if logins:
      sections.append(new_section('Logins', 'Number of times each user logged in.', login_result))
    if online_time:
      sections.append(new_section('Online Time', 'Time each user was online.',online_time_result))

    if by_logins:
      if chat:
        # chats by login
        sections.append(new_section('Chats by Logins', 'Number of times each user used the chat by number of logins.', chat_by_logins))
      if deaths:
        # deaths by login
        sections.append(new_section('Deaths by Logins', 'Number of times each user died by number of logins.', deaths_by_logins))
    if by_time:
      if chat:
        # time by chat
        sections.append(new_section('Time by Chat', 'Time each user was online by chat message.', time_by_chat))
      if deaths:
        # time by death
        sections.append(new_section('Time by Death', 'Time each user was online by Death.', time_by_death))
      if logins:
        # time by login
        sections.append(new_section('Time by Login', 'Time each user was online by login.', time_by_login))

    output_file = open(outname, 'w')
    output_file.write(render_html(content))
    output_file.close()



# standard boilerplate
if __name__ == '__main__':
  main()
