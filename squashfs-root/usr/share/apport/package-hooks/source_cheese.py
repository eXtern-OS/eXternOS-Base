import os
import subprocess
import apport.packaging
import apport.hookutils
import stat

HOME = os.path.expanduser("~")

def add_info(report, ui):
    add_tags = []

    response = ui.information("Before continuing, please close Cheese if it is already running!\n\nCheese will now be started in debugging mode.\n\nTry to reproduce the problem you are facing\nand 'Close' Cheese.")
    ## run cheese in debug mode all the bugs need this!
    os.popen("env GST_DEBUG=*cheese*:3 cheese 2>&1 | tee /dev/tty >>~/.cache/CheeseDebug.txt")

    report['CheeseDebug.txt'] = ('.cache/CheeseDebug.txt', False)
    report['lspci'] = apport.hookutils.command_output(['lspci', '-vvnn'])
    report['lsusb'] = apport.hookutils.command_output(['lsusb'])

    apport.hookutils.attach_related_packages(report, [
        "cheese",
        "cheese-common"
        ])

    ## Clear the screen to keep things tidy
    os.system("clear")

    response = ui.choice("How would you describe the problem you are facing?", ["Cheese does not work properly", "The webcam image displayed has problems"], False)

    if response == None: ## user cancelled
        raise StopIteration
    if response[0] == 1: ## the image problems are usually due to bad drivers,so we test direct video input from gstreamer to rule out cheese error
        response = ui.information("A video image will now be displayed directly from your webcam.\n\nPlease observe if it has the same image problems\nand 'Close' the window.")
        ## run gstreamer,will auto detect the src and display the webcam input
        os.system("gst-launch-1.0 autovideosrc ! videoconvert ! autovideosink")

        response = ui.choice("Did you notice the same image problem in the test video?", ["Yes", "No"], False)

    if response == None: ## user cancelled
        raise StopIteration

    if response[0] == 0: ## the issue is mostly related to bad drivers and not cheese!
        add_tags.append('gstreamer-error')
        report['SourcePackage'] = 'linux'

    if response[0] == 1: ## the video input works fine, cheese is messing up the video!
        add_tags.append('gstreamer-ok')

    dmi_dir = '/sys/class/dmi/id'
    if os.path.isdir(dmi_dir):
         for f in os.listdir(dmi_dir):
             p = '%s/%s' % (dmi_dir, f)
             st = os.stat(p)
             ## ignore the root-only ones, since they have serial numbers
             if not stat.S_ISREG(st.st_mode) or (st.st_mode & 4 == 0):
                 continue
             if f in ('subsystem', 'uevent', 'chassis_asset_tag'):
                 continue

             try:
                 value = open(p).read().strip()
             except (OSError, IOError):
                 continue
             if value:
                 report['dmi.' + f.replace('_', '.')] = value

        ## Use the hardware information to create a machine type.
    if 'dmi.sys.vendor' in report and 'dmi.product.name' in report:
         report['MachineType'] = '%s %s' % (report['dmi.sys.vendor'],
                 report['dmi.product.name'])

    apport.hookutils.attach_file(report, '/proc/cpuinfo', 'ProcCpuinfo')

    if add_tags:
        if 'Tags' in report:
            report['Tags'] += ' ' + ' '.join(add_tags)
        else:
            report['Tags'] = ' '.join(add_tags)
