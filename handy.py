
import os
import pandas as pd
import numpy as np
import re
import itertools
import io
import importlib
import subprocess

# Fix column names
def fixcols(df):
    """Simplify and ensure unique non-empty column names (remove non-latin symbols and lowercase)"""
    df.columns = [re.sub('[^a-zA-Z0-9_]', '', c).lower() for c in list(df.columns)]
    counts = {}
    names = []
    for col in df.columns:
        if col.strip() == '':
            col = 'x'
        if col in counts:
            counts[col] = counts[col] + 1
            names.append(col + str(counts[col]))
        else:
            names.append(col)
            counts[col] = 1
    df.columns = names
    return df

# Assure that some columns exist
def havecols(df, cols, fill = np.nan, types = None):
    """Ensure 'df' has columns 'cols' of type 'types'"""
    newcols = list(set(cols).difference(set(df.columns)))
    for col in newcols:
        df = df.assign(**{col: fill})
    if type(types) == list:
        for i, col in enumerate(cols):
            df[col] = df[col].apply(types[i])
    return df

# Make all combinations in dict
def expand(d):
    """Create all combination of keys in dict, e.g. {'a':[1,2], 'b': [3,4]} -> [[a1,b4],[a1,b4]...etc]"""
    return pd.DataFrame([row for row in itertools.product(*d.values())], columns=d.keys())


# freq = '1D', '1H', '15min'
def complete(df, time0, time1, freq = '15min', fillna = None):
    idx = df.index.name
    times = pd.date_range(
        pd.Timestamp(time0),
        pd.Timestamp(time1),
        freq = freq
    )
    # messes up the timezones: times = times.to_series().apply(pd.Timestamp, tz = 'CET')
    df0 = pd.DataFrame({idx: times }).set_index(idx)
    df0 = df0.join(df)
    df0 = df0.tz_convert('CET')
    if not fillna == None:
        df0 = df0.fillna(method = fillna)
    return df0


def cut(df, col, newcol, bins, labels):
    df[newcol] = pd.cut(df[col], bins = bins, labels = labels)
    df[newcol] = df[newcol].apply(lambda s: newcol + re.sub('[^0-9]', '', str(s)))
    return df

def flatcols(df, sep = '_', drop = False):
    """Flatten multi-index columns by separating level 0 and level 1 by <sep> ... drop level 0 if drop = True"""
    df = df.copy() # do not change original data-frame
    if drop:
        df.columns = [col[1] for col in df.columns.values]
    else:
        df.columns = [sep.join([str(c) for c in col]) for col in df.columns.values]
    return df

def atm(t = 'now', u = 'H', n = 0):
    return pd.Timestamp(t, tz = 'CET').floor(u) + n * pd.Timedelta(u)

def rtm(n = 0, u = 'H'):
    return atm('now', u = u, n = n)


# Walk a trail into the data and retrieve a None or a value
def descent(data, trail, fail = None):
    """Safely retrieve subitems from (deep) lists or dicts"""

    # always ensure our trail is a list
    if type(trail) != list:
        trail = [trail]

    # walk the trail
    for step in trail:
        
        # escape if we cannot descent into data
        if type(data) != dict and type(data) != list:
            return fail
        
        # escape if we have a non-integer step in list trail
        if type(data) == list and type(step) != int:
            return fail
        
        # check if step is in dictionary
        if type(data) == dict and not step in data:
            return fail
        
        # check if item is in list
        if type(data) == list and len(data) <= step: # abs() for -1 index retrieval?
            return fail
        
        # safely take one step
        data = data[step]
        
    # If found, but None, still return desired fail value
    if data is None:
        data = fail
    
    return data

# Inverse a dict mapping {'a': 'b'} -> {'b': 'a'}
def inv(mapping):
    """Inverse a mapping dict {'key': 'val'} -> {'val': 'key'}"""
    invmap = {}
    for key, val in mapping.items():
        invmap[val] = key
    return invmap

# Disable https warnings
def dontwarn():
    """Disable warning for non-verified https requests"""
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        print('disabled https warnings')
    except Exception:
        print('cannot disable https warnings')

def flatlist(lst):
    """Flatten list of lists into list"""
    return list(itertools.chain(*lst))

def rls(f):
    """Recursive listing of files in folder"""
    if os.path.isdir(f):
        l = os.listdir(f)
        return sum([rls(f + '/' + i) for i in l], [])
    else:
        return [f.lower()]

def mkdir(folder):
    """Safely create folder ... """
    return os.mkdir(folder) if not os.path.exists(folder) else None

def aslist(x):
    """Make sure to always return a list object"""
    return x if type(x) == list else list()

def asstr(x):
    """Make sure to always return a str object"""
    return x if type(x) == str  else str()

def saferead(file, fail = ''):
    """Safely read file and always return 'fail'"""
    if not os.path.isfile(file):
        return fail
    with open(file, 'r') as fp:
        return fp.read()

saveread = saferead

def read_tail(file, nchars = 1000, **kwargs):
    """read only <nchars> bytes from end of <file> and return pandas dataframe (passing **kwargs to pd)"""
    f = open(file, 'rb')
    n = f.seek(-nchars, os.SEEK_END)
    s = f.readlines()
    f.close()
    s[0] = b''
    s = b''.join(s)
    s = s.decode('utf8')
    data = pd.read_csv(io.StringIO(s), header = None, **kwargs)
    return data

def read_log(file, nchars = 1000):
    """read only <nchars> bytes from end of <file>"""
    if not os.path.exists(file) or not os.path.isfile(file):
        print('read_log: warning: file doesn\'t exist')
        return None
    with open(file, 'rb') as f:
        size = os.path.getsize(file)
        if size == 0:
            return ''
        n = min(size, nchars)
        n = f.seek(-n, os.SEEK_END)
        s = f.readlines()
        if len(s) > 1 and size > nchars: s[0] = b''
        s = b''.join(s)
        s = s.decode('utf8')
        return s

#data = read_tail('./cache/task01.sts', 1000, sep = '\t')


def uncache(libs):
    """Reload libraries (libs = list of modules)"""
    lib1 = []
    for lib in libs:            
        lib = importlib.reload(lib)
        lib1.append(lib)
    return lib1

# Proxy fix Nabi
def proxyoff():
    os.environ['HTTP_PROXY'] = ''
    os.environ['HTTPS_PROXY'] = ''

# Get first host-ip found on windows computers using ip
def gethost():
    ipconfig = subprocess.run(['ipconfig'], stdout = subprocess.PIPE)
    stdout = ipconfig.stdout.decode('utf-8')
    pattern = r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'
    host = re.findall(pattern, stdout)[0]
    return host
