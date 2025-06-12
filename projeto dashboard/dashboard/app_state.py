
import pandas as pd

class AppState:

    def __init__(self):
        self.logged_in = False
        self.user_role = None
        self.username = None
        self.user_permissions = {}
        self.df_vendas = None
        self.df_filtrado = None
