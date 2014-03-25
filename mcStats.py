#!/usr/bin/python -tt

# import modules used here
import sys
import os
import gzip
import re
import copy

"""
This are the regexes used in the script
"""

class regex:
  # this regex is supposed to find the date
  date = re.compile("\[(\d\d):(\d\d):(\d\d)\]")
  # this regex finds a login
  login = re.compile("(\S+) joined the game")
  # this regex finds a logout
  logout = re.compile("(\S+) left the game")
  # this regex finds kick events
  kick = re.compile("Kicked (\S+) from the game")
  # this regex finds a server stop
  stop = re.compile("Stopping( the)* server")

class font:
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
  #everything until return is garbage FIXME
  raw = copy.deepcopy(raw_data)
  raw = raw[0].split('\n')
  date = re.search(regex.date, raw[0])
  if date:
    print 'date', date.group(1), date.group(2), date.group(3)

  user = re.search(regex.login, raw[23])
  if user:
    print 'login', user.group(1)

  user = re.search(regex.logout, raw[31])
  if user:
    print 'logout', user.group(1)

  user = re.search(regex.kick, raw[47])
  if user:
    print 'kick', user.group(1)

  serverstop = re.search(regex.stop, raw[57])
  if serverstop:
    print 'serverstop 1', True
  serverstop = re.search(regex.stop, raw[58])
  if serverstop:
    print 'serverstop 2', True

  return {'herobrine': 42}


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
  print '\t\tGive the number of times each player has logged in.', font.bold + font.red + 'not yet implemented' + font.normal
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

  if not args:
    print font.red + 'no files given\n' + font.normal
    print_help()

  filenames = args
  raw_data = read_logfiles(filenames)

  if online_time:
    online_time_result = process_online_time(raw_data)

  if logins:
    login_result = process_logins(raw_data)


# standard boilerplate
if __name__ == '__main__':
    main()
