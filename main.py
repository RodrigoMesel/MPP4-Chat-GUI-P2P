from datetime import datetime
from time import sleep
from tkinter import *
from socket import *
from threading import *
from tkinter import filedialog
from pygame import mixer
from PIL import Image, ImageTk
import os
import tqdm


class GUI:
    def __init__(self, largura, altura, name):
        self.window = Tk()

        self.FILE_INDICATOR = '<F!L&_!$_(0m!nG>'
        self.BUFFER_SIZE = 4096

        self.canva = Canvas(self.window, width= largura, height= altura)
        self.canva.grid(columnspan= 3)
        self.createWidgets()
        self.name = name
        self.window.title("Chat P2P de " + self.name)

        self.con = self.serv_connect()
        self.user_connect(self.con) 

        # locks
        self.sendFileLock = Lock()
        self.recvFileLock = Lock()

        #listas
        self.img_bank = list()
        self.audio_bank = dict()
        self.video_bank = dict()

        mixer.init()
        self.audio_player = mixer.Channel(0)

        #threadSend = Thread(target= self.send, daemon= True)
        threadRecv = Thread(target= self.receive, daemon= True)

        threadRecv.start()

        self.send()


    def createWidgets(self):
        self.txt_area       = Text(self.canva, border=0, width= 80, height= 35)
        self.txt_field      = Entry(self.canva, width=50, border=1, bg= '#FFF')
        self.send_button    = Button(self.canva, text='Send', width= 10 , padx= 20, command=self.send)
        self.clear_button   = Button(self.canva, text='Clear', width= 10, padx= 20, command=self.clear)
        self.getFile_button = Button(self.canva, text='File', width= 10, padx= 10, command=self.getFile)
        
        self.window.bind('<Return>', self.send)
        self.txt_area.config(background= "#A0e6a4")

        self.txt_area   .grid(column=0, row=0, columnspan=6)
        self.txt_field  .grid(column=0, row=1, columnspan=2)
        self.send_button.grid(column=3, row=1)
        self.clear_button.grid(column=5, row=1)
        self.getFile_button.grid(column=4, row=1)

        self.window.bind('<Return>', self.send)

    def start(self):
        self.window.mainloop()


    def serv_connect(self) -> socket:
        self.s = socket(AF_INET, SOCK_STREAM)
        self.s.connect(('localhost', 26262))
        return self.s


    def fix_addr(self, addr_user) -> tuple:
        self.decode_addr = addr_user.decode('utf-8')
        self.list_addr = self.decode_addr.strip('()')
        self.list_addr = self.list_addr.replace("'", "")
        self.list_addr = self.list_addr.split(', ')
        self.list_addr[1] = int(self.list_addr[1])
        self.tuple_addr = tuple(self.list_addr)

        return self.tuple_addr


    def user_connect(self, s):
        self.addr_user = s.recv(1024)
        self.addr_this = s.recv(1024)
        self.addr_user_fixed = self.fix_addr(self.addr_user)
        self.addr_my_fixed = self.fix_addr(self.addr_this)
        print(f'{self.addr_my_fixed} connected with {self.addr_user_fixed}\n')
        self.soc = socket(AF_INET, SOCK_DGRAM) # UDP
        self.soc.bind(self.addr_my_fixed)

    def send(self, event= NONE):
        self.time = datetime.now()
        self.time = self.time.strftime('%H:%M, %d/%m/%Y')
        self.msg = self.txt_field.get()
        if self.msg == "":
            return
        elif self.msg[0:5] == '!open':
            try:
                os.startfile(os.getcwd()+'\\'+ self.msg[6:])
            except:
                print('FUDEU')
        else:
            self.completeMessage = self.name + ' - ' + self.time + ':\n' + self.msg + '\n\n'
            #mandando no buffer a mensagem com nome e hora
            self.soc.sendto(bytes(self.completeMessage, 'utf-8'), self.addr_user_fixed)
            self.txt_area.insert(END, self.completeMessage)

        self.txt_field.delete(0, END)

    def receive(self):
        while True:

            #recebe a mensagem com data e hora
            self.msgComplRecv, self.addr = self.soc.recvfrom(1024)
            #decodifica ela
            self.msgComplRecv = self.msgComplRecv.decode('utf-8')
            #Se tiver mensagem, bota na tela
            # começa a receber o arquivo
            if self.msgComplRecv == self.FILE_INDICATOR:

                self.recvFileLock.acquire()

                senderName, senderTime = self.soc.recv(self.BUFFER_SIZE).decode('utf-8').split('<@>')
                self.txt_area.insert(END, senderName + ' - ' + senderTime + ':\n')

                file_path, file_size = self.soc.recv(self.BUFFER_SIZE).decode('utf-8').split('<@>')
                file_size = int(file_size)

                # create progressbar 
                progress_bar = tqdm.tqdm(
                    range(file_size), 
                    f"Receiving .{file_path.split('.')[-1]} file", 
                    unit="B", 
                    unit_scale=True, 
                    unit_divisor=1024)

                # começar a receber o arquivo
                with open(file_path, 'wb') as f:

                    while file_size > 0:
                        data = self.soc.recv(self.BUFFER_SIZE)
                        file_size -= self.BUFFER_SIZE

                        f.write(data)
                        progress_bar.update(len(data))
                f.close()

                self.recvFileLock.release()

                # analisar o formato do arquivo
                file_format = file_path.split('.')[-1]

                # verificar se é arqivo de audio
                if file_format in ['mp3', 'wav', 'ogg']:
                    audio = mixer.Sound(file_path)
                    self.audio_bank[file_path] = audio

                    
                    self.txt_area.insert(END, f"$AUDIO: {file_path.split('/')[-1]}")
                
                elif file_format == 'mp4':
                    self.txt_area.insert(END, f"$VIDEO: {file_path.split('/')[-1]}")

                else:
                    try:
                        img = Image.open(file_path)

                        miniature_img = img.resize((325, (325*img.height)//img.width), Image.ANTIALIAS)
                        my_img = ImageTk.PhotoImage(miniature_img)
                        self.img_bank.append(my_img)
                        self.txt_area.image_create(END, image=self.img_bank[-1])
                        self.txt_area.insert(END, "\n\n")

                    except:
                        self.txt_area.insert(END, f"$FILE: {file_path.split('/')[-1]}")
                
            else:
                self.txt_area.insert(END, self.msgComplRecv)


    def clear(self):
        self.txt_area.delete(1.0, END)

    def getFile(self, event=NONE):
        path = filedialog.askopenfilename() # abrir seletor de arquivo

        # verificar se arquivo não vazio foi selecionado
        if path == '':
            return
    

        self.time = datetime.now()
        self.time = self.time.strftime('%H:%M, %d/%m/%Y')
        self.txt_area.insert(END, self.name + ' - ' + self.time + ':\n')

        # analisar o formato do arquivo
        file_format = path.split('.')[-1]

        # verificar se é arqivo de audio
        if file_format in ['mp3', 'wav', 'ogg']:
            audio = mixer.Sound(path)
            self.audio_bank[path] = audio

            
            self.txt_area.insert(END, f"$AUDIO: {path.split('/')[-1]}")
        
        elif file_format == 'mp4':
            self.txt_area.insert(END, f"$VIDEO: {path.split('/')[-1]}")

        else:
            try:
                img = Image.open(path)

                miniature_img = img.resize((325, (325*img.height)//img.width), Image.ANTIALIAS)
                my_img = ImageTk.PhotoImage(miniature_img)
                self.img_bank.append(my_img)
                self.txt_area.image_create(END, image=self.img_bank[-1])
                self.txt_area.insert(END, "\n\n")

            except:
                self.txt_area.insert(END, f"$FILE: {path.split('/')[-1]}")
        


        # indicar ao outro peer que um arquivo será enviado
        self.soc.sendto(bytes(self.FILE_INDICATOR, 'utf-8'), self.addr_user_fixed)
        
        print('enviando')
        thr = Thread(target= self.sendFile, args= (path,), daemon= True)
        thr.start()

    def sendFile(self, file_path : str):

        file_size = os.path.getsize(file_path)
        path = file_path.split('/')[-1]

        self.time = datetime.now()
        self.time = self.time.strftime('%H:%M, %d/%m/%Y')

        self.soc.sendto(f"{self.name}<@>{self.time}".encode('utf-8'),self.addr_user_fixed)
        
        self.sendFileLock.acquire()

        # enviar nome e tamnho do arquivo
        self.soc.sendto(f"{path}<@>{file_size}".encode('utf-8'), self.addr_user_fixed)

        # create progressbar 
        progress_bar = tqdm.tqdm(
            range(file_size), 
            f"Sending .{path.split('.')[-1]} file", 
            unit="B", 
            unit_scale=True, 
            unit_divisor=1024)

        # enviar arquivo
        with open(file_path, "rb") as f:
            bytes = f.read(self.BUFFER_SIZE)
            # atualizar progress bar
            progress_bar.update(len(bytes))
            while bytes:
                sleep(0.0005)
                self.soc.sendto(bytes, self.addr_user_fixed)
                # ler os bytes do arquivo
                bytes = f.read(self.BUFFER_SIZE)
                # atualizar progress bar
                progress_bar.update(len(bytes))
        
        f.close()
        self.sendFileLock.release()
        
               


if __name__ == '__main__':
    name = input("Digite o nome do usuário: ")
    interface = GUI(600,800, name)
    interface.start()
