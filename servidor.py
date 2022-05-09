from socket import *

s = socket(AF_INET, SOCK_STREAM)

s.bind(('localhost', 26262))

s.listen(2)

while 1:

    print('Buscando conexão...')
    
    firstConnection, address1 = s.accept()
    secondConnection, address2 = s.accept()

    print(f'Primeiro usuário: {address1}')
    print(f'Segundo usuário: {address2}')

    strAdd1 = str(address1)
    strAdd2 = str(address2)


    firstConnection.sendto(bytes(strAdd1, 'utf-8'), address1)
    firstConnection.sendto(bytes(strAdd2, 'utf-8'), address1)
    
    secondConnection.sendto(bytes(strAdd2, 'utf-8'), address2)
    secondConnection.sendto(bytes(strAdd1, 'utf-8'), address2)

    print('Conexão realizada entre usuários')

    firstConnection.close()
    secondConnection.close()