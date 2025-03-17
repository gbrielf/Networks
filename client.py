import socket  # Importa o módulo socket para comunicação de rede.
import json  # Importa o módulo json para manipulação de dados em formato JSON.
import psutil  # Importa o módulo psutil para coletar informações do sistema.

class Cliente:  # Define a classe Cliente.
    def __init__(self, servidor_ip='192.168.37.83', servidor_porta=8080):  # Método construtor da classe.
        self.servidor_ip = servidor_ip  # Atribui o endereço IP do servidor à variável de instância.
        self.servidor_porta = servidor_porta  # Atribui a porta do servidor à variável de instância.
        self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Cria um socket TCP.

    def coletar_dados(self):  # Método para coletar dados do sistema.
        """Coleta informações do sistema."""  # Docstring que descreve a função.
        dados = {  # Cria um dicionário para armazenar os dados coletados.
            "processadores": psutil.cpu_count(logical=True),  # Conta o número de processadores lógicos.
            "memoria_ram_livre": round(psutil.virtual_memory().available / (1024 * 1024), 2),  # Obtém a memória RAM livre em MB.
            "espaco_disco_livre": round(psutil.disk_usage('/').free / (1024 * 1024 * 1024), 2),  # Obtém o espaço livre em disco em GB.
        }
        return json.dumps(dados)  # Converte o dicionário em uma string JSON e retorna.

    def conectar_servidor(self):  # Método para conectar ao servidor e enviar dados.
        """Conecta ao servidor e envia os dados."""  # Docstring que descreve a função.
        try:  # Inicia um bloco try para capturar exceções.
            self.socket_cliente.connect((self.servidor_ip, self.servidor_porta))  # Conecta ao servidor usando o IP e a porta.
            dados = self.coletar_dados()  # Coleta os dados do sistema.
            self.socket_cliente.sendall(dados.encode())  # Envia os dados para o servidor.
            resposta = self.socket_cliente.recv(1024).decode()  # Recebe a resposta do servidor.
            print(f"Resposta do servidor: {resposta}")  # Imprime a resposta recebida do servidor.
        except Exception as e:  # Captura qualquer exceção que ocorra.
            print(f"Erro na conexão: {e}")  # Imprime a mensagem de erro.
        finally:  # Bloco que sempre será executado, independentemente de erro ou não.
            self.socket_cliente.close()  # Fecha o socket do cliente.

    def escutar_broadcast(self):  # Método para escutar mensagens de broadcast do servidor.
        """Escuta mensagens de descoberta do servidor."""  # Docstring que descreve a função.
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Cria um socket UDP.
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permite reutilizar o endereço do socket.
        udp_socket.bind(('', 5050))  # Vincula o socket a todas as interfaces na porta 5050.
        
        while True:  # Inicia um loop infinito para escutar mensagens.
            mensagem, endereco = udp_socket.recvfrom(1024)  # Recebe mensagens do socket UDP.
            if mensagem.decode() == "DESCUBRA_CLIENTES":  # Verifica se a mensagem recebida é "DESCUBRA_CLIENTES".
                resposta = f"CLIENTE:{socket.gethostbyname(socket.gethostname())}"  # Prepara a resposta com o IP do cliente.
                udp_socket.sendto(resposta.encode(), endereco)  # Envia a resposta de volta ao endereço do servidor.
                print("Servidor encontrado! Enviando resposta...")  # Imprime uma mensagem indicando que a resposta foi enviada.

if __name__ == "__main__":  # Verifica se o script está sendo executado diretamente.
    cliente = Cliente()  # Cria uma instância da classe Cliente.
    cliente.escutar_broadcast()  # Chama o método para escutar broadcasts.
