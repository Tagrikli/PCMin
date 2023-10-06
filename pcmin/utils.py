from datetime import datetime

def dbus_get_properties(bus, sender, path, interface):
    bus.get_object(sender, path).GetAll(
        interface, dbus_interface="org.freedesktop.DBus.Properties"
    )

def create_date():
    return datetime.now().strftime("%Y-%m-%d_%H.%M.%S")

