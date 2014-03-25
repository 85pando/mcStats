#!/usr/bin/python -tt

# import modules used here
import sys
import os
import gzip
import re
import copy

class regex:
  """
  The regex class includes the regexes used to find certain things in the logs.
  """
  # this regex is supposed to find the date
  # ex: [10:42:23] [<thread>/<INFO|WARN|...>]: <message>
  time = re.compile("\[(\d\d):(\d\d):(\d\d)\]")
  # this regex finds a login
  # ex: [10:42:23] [Server thread/INFO]: herobrine joined the game
  login = re.compile("(\S+) joined the game")
  # this regex finds a logout
  # ex: [10:42:23] [Server thread/INFO]: herobrine left the game
  logout = re.compile("(\S+) left the game")
  # this regex finds kick events
  # ex: [10:42:23] [Server thread/INFO]: Kicked herobrine from the game: 'herobrine is not wanted'
  kick = re.compile("Kicked (\S+) from the game")
  # this regex finds connections losses TODO
  # ex: [10:42:23] [Server thread/INFO]: herobrine lost conection: TextComponent...
  con_lost = re.compile("(\S+) lost connection:")
  # this regex finds a server stop
  # ex: [10:42:23] [Server thread/INFO]: Stopping the server
  # ex: [10:42:23] [Server thread/INFO]: Stopping server
  stop = re.compile("Stopping( the)* server")

class font:
  """
  The font class includes some shortcuts to format the output.
  """
  normal    = '\033[0m'
  bold      = '\033[1m'
  underline = '\033[4m'
  red       = '\033[31m'
  blue      = '\033[34m'
  yellow    = '\033[33m'
  green     = '\033[32m'
  magenta   = '\033[35m'
  cyan      = '\033[36m'

def read_logfiles(filenames):
  """
  Give a list of valid minecraft logfiles in either gzipped (.gz) or plaintext (.log) format, read_logfiles extract the text from all logfiles as a list.
  """
  logfiles = []
  for singlefile in filenames:
    if os.path.exists(os.path.abspath(singlefile)):
      logfiles.append(read_single_file(singlefile))
    else:
      print singlefile, 'is not a file'
  return logfiles

def read_single_file(filename):
  """
  Given either a .gz or .log file, read_single_file will extract the content of the file and give it back as a string.
  """
  file_name, file_extension = os.path.splitext(filename)
  if file_extension == '.gz':
    print 'open gzipped file', filename
    f = gzip.open(filename, 'rU')
  else:
    print 'open file', filename
    f = open(filename, 'rU')
  text = ''
  if file_extension == '.gz' or file_extension == '.log':
    print 'processing', filename
    text = f.read()
  else:
    print 'not a logfile'
  f.close()
  return text

def process_online_time(raw_data):
  """
  Given a list of the content of valid minecraft logfiles, process_online_time will calculate the online time for each player.
  """
  # TODO
  return {'herobrine': (42,42,42)}

def process_logins(raw_data):
  """
  Given a list of the content of valid minecraft logfiles, process_online_time will calculate the number of logins for this player.
  """
  # logins will be the dictionary which contains the number of logins for each player
  logins = {}
  # raw data is a list of strings, each string is one logfile
  for logfile in raw_data:
    # split logfile into a list of lines
    lines = logfile.split('\n')
    for line in lines:
      search_result = re.search(regex.login, line)
      if search_result:
        search_result = search_result.group(1)
        # now search result contains just the name of the user login in
        if search_result in logins:
          logins[search_result] = logins[search_result] + 1
        else:
          logins[search_result] = 1
  return logins

def test_regexes():
  """
  text_regexes is used to test the regexes used to find stuff in the logfiles. This is written for the included test.log but in theory should work on any valid logfile. For the test.log you should get output for every regex.
  """
  logfile = read_logfiles(['test.log'])[0].split('\n')
  # FIXME make loops and got through the file, break once one is found
  print 'testing time regex'
  for line in logfile:
    time = re.search(regex.time, line)
    if time:
      print '\ttime:', time.group(1), time.group(2), time.group(3)
      break
  print 'testing login regex'
  for line in logfile:
    user = re.search(regex.login, line)
    if user:
      print '\tlogin:', user.group(1)
      break
  print 'testing logout regex'
  for line in logfile:
    user = re.search(regex.logout, line)
    if user:
      print '\tlogout:', user.group(1)
      break
  print 'testing kick regex'
  for line in logfile:
    user = re.search(regex.kick, line)
    if user:
      print '\tkick:', user.group(1)
      break
  print 'testing connection lost regex'
  for line in logfile:
    user = re.search(regex.con_lost, line)
    if user:
      print '\tlost connection:', user.group(1)
      break
  print 'testing serverstop regex (should be two results)'
  for line in logfile:
    serverstop = re.search(regex.stop, line)
    if serverstop:
      print '\tserverstop:', True

def print_dict(dictionary, string=None, sort_key=None):
  if string:
    print font.bold + string + font.normal
  if not sort_key:
    sort_key = sorted(dictionary)
  for name in sort_key:
    print '\t', name + ':', dictionary[name]
  return

def print_help():
  """
  print_help will display usage instructions for mcStats. It will stop the program after printing.
  """
  print 'Minecraft Statistics - Usage'
  print font.bold + 'mcStats' + font.normal, '[--help] [--write outputfile] [--online-time] [--logins] [--deaths]', font.bold + 'file [file ...]' + font.normal
  print font.bold + '\t--write outputfile' + font.normal
  print '\t\tDon\'t write the output to stdout but to the outputfile.', font.bold + font.red + 'not yet implemented' + font.normal
  print font.bold + '\t --online-time' + font.normal
  print '\t\tCalculate the overall time each player has been online.', font.bold + font.red + 'not yet implemented' + font.normal
  print font.bold + '\t --logins' + font.normal
  print '\t\tGive the number of times each player has logged in.'
  print font.bold + '\t --deaths' + font.normal
  print '\t\tGive the number of deaths for each player.', font.bold + font.red + 'not yet implemented' + font.normal

  exit(0)

def main():
  online_time = False
  logins = False
  deaths = False
  write = False
  args = sys.argv[1:]
  if not args:
    print font.red + font.bold + 'no files or options given\n' + font.normal
    print_help()

  if '-h' in args:
    print_help()

  if '--help' in args:
    print_help()

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
    print font.red + 'no files given\n' + font.normal
    print_help()

  filenames = args
  raw_data = read_logfiles(filenames)

  if online_time:
    online_time_result = process_online_time(raw_data)

  if logins:
    login_result = process_logins(raw_data)
    sorter = sorted(login_result, key=lambda x: login_result[x], reverse=True)
    print_dict(login_result, 'Logins:', sorter)

# standard boilerplate
if __name__ == '__main__':
    main()
