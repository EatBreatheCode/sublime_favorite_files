import sublime
import sublime_plugin

import os

from .lib.packages import *
from .lib.output_view import output_to_view

###-----------------------------------------------------------------------------

class OverrideAuditDiffOverrideCommand(sublime_plugin.WindowCommand):
    def _perform_diff(self, pkg_info, file):
        settings = sublime.load_settings("OverrideAudit.sublime-settings")
        action = settings.get("diff_unchanged", "diff")

        diff_info = pkg_info.override_diff(file, settings.get("diff_context_lines", 3))

        if diff_info is None:
            return

        if diff_info == "":
            sublime.status_message("No changes detected in override")

            if action == "open":
                full_filename = os.path.join(sublime.packages_path(), pkg_info.name, file)
                self.window.open_file(full_filename)
                return
            elif action == "ignore":
                return

        output_to_view(self.window,
           "Override of %s" % os.path.join(pkg_info.name, file),
           "No differences found" if diff_info == "" else diff_info,
           reuse=settings.get("reuse_views", True),
           clear=settings.get("clear_existing", True),
           syntax="Packages/Diff/Diff.sublime-syntax")

    def _file_pick(self, pkg_info, override_list, index):
        if index >= 0:
            self._perform_diff(pkg_info, override_list[index])

    def _show_override_list(self, pkg_info):
        override_list = list(pkg_info.override_files())
        if not override_list:
            print("Package '%s' has no overrides" % pkg_info.name)
        self.window.show_quick_panel(
            items=override_list,
            on_select=lambda i: self._file_pick(pkg_info, override_list, i))

    def _pkg_pick(self, pkg_list, pkg_override_list, index):
        if index >= 0:
            self._show_override_list(pkg_list[pkg_override_list[index]])

    def _show_pkg_list(self, pkg_list):
        settings = sublime.load_settings("OverrideAudit.sublime-settings")
        ignored = settings.get("ignore_overrides_in", [])

        items = [name for name,pkg in pkg_list if len(pkg.override_files()) > 0
                                                  and name not in ignored]
        if not items:
            print("No unignored packages have overrides")
        self.window.show_quick_panel(
                items=items,
                on_select=lambda i: self._pkg_pick(pkg_list, items, i))

    def run(self, package=None, file=None):
        pkg_list = PackageList()

        if package is None:
            self._show_pkg_list(pkg_list)
        else:
            if package in pkg_list:
                pkg_info = pkg_list[package]
                if file is None:
                    self._show_override_list(pkg_info)
                else:
                    if pkg_info.has_possible_overrides():
                        self._perform_diff(pkg_info, file)
                    else:
                        print("Package '%s' has no overrides to diff" % package)
            else:
                print("Unable to diff; no such package '%s'" % package)

###-----------------------------------------------------------------------------

class OverrideAuditListPackagesCommand(sublime_plugin.WindowCommand):
    def run(self):
        pkg_list = PackageList()
        pkg_counts = pkg_list.package_counts()

        settings = sublime.load_settings("OverrideAudit.sublime-settings")

        title = "Packages: {} ({} dependencies)".format(len(pkg_list), pkg_counts[4])
        t_sep = "=" * len(title)

        stats = ("Shipped:   {:<6} (Shipped with Sublime)\n"
                 "Installed: {:<6} (Installed as sublime-package files)\n"
                 "Unpacked:  {:<6} (Unpacked in Packages\\ directory)\n"
                 "Disabled:  {:<6} (Currently in ignored_packages)\n").format(*pkg_counts)

        row = "| {:<40} | {:3} | {:3} | {:<3} |".format("", "", "", "")
        r_sep = "-" * len(row)

        result = [title, t_sep, "", stats, r_sep]
        for pkg_name, pkg_info in pkg_list:
            if pkg_info.is_disabled:
                pkg_name = "[{}]".format (pkg_name)
            elif pkg_info.is_dependency:
                pkg_name = "<{}>".format (pkg_name)
            result.append (
                "| {:<40} | [{:1}] | [{:1}] | [{:1}] |".format(
                pkg_name,
                "S" if pkg_info.shipped_path is not None else " ",
                "I" if pkg_info.installed_path is not None else " ",
                "U" if pkg_info.unpacked_path is not None else " "))
        result.extend([r_sep, ""])

        output_to_view(self.window,
                       "OverrideAudit: Package List",
                       result,
                       reuse=settings.get("reuse_views", True),
                       clear=settings.get("clear_existing", True),
                       syntax="Packages/OverrideAudit/syntax/OverrideAudit-table.sublime-syntax")

###-----------------------------------------------------------------------------

# This is still crude as hell; proof of proof of concept type styff
class OverrideAuditListPackageOverridesCommand(sublime_plugin.WindowCommand):
    def run(self):
        pkg_list = PackageList()
        pkg_counts = pkg_list.package_counts()

        settings = sublime.load_settings("OverrideAudit.sublime-settings")
        ignored = settings.get ("ignore_overrides_in", [])

        result = []
        for pkg_name, pkg_info in pkg_list:
            normal_overrides = pkg_info.override_files(simple=True)
            shipped_overrides = pkg_info.override_files(simple=False)
            if pkg_name in ignored or (not normal_overrides and not shipped_overrides):
               continue

            if pkg_info.is_disabled:
                pkg_name = "[{}]".format (pkg_name)
            elif pkg_info.is_dependency:
                pkg_name = "<{}>".format (pkg_name)

            result.append (
                "[{}{}{}] {}".format(
                "S" if pkg_info.shipped_path is not None else " ",
                "I" if pkg_info.installed_path is not None else " ",
                "U" if pkg_info.unpacked_path is not None else " ",
                pkg_name))

            # Technically this makes no sense at some level because sublime is
            # ignoring the shipped version entirely, so the list of files can be
            # radically different. However this still seems useful at some
            # level. Possibly add an option to exclude these or change the text
            # to be more expressive?
            if shipped_overrides:
                result.append("  `- Complete Overrides")
                result.extend(["    `- {}".format(item) for item in shipped_overrides])

            if normal_overrides:
                result.append("  `- Simple Overrides")
                result.extend(["    `- {}".format(item) for item in normal_overrides])

        if len(result) == 0:
            result.append("No packages with overrides found")

        output_to_view(self.window,
                       "OverrideAudit: Package Override List",
                       result,
                       reuse=settings.get("reuse_views", True),
                       clear=settings.get("clear_existing", True))
