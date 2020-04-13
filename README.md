# diskusage
Shows the oldest biggest files, so you can clean out old stuff

Only tested on windows

### Requirements
* Python 3
* curses
  * `pip3 install windows-curses`

Usage: `python3 main.py PATH_TO_ANALYZE -s MIN_SIZE_GB `

`python3 main.py c:/steamlibrary`

To change the minimum size, you can use `-s`

To only show folder over 10GB, use `-s 10`

`python3 main.py c:/steamlibrary -s 10`