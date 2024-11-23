import socket
import random
import time
import logging
import hashlib
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HOST = 'localhost'
PORT = 12345
WINDOW_SIZE = 5
BUFFER_SIZE = 1024
INTEGRITY_CHECK_PASS_RATE = 0.8
TIMEOUT = 5


LOST_ACK_PACKETS = {3, 7}  

class PacketError(Exception):
    pass

class IntegrityError(PacketError):
    pass

class OutOfOrderError(PacketError):
    pass

def calculate_checksum(data):
    return hashlib.md5(data.encode('utf-8')).hexdigest()

def verify_integrity(received_checksum, payload):
    return calculate_checksum(payload) == received_checksum

def process_packet(seq_num, payload, expected_seq_num, buffer):
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

def resend_packet(conn, seq_num, payload):
    checksum = calculate_checksum(payload)
    data = f"{seq_num}:{checksum}:{payload}".encode('utf-8')
    conn.sendall(data)
    logging.info(f"Pacote {seq_num} reenviado após timeout")

def set_timer(conn, seq_num, payload):
    timer = threading.Timer(TIMEOUT, resend_packet, args=(conn, seq_num, payload))
    timer.start()
    return timer

def handle_client_connection(conn, addr):
    logging.info(f"Nova conexão de {addr}")
    expected_seq_num = 0
    buffer = {}
    timers = {}

    try:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                logging.info("Cliente desconectou normalmente")
                break

            try:
                if data == b'erro':
                    raise IntegrityError("Erro de integridade simulado recebido")

                seq_num, received_checksum, payload = data.decode('utf-8').split(':', 2)
                seq_num = int(seq_num)

                if not verify_integrity(received_checksum, payload):
                    raise IntegrityError(f"Falha na verificação de integridade do pacote {seq_num}")

                processed, expected_seq_num = process_packet(seq_num, payload, expected_seq_num, buffer)
                
                if processed:
                    
                    if seq_num in LOST_ACK_PACKETS:
                        logging.warning(f"Simulando perda de ACK para o pacote {seq_num}")
                        continue 

                    conn.sendall(f"ACK:{seq_num}".encode('utf-8'))
                    
                    if seq_num in timers:
                        timers[seq_num].cancel()
                        del timers[seq_num]
                    
                    while expected_seq_num in buffer:
                        logging.info(f"Processando do buffer: pacote {expected_seq_num}")
                        del buffer[expected_seq_num]
                        expected_seq_num += 1
                else:
                    conn.sendall(f"ACK:{expected_seq_num-1}".encode('utf-8'))

                if expected_seq_num not in timers:
                    timers[expected_seq_num] = set_timer(conn, expected_seq_num, "")

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
        for timer in timers.values():
            timer.cancel()
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
