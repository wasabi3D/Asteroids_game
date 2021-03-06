import socket
import threading


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('10.255.255.255', 1))
    ip = s.getsockname()[0]
    s.close()
    return ip


class Packet:
    """Class pour faciliter d'envoyer les données."""
    def __init__(self, type_: str, message: str, value, other):
        self.info_type = type_
        self.msg = message
        self.value = value
        self.other = other

    def d(self):
        return self.__dict__


class Receive(threading.Thread):
    """Class pour recevoir des messages."""
    def __init__(self, port: int, on_receive_func, m_size=4096):
        """:param port: Le port où la class écoute pour les messages.
        :param on_receive_func: Une fonction qui est executée lors de l'arrivée d'un message.
        :param m_size: Taille maximale par message en byte."""
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
        except OSError:
            print("warn: socket os error")

        try:
            self.sock.close()
        except OSError:
            print("warn: socket os error (close)")

        self.stop_ev.set()
        self.do_run = False
        self.join()


class Send:
    """Class pour envoyer des messages."""
    def __init__(self, address: str, port: int, m_size=4096):
        """:param address: Adresse IP de l'autre ordinateur.
        :param port: Port où cette class envoie le message.
        :param m_size: La taille maximale d'un message."""
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

    def copy(self):
        s = Send(self.address[0], self.address[1])
        return s
