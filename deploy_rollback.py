import sys
sys.argv = ['deploy_ota.py', 'remote', 'thermostat.py', 'webserver.py']
exec(open('deploy_ota.py').read())
