import os, apport.packaging
from apport.hookutils import *

def add_info(report):
	# the crash is not in nautilus code so reassign
	if "Stacktrace" in report and "/usr/lib/nautilus" in report["Stacktrace"]:
		for words in report["Stacktrace"].split():
			if words.startswith("/usr/lib/nautilus"):
				report.add_package_info(apport.packaging.get_file_package(words))
				return

	# collect informations on the /usr/lib/nautilus components 
	plugin_packages = set()
	for dirpath, dirnames, filenames in os.walk("/usr/lib/nautilus"):
		for filename in filenames:
			path = os.path.join(dirpath, filename)
			package = apport.packaging.get_file_package(path)
			if package == 'nautilus':
				continue

			plugin_packages.add(package)

	report["usr_lib_nautilus"] = package_versions(*sorted(plugin_packages))
	attach_gsettings_package(report, 'nautilus-data')

