import customtkinter
import tkinter as tk

class LoginPageUI(customtkinter.CTkFrame):
    def __init__(self, master, app_instance, *args, **kwargs):
        super().__init__(master, fg_color="transparent", *args, **kwargs)
        self.app = app_instance

        
        font_title = self.app.font_title
        font_header = self.app.font_header
        font_normal = self.app.font_normal
        font_bold = self.app.font_bold

        customtkinter.CTkLabel(self, text="Bem-vindo ao Dashboard de Vendas", font=font_title).pack(pady=(0,10))
        customtkinter.CTkLabel(self, text="Login", font=font_header).pack(pady=(0,20))

        form_frame = customtkinter.CTkFrame(self)
        form_frame.pack()

        customtkinter.CTkLabel(form_frame, text="Usuário:", font=font_normal).grid(row=0, column=0, padx=5, pady=10, sticky="w")
        self.username_entry = customtkinter.CTkEntry(form_frame, width=250, font=font_normal)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)

        customtkinter.CTkLabel(form_frame, text="Senha:", font=font_normal).grid(row=1, column=0, padx=5, pady=10, sticky="w")
        self.password_entry = customtkinter.CTkEntry(form_frame, show="*", width=250, font=font_normal)
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        login_button = customtkinter.CTkButton(form_frame, text="Entrar", command=self._on_login_attempt, font=font_bold)
        login_button.grid(row=2, column=0, columnspan=2, pady=20)

        self.bind('<Return>', lambda event: self._on_login_attempt())
        self.username_entry.bind('<Return>', lambda event: self._on_login_attempt())
        self.password_entry.bind('<Return>', lambda event: self._on_login_attempt())


    def _on_login_attempt(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        self.app._attempt_login(username, password)

    def clear_password_entry(self):
        self.password_entry.delete(0, "end")

    def set_focus(self):
        
        self.username_entry.focus()