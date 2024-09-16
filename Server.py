import socket
import random

# Configurações
HOST = 'localhost'  # Ou '0.0.0.0' para aceitar conexões de qualquer IP
PORT = 12345
WINDOW_SIZE = 5

def verify_integrity(data):
    # Simula verificação de integridade
    return random.random() > 0.2  # 80% de chance de passar na verificação

def server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Servidor escutando em {HOST}:{PORT}")
        
        conn, addr = s.accept()
        with conn:
            print(f"Conectado por {addr}")
            expected_seq_num = 0
            buffer = {}
            
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                
                if data == b'erro':
                    print("Erro de integridade simulado recebido")
                    conn.sendall(f"NACK:{expected_seq_num}".encode('utf-8'))
                    continue
                
                try:
                    seq_num, payload = data.decode('utf-8').split(':', 1)
                    seq_num = int(seq_num)
                    
                    if verify_integrity(payload):
                        if seq_num == expected_seq_num:
                            print(f"Recebido e aceito: {payload}")
                            conn.sendall(f"ACK:{seq_num}".encode('utf-8'))
                            expected_seq_num += 1
                            
                            # Processa pacotes em buffer, se houver
                            while expected_seq_num in buffer:
                                print(f"Processando do buffer: {buffer[expected_seq_num]}")
                                del buffer[expected_seq_num]
                                expected_seq_num += 1
                        elif seq_num > expected_seq_num:
                            print(f"Recebido fora de ordem, armazenando: {payload}")
                            buffer[seq_num] = payload
                            conn.sendall(f"ACK:{expected_seq_num-1}".encode('utf-8'))
                        else:
                            print(f"Pacote duplicado ignorado: {payload}")
                            conn.sendall(f"ACK:{expected_seq_num-1}".encode('utf-8'))
                    else:
                        print(f"Falha na verificação de integridade: {payload}")
                        conn.sendall(f"NACK:{expected_seq_num}".encode('utf-8'))
                except ValueError:
                    print(f"Dados inválidos recebidos: {data}")
                    conn.sendall(f"NACK:{expected_seq_num}".encode('utf-8'))

if __name__ == "__main__":
    server()