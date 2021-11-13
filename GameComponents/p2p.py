import socket
import threading


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('10.255.255.255', 1))
    ip = s.getsockname()[0]
    s.close()
    return ip


class GameCom:
    def __init__(self, type_: str, message: str, value, other):
        self.info_type = type_
        self.msg = message
        self.value = value
        self.other = other

    def d(self):
        return self.__dict__


class PackedUpdateData:
    def __init__(self):
        self.dat = {}


class Receive(threading.Thread):
    def __init__(self, port: int, on_receive_func, m_size=1024):
        super(Receive, self).__init__()
        self.received_raw = ""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.M_SIZE = m_size
        self.local_ip = get_local_ip()
        print("Local ip:", self.local_ip)
        self.sock.bind((self.local_ip, port))
        self.setName("Rec_Th")
        self.stop_ev = threading.Event()
        self.do_run = True
        self.on_receive = on_receive_func

    def run(self) -> None:
        while self.do_run:
            try:
                g = self.sock.recvfrom(self.M_SIZE)
                if g is None:
                    break
                rx_meesage, addr = g
                self.on_receive(rx_meesage.decode('utf-8'), addr)

            except OSError:
                print("warn: socket os error")
            # print(f"\n[Received] from {addr}, raw: {rx_meesage.decode('utf-8')}")

    def kill(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
        except OSError:
            print("warn: socket os error")

        self.stop_ev.set()
        self.do_run = False
        self.join()


class Send:
    def __init__(self, address: str, port: int, m_size=1024):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.M_SiZE = m_size
        self.message = ""
        self.address = (address, port)

    def run(self) -> None:
        self.sock.sendto(self.message.encode('utf-8'), self.address)

    def set_message(self, msg: str):
        self.message = msg

    def send_message(self, msg: str):
        self.set_message(msg)
        self.run()
        self.sock.close()
