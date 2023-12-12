import socket
from os import stat

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
    pout.data = data
    pout.datalen = len(pout.data)
    pout.flags = flags
    pout.window = window
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
        
        expected_ack = START
        data_len = START
        ack_num = START
        seqnum = START
        window = pin.window

        with open(file_name,'r') as file:

            while(ack_num <= FILE_LEN - 1):

                file.seek(ack_num)

                if (pin.window > (FILE_LEN - ack_num) and pin.window <= 255):
                    pout = SDTPPacket()    
                    dif = FILE_LEN - ack_num
                    pout.seqnum = pin.acknum
                    pout.data = file.read(dif)
                    pout.datalen = len(pout.data)

                    send_packet(s, pout)
                    
                else:
                    if pin.window <= 255:     
                        pout = SDTPPacket()
                        pout.seqnum = seqnum 
                        pout.flags = 0x0
                        pout.data = file.read(window)
                        pout.datalen = len(pout.data)
                        pout.checksum = compute_checksum(pout.to_struct())

                    if pout.seqnum + len(pout.data) > expected_ack:
                        expected_ack = pout.seqnum + len(pout.data)

                    send_packet(s, pout)
                    print("Pacote enviado:")
                    pout.print()

                response = recvtimeout(s, 2000)
                
                if response == -1 or response == -2:
                    if pin.window <= 255:
                        print("O pacote foi perdido - renviar o pacote")
                        pout = SDTPPacket()
                        pout.seqnum = seqnum 
                        pout.flags = 0x0
                        pout.data = file.read(window)
                        pout.datalen = len(pout.data)
                        pout.checksum = compute_checksum(pout.to_struct())
                        send_packet(s, pout)
                else:
                    pin = SDTPPacket()
                    pin.from_struct(response)
                        
                    if ((pin.flags == TH_ACK) and
                        (pin.window <= 255) and 
                        (compute_checksum(pin.to_struct()) == pin.checksum) and
                        (pin.acknum <= expected_ack)
                        ):

                        print('pacote recebido é uma ack sem erros')
                        pin.print()

                        window = pin.window
                        ack_num = pin.acknum
                        seqnum = pin.acknum
            state = 3        
            
    if state == 3:
        pout = SDTPPacket()
        pout.flags = TH_FIN
        send_packet(s,pout)
        
        response = recvtimeout(s,2000)

        if response == -1 or response == -2:
            send_packet(s,pout)
        else: 
            pin = SDTPPacket()
            pin.from_struct(response)

            if pin.flags == TH_RST and (compute_checksum(pin.to_struct())== pin.checksum):
                print("Finalizado com Sucesso!")
                
                break # Finalizando com estilo