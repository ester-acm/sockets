import socket
import logging
import hashlib
import threading
import random

HOST = 'localhost'
PORT = 12345
WINDOW_SIZE = 5
BUFFER_SIZE = 1024
TIMEOUT = 5
LOSS_PROBABILITY = 0.1  
CORRUPT_PROBABILITY = 0.1  

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_checksum(data):
    return hashlib.md5(data.encode('utf-8')).hexdigest()

def verify_integrity(received_checksum, payload):
    return calculate_checksum(payload) == received_checksum

def simulate_loss_or_corruption(response):
    if random.random() < LOSS_PROBABILITY:
        logging.warning(f"Simulando perda de confirmação: {response}")
        return None
    if random.random() < CORRUPT_PROBABILITY:
        corrupted_response = f"CORRUPT:{response}"
        logging.warning(f"Simulando corrupção de confirmação: {corrupted_response}")
        return corrupted_response.encode('utf-8')
    return response.encode('utf-8')

def negotiate_protocol(conn):
    conn.sendall("NEGOTIATE:Select_GBN".encode('utf-8'))
    protocol = conn.recv(BUFFER_SIZE).decode('utf-8')
    logging.info(f"Protocolo negociado com cliente: {protocol}")
    return protocol

def handle_client_connection(conn, addr):
    logging.info(f"Nova conexão de {addr}")
    expected_seq_num = 0
    buffer = {}
    rwnd = WINDOW_SIZE

    protocol = negotiate_protocol(conn)

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
                response = f"NACK:{seq_num}"
                corrupted_response = simulate_loss_or_corruption(response)
                if corrupted_response:
                    conn.sendall(corrupted_response)
                continue

            if seq_num == expected_seq_num:
                logging.info(f"Pacote {seq_num} aceito: {payload}")
                expected_seq_num += 1
                rwnd = max(0, rwnd - 1)  
                response = f"ACK:{seq_num};RWND:{rwnd}"
                corrupted_response = simulate_loss_or_corruption(response)
                if corrupted_response:
                    conn.sendall(corrupted_response)

                while expected_seq_num in buffer:
                    logging.info(f"Processando do buffer: pacote {expected_seq_num}")
                    del buffer[expected_seq_num]
                    expected_seq_num += 1
                    rwnd = max(0, rwnd - 1)

            elif seq_num > expected_seq_num:
                logging.info(f"Pacote {seq_num} fora de ordem, armazenando no buffer")
                buffer[seq_num] = payload
                response = f"ACK:{expected_seq_num - 1};RWND:{rwnd}"
                corrupted_response = simulate_loss_or_corruption(response)
                if corrupted_response:
                    conn.sendall(corrupted_response)
            else:
                logging.warning(f"Pacote {seq_num} duplicado ignorado")
                response = f"ACK:{seq_num};RWND:{rwnd}"
                corrupted_response = simulate_loss_or_corruption(response)
                if corrupted_response:
                    conn.sendall(corrupted_response)

            rwnd = min(WINDOW_SIZE, rwnd + 1)  
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
