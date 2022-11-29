import requests
import sys
import os

def upload(file):
    global config
    """
    Upload a file to the remote
    :param config: configuration info
    :param file: filename to upload
    :return:
    """
    if not os.path.exists(file):
        return None

    filedata = open(file, 'rb')
    url = f"http://{config['hostname']}/fs/{file}"
    basic = requests.auth.HTTPBasicAuth('', config['password'])
    headers = {'X-Timestamp': str(int(os.path.getmtime(file)) *1000)}
    resp = requests.put(url, data=filedata, auth=basic, headers=headers)
    return resp

def getfiles(path):
    """
    Retrieve a list of local files
    :param path: path to scan for files
    :return: list of dicts of file details
    """
    global config

    flist = []
    files = [f for f in os.listdir(path) if os.path.isfile(f)]
    for file in files:
        fdata = {}
        # Skip ourselves
        if file == config['name']:
            continue

        fdata['name'] = file
        fdata['file_size'] = int(os.path.getsize(file))
        if config['WOeventimestamp']:
            fdata['modified_s'] = int(os.path.getmtime(file)/2)*2
        else:
            fdata['modified_s'] = int(os.path.getmtime(file))
        flist.append(fdata)
    return flist

def getremotefiles():
    global config
    # hostname,password):
    """
    Retreive the list of remote files in the root
    :param hostname: host to connect to
    :param password: password to auth with
    :return: list of dicts of file details
    """
    # Yes, the dot is important - it gets the directory contents!
    url = f"http://{config['hostname']}/fs/."
    basic = requests.auth.HTTPBasicAuth('', config['password'])
    headers = {'Accept':'application/json'}
    resp = requests.get(url,  auth=basic, headers=headers)
    # Clean up the list
    remotefiles=[]
    for item in resp.json():
        if item['directory'] is True:
            continue
        else:
            item['modified_s'] = int(item['modified_ns']/1000000000)
            remotefiles.append(item)
    return remotefiles

def findfilestoupdate(localfiles, remotefiles):
    """
    Compare two lists of files to identify changed by size and date
    :param localfiles: list of dicts of file details
    :param remotefiles: list of dicts of file details
    :return: list of dict with file details
    """
    updatefiles = []
    for file in localfiles:
        update = False
        res = next((sub for sub in remotefiles if sub['name'] == file['name']), None)
        # The file doesn't exist remotely
        if res is None:
            update = True
        else:
            if res['modified_s']<file['modified_s']:
                update = True

            if res['file_size'] != file['file_size']:
                update = True

            if res['modified_s'] > file['modified_s']:
                update = False
                print(f" ! {file['name']} is newer om remote! Not touching.")
                print(f"{file['name']} - Local:{file['modified_s']} older than remote:{res['modified_s']} ")
        if update:
            updatefiles.append(file)
    return updatefiles

def getdevice():
    global config
    url = f"http://{config['hostname']}/cp/version.json"
    basic = requests.auth.HTTPBasicAuth('', config['password'])
    headers = {'Accept': 'application/json'}
    resp = requests.get(url, auth=basic, headers=headers)
    return resp.json()

def getdevices():
    global config
    url = f"http://{config['hostname']}/cp/devices.json"
    basic = requests.auth.HTTPBasicAuth('', config['password'])
    headers = {'Accept': 'application/json'}
    resp = requests.get(url, auth=basic, headers=headers)
    return resp.json()

def checkaccess():
    global config
    url = f"http://{config['hostname']}/fs/."
    basic = requests.auth.HTTPBasicAuth('', config['password'])
    headers = {'Accept': 'application/json'}
    resp = requests.get(url, auth=basic, headers=headers)
    return resp.status_code

def main():
    global config

    data = getdevice()
    print(f" Connected to {data['hostname']} ({data['board_id']} - {data['mcu_name']}) at {data['ip']}")
    # Make sure we lock onto this host
    config['hostname'] = data['hostname']

    if checkaccess() == 401:
        print(' ! Wrong password specified')
        quit(1)

    rf = getremotefiles()
    lf = getfiles('.')

    updatelist = findfilestoupdate(lf, rf)

    if len(updatelist) == 0:
        print(' * All files are up to date, nothing to do.')
        quit(2)

    print(f' * Going to upload {len(updatelist)} files.')
    for item in updatelist:
        print(f" * Uploading {item['name']}")
        upload(item['name'])

def showusage():
    global config
    print(f"{config['name']} - upload files in current directory to Web Workflow enabled board\n\n"
          f" Usage:\n"
          f"     {config['name']} [hostname] [password]\n")
    quit(1)

def cleaninput(val: str):
    """
    Clean up parameters as necessary
    :param val: string to clean up
    :return: String potentially cleaned up
    """
    # Strip quote marks
    if (val.startswith('"') and val.endswith('"')) or \
            (val.startswith("'") and val.endswith("'")):
        val = val[1:-1]

    return val

config = {
    'WOeventimestamp': True,
    'hostname': '',
    'password':'',
    'name': f'{os.path.basename(sys.argv[0])}'
}

if len(sys.argv) != 3:
    showusage()

config['hostname'] = sys.argv[1]
config['password'] = sys.argv[2]

if __name__ == "__main__":
    main()


