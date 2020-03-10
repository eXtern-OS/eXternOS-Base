
add_library(Qt5::QEglFSKmsEglDeviceIntegrationPlugin MODULE IMPORTED)

_populate_Gui_plugin_properties(QEglFSKmsEglDeviceIntegrationPlugin RELEASE "egldeviceintegrations/libqeglfs-kms-egldevice-integration.so")

list(APPEND Qt5Gui_PLUGINS Qt5::QEglFSKmsEglDeviceIntegrationPlugin)
