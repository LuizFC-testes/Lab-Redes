from socket import *

hostname = gethostname()
ip = gethostbyname(hostname)
SERVER_PORT = 8000

print(f"Rodando host {hostname} no endereço {ip}")

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind((ip, SERVER_PORT))
serverSocket.listen(1)

while True:
    connectionSocket, addr = serverSocket.accept()
    data = connectionSocket.recv(1024).decode()
    if not data:
        break
    print(f"Mensagem recebida: {data}")
    connectionSocket.sendall(data.title().encode())
connectionSocket.close()
serverSocket.close()