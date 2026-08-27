from socket import *

SERVER_PORT = 8000

clientSocket = socket(AF_INET, SOCK_STREAM)

ip = input("Digite o IP do servidor: ")

clientSocket.connect((ip, SERVER_PORT))

mensagem = input("Digite a mensagem a ser enviada: ")

clientSocket.send(mensagem.encode())

msgRec = clientSocket.recv(1024)
msgRecDec = msgRec.decode()

print(f"Mensagem recebida: {msgRecDec}")

clientSocket.close()