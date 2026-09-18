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
        self.img = PhotoImage(file="caminho_da_imagem.png") # Substitua pelo caminho da imagem
        self.lb_img = ctk.CTkLabel(self, text=None, image=self.img)
        self.lb_img.grid(row=0, column=0, padx=10)

        #titulo da nossa plataforma
        self.title = ctk.CTkLabel(self, text="faça seu login ou \n cadastre-se", font=("Century Gothic bold", 14))
        self.title.grid(row=1, column=0, pady=10)

        #Criar frame do formulário de login
        self.frame_login = ctk.CTkFrame(self, width=350, height=380)
        self.frame_login.place(x=350, y=10)

        #colocando widgets dentro do frame - formulario de login
        self.lb_title = ctk.CTkLabel(self.frame_login, text="faça o seu login", font=("Century Gothic bold", 22))
        self.lb_title.grid(row=0, column=0, pady=10, padx=10)

        self.username_login_entry = ctk.CTkEntry(self.frame_login, width=300, placeholder_text="Seu nome de usuario",font=("Century Gothic bold", 16), corner_radius=15, border_color="blue") 
        self.username_login_entry.grid(row=1, column=0, pady=10, padx=10)

        self.senha_login_entry = ctk.CTkEntry(self.frame_login, width=300, placeholder_text="Sua senha...", font=("Century Gothic bold", 16), corner_radius=15, border_color="blue")
        self.senha_login_entry.grid(row=2, column=0, pady=10, padx=10)

        self.ver_senha = ctk.CTkCheckBox(self.frame_login,text="clique para ver a senha", font=("Century Gothic bold", 14),corner_radius=20)
        self.ver_senha.grid(row=3, column=0, pady=10, padx=10)

        self.btn_login = ctk.CTkButton(self.frame_login, width=300,text="Fazer Login".upper(), font=("Century Gothic bold", 16), corner_radius=15)
        self.btn_login.grid(row=4, column=0, pady=10, padx=10)

        self.sap = ctk.CTkLabel(self.frame_login, text="Se não tiver conta,\n clique no botão abaixo para se cadastrar", font=("Century Gothic bold", 10))
        self.sap.grid(row=5, column=0, pady=10, padx=10)

        self.btn_cadastrar = ctk.CTkButton(self.frame_login, width=300,fg_color="green",hover_color="darkgreen",text="Fazer Cadastro".upper(), font=("Century Gothic bold", 16), corner_radius=15)
        self.btn_cadastrar.grid(row=6, column=0, pady=10, padx=10)




if __name__ == "__main__":
    app = App()
    app.mainloop()