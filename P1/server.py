from socket import *
from math import ceil
import threading as th
import sys
import os

class ConnectionLock():
    def __init__(self):
        self._lock = th.Lock()
        self.running = True

    def is_running(self):
        return self.running

    def stop(self):
        self.running = False

    def acquire(self):
        self._lock.acquire()

    def release(self):
        self._lock.release()

def get_content(
        c_sock:socket, 
        addr:tuple, 
        c_lock:ConnectionLock
):
    try:
        message = c_sock.recv(1024).decode()
        filename = message.split()[1]

        if filename == "/stop":
            c_lock.acquire()
            print("Encerrando conexão")
            c_lock.stop()
            c_lock.release()
        else:
            f = open(filename[1:])
            outputdata = list()
            while True:
                try:
                    nextmsg = f.read(1024)
                    if not nextmsg:
                        break
                    outputdata.append(nextmsg)
                except EOFError:
                    break
            header = "HTTP/1.1 200 OK\n"
            c_sock.send(header.encode())
            for i in range(0, len(outputdata)):
                c_sock.send(outputdata[i].encode())
            print(f"Página {filename} enviada")
    except IOError:
        c_sock.send("HTTP/1.1 404 Not Found".encode())
        print(f"Página {filename} não encontrada")
    c_sock.send("\r\n".encode())
    c_sock.close()

def server_running(c_lock:ConnectionLock):
    c_lock.acquire()
    is_running = c_lock.is_running()
    c_lock.release()
    return is_running
    
def main():
    c_lock = ConnectionLock()

    hostname = gethostname()
    ip = gethostbyname(hostname)
    SERVER_PORT = 8000
    curr_dir = os.getcwd()

    print(f"Rodando host {hostname} no endereço {ip}")
    print(f"Rodando a partir de: {curr_dir}")

    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind((ip, SERVER_PORT))
    serverSocket.listen(5)

    while server_running(c_lock):
        print("Aguardando nova conexão...")
        connectionSocket, addr = serverSocket.accept()
        connection_th = th.Thread(
            target=get_content, 
            args=(connectionSocket, addr, c_lock,)
        )
        connection_th.start()

    for s in th.enumerate():
        if s.is_alive() and not s.daemon and s is not th.main_thread():
            s.join()
    serverSocket.close()
    sys.exit()

main()