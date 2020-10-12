import shlex
import subprocess
from xmlrpc.server import SimpleXMLRPCServer
import win32wnet
import win32netcon
import os
import pywintypes

base_path = r'C:\hivemind'
share_name = "HUNC"
share_drive_letter = 'K:'


net_check_admin = r"NET SESSIONS"

net_create_user = r"NET USERS {} {} /ADD /Y"

net_delete_user = r"NET USERS {} /DELETE"

net_share_create = "NET SHARE \"" + share_name + "\"=\"" + base_path + "\" /GRANT:\"{}\",FULL"

net_share_destroy = r"NET SHARE " + share_name + r" /DELETE /YES"

ps_create_elevated_proc = rf'powershell -Command Start-Process -Verb runas python -ArgumentList "{os.path.realpath(__file__)}" '

fake = False


def _invoke_string_template(template: str, *args):
    if not fake:
        return subprocess.Popen(shlex.split(template.format(*args)),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True)
    else:
        return False


def CreateElevatedProc():
    _invoke_string_template(ps_create_elevated_proc)
    return False


def NetCheckAdmin() -> bool:
    process = _invoke_string_template(net_check_admin)
    err = process.returncode
    if err != 0:
        return False
    return True


def NetCreateUser(user: str, password: str):
    p = _invoke_string_template(net_create_user, user, password)
    return p.communicate()[0] + p.communicate()[1]


def NetDeleteUser(user: str):
    _invoke_string_template(net_delete_user, user)
    return False


def NetShareCreate(user: str):
    p = _invoke_string_template(net_share_create, user)
    return p.communicate()[0] + p.communicate()[1]


def NetShareDestroy():
    _invoke_string_template(net_share_destroy)
    return False


def NetShareConnect(remote: str, user: str, password: str):
    remote = f"\\\\{remote}\\HUNC"
    try:
        win32wnet.WNetAddConnection2(win32netcon.RESOURCETYPE_DISK, share_drive_letter, remote, None, user, password)
    except pywintypes.error as err:
        if err.winerror == 85:
            return True
        else:
            return False
    return True


if __name__ == "__main__":
    server = SimpleXMLRPCServer(("localhost", 9808))
    server.register_function(NetCheckAdmin, "NetCheckAdmin")
    server.register_function(NetCreateUser, "NetCreateUser")
    server.register_function(NetDeleteUser, "NetDeleteUser")
    server.register_function(NetShareCreate, "NetShareCreate")
    server.register_function(NetShareConnect, "NetShareConnect")
    server.register_function(NetShareDestroy, "NetShareDestroy")

    server.register_function(os._exit, "exit")

    server.serve_forever()
