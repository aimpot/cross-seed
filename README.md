# Cross-seed
**Cross-seed** is a portable Python script that will let you easily cross-seed torrents between multiple trackers. It can also show you which of your data may be uploadable on which trackers due to it not being present already.

You point the script at the locations of your torrent data and the script will scan them. Based on meta-data of the torrents the script will search various trackers for matches, save the torrent file download links and download them for you. You then put the downloaded torrent files into your torrent client's watch folder and viola. You're seeding the data on multiple trackers.

The script is currently in beta. Please see the feeback section if you want to try it out and help identify issues.

**Cross-seed** currently supports the following trackers (with more to come--I hope).
If you're staff and want your tracker added to the list please reach out. Look for forum threads on supported trackers.

> `BLU`

# Setup
The script should be platform independent, but you will need to have `python3` and the `requests` module installed. That's all. If you're on Debian/Ubuntu you probably already have `python3`, but if not, you can install it like so.
Once you have `python3` the following installation of `requests` will probably work on most platforms:

```bash
$ sudo apt update && sudo apt install -y python3
$ python3 -m pip install --user requests
```

If you're on Windows 10 I'd recommend [installing the Ubuntu Subsystem]([https://docs.microsoft.com/en-us/windows/wsl/install-win10](https://docs.microsoft.com/en-us/windows/wsl/install-win10)) which should let you launch `bash`, a Linux terminal, from which you can install the above and run the scripts.

All you have left to do is generate a new config file and fill it out. To do so just download the script, navigate in a terminal to where you put it and run it without arguments.
This will create an empty config file next to the script called `cross-seed.json`. The config file looks like this, and you'll need to open it in a text editor and put in your API keys for the supported trackers you want to use:
```bash
$ python3 cross-seed.py
```

```json
{
    "api_keys": {
        "BLU": ""
    },
    "torrents": {}
}
```

If you want another config path use the `--config` option:

```bash
$ python3 cross-seed.py --config /path/to/config/cross-seed.json
```

# Usage

The script has a lot of options. See `-h` or `--help` for a full list.
Here are some examples of how you'd typically run the script. For further details on flags please see the help output below.

To initially test if it seems to be working on a specific torrent that you expect to find or not find:

```bash
$ python3 cross-seed.py -v --scan-torrent /path/to/torrents/Ubuntu.20.04.2020.LTS.64.bit-CANONiCAL/ --downloadto ./torrentfiles/ --redo-all
```

To initially test if it seems to be working on a directory full of torrents that you expect to find or not find:

```bash 
$ python3 cross-seed.py -v --scan-torrents /path/to/torrents/ --downloadto ./torrentfiles/ --redo-all --limit 10
```

To run it for real:

```bash 
$ python3 cross-seed.py -v --scan-torrents /path/to/torrents/ --downloadto ./torrentfiles/
```

If you mess up and get your config file corrupted, you can completely reset it except for API keys using `--reset`. Or you can reset all information for a given tracker using `--nuke TRACKER_ABBREVIATION`.

**Cross-seed** will store all its prior work and will not repeat what it has already done unless you force it to. To do so, see the `--rescan`, `--recheck`, `--recheck-all`, `--redownload`, and `--redo-all` flags.

To control output verbosity or get useful summaries use `--verbose`, `--quiet`, `--stats`, `--show-found`, and `--show-notfound` flags.

Here is the help page as of the time of this writing:

```
usage: cross-seed.py [-h] [--config CONFIG_PATH]
                     [--scan-torrent [TORRENT_PATH [TORRENT_PATH ...]]]
                     [--scan-torrents [TORRENTS_DIR [TORRENTS_DIR ...]]]
                     [--ignore-subfolders IGNORE_SUBFOLDERS]
                     [--downloadto DOWNLOADS_DIR] [--limit LIMIT]
                     [--tracker {BLU}] [--dry-run] [--rescan] [--recheck]
                     [--recheck-all] [--redownload] [--redo-all] [--stats]
                     [--show-found] [--show-notfound] [--nuke {BLU}] [--reset]
                     [--ext-whitelist [EXT_WHITELIST [EXT_WHITELIST ...]]]
                     [--ext-blacklist [EXT_BLACKLIST [EXT_BLACKLIST ...]]]
                     [-v] [-q] [--version]

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG_PATH  Use specified config location
  --scan-torrent [TORRENT_PATH [TORRENT_PATH ...]]
                        Scan the single torrent at path
  --scan-torrents [TORRENTS_DIR [TORRENTS_DIR ...]]
                        Scan all torrents in dir
  --ignore-subfolders IGNORE_SUBFOLDERS
                        Find the torrent data starting a number of subfolders
                        into the path
  --downloadto DOWNLOADS_DIR
                        Download torrent files to this directory
  --limit LIMIT         Limit lookups/downloads per run
  --tracker {BLU}       Only apply to this tracker
  --dry-run             Scan local files only, no API operations
  --rescan              Rescan all paths even if they're known
  --recheck             Recheck availability of unfound torrents
  --recheck-all         Recheck availability of all torrents
  --redownload          Redownload torrents files
  --redo-all            Redo everything, same as --rescan --recheck-all
                        --redownload
  --stats               Print torrent and tracker statistics
  --show-found          Print torrents found on active trackers
  --show-notfound       Print torrents not found on active trackers
  --nuke {BLU}          Nuke all entries for tracker in torrents
  --reset               Delete everything but API keys. Warning: Fatal.
  --ext-whitelist [EXT_WHITELIST [EXT_WHITELIST ...]]
                        Only include files with these extensions
  --ext-blacklist [EXT_BLACKLIST [EXT_BLACKLIST ...]]
                        Ignore files with these extensions
  -v, --verbose         Verbose output
  -q, --quiet           Summary output only
  --version             Show version
```

# Help, I did things to my torrents

The script assumes it's working on the folder where your torrent client stores completed downloads.
Specifically, the script assumes each torrent is stored as-is as direct children of the downloads folder you put in `--scan-torrents`.

In general, if you want to cross-seed or re-seed or upload torrents anew, you should not touch the original files at all. Instead, you should create hard-links of the torrent files to somewhere else, where you can then re-arrange and rename things as you please.

If you have actually modified the names of the torrents downloaded, you have corrupted the meta-data and you will not be able to search for it on the trackers. In this case, you will first need to revert your changes to the original names.

If you have merely put the original torrent data inside folders of your own creation, you can instruct **Cross-seed** to ignore the first X layers of folders inside your downloads directory specified in `--scan-torrents`:

```bash
$ python3 cross-seed.py -v --scan-torrents /path/to/torrents/ --downloadto ./torrentfiles/ --ignore-subfolders 2
```

This should work for file structures like this:

```
/path/to/torrents/
/path/to/torrents/Operating Systems/
/path/to/torrents/Operating Systems/Ubuntu/
/path/to/torrents/Operating Systems/Ubuntu/Ubuntu.20.04.2020.LTS.64.bit-CANONiCAL/
```

If you have put junk files inside your torrent structures, then you will need to either filter out the extensions of these junk files, or filter which torrent files you want to find. I.e.: `--ext-blacklist txt log md`, or `--ext-whitelist iso dpkg`.

# Feedback

The script is still in a beta version. Few people have tested it so far.
If you're interested, please try out the script and keep an eye out for unexpected behaviour.
I'm especially interested in help to find:

* Scenarios that make the  script crash
* False negatives, where the script does not find a match on the tracker but the match exists
* False positives, where the script reports a match on the tracker but finds the wrong thing

If you do find anything, or just want to leave any feedback/suggestions etc, please find the relevant thread at supported trackers and I'll see it.

# I've got a bunch of torrent files, what now?

You can either use your GUI or web interface to upload the torrent files to your torrent client, or you can just dump them in the watch folder that your torrent client monitors. Your torrent client will then add the torrent files, find the data in its download directories, check the data against computed checksums and start seeding the torrent.

**Important**: You *must* ensure that your torrent client looks for data in the folder where your data is located. If your torrent client does not find the data where it expects it, it will conclude you do not have the data and it will start downloading it from the tracker. This might severely hurt your account.

I suggest you manually handle and verify the first few torrent files you add to your client for cross-seeding. You want to see that it checks your torrent and then starts seeding, without beginning to download.
