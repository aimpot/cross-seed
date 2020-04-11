#!/usr/bin/env python3
# Source: https://github.com/aimpot/cross-seed
# Are you staff and want this for your tracker? Reach out.

# Credits client: aimpot
# Credits testing: Peterlol2x
# Credits tracker api: Mewtwo

# Do not make changes to this file.
# A config file will be created on first run. Make your changes in the config file.

import json, os, sys, argparse, requests, tempfile, time, traceback, string

version = '0.4'
config = None
config_path = 'cross-seed.json'
supported_trackers = ['BLU']
default_config = {
    'api_keys': dict([(tracker, '') for tracker in supported_trackers]),
    'torrents': dict(),
}

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('--config', dest='config_path', default=config_path, help='Use specified config location')
parser.add_argument('--scan-torrent', dest='torrent_path', default=[], nargs='*', help='Scan the single torrent at path')
parser.add_argument('--scan-torrents', dest='torrents_dir', default=[], nargs='*', help='Scan all torrents in dir')
parser.add_argument('--ignore-subfolders', dest='ignore_subfolders', type=int, default=0, help='Find the torrent data starting a number of subfolders into the path')
parser.add_argument('--downloadto', dest='downloads_dir', help='Download torrent files to this directory')
parser.add_argument('--limit', dest='limit', type=int, default=-1, help='Limit lookups/downloads per run')
parser.add_argument('--tracker', dest='tracker', choices=supported_trackers, default='', help='Only apply to this tracker')
parser.add_argument('--dry-run', dest='dry_run', default=False, action='store_true', help='Scan local files only, no API operations')
parser.add_argument('--rescan', dest='rescan', default=False, action='store_true', help="Rescan all paths even if they're known")
parser.add_argument('--recheck', dest='recheck', default=False, action='store_true', help="Recheck availability of unfound torrents")
parser.add_argument('--recheck-all', dest='recheck_all', default=False, action='store_true', help="Recheck availability of all torrents")
parser.add_argument('--redownload', dest='redownload', default=False, action='store_true', help="Redownload torrents files")
parser.add_argument('--redo-all', dest='redo_all', default=False, action='store_true', help='Redo everything, same as --rescan --recheck-all --redownload')
parser.add_argument('--stats', dest='stats', default=False, action='store_true', help='Print torrent and tracker statistics')
parser.add_argument('--show-found', dest='show_found', default=False, action='store_true', help='Print torrents found on active trackers')
parser.add_argument('--show-notfound', dest='show_notfound', default=False, action='store_true', help='Print torrents not found on active trackers')
parser.add_argument('--nuke', dest='nuke', choices=supported_trackers, default='', help='Nuke all entries for tracker in torrents')
parser.add_argument('--reset', dest='reset', default=False, action='store_true', help='Delete everything but API keys. Warning: Fatal.')
parser.add_argument('--ext-whitelist', dest='ext_whitelist', default=[], nargs='*', help='Only include files with these extensions')
parser.add_argument('--ext-blacklist', dest='ext_blacklist', default=[], nargs='*', help='Ignore files with these extensions')
parser.add_argument('-v', '--verbose', dest='verbose', default=False, action='store_true', help='Verbose output')
parser.add_argument('-q', '--quiet', dest='quiet', default=False, action='store_true', help='Summary output only')
parser.add_argument('--version', dest='version', default=False, action='store_true', help='Show version')
args = parser.parse_args()
if args.redo_all:
    args.rescan = True
    args.recheck_all = True
    args.redownload = True

def log(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(''.join([c if c in string.printable else '?' for c in text]))

def load_config():
    try:
        with open(args.config_path) as f:
            config = json.load(f)
        if args.verbose:
            log("Using config: '%s'" % args.config_path)
        return config
    except ValueError:
        log('Existing config file is corrupted. Please fix or delete it. Aborting. Trace:\n%s' % traceback.format_exc())
        sys.exit(-1)
    except FileNotFoundError:
        pass
    return None

def save_config():
    with open(args.config_path, 'w') as f:
        json.dump(config, f, indent=4, sort_keys=True)

def ext_is_bad(path):
    ext = path.split(os.path.extsep)[-1]
    if ext in args.ext_blacklist:
        return True
    if args.ext_whitelist and ext not in args.ext_whitelist:
        return True
    return False

def scan_torrent(scan_path):
    prefix = os.path.dirname(scan_path.rstrip(os.path.sep))
    name = scan_path[len(prefix):].strip(os.path.sep)
    if name in config['torrents'] and not args.rescan:
        return 0

    path = ''
    size = 0
    if os.path.isfile(scan_path):
        if ext_is_bad(scan_path):
            return 0
        path = scan_path
        size = os.path.getsize(scan_path)
    elif os.path.isdir(scan_path):
        for dirpath, dirnames, filenames in os.walk(scan_path):
            for f in filenames:
                if ext_is_bad(scan_path):
                    continue
                path = os.path.join(dirpath, f)
                if not os.path.islink(path):
                    size += os.path.getsize(path)
    else:
        raise Exception('Path type not supported: "%s"' % scan_path)

    if size == 0:
        return 0

    path = path[len(prefix):].strip(os.path.sep)

    if args.verbose:
        log("Found new torrent: '%s'" % name)
    trackers = config['torrents'][name]['trackers'] if name in config['torrents'] else dict()
    config['torrents'][name] = {
        'path': path,
        'size': size,
        'trackers': trackers,
    }
    return 1

def scan_torrents(scan_dir, skip=0):
    new = 0
    for torrent in os.listdir(scan_dir):
        subdir = os.path.join(scan_dir, torrent)
        if skip != 0 and not os.path.isdir(subdir):
            log("Skipping non-dir before ignore-subfolders reached: '%s'" % subdir)
            continue
        new += scan_torrent(subdir) if skip == 0 else scan_torrents(subdir, skip - 1)
    return new

def lookup_torrent(tracker, name, d):
    if tracker == 'BLU':
        j = requests.get('https://blutopia.xyz/api/torrents/filter', params={
            'api_token': config['api_keys'][tracker],
            'file_name': d['path'],
            'size': d['size']
        }).json()
        url =  j['data'][0]['attributes']['download_link'] if len(j['data']) == 1 else ''
        if not args.quiet:
            log("BLU lookup %ssuccessful on '%s'" % ('' if url else 'not ', name))
        return url
    else:
        raise Exception('Tracker "%s" not supported.' % tracker)

def download_torrent(tracker, name, d):
    res = requests.get(d['trackers'][tracker]['torrent_url'], params={'stream':True})

    fd, tmp_path = tempfile.mkstemp()
    if res.status_code == 200:
        with open(fd, 'wb') as f:
            for chunk in res.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    else:
        raise Exception('Bad status code %d on "%s"' % (res.status_code, d['trackers'][tracker]['torrent_url']))

    torrent_filename = '[%s]%s.torrent' % (tracker, name)
    torrent_path = os.path.join(args.downloads_dir, torrent_filename)
    os.rename(tmp_path, torrent_path)
    if not args.quiet:
        log("Downloaded '%s'" % torrent_path)

# Load config
config = load_config()
if not config:
    if args.verbose:
        log('No config file found. Creating fresh config.')

    config = default_config
    save_config()

# Reset config
if args.reset:
    log('Config reset. Hope you meant to do that.')
    config['torrents'] = dict()
    save_config()
    sys.exit(0)

# Get active trackers (supported + API keys available)
if args.tracker:
    active_trackers = [args.tracker] if args.tracker in supported_trackers and config['api_keys'][args.tracker] else []
else:
    active_trackers = list(filter(lambda x: x in supported_trackers and config['api_keys'][x], config['api_keys']))
if args.verbose:
    log("API keys loaded for trackers: '%s'" % ', '.join(active_trackers))

# Show version
if args.version:
    log('cross-seed %s (https://github.com/aimpot/cross-seed)' % version)
    sys.exit(0)

# Nuke entries of tracker in torrents
if args.nuke:
    for torrent in config['torrents']:
        config['torrents'][torrent]['trackers'].pop(args.nuke, None)
    log('Nuked %s entries in all torrents' % args.nuke)

    save_config()
    sys.exit(0)

# Print torrent and tracker statistics
if args.stats:
    total_count = len(config['torrents'])
    total_size = 0
    count = dict(zip(active_trackers, [0]*len(active_trackers)))
    count_seedable = dict(zip(active_trackers, [0]*len(active_trackers)))
    size = dict(zip(active_trackers, [0]*len(active_trackers)))
    size_seedable = dict(zip(active_trackers, [0]*len(active_trackers)))
    for torrent in config['torrents']:
        torrent = config['torrents'][torrent]
        total_size += torrent['size']
        for tracker in torrent['trackers']:
            count[tracker] += 1 if torrent['trackers'][tracker]['torrent_url'] else 0
            count_seedable[tracker] += 1 if torrent['trackers'][tracker]['downloaded'] else 0
            size[tracker] += torrent['size'] if torrent['trackers'][tracker]['torrent_url'] else 0
            size_seedable[tracker] += torrent['size'] if torrent['trackers'][tracker]['downloaded'] else 0

    log('Total torrent count: %d' % total_count)
    log('Total torrents size: %.2f GiB' % (total_size / 1024**3))
    for tracker in active_trackers:
        if count[tracker] == 0:
            continue
        log('%s torrent count: %d (%d seedable)' % (tracker, count[tracker], count_seedable[tracker]))
        log('%s torrents size: %.2f GiB (%.2f GiB seedable)' % (tracker, size[tracker] / 1024**3, size_seedable[tracker] / 1024**3))

    sys.exit(0)

# Print torrents found or not found on active trackers
if args.show_found or args.show_notfound:
    count = dict(zip(active_trackers, [0]*len(active_trackers)))
    for torrent in config['torrents']:
        t = config['torrents'][torrent]
        for tracker in t['trackers']:
            found = 'torrent_url' in t['trackers'][tracker] and t['trackers'][tracker]['torrent_url']
            match = (found and args.show_found) or (not found and args.show_notfound)
            if not match:
                continue
            count[tracker] += 1 if match else 0
            log("%s %s '%s'" % (tracker, 'has' if found else 'does not have', torrent))
    for tracker in count:
        log('%s %s %d / %d torrents.' % (tracker, 'has' if args.show_found else 'does not have', count[tracker], len(config['torrents'])))

    sys.exit(0)

# Scan paths for torrents
if args.torrent_path or args.torrents_dir:
    new = 0
    for p in args.torrent_path:
        if not os.path.exists(p):
            log("Path not found, breaking: '%s'" % p)
            break
        new += scan_torrent(p)
    for d in args.torrents_dir:
        if not os.path.exists(d):
            log("Path not found, breaking: '%s'" % d)
            break
        new += scan_torrents(d, args.ignore_subfolders)

    save_config()
    log('Scan found %d new torrent(s)' % new)
else:
    if args.verbose:
        log('No paths to scan, skipping.')

# Verify APIs are configured
if not active_trackers:
    if args.verbose:
        log('No tracker API keys specified, skipping lookups and downloads.')
    log("Please add your API keys to the config file '%s'" % args.config_path)
    log('IMPORTANT: Do not share your API keys or download links with anyone.')

# Check trackers for torrents
if active_trackers and not args.dry_run:
    count = 0
    for torrent in config['torrents']:
        if count == args.limit:
            if not args.quiet:
                log('Limit of %d lookups reached, stopping.' % args.limit)
            break
        d = config['torrents'][torrent]
        for tracker in active_trackers:
            if tracker in d['trackers']:
                if not args.recheck and not args.recheck_all:
                    continue
                elif args.recheck and d['trackers'][tracker]['torrent_url']:
                    continue

            url = lookup_torrent(tracker, torrent, d)
            downloaded = d['trackers'][tracker]['downloaded'] if tracker in d['trackers'] and url != d['trackers'][tracker]['torrent_url'] else False
            d['trackers'][tracker] = {
                'torrent_url': url,
                'downloaded': downloaded,
            }
            count += 1
            time.sleep(1)

    save_config()

# Download torrents from trackers
if active_trackers and not args.dry_run and args.downloads_dir:
    try:
        os.makedirs(args.downloads_dir)
    except FileExistsError as e:
        if not os.path.isdir(args.downloads_dir):
            raise e

    count = 0
    for torrent in config['torrents']:
        if count == args.limit:
            if not args.quiet:
                log('Limit of %d downloads reached, stopping.' % args.limit)
            break
        d = config['torrents'][torrent]
        for tracker in active_trackers:
            if tracker not in d['trackers']:
                continue
            if not d['trackers'][tracker]['torrent_url']:
                continue
            if d['trackers'][tracker]['downloaded'] and not args.redownload:
                continue

            download_torrent(tracker, torrent, d)
            config['torrents'][torrent]['trackers'][tracker]['downloaded'] = True
            count += 1
            time.sleep(1)

    save_config()
