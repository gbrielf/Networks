import socket  # Importa o módulo socket para comunicação de rede.
import psutil  # Importa o módulo psutil para coletar informações do sistema.
import json  # Importa o módulo json para manipulação de dados em formato JSON.
import wmi  # Importa o módulo wmi para interagir com o Windows Management Instrumentation.
import threading  # Importa o módulo threading para permitir a execução de múltiplas threads.

class Servidor:  # Define a classe Servidor.
    def __init__(self, host='0.0.0.0', porta=8080, porta_broadcast=5050):  # Método construtor da classe.
        self.host = host  # Atribui o endereço IP do servidor à variável de instância.
        self.porta = porta  # Atribui a porta do servidor à variável de instância.
        self.porta_broadcast = porta_broadcast  # Atribui a porta de broadcast à variável de instância.
        self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Cria um socket TCP.
        self.socket_servidor.bind((self.host, self.porta))  # Vincula o socket ao endereço e porta especificados.
        self.socket_servidor.listen(5)  # Coloca o socket em modo de escuta, permitindo até 5 conexões pendentes.
        self.clientes_descobertos = []  # Inicializa uma lista para armazenar os IPs dos clientes descobertos.
        print(f"Servidor iniciado em {self.host}:{self.porta}")  # Imprime uma mensagem indicando que o servidor foi iniciado.

    def coletar_dados(self):  # Método para coletar dados do sistema.
        dados = {  # Cria um dicionário para armazenar os dados coletados.
            "processadores": psutil.cpu_count(logical=True),  # Conta o número de processadores lógicos.
            "memoria_ram_livre": round(psutil.virtual_memory().available / (1024 * 1024), 2),  # Obtém a memória RAM livre em MB.
            "espaco_disco_livre": round(psutil.disk_usage('/').free / (1024 * 1024 * 1024), 2),  # Obtém o espaço livre em disco em GB.
        }
        
        try:  # Inicia um bloco try para capturar exceções.
            conn = wmi.WMI(namespace="root\\cimv2")  # Conecta ao namespace WMI para coletar informações do sistema.
            infos = conn.Sensor()  # Obtém informações dos sensores disponíveis.
            temperatura_CPU = ""  # Inicializa uma string para armazenar as temperaturas da CPU.
            for sensor in infos:  # Itera sobre os sensores coletados.
                if 'GPU' not in sensor.Name and sensor.SensorType == 'Temperature':  # Filtra sensores de temperatura que não são de GPU.
                    if temperatura_CPU:  # Se já houver uma temperatura registrada, adiciona um separador.
                        temperatura_CPU += ' | '
                    temperatura_CPU += f"{sensor.Name} ({sensor.Value:.0f})"  # Adiciona a temperatura do sensor à string.
            dados["temperatura_cpu"] = temperatura_CPU  # Adiciona a temperatura da CPU ao dicionário de dados.
        except Exception as e:  # Captura qualquer exceção que ocorra.
            dados["temperatura_cpu"] = f"Erro ao coletar a temperatura: {str(e)}"  # Registra um erro se a coleta falhar.

        return json.dumps(dados)  # Converte o dicionário em uma string JSON e retorna.

    def descobrir_clientes(self):  # Método para enviar um broadcast e descobrir clientes.
        """Envia um broadcast e aguarda respostas dos clientes."""  # Docstring que descreve a função.
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Cria um socket UDP.
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Permite o envio de broadcasts.
        broadcast_socket.settimeout(5)  # Define um tempo de espera de 5 segundos para respostas.
        mensagem = "SERVIDOR: Descoberta de clientes"  # Mensagem de broadcast a ser enviada.
        broadcast_socket.sendto(mensagem.encode(), ('255.255.255.255', self.porta_broadcast))  # Envia a mensagem de broadcast.
        print("[BROADCAST] Mensagem de descoberta enviada...")  # Imprime uma mensagem indicando que o broadcast foi enviado.
        
        try:  # Inicia um bloco try para capturar exceções.
            while True:  # Inicia um loop infinito para escutar respostas.
                dados, endereco = broadcast_socket.recvfrom(1024)
                ip_cliente = endereco[0]
                if ip_cliente not in self.clientes_descobertos:
                    self.clientes_descobertos.append(ip_cliente)
                    print(f"[BROADCAST] Cliente descoberto: {ip_cliente}")
        except socket.timeout:
            print("[BROADCAST] Descoberta finalizada.")
        
        broadcast_socket.close()

    def iniciar(self):
        threading.Thread(target=self.descobrir_clientes).start()
        
        while True:
            conn, addr = self.socket_servidor.accept()
            print(f"Conexão estabelecida com {addr}")
            dados = self.coletar_dados()
            conn.sendall(dados.encode())
            conn.close()

if __name__ == "__main__":
    servidor = Servidor()
    servidor.iniciar()
