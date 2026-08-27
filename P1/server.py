from socket import *
from math import ceil
import sys
import os

hostname = gethostname()
ip = gethostbyname(hostname)
SERVER_PORT = 8000
curr_dir = os.getcwd()

print(f"Rodando host {hostname} no endereço {ip}")
print(f"Rodando a partir de: {curr_dir}")

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind((ip, SERVER_PORT))
serverSocket.listen(5)

while True:
    print("Aguardando conexão...")
    connectionSocket, addr = serverSocket.accept()
    try:
        message = connectionSocket.recv(1024).decode()
        filename = message.split()[1]
        if curr_dir.split("/")[-1] == "Lab-Redes":
            filename = "/P1" + filename
        #file_size = os.path.getsize(filename[1:])

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
        connectionSocket.send(header.encode())
        for i in range(0, len(outputdata)):
            connectionSocket.send(outputdata[i].encode())
        connectionSocket.send("\r\n".encode())


    except IOError:
        connectionSocket.send("HTTP/1.1 404 Not Found".encode())
        connectionSocket.send("\r\n".encode())
        connectionSocket.close()

    serverSocket.close()
    sys.exit()
