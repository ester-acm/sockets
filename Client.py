import socket
import time
import hashlib
import threading

HOST = 'localhost'
PORT = 12345
INITIAL_WINDOW_SIZE = 4
MAX_WINDOW_SIZE = 10
MIN_WINDOW_SIZE = 1
TIMEOUT = 5
MAX_RETRIES = 5  # Número máximo de retransmissões por pacote

def calculate_checksum(data):
    return hashlib.md5(data.encode('utf-8')).hexdigest()

def send_packet(conn, seq_num, payload):
    try:
        checksum = calculate_checksum(payload)
        data = f"{seq_num}:{checksum}:{payload}".encode('utf-8')
        conn.sendall(data)
        print(f"Pacote {seq_num} enviado: {payload}")
    except Exception as e:
        print(f"Erro ao enviar pacote {seq_num}: {e}")

class PacketSender:
    def __init__(self, conn, single_mode):
        self.conn = conn
        self.single_mode = single_mode
        self.window_size = INITIAL_WINDOW_SIZE
        self.base = 0
        self.next_seq_num = 0
        self.buffer = {}
        self.ack_received = threading.Event()
        self.lock = threading.Lock()
        self.timers = {}
        self.packets = []
        self.errored_packets = set()
        self.running = True
        self.retries = {}

    def start_timer(self, seq_num):
        self.timers[seq_num] = threading.Timer(TIMEOUT, self.retransmit, args=[seq_num])
        self.timers[seq_num].start()

    def retransmit(self, seq_num):
        with self.lock:
            if seq_num in self.buffer:
                self.retries[seq_num] = self.retries.get(seq_num, 0) + 1
                if self.retries[seq_num] > MAX_RETRIES:
                    print(f"Desistindo do pacote {seq_num} após {MAX_RETRIES} tentativas")
                    del self.buffer[seq_num]
                    if seq_num in self.timers:
                        self.timers[seq_num].cancel()
                        del self.timers[seq_num]
                    self.base = seq_num + 1
                    self.ack_received.set()
                else:
                    print(f"Timeout para pacote {seq_num}. Retransmitindo... (Tentativa {self.retries[seq_num]})")
                    send_packet(self.conn, seq_num, self.buffer[seq_num])
                    self.start_timer(seq_num)
                    self.adjust_window_size(decrease=True)

    def receive_ack(self):
        buffer = ""
        while self.running:
            try:
                data = self.conn.recv(1024).decode('utf-8')
                if not data:
                    print("Conexão encerrada pelo servidor.")
                    break
                buffer += data
                while '\n' in buffer:
                    response, buffer = buffer.split('\n', 1)
                    if "NACK" in response:
                        nack_num = int(response.split(':')[1])
                        print(f"Recebido NACK para pacote {nack_num}")
                        self.retransmit(nack_num)
                    elif "ACK" in response:
                        parts = response.split(';')
                        ack_num = int(parts[0].split(':')[1])
                        rwnd = int(parts[1].split(':')[1])
                        print(f"Recebido ACK para pacote {ack_num}, RWND: {rwnd}")
                        self.process_ack(ack_num)
            except Exception as e:
                print(f"Erro ao receber ACK/NACK: {e}")
                break

    def process_ack(self, ack_num):
        with self.lock:
            if ack_num >= self.base:
                for seq_num in range(self.base, ack_num + 1):
                    if seq_num in self.buffer:
                        del self.buffer[seq_num]
                    if seq_num in self.timers:
                        self.timers[seq_num].cancel()
                        del self.timers[seq_num]
                    if seq_num in self.retries:
                        del self.retries[seq_num]
                self.base = ack_num + 1
                self.adjust_window_size(increase=True)
                print(f"ACK processado para pacote {ack_num}")
                self.ack_received.set()
                self.send_window()

    def adjust_window_size(self, increase=False, decrease=False):
        if increase:
            self.window_size = min(self.window_size + 1, MAX_WINDOW_SIZE)
        elif decrease:
            self.window_size = max(self.window_size // 2, MIN_WINDOW_SIZE)
        print(f"Janela ajustada para {self.window_size}")

    def send_window(self):
        with self.lock:
            while len(self.buffer) < self.window_size and self.next_seq_num < len(self.packets):
                payload = self.packets[self.next_seq_num]
                if self.next_seq_num in self.errored_packets:
                    payload = f"{payload}_erro"
                self.buffer[self.next_seq_num] = payload
                send_packet(self.conn, self.next_seq_num, payload)
                self.start_timer(self.next_seq_num)
                self.next_seq_num += 1
                if self.single_mode:
                    break

    def send_packets(self, packets, errored_packets=None):
        self.packets = packets
        self.errored_packets = set(errored_packets or [])
        
        ack_thread = threading.Thread(target=self.receive_ack)
        ack_thread.daemon = True
        ack_thread.start()

        self.send_window()

        while self.base < len(packets):
            self.ack_received.wait(TIMEOUT)
            self.ack_received.clear()

        self.running = False
        ack_thread.join(timeout=1)
        print("Todos os pacotes foram enviados e confirmados.")

def client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            
            print("Escolha o modo de envio:")
            print("1 - Envio único")
            print("2 - Envio em rajada")
            choice = input("Digite sua escolha (1 ou 2): ").strip()
            single_mode = choice == "1"

            sender = PacketSender(s, single_mode)
            packets = [f"Pacote {i}" for i in range(20)]
            errored_packets = [2, 4]
            sender.send_packets(packets, errored_packets=errored_packets)
        except Exception as e:
            print(f"Erro ao conectar ao servidor: {e}")

if __name__ == "__main__":
    client()