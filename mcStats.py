#!/usr/bin/python -tt

# import modules used here
import sys
import os
import gzip

""" extract logfiles from their archives and read their content
"""
def read_logfiles(filenames):
  #do files exist
  for singlefile in filenames:
    if os.path.exists(os.path.abspath(singlefile)):
#      print 'processing:', singlefile
      process_single_file(singlefile)
    else:
      print singlefile, 'not a file'
      sys.stderr.write('not a file')
  return

def process_single_file(filename):
  file_name, file_extension = os.path.splitext(filename)
  if file_extension == '.gz':
    print 'open gzipped file', filename
    f = gzip.open(filename, 'rU')
  else:
    print 'open file', filename
    f = open(filename, 'rU')


  if file_extension == '.gz' or file_extension == '.log':
    print 'processing', filename
    text = f.read()
    print text
  else:
    print 'not a logfile'
  f.close()
  return

def main():
  unzip = False
  args = sys.argv[1:]
  if not args:
    print "usage: [--unzip] file [file ...]"
    sys.exit(1)
  if args[0] == '--unzip':
    unzip = True
    del args[0]

  filenames = args
  raw_data = read_logfiles(filenames)

# standard boilerplate
if __name__ == '__main__':
    main()
