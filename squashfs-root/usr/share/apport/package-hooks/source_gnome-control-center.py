import os, apport.packaging, re
import glob
from apport.hookutils import *

def add_info(report):
	# the issue is not in the gnome-control-center code so reassign
	if "Stacktrace" in report and "/control-center-1/" in report["Stacktrace"]:
		for words in report["Stacktrace"].split():
			if words.startswith("/usr/lib/") and "/control-center-1/" in words:
			    if apport.packaging.get_file_package(words) != 'gnome-control-center':
    				report.add_package_info(apport.packaging.get_file_package(words))
    				return    				
			    component = re.compile("lib(\w*).so").search(words).groups(1)[0]
			    report['Title'] = '[%s]: %s' % (component, report.get('Title', report.standard_title()))
			    report['Tags'] = '%s %s' % (report.get('Tags', ""), component)
			    break # Stop on the first .so that's the interesting one

	# collect informations on the /usr/lib/control-center-1 components 
	plugin_packages = set()
	for paneldir in (['/usr/lib/control-center-1'] + glob.glob('/usr/lib/*/control-center-1')):
		for dirpath, dirnames, filenames in os.walk(paneldir):
			for filename in filenames:
				path = os.path.join(dirpath, filename)
				package = apport.packaging.get_file_package(path)
				if package == 'gnome-control-center':
					continue
				if not package:
					continue

				plugin_packages.add(package)
		if plugin_packages:
			report["usr_lib_gnome-control-center"] = package_versions(*sorted(plugin_packages))
