import customtkinter as ctk
from tkinter import PhotoImage



class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.configuracoes_da_janela_inicial()
        self.tela_de_login()

    #configurando a janela principal
    def configuracoes_da_janela_inicial(self):
        self.geometry("700x400") 
        self.title("Login")
        self.resizable(False, False) 

    def tela_de_login(self):
        #trabalhando com as imagens
        self.img = PhotoImage(file="caminho_da_imagem.png") # Substitua pelo caminho da sua imagem
        self.lb_img = ctk.CTkLabel(self, text=None, image=self.img)
        self.lb_img.grid(row=0, column=0, padx=10)

        #titulo da nossa plataforma
        self.title = ctk.CTkLabel(self, text="faça seu login ou \n cadastre-se", font=("Century Gothic bold", 14))
        self.title.grid(row=1, column=0, pady=10)

        #Criar frame do formulário de login
        self.frame_login = ctk.CTkFrame(self, width=350, height=380)
        self.frame_login.place(x=350, y=10)

        #colocando widgets dentro do frame - formulario de login
        self.ln_title = ctk.CTkLabel(self.frame_login, text="faça o seu login", font=("Century Gothic bold", 22))
        self.lc_title.grid(row=0, column=0, pady=10, padx=10)




if __name__ == "__main__":
    app = App()
    app.mainloop()