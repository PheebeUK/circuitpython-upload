# circuitpython-upload
A simple uploader script for the CircuitPython web workflow. 
Basically, call it with a hostname and password and it'll compare the local directory with the remote and upload newer files.

## Usage
`upload.py [hostname] [password]`

Yu can use circuitpython.local as the hostname as long as there's only one device on your network. Otehrwise it's better to specify the name of the device!

I use it in Pycharm so I can hit run on the upload script and it'll upload changed files.
