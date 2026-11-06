"""Iniciador local da demonstracao academica Luxo Mundo Pet."""
import os
from pathlib import Path
import runpy
import threading
import webbrowser

os.environ['HOST'] = '127.0.0.1'
os.environ.setdefault('PORT', '8080')
os.environ['ADMIN_PASSWORD'] = 'GrupoPet2026!'
url = 'http://127.0.0.1:' + os.environ['PORT']
print('\nLUXO MUNDO PET - DEMONSTRACAO DA FACULDADE')
print('Loja: ' + url)
print('Painel: ' + url + '/admin')
print('Senha do painel: GrupoPet2026!')
print('Mantenha esta janela aberta. Para encerrar, pressione Ctrl+C.\n')
threading.Timer(1.5, lambda: webbrowser.open(url)).start()
runpy.run_path(str(Path(__file__).with_name('app.py')), run_name='__main__')
