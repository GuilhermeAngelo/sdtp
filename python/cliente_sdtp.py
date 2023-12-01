import socket
from os import *
from pathlib import *
from random import randint

# importando as constantes e funcoes de sdtp.py

from sdtp import *
#from sdtp.python.sdtp import *

FILE_PATH =  "lorem_ipsum.txt"

state = 0

while(1):

    if(state == 0):    
        # criando um pacote SDTP
        pout = SDTPPacket(0, 0, 0, TH_SYN, 0)
        pout.checksum = compute_checksum(pout.to_struct())

        print(f'check:{pout.checksum}')
        # imprimindo o pacote
        print("Pacote enviado:")

        # criando um socket UDP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # enviando o pacote SDTP para o servidor
        s.sendto(pout.to_struct(), (IP, PORTA))

        state = 1

    if (state == 1):
# recebendo um pacote pelo socket 's' e aguardando 2 segundos
        response = recvtimeout(s, 2000)

        if (response == -2):
            print("Erro de timeout - reenviar o pacote")
            s.sendto(pout.to_struct(), (IP, PORTA))

        else:
            print("Pacote recebido:")
            pin = SDTPPacket()
            pin.from_struct(response)

            if(pin.flags == TH_SYN | TH_ACK):
                pout = SDTPPacket(0,0,0,TH_ACK,0)
                s.sendto(pout.to_struct(), (IP, PORTA))
                
                print("pacote enviado")
                pout.print_struct()
                
                
                state = 2

    if(state == 2):
        FILE_LEN = stat(FILE_PATH).st_size
        cumulative_send = 0
        expected_ack = 1
        start_seqnum = randint(0,100)
          
        file = open("lorem_ipsum.txt","r")

# references: 
# 1. https://wiki.python.org/moin/UdpCommunication

