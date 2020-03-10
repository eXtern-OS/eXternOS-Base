
add_library(Qt5::QLibInputPlugin MODULE IMPORTED)

_populate_Gui_plugin_properties(QLibInputPlugin RELEASE "generic/libqlibinputplugin.so")

list(APPEND Qt5Gui_PLUGINS Qt5::QLibInputPlugin)
