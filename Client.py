import socket
import time
import random
import hashlib

HOST = 'localhost'  
PORT = 12345

def calculate_checksum(data):
    """Calcula a soma de verificação do pacote usando MD5."""
    return hashlib.md5(data.encode('utf-8')).hexdigest()

def send_packet(conn, seq_num, payload):
    checksum = calculate_checksum(payload)
    data = f"{seq_num}:{checksum}:{payload}".encode('utf-8')
    conn.sendall(data)

def client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        seq_num = 0  

        while True:
            # Solicita ao usuário para enviar um pacote ou sair
            user_input = input("Pressione Enter para enviar o próximo pacote ou 'sair' para encerrar: ")
            if user_input.lower() == 'sair':
                print("Encerrando conexão...")
                break

            payload = f"Pacote {seq_num}"
            send_packet(s, seq_num, payload)

            # Simula envio de erro de integridade aleatório
            if random.choice([True, False]):
                s.sendall(b'erro')

            # Recebe confirmação
            response = s.recv(1024).decode('utf-8')
            if "ACK" in response:
                print(f"Recebido ACK para pacote {response.split(':')[1]}")
            elif "NACK" in response:
                print(f"Recebido NACK para pacote {response.split(':')[1]}")
            
            #Incrementa o número de sequência para o próximo pacote
            seq_num += 1

            time.sleep(1)

if __name__ == "__main__":
    client()
