import sublime
import sublime_plugin

from ..core import ContextHelper, delete_override


###----------------------------------------------------------------------------


class OverrideAuditDeleteOverrideCommand(ContextHelper,sublime_plugin.TextCommand):
    """
    Delete the provided override file from disk.
    """
    def run(self, edit, **kwargs):
        target = self.view_target(self.view, **kwargs)
        package, override, _ = self.view_context(target, False, **kwargs)

        delete_override(target.window(), package, override)

    def description(self, **kwargs):
        target = self.view_target(self.view, **kwargs)
        package, override, _ = self.view_context(target, False, **kwargs)

        return "OverrideAudit: Delete Override '%s'" % override

    # TODO this should only trigger if the file that's going to be potentially
    # deleted actually exists on disk right now. Currently delete_override()
    # will do nothing, so this should not offer it.
    def is_visible(self, **kwargs):
        target = self.view_target(self.view, **kwargs)
        package, override, _ = self.view_context(target, False, **kwargs)

        return package is not None and override is not None

    def is_enabled(self, **kwargs):
        target = self.view_target(self.view, **kwargs)
        package, override, _ = self.view_context(target, False, **kwargs)

        return package is not None and override is not None


###----------------------------------------------------------------------------
