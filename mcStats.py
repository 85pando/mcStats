#!/usr/bin/python -tt

# import modules used here
import sys
import os
import gzip
import re
#import copy
import datetime

# global variables (ugh)
global verbose
verbose = False


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
      #if verbose:
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
    f = gzip.open(filename, 'rU')
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
  return (chatless, chatfull)
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
    for line in lines:
      search_date = re.search(Regex.time, line)
      if not search_date:
        if verbose:
          sys.stderr.write('line contains no date:\n\t' + line + '\n')
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
          sys.stderr.write('user comes online although he is already online\n\t' + file_date + ':\n\t' + line + '\n')
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
  deathlist_file = open('deathlist', 'r')
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
          sys.stderr.write('found a line with a death, but no username\n\t' + line + '\n')
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

def print_dict(dictionary, string=None, sort_list=None):
  """
  print_dict prints a dictionary in a nicely readable manner. string will be printed as a header, if given. The sort_list can be used to sort the dictionary differently. By default it will be sorted naturally after the key. This can be used to sort by the value or similar.
  dictionary - a python dictionary containing some printable stuff
  string - print something in front of the output, if nothing is supplied 'Output:' will be used
  sort_list - supply a list of keys for output, the output will be sorted via this list, can also be used to print only parts of the dictionary (only stuff in this list will be printed), if not supplied, keys will be sorted alphabetically
  """
  if string:
    # print something before the dictionary
    print FontStyle.bold + string + FontStyle.normal
  else:
    # just print the default
    print FontStyle.bold + 'Output:' + FontStyle.normal
  if not sort_list:
    # no special sorting preferences, do it alphabetically
    sort_list = sorted(dictionary)
  for name in sort_list:
    # print each entry from the sorted_list
    print '\t', name + ':', dictionary[name]
  return


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
  print FontStyle.bold + '\t--verbose' + FontStyle.normal
  print '\t\tPrint more stuff. Depending on the number of logfiles, this will be a mess. You have been warned.'

  exit(1)


# >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-<

def main():
  # variables for flags
  chat = False
  deaths = False
  logins = False
  online_time = False
  write = False
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

  if '--write' in args:
    write = True
    del args[args.index('--write')]

  # this is just to test the regexes against a logfile
  if '--test' in args:
    test_regexes()
    exit(0)

  if not args:
    print FontStyle.red + 'no files given\n' + FontStyle.normal
    print_help()

  filenames = args
  raw_data = read_logfiles(filenames)

  # the chat data is not really needed in the normal log file, split chat into seperate file
  (chatless_data, chat_data) = purge_chat(raw_data)

  if chat:
    chat_result = process_chats(chat_data)
    sorter = sorted(chat_result, key=lambda x: chat_result[x], reverse=True)
    print_dict(chat_result, 'Chats:', sorter)


  if deaths:
    death_result = process_deaths(chatless_data)
    sorter = sorted(death_result, key=lambda x: death_result[x], reverse=True)
    print_dict(death_result, 'Deaths:', sorter)


  if logins:
    #login_result = process_logins(raw_data)
    login_result = process_logins(chatless_data)
    sorter = sorted(login_result, key=lambda x: login_result[x], reverse=True)
    print_dict(login_result, 'Logins:', sorter)


  if online_time:
    online_time_result = process_online_time(chatless_data)
    # TODO sort results by online time
    #sorter = sorted(online_time_result, key=lambda x: online_time_result[x], reverse=True)
    print_dict(online_time_result, 'Online-Time:')

# standard boilerplate
if __name__ == '__main__':
  main()
