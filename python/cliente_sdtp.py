import socket
from os import stat
from random import randint

# importando as constantes e funcoes de sdtp.py
file_name = 'lorem_ipsum.txt'
FILE_LEN = stat(file_name).st_size
START = 0

from sdtp import *
#from sdtp.python.sdtp import *

state = 0

def mk_packet(seqnum, acknum, flags, window, data = ""):
    pout = SDTPPacket()
    pout.seqnum = seqnum
    pout.acknum = acknum
    pout.datalen = len(data)
    pout.flags = flags
    pout.window = window
    pout.data = data
    pout.checksum = compute_checksum(pout.to_struct())
    
    return pout

def send_packet(socket, pout):
    socket.sendto(pout.to_struct(), (IP, PORTA))

while(True):

    if(state == 0):    
        # criando um pacote SDTP
        pout = mk_packet(0, 0, TH_SYN, 0)

        # imprimindo o pacote
        print("Pacote enviado:")
        pout.print()

        # criando um socket UDP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # enviando o pacote SDTP para o servidor
        send_packet(s, pout)

        state = 1

    if (state == 1):
        # recebendo um pacote pelo socket 's' e aguardando 2 segundos
        response = recvtimeout(s, 2000)

        if (response == -2):
            print("Erro de timeout - reenviar o pacote")
            send_packet(s,pout)

        else:
            print("Pacote recebido:")
            
            pin = SDTPPacket()
            pin.from_struct(response)
           
            pin.print()

            if(pin.flags == TH_SYN | TH_ACK):
                pout = mk_packet(0,0,TH_ACK,0)
                send_packet(s, pout)
                
                print("pacote enviado:")
                pout.print_struct()

                state = 2

    if(state == 2):
        
        comulative_send = START
        expected_ack = START
        data_len = START
        ack_num = START

        seqnum = 0
        
        with open(file_name,'r') as file:

            while(comulative_send < FILE_LEN):

                file.seek(comulative_send)

                if pout.seqnum + len(pout.data) > expected_ack:
                    expected_ack = pout.seqnum + len(pout.data) + 1

                if (pin.window >= (FILE_LEN - comulative_send)):
                    dif = FILE_LEN - comulative_send
                    pos = file.seek(dif)
                    pout = mk_packet(pin.acknum + 1, pin.acknum + len(file.read(255)), 0x0, 0, file.read(dif))
                    send_packet(s, pout)
                else:

                    pout = SDTPPacket()
                    pout.seqnum = seqnum 
                    pout.flags = 0x0
                    pout.data = file.read(pin.window)
                    pout.datalen = int(len(pout.data))
                    pout.acknum = pout.datalen + seqnum 
                    pout.checksum = compute_checksum(pout.to_struct())
 
                    
                    send_packet(s,pout)

                    print("Pacote enviado:")
                    pout.print()

                    
                if(response == -1 or response == -2):
                    print("O pacote foi perdido - renviar o pacote")
                    send_packet(s, pout)
                    

                if (pin.flags == TH_ACK) and (response != -2 and response != -1) and compute_checksum(pin.to_struct()) == pin.checksum and pin.window <= 255:
                    print('pacote recebido é uma ack sem erros')
                    pin.print()

                    comulative_send += pout.datalen + 1
                    seqnum += pin.acknum + 1
                    
                response = recvtimeout(s, 2000)
                pin = SDTPPacket()
                pin.from_struct(response)
        
        state = 3        
            
    if state == 3:
        print("Deu certo")
        state = 4
    
    if state == 4:
        break                            
# references: 
# 1. https://wiki.python.org/moin/UdpCommunication