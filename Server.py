import socket
import random
import time
import logging
import hashlib


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurações
HOST = 'localhost'
PORT = 12345
WINDOW_SIZE = 5
BUFFER_SIZE = 1024
INTEGRITY_CHECK_PASS_RATE = 0.8

class PacketError(Exception):
    
    pass

class IntegrityError(PacketError):
    
    pass

class OutOfOrderError(PacketError):
    
    pass

def calculate_checksum(data):
    """Calcula a soma de verificação do pacote usando MD5."""
    return hashlib.md5(data.encode('utf-8')).hexdigest()

def verify_integrity(received_checksum, payload):
    """Verifica se a soma de verificação do payload corresponde ao checksum recebido."""
    return calculate_checksum(payload) == received_checksum

def process_packet(seq_num, payload, expected_seq_num, buffer):
    """Processa um pacote recebido."""
    if seq_num == expected_seq_num:
        logging.info(f"Pacote {seq_num} aceito: {payload}")
        return True, expected_seq_num + 1
    elif seq_num > expected_seq_num:
        logging.info(f"Pacote {seq_num} fora de ordem, armazenando no buffer")
        buffer[seq_num] = payload
        raise OutOfOrderError(f"Pacote {seq_num} recebido, esperava {expected_seq_num}")
    else:
        logging.warning(f"Pacote {seq_num} duplicado ignorado")
        return False, expected_seq_num

def handle_client_connection(conn, addr):
    
    logging.info(f"Nova conexão de {addr}")
    expected_seq_num = 0
    buffer = {}

    try:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                logging.info("Cliente desconectou normalmente")
                break

            try:
                if data == b'erro':
                    raise IntegrityError("Erro de integridade simulado recebido")

                # Desempacota o dado recebido
                seq_num, received_checksum, payload = data.decode('utf-8').split(':', 2)
                seq_num = int(seq_num)

                # Verifica a integridade dos dados
                if not verify_integrity(received_checksum, payload):
                    raise IntegrityError(f"Falha na verificação de integridade do pacote {seq_num}")

                processed, expected_seq_num = process_packet(seq_num, payload, expected_seq_num, buffer)
                
                if processed:
                    conn.sendall(f"ACK:{seq_num}".encode('utf-8'))
                    
                    while expected_seq_num in buffer:
                        logging.info(f"Processando do buffer: pacote {expected_seq_num}")
                        del buffer[expected_seq_num]
                        expected_seq_num += 1
                else:
                    conn.sendall(f"ACK:{expected_seq_num-1}".encode('utf-8'))

            except (ValueError, IndexError):
                logging.error(f"Dados inválidos recebidos: {data}")
                conn.sendall(f"NACK:{expected_seq_num}".encode('utf-8'))
            except IntegrityError as e:
                logging.warning(str(e))
                conn.sendall(f"NACK:{seq_num}".encode('utf-8'))
            except OutOfOrderError as e:
                logging.info(str(e))
                conn.sendall(f"ACK:{expected_seq_num-1}".encode('utf-8'))

    except ConnectionResetError:
        logging.error("Conexão resetada pelo cliente")
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
            try:
                conn, addr = s.accept()
                handle_client_connection(conn, addr)
            except KeyboardInterrupt:
                logging.info("Servidor encerrado pelo usuário")
                break
            except Exception as e:
                logging.error(f"Erro ao aceitar conexão: {e}")
                time.sleep(1)

if __name__ == "__main__":
    server()
