import socket
import threading
import time
import datetime
import netifaces
import re

class HostnameError(Exception):
    pass

class LocalIPError(Exception):
    pass

class NetworkIPError(Exception):
    pass

class SendMessageError(Exception):
    pass

class Network:

    def __init__(self, port=12345):
        def search_net_ip(addrs):
            for addr in addrs:
                if addr[:3] == '192':
                    return addr
            raise NetworkIPError("Не найден сетевой IP")


        def search_local_ip(addrs):
            for addr in addrs:
                if addr[:3] == '127':
                    return addr
            raise NetworkIPError("Не найден сетевой IP")      
        

        try:
            self.__hostname = socket.gethostname()
        except socket.error as e:
            raise HostnameError(f'Ошибка получения имени хоста: {e}') from e
        except Exception as e:
            raise HostnameError(f'Неожиданная ошибка получения имени хоста: {e}') from e

        try: 
            interfaces = netifaces.interfaces()
            if not interfaces:
                raise NetworkIPError(f'Не найдены сетевые интерфейсы')
            nets = []

            for interface in interfaces:
                if 2 in netifaces.ifaddresses(interface).keys():
                    ip = netifaces.ifaddresses(interface)[2][0]['addr']
                    nets.append(ip)
                else:
                    continue
            
            self.__local_ip = search_local_ip(nets)
            self.__network_ip = search_net_ip(nets)
            
        except socket.error as e:
            raise NetworkIPError(f'Ошибка получения сетевого IP: {e}') from e
        except Exception as e:
            raise NetworkIPError(f'Неожиданная ошибка получения сетевого IP: {e}') from e

        self.__port = port 

    @property
    def get_hostname(self):
        return self.__hostname  

    @property
    def get_local_ip(self):
        return self.__local_ip
    
    @property
    def get_network(self):
        return self.__network_ip
    
    @property
    def get_port(self):
        return self.__port


def create_network(port=12345):
    try:
        ntw = Network(port=port)

        print(f'Имя хоста: {ntw.get_hostname}')
        print(f'Локальный IP: {ntw.get_local_ip}')
        print(f'Сетевой IP: {ntw.get_network}')
        print(f'Активный порт: {ntw.get_port}')
        return ntw, 0
    except HostnameError as e:
        print(f'Критическая ошибка имени хоста: {e}')
        return None, 1
    except LocalIPError as e:
        print(f'Критическая ошибка локального IP: {e}')
        return None, 2
    except NetworkIPError as e:
        print(f'Критическая ошибка сетевого IP: {e}')
        return None, 3
    except Exception as e:
        print(f'Неожиданная ошибка: {e}')
        return None, 4


def receive_messages(sock, port):
    print(f'Поток запущен на порту {port}')
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            print(f'[{timestamp}] Сообщение от {addr[0]}: {data.decode("utf-8")}')
            print('Введите сообщение >>> ', end='', flush=True)
        except socket.timeout:
            continue
        except Exception as e:
            print(f'Ошибка приема: {e}')
            break

def send_message(sock, target_ip, port=12345):
    print(f'Отправка на {target_ip}:{port}')
    while True:
        try:
            message = input('Введите сообщение >>> ')
            if message.lower().strip() == 'exit':
                break

            sock.sendto(message.encode('utf-8'), (target_ip, port))
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            print(f'[{timestamp}] Вы: {message}')
            print(f'Отправлено на {target_ip}:{port}')
        except Exception as e:
            print(f'Ошибка отправки: {e}')


def start_udp_socket(target_ip, port=12345):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # IPv4, UDP
        sock.bind(('0.0.0.0', port))
        sock.settimeout(1.0)

        print(f'Слушаю порт {port}')
        print(f'Отправляю сообщения на {target_ip}:{port}')
        print('Для выхода введите "exit"')
        print('-' * 50)

        receiver = threading.Thread(target=receive_messages, args=(sock, port))
        receiver.daemon = True
        receiver.start()

        time.sleep(.5)

        send_message(sock, target_ip, port)

    except Exception as e:
        raise SendMessageError(f'Неизвестная ошибка отправки сообщения: {e}') from e


def check_ip(ip):
    pattern = r'^192\.168\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return bool(re.match(pattern=pattern, string=ip))

def main():
    print('=== Простой UDP-чат для локальной сети на одном порту ===')

    ntw, code_error = create_network()
    if not ntw:
        return code_error
    
    target_ip = input('Введите адрес собеседника >>> ')
    if not check_ip(target_ip):
        target_ip = input('Введите правильный адрес собеседника >>> ')

    try:
        start_udp_socket(target_ip)
        return 0
    except Exception as e:
        print(f'Неизвестная ошибка в udp-сокете: {e}')
        exit(5)
     

if __name__ == '__main__':
    exit(main())
