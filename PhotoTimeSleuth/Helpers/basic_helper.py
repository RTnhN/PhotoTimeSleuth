import psutil


def get_local_ip():
    for _, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == 2 and addr.address.startswith("192.168."):
                return addr.address  # Returns the first 192.168.x.x address found
    return None
