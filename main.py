from datetime import datetime
from tkinter import *
from socket import *
from threading import *
from tkinter import filedialog
from pygame import mixer
from PIL import Image, ImageTk
import os

class GUI:
    def __init__(self, largura, altura, name):
        self.window = Tk()

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
        self.txt_area       = Text(self.canva, border=1, width= 125, height= 35)
        self.txt_field      = Entry(self.canva, width=85, border=1, bg= '#FFF')
        self.send_button    = Button(self.canva, text='Send', width= 20 , padx= 20, command=self.send)
        self.clear_button   = Button(self.canva, text='Clear', width= 20, padx= 20, command=self.clear)
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
        # ('0.0.0.0', 8271)

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
        self.completeMessage = self.msg + '\n' + self.name + ' - ' + self.time + '\n'

        #mandando no buffer a mensagem sem o nome e a hora
        self.soc.sendto(bytes(self.msg, 'utf-8'), self.addr_user_fixed) 
        #mandando no buffer a mensagem com nome e hora
        self.soc.sendto(bytes(self.completeMessage, 'utf-8'), self.addr_user_fixed)

        #se alguma coisa foi digitada e mandada, aparece na tela
        if self.msg != "":
            self.txt_area.insert(END, self.completeMessage)
            self.txt_field.delete(0, END)


    def receive(self):
        while True:

            #recebe a mensagem sem data e hora
            self.msgRecv, self.addr = self.soc.recvfrom(1024)
            #recebe a mensagem com data e hora
            self.msgComplRecv, self.addr = self.soc.recvfrom(1024)
            #decodifica elas
            self.msgRecv = self.msgRecv.decode('utf-8')
            self.msgComplRecv = self.msgComplRecv.decode('utf-8')
            #Se tiver mensagem, bota na tela
            if self.msgRecv != "":
                self.txt_area.insert(END, self.msgComplRecv)

    def clear(self):
        self.txt_area.delete(1.0, END)

    def getFile(self, event=NONE):
        path = filedialog.askopenfilename() # abrir seletor de arquivo

        # verificar se arquivo não vazio foi selecionado
        if path == '':
            return
        
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

            except:
                self.txt_area.insert(END, f"$FILE: {path.split('/')[-1]}")
        
        self.time = datetime.now()
        self.time = self.time.strftime('%H:%M, %d/%m/%Y')
        self.txt_area.insert(END, f'\n' + self.name + ' - ' + self.time + '\n')
        thr = Thread(target= self.sendFile, args= (path,), daemon= True)
        thr.start()

    def sendFile(self, file_path):
        self.sendFileLock.acquire()

        file_size = os.path.getsize(file_path)

        

        
        


if __name__ == '__main__':
    name = input("Digite o nome do usuário: ")
    interface = GUI(600,800, name)
    interface.start()
