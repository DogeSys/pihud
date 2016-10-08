import os
import sys
import obd
import shutil
import subprocess
import time
from PiHud import PiHud
from PyQt4 import QtGui
from GlobalConfig import GlobalConfig

try:
    import RPi.GPIO as GPIO
except:
    print "[pihud] Warning: RPi.GPIO library not found"

# file paths
running_dir = os.path.dirname(os.path.realpath(__file__))
default_config_path = os.path.join(running_dir, 'default.rc')
config_path = os.path.join(os.path.expanduser('~'), 'pihud.rc')


def main():
    """ entry point """

    # ============================ Config loading =============================

    if not os.path.isfile(config_path):
        # copy the default config
        if not os.path.isfile(default_config_path):
            print "[pihud] Fatal: Missing default config file. Try reinstalling"
            sys.exit(1)
        else:
            shutil.copyfile(default_config_path, config_path)

    global_config = GlobalConfig(config_path)

    # =========================== OBD-II Connection ===========================

    if global_config["debug"]:
        obd.logger.setLevel(obd.logging.DEBUG)  # enables all debug information

    connection = obd.OBD()

    # if global_config["debug"]:
    #     for i in range(32):
    #         connection.supported_commands.append(obd.commands[1][i])

    # ============================ QT Application =============================

    app = QtGui.QApplication(sys.argv)
    pihud = PiHud(global_config, connection)

    # ============================== GPIO Setup ===============================

    try:
        pin = pihud.config.page_adv_pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin,
                   GPIO.IN,
                   pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(pin,  # Adjusted this from GIO to GPIO, to resolve incorrect ref
                              GPIO.FALLING,
                              callback=pihud.next_page,
                              bouncetime=200)
    except:
        pass

    # ================================= Start =================================
    """This subroutine is used to create a new command and query, then using that routine, can determine
        a shutdown condition that fits our needs"""

    def check_timeout():
        timeout = time.time() + 3
        if in_RPM == 0 & time.time() > timeout:
            connection.close()
            subprocess.call("./shutdown.sh", shell=True)
            sys.exit()

    cmd_RPM = obd.commands.RPM
    in_RPM = connection.query(cmd_RPM)

    # The simple logic gate, if there is a connection continously check the timout method
    # while connection.is_connected():
        # check_timeout()

    # --------------------------------------------------------------------------

    status = app.exec_()  # blocks until application quit

    # ================================= Exit ==================================

    connection.close()
    sys.exit(status)


if __name__ == "__main__":
    main()
