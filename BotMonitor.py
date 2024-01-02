""" Program run on the remote machine to handle automatic restart of the bot if it hard crashes. """
from psutil import process_iter, NoSuchProcess, AccessDenied, ZombieProcess
import time
import os

check_rate = 15     # in mins
program_name = 'PaladinsAssistant.py'
log_name = 'bot_auto_log.txt'

while True:
    bFound = False
    # Loop through all running process and see if we find it
    for proc in process_iter():
        try:
            if 'python' in proc.name().lower():
                for parm in proc.cmdline():
                    if program_name in parm:
                        bFound = True
                        break

        except (NoSuchProcess, AccessDenied, ZombieProcess):
            pass

    # Check if the process was not running and then restart it
    if not bFound:
        os.system(f'nohup python3 -u PaladinsAssistant.py > {log_name} &')
        print("Program was not found to be running")
    else:
        print("Program is still running :)")

    # Delay checking again
    time.sleep(60 * check_rate)
