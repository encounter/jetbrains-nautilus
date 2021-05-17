# JetBrains (Toolbox) Nautilus Extension
#
# Place this in ~/.local/share/nautilus-python/extensions
# Install the python-nautilus package and restart Nautilus.

import json
import os
from distutils.version import LooseVersion
from subprocess import Popen, DEVNULL

from gi import require_version
from gi.repository import Nautilus, GObject

require_version('Gtk', '3.0')
require_version('Nautilus', '3.0')

APPS_BASE = os.environ.get('HOME') + '/.local/share/JetBrains/Toolbox/apps'


def check_channel(base, v):
    return str.startswith(v, 'ch-') and \
           os.path.isdir(os.path.join(base, v))


def check_version(base, v):
    return os.path.isdir(os.path.join(base, v)) and \
           os.path.isfile(os.path.join(base, v, 'product-info.json'))


def find_versions(app):
    results = []
    app_base = os.path.join(APPS_BASE, app)
    channels = [v for v in os.listdir(app_base) if check_channel(app_base, v)]
    for channel in channels:
        channel_base = os.path.join(app_base, channel)
        versions = sorted([LooseVersion(v) for v in os.listdir(channel_base) if check_version(channel_base, v)],
                          reverse=True)
        if len(versions) == 0:
            continue
        latest_version = str(versions[0])
        version_base = os.path.join(channel_base, latest_version)
        with open(os.path.join(version_base, 'product-info.json')) as f:
            product_info = json.load(f)
        product_name = product_info['name']
        if 'versionSuffix' in product_info:
            product_name += ' ' + product_info['versionSuffix']
        launch_info = product_info['launch'][0]
        launch_args = [os.path.join(version_base, launch_info['launcherPath'])]
        if 'startupWmClass' in launch_info:
            launch_args.extend(['--class', launch_info['startupWmClass']])
        icon_path = os.path.join(version_base, product_info['svgIconPath'])
        results.append([product_name, launch_args, icon_path])
    return results


def find_apps():
    results = []
    apps = os.listdir(APPS_BASE)
    for app in apps:
        results.extend(find_versions(app))
    return sorted(results, key=lambda result: result[0])


class JetbrainsExtension(GObject.GObject, Nautilus.MenuProvider):

    # noinspection PyMethodMayBeStatic
    def launch(self, menu, launch, files):
        Popen([*launch, *[file.get_location().get_path() for file in files]],
              start_new_session=True, stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL)

    def get_file_items(self, window, files):
        apps = find_apps()
        if len(apps) == 0:
            return []
        root_item = Nautilus.MenuItem(
            name='JetBrainsOpen',
            label='Open in JetBrains...',
            tip='Opens the selected files with a JetBrains product'
        )
        menu = Nautilus.Menu()
        for [app_name, launch, icon] in apps:
            item = Nautilus.MenuItem(
                name=str.replace(app_name, ' ', '') + 'Open',
                label=app_name,
                tip='Opens the selected files with ' + app_name,
                icon=icon
            )
            item.connect('activate', self.launch, launch, files)
            menu.append_item(item)
        root_item.set_submenu(menu)
        return root_item,

    def get_background_items(self, window, file_):
        apps = find_apps()
        if len(apps) == 0:
            return []
        root_item = Nautilus.MenuItem(
            name='JetBrainsOpenBackground',
            label='Open in JetBrains...',
            tip='Opens a JetBrains product in the current directory'
        )
        menu = Nautilus.Menu()
        for [app_name, launch, icon] in apps:
            item = Nautilus.MenuItem(
                name=str.replace(app_name, ' ', '') + 'OpenBackground',
                label=app_name,
                tip='Opens ' + app_name + ' in the current directory',
                icon=icon
            )
            item.connect('activate', self.launch, launch, [file_])
            menu.append_item(item)
        root_item.set_submenu(menu)
        return root_item,
