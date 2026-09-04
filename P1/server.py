from typing import Tuple
from math import ceil
import threading as th
import socket
import sys
import os

class ConnectionLock():
    """
    Lock para controlar o acesso compartilhado das threads (sockets de conexão) e da função principal
    ao valor da variável que controla o loop de execução das chamadas 'accept' do socket do servidor.
    A variável 'running' foi implementada como atributo dessa classe para reunir o lock com seu recurso
    correspondente, além de garantir que a variável seja passada por referência em vez de por atribuição,
    garantindo que o mesmo espaço de memória seja efetivamente compartilhado por todas as threads.
    """
    def __init__(self):
        # O lock que controla o acesso ao recurso compartilhado (a variável 'running')
        self._lock = th.Lock()
        # Recurso a ser compartilhado pelas threads dos sockets de conexão e pela função principal
        # Inicializado como 'True', controla repetição das chamadas 'accept' e a consequente criação
        # de novos sockets de conexão
        self.running = True

    def is_running(self) -> bool:
        """
        Retorna o valor da variável 'running' (usada no loop da função principal)
        """
        return self.running

    def stop(self):
        """
        Define o valor da variável 'running' como 'False', para sinalizar à função principal que
        interrompa o loop de chamadas 'accept' do socket do servidor
        """
        self.running = False

    def acquire(self):
        """
        Requisita ao Lock o acesso à variável compartilhada ('running')
        """
        self._lock.acquire()

    def release(self):
        """
        Libera o acesso ao Lock
        """
        self._lock.release()

def get_content(
        c_sock:socket.socket, 
        addr:Tuple[str, int], 
        c_lock:ConnectionLock
):
    """
    Função de recebimento de requisição HTTP e envio de resposta HTTP. Usada para criação de threads com
    os sockets de conexão.
    
    Parâmetros:
    * c_sock: socket de conexão
    * addr: endereço IPv4 e porta de origem da requisição HTTP
    * c_lock: Lock de acesso à variável de controle do loop da função principal
    """
    try:
        # Receber a mensagem enviada pelo cliente (primeiros 1024 bytes) e decodificar (bits para string)
        message = c_sock.recv(1024).decode()
        # Recuperar o arquivo solicitado pelo cliente, a partir da linha de requisição HTTP
        filename = message.split()[1]

        if filename == "/stop":
            # Faz o programa servidor parar de aceitar novas requisições de conexão

            # Solicita acesso ao lock
            c_lock.acquire()
            # Modifica para 'False' o valor da variável de controle do loop da função principal
            c_lock.stop()
            # Libera o acesso ao lock
            c_lock.release()
        else:
            # Abre o arquivo requisitado, desde que exista no mesmo diretório do script do programa
            f = open(filename[1:])
            # Cria uma lista para armazenar os pacotes de 1024 bytes (tamanho do campo de dados) do 
            # arquivo, em sequência
            outputdata = list()
            while True:
                try:
                    # Lê o próximo fluxo de 1024 bytes (ou menos) do arquivo
                    nextmsg = f.read(1024)
                    # Se o fluxo lido for vazio, para de ler
                    if not nextmsg:
                        break
                    # Adiciona o fluxo de bytes lido à lista de dados
                    outputdata.append(nextmsg)
                except EOFError:
                    # Se houver erro de leitura por conta de fim do arquivo, também para de ler
                    break
            # Envia o campo de cabeçalho indicando que o arquivo foi encontrado
            header = "HTTP/1.1 200 OK\n"
            c_sock.send(header.encode())
            # Envia o corpo da mensagem, em frações de 1024 bytes (ou menos, se for a última)
            for i in range(0, len(outputdata)):
                c_sock.send(outputdata[i].encode())
            # Log no terminal para monitoramento da atividade do servidor e debugging
            print(f"Página {filename} enviada")
    except IOError:
        # Envia a linha de resposta HTTP para "Página não encontrada", sem corpo
        c_sock.send("HTTP/1.1 404 Not Found".encode())
        # Log para monitorar a atividade do servidor e debugging
        print(f"Página {filename} não encontrada")
    # Enviar a terminação da mensagem de resposta HTTP
    c_sock.send("\r\n".encode())
    # Fechar o socket de conexão
    c_sock.close()

def server_running(c_lock:ConnectionLock) -> bool:
    """
    Função para ser usada no teste lógico do loop da função principal, permitindo o uso do Lock para 
    controlar o acesso ao recurso compartilhado.

    Parâmetros:
    * c_lock: Lock de acesso à variável 'running', que controla o loop da função principal

    Saída:
    * is_running: variável indicando se o loop deve continuar aceitando conexões TCP
    """
    # Solicita acesso ao lock
    c_lock.acquire()
    # Obtém o valor da variável compartilhada 'running'
    is_running = c_lock.is_running()
    # Libera o acesso ao lock
    c_lock.release()
    return is_running
    
def main():
    # Cria o lock de acesso à variável 'running'
    c_lock = ConnectionLock()

    # Configura as variáveis do socket do servidor
    hostname = socket.gethostname()
    # Variável 'hardcoded', precisa ser substituída pelo valor obtido por terminal (comando "hostname -I")
    # para conseguir estabelecer conexão com um navegador remoto
    ip = "192.168.0.6"
    SERVER_PORT = 8000

    # Log para monitoramento da atividade do servidor e debugging
    print(f"Rodando host {hostname} no endereço {ip}")

    # Criar o socket do servidor TCP
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Associar o socket ao endereço IP e à porta de entrada
    serverSocket.bind((ip, SERVER_PORT))
    # Configurar o socket para permitir até 5 conexões simultâneas
    serverSocket.listen(5)
    print("Aceitando conexões")

    while server_running(c_lock): # Confere a variável 'running' para decidir se continua aceitando conexões
        # Espera por uma nova solicitação de conexão para aceitar e cria um socket para a nova conexão
        connectionSocket, addr = serverSocket.accept()
        # Cria uma nova thread para troca de dados através do novo socket de conexão
        connection_th = th.Thread(
            target=get_content, 
            args=(connectionSocket, addr, c_lock,)
        )
        # Inicia essa nova thread
        connection_th.start()


    print("Encerrando conexão")
    # Aguarda pelo fim de todas as threads de conexão ainda ativas
    for s in th.enumerate():
        if s.is_alive() and not s.daemon and s is not th.main_thread():
            s.join()

    # Fecha o socket de servidor
    serverSocket.close()
    sys.exit()

main()