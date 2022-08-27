# -*- coding: utf-8 -*-

from guis.GuiContext import GuiContext

ctx = GuiContext()

ctx.log(u"TC - Navigate options on the main menu.")

ctx.mainmenu.action('INVOKE')

for option in ctx.mainmenu.get('OPTION'):
    ctx.log(u"Navigate to %s." % option)
    ctx.mainmenu.action('NAVIGATE', target=option)
