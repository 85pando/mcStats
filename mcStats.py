#!/usr/bin/python -tt

# import modules used here
import sys
import os
import gzip
import re
import copy
import datetime

# global variables (ugh)
global verbose
verbose = False
def set_verbose(boolean = True):
  global verbose
  verbose = boolean
  return

class regex:
  """
  The regex class includes the regexes used to find certain things in the logs.
  """
  # this regex is supposed to find the date
  # ex: [10:42:23] [<thread>/<INFO|WARN|...>]: <message>
  time = re.compile('\[(\d\d:\d\d:\d\d)\]')
  # this regex finds a login
  # ex: [10:42:23] [Server thread/INFO]: herobrine joined the game
  login = re.compile('(\S+) joined the game')
  # this regex finds a logout
  # ex: [10:42:23] [Server thread/INFO]: herobrine left the game
  logout = re.compile('(\S+) left the game')
  # this regex finds kick events
  # ex: [10:42:23] [Server thread/INFO]: Kicked herobrine from the game: 'herobrine is not wanted'
  kick = re.compile('Kicked (\S+) from the game')
  # this regex finds connections losses TODO
  # ex: [10:42:23] [Server thread/INFO]: herobrine lost conection: TextComponent...
  con_lost = re.compile('(\S+) lost connection:')
  # this regex finds a server stop
  # ex: [10:42:23] [Server thread/INFO]: Stopping the server
  # ex: [10:42:23] [Server thread/INFO]: Stopping server
  stop = re.compile('Stopping( the)* server')
  # this regex is used to extract the date from the filename
  file_date = re.compile('(\d{4}-\d{2}-\d{2})')

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

def process_online_time(raw_data):
  """
  Given a list of the content of valid minecraft logfiles, process_online_time will calculate the online time for each player.
  raw_data - a list of logfiles, each logfile is a string containing the whole file
  """
  online_time= {}
  online = {}
  for logfile in raw_data:
    # logfile is the content of a single log file
    lines = logfile.split('\n')
    # extract date from file
    file_date = re.search(regex.file_date, lines[0])
    if file_date:
      file_date =  file_date.group()
    else:
      # if the regex is not found in the first line, it is assumed to be latest.log or test.log
      if verbose:
        print 'assuming the filename is latest or test:', lines[0]
      #file_date = 'date', datetime.datetime.now().date()
      file_date = datetime.datetime.now().date()
    # lines is a list of all lines from the logfile
    for line in lines:
      search_date = re.search(regex.time, line)
      if not search_date:
        if verbose:
          sys.stderr.write('line contains no date:\n\t' + line + '\n')
        continue
      else:
        #timestamp = file_date + ' ' + search_date.group(1)
        time = datetime.datetime.strptime(str(file_date) + " " + search_date.group(1), '%Y-%m-%d %H:%M:%S')
      # search for login
      search_result = re.search(regex.login, line)
      if search_result:
        user =  search_result.group(1)
        # user logged in
        if user in online:
          # this should not happen
          sys.stderr.write('user comes online although he is already online\n')
        else:
          # user is not online, comes online
          online[user] = time
      else:
        # search for disconnects
        for cur_reg in [regex.logout,regex.kick,regex.con_lost]:
          # looking for any of the part messages
          search_result = re.search(cur_reg, line)
          if search_result:
            break # we found a msg in this line
        if search_result:
          user = search_result.group(1)
          # user has a part message
          if user in online:
            from_time = online[user]
            del online[user]
            # user was online, is now parting
            if user in online_time:
              # user has been online before
              online_time[user] += time-from_time # join-part
            else:
              # this was the first time, the user was online
              online_time[user] = time-from_time # join-part
          else:
            if verbose:
              print 'redundant part message', line
        else:
          # we found no part message, look for server stop
          search_result = re.search(regex.stop, line)
          if search_result:
            user_list = []
            for user in online:
              from_time = online[user]
              user_list.append(user)
              if user in online_time:
                online_time[user] += time-from_time
              else:
                online_time[user] = time-from_time
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
          # user already in dictionary, increment
          logins[search_result] = logins[search_result] + 1
        else:
          # user not yet in dictionary, insert
          logins[search_result] = 1
  return logins

# >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-<

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
      print '\ttime:', time.group(1)
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
    print font.bold + string + font.normal
  else:
    # just print the default
    print font.bold + 'Output:' + font.normal
  if not sort_list:
    # no special sorting prefrerences, do it alphabetically
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
  print font.bold + 'mcStats' + font.normal, '[--help] [--write outputfile] [--online-time] [--logins] [--deaths] [--verbose]', font.bold + 'file [file ...]' + font.normal
  print font.bold + '\t--help' + font.normal
  print '\t\tPrint the help text. If this option is given, all other options will be ignored.'
  print font.bold + '\t--write outputfile' + font.normal
  print '\t\tDon\'t write the output to stdout but to the outputfile.', font.bold + font.red + 'not yet implemented' + font.normal
  print font.bold + '\t--online-time' + font.normal
  print '\t\tCalculate the overall time each player has been online.'
  print font.bold + '\t--logins' + font.normal
  print '\t\tGive the number of times each player has logged in.'
  print font.bold + '\t--deaths' + font.normal
  print '\t\tGive the number of deaths for each player.', font.bold + font.red + 'not yet implemented' + font.normal
  print font.bold + '\t--verbose' + font.normal
  print '\t\tPrint more stuff. Depending on the number of logfiles, this will be a mess. You have been warned.'

  exit(0)

# >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-< >-<

def main():
  # variables for flags
  deaths = False
  logins = False
  online_time = False
  write = False
  # input arguments
  args = sys.argv[1:]
  if not args:
    # no arguments supplied, print warning and help
    print font.red + font.bold + 'no files or options given\n' + font.normal
    print_help()

  if '-h' in args:
    print_help()
  if '--help' in args:
    print_help()

  if '--verbose' in args:
    set_verbose(True)
    del args[args.index('--verbose')]

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
    print online_time_result
    sorter = sorted(online_time_result, key=lambda x: online_time_result[x], reverse=True)
    print_dict(online_time_result, 'Online-Time:')

  if logins:
    login_result = process_logins(raw_data)
    sorter = sorted(login_result, key=lambda x: login_result[x], reverse=True)
    print_dict(login_result, 'Logins:', sorter)

# standard boilerplate
if __name__ == '__main__':
    main()
