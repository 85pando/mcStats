# Minecraft Statistics

This programm will create statistics for your minecraft server.

## Features

* mcStats can read log files. It does not matter, if they are plaintex (.log) or zipped (.gz). Several option included, simple help included. Most options do nothing at the moment.  )-:
* ```--logins```: counts the logins of each user.
* ```--online-time```: calculates the time each user was online.
* ```--deaths```: calculate number of deaths.
* ```--verbose```: print unimportant stuff only if requested.
* ```--chat```: calculate the number of times each player has used chat or emotes.
* ```--by-login```: calculate values for the other flags by number of logins, includes ```--logins```
* ```--by-time```: calculates average times for the other flags, includes ```--online-time```.
* ```--write outfile```: don't write the output to stdout but into outfile as a simple html file.

## Usage

T.b.d. Use ```python mcStats.py --help```

## Files

| File            | What it does/is |
|:----------------|-----------------|
| mcStats.py      | This is the actual script |
| deathlist       | This file contains all possible death messages without any user/mob/item names, to allow easy parsing of them for death messages (not having to create regexes for this). |
| test.log        | This is a log which contains most of the log messages for testing the script. What is not in here will probably not be found, if not stated anywhere else. |
| death.log       | This is a pseudo-logfile that contains all possible death messages. |
| serverstart.log | This is a log that is used to test if the server has been restarted for this logfile. It is used to find unclean server shutdowns or crashes. |

## TODO

* textual statistics
    * -sort online-time by online-time-
    * online-time relative to time first online
    * deaths (number if times killed by xyz)
    * uptime
    * accept folders as input
    * find out, why some users are logged as online but come online again
* create some visual statistics for the above
* make nicer indenting for help
* include old one-logfile format

## other log formats

The log format mcStats uses is the one produced by the multi-threaded server. The single-threaded server used priorly has a different format. Until now I did not include this older format, but may do so at some point.

Until then there is the [Minecraft Log Parser][1] which can calculate the online-time for this older log format

## about runtime

I am aware that several of the functions could be made much more efficient. Maybe Later...



[1]: https://github.com/stevenleeg/Minecraft-Log-Parser
