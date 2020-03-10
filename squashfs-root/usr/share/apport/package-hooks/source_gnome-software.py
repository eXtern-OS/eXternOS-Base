import apport.packaging

def add_info(report, ui):
    report["InstalledPlugins"] = apport.hookutils.package_versions(
        'gnome-software-plugin-flatpak',
        'gnome-software-plugin-limba',
        'gnome-software-plugin-snap')
