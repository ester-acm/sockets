import socket
import logging
import hashlib
import threading

HOST = 'localhost'
PORT = 12345
WINDOW_SIZE = 5
BUFFER_SIZE = 1024
TIMEOUT = 5

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_checksum(data):
    return hashlib.md5(data.encode('utf-8')).hexdigest()

def verify_integrity(received_checksum, payload):
    return calculate_checksum(payload) == received_checksum

def handle_client_connection(conn, addr):
    logging.info(f"Nova conexão de {addr}")
    expected_seq_num = 0
    buffer = {}
    rwnd = WINDOW_SIZE

    try:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                logging.info("Cliente desconectou normalmente")
                break

            seq_num, received_checksum, payload = data.decode('utf-8').split(':', 2)
            seq_num = int(seq_num)

            if not verify_integrity(received_checksum, payload):
                logging.warning(f"Erro de integridade no pacote {seq_num}")
                conn.sendall(f"NACK:{seq_num}".encode('utf-8'))
                continue

            if seq_num == expected_seq_num:
                logging.info(f"Pacote {seq_num} aceito: {payload}")
                expected_seq_num += 1
                conn.sendall(f"ACK:{seq_num}".encode('utf-8'))

                while expected_seq_num in buffer:
                    logging.info(f"Processando do buffer: pacote {expected_seq_num}")
                    del buffer[expected_seq_num]
                    expected_seq_num += 1
            elif seq_num > expected_seq_num:
                logging.info(f"Pacote {seq_num} fora de ordem, armazenando no buffer")
                buffer[seq_num] = payload
                conn.sendall(f"ACK:{expected_seq_num-1}".encode('utf-8'))
            else:
                logging.warning(f"Pacote {seq_num} duplicado ignorado")
                conn.sendall(f"ACK:{seq_num}".encode('utf-8'))
    except Exception as e:
        logging.error(f"Erro inesperado: {e}")
    finally:
        conn.close()
        logging.info(f"Conexão com {addr} encerrada")

def server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        logging.info(f"Servidor escutando em {HOST}:{PORT}")
        
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client_connection, args=(conn, addr)).start()

if __name__ == "__main__":
    server()
