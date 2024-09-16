import socket
import time
import random

# Configurações
HOST = 'localhost'  # Ou use o IP do servidor
PORT = 12345
WINDOW_SIZE = 5

def send_packet(conn, seq_num, payload):
    data = f"{seq_num}:{payload}".encode('utf-8')
    conn.sendall(data)

def client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        for i in range(10):
            # Envia pacotes
            send_packet(s, i, f"Pacote {i}")
            # Simula erro de integridade
            if random.choice([True, False]):
                s.sendall(b'erro')

            # Recebe confirmação
            response = s.recv(1024).decode('utf-8')
            if "ACK" in response:
                print(f"Recebido ACK para pacote {response.split(':')[1]}")
            elif "NACK" in response:
                print(f"Recebido NACK para pacote {response.split(':')[1]}")
            
            time.sleep(1)

if __name__ == "__main__":
    client()