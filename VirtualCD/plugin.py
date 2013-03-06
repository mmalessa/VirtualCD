#from Components.config import config, ConfigSubsection, ConfigYesNo
from Plugins.Plugin import PluginDescriptor
 
import virtualcd
 
# ladowane przy starcie sesji
def sessionstart(session, **kwargs):
	return
 
# ladowane przy starcie pluginu
def main(session, **kwargs):
	reload(virtualcd)
	session.open(virtualcd.VirtualCDScreen)


# nie wiem czy to potrzebne
def menu(menuid, **kwargs):
    if menuid == "mainmenu":
        return[("VirtualCD",main,"virtualcd",47)]
    return []



 
def Plugins(**kwargs):
	list = [PluginDescriptor(name="VirtualCD", description="Virtual CD player", where = [PluginDescriptor.WHERE_PLUGINMENU], icon = "plugin.png", fnc=main)]
	#if config.plugins.virtualcd.virtualcdInExtendedPluginlist.value:
	list.append(PluginDescriptor(name="VirtualCD", description="Virtual CD player", where = [PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main))
	#if config.plugins.virtualcd.virtualcdInMainMenu.value:
	list.append(PluginDescriptor(name="VirtualCD", description="Virtual CD player", where = [PluginDescriptor.WHERE_MENU], fnc=menu))
	#list.append(PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = autostart))
	return list
