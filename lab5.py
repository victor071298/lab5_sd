import rpyc
from rpyc.utils.server import ThreadedServer
import threading
import os
import time

#Tomando o ID e a porta dos n processos
id = input("Informe o ID referente a sua aplicação (1 ate n)")
id = int(id)
porta = 5000 + id

#Fila de prioridade dos processos que estão esperando para escrever
fila = []

#Variável que será replicada
x = 0

#Variável booleana que indicará se o processo é a cópia primária, o processo de id 1 terá inicialmente essa característica
if id == 1:
    p = True
else:
    p = False

#Dicionário para armazenar as mudanças que ocorreram na cópia primária, como um histórico
h = {}

#Boolean que indica se a thread está alterando o valor da variável x
a = False

#Interface utilizada
def interface():
    global fila
    global a
    global h
    global x
    global id
    global p
    while True:
        f = int(input("Digite que operação deseja fazer, de 1 a 4, sendo:\n 1)ler o valor atual de x na replica\n 2)ler o historico de alteracoes do valor de x\n 3)alterar o valor de x\n 4)finalizar o programa\n"))
        #mostrando o valor de x
        if f == 1:
            print("A variavel x e: {}\n".format(x))  
        #mostrando o historico de alterações
        if f == 2:
            print("Historico de atualizacoes:{}\n".format(h))
        #tentando realizar o processo de escrita
        if f == 3:
            #Checando se o processo ja possui o chapeu
            #se não possuir, ele entrará em uma fila e quando tiver a certeza de o processo com o chapeu nao esta escrevendo no momento, ele tentará escrever
            if not p:
                #tomando as possiveis listas de outros processos que ja entraram antes dele na fila
                for i in range(4):
                        id_teste_k = i+1
                        if id_teste_k!=id:
                            conn = rpyc.connect('localhost',5000+i+1)
                            fila_atual = conn.root.exposed_fila()
                            if len(fila_atual) != 0:                            
                                for elemento in fila_atual:
                                    fila.append(elemento)
                            conn.close()
                fila.append(id)
                #Eliminando duplicatas
                fila = list(dict.fromkeys(fila))
                #Aguardando que o processo que tem o chapeu termina sua escrita, enquanto atualiza frequentemente a lista de usuarios com chapeu, para garantir que esta observando o processo correto
                while True:
                    #Aguardando um segundo para o caso do processo que toma o chapeu se eliminar da fila antes que o processo que possui chapeu no momento seja atualizado
                    time.sleep(1)
                    for i in range(4):
                        id_teste_i = i+1
                        if id_teste_i != id:
                            conn = rpyc.connect('localhost',5000+id_teste_i)
                            p_teste = conn.root.exposed_tem_chapeu()
                            conn.close()
                            if p_teste:
                                conn = rpyc.connect('localhost',5000+id_teste_i)
                                a_teste = conn.root.exposed_esta_escrevendo()
                                conn.close()
                                break
                    #uma vez que nao ha ninguem escrevendo e o processo é o unicom sua fila, ele finalmente podera pegar o chapeu e se remover da fila dos outros processos
                    if not a_teste and len(fila) == 1:
                        copia_primaria.exposed_pegar_chapeu(copia_primaria,id_teste_i)
                        a = True
                        fila.remove(id)
                        for i in range(4):
                            id_teste_j = i+1
                            if id_teste_j!=id:
                                conn = rpyc.connect('localhost',5000+id_teste_j)
                                conn.root.exposed_atualizar_fila(id)
                                conn.close()
                        break
            #se o processo ja possuir o chapeu, basta alterar a variavel 'a' para deixar claro que a partir de agora ele ira iniciar um processo de escrita
            else:
                a = True
            c = input("Digite o novo valor que deseja para a variavel x\n")
            c = int(c)
            copia_primaria.exposed_modificar_variavel_local(copia_primaria,c)
            #Finalmente, realizando o processo de escrita, até que o usuario digite 'n', indicando que nao deseja mais escrever
            while True:
                c = input("Digite o novo valor que deseja para variavel local, caso nao deseje mais modificar a variavel, digite a letra n\n")
                #Uma vez que o usuario digitar 'n', atualizamos todos os outros processos com o novo valor de x e indicamos que este processo nao esta mais escrevendo 
                if c == 'n':
                    print("Finalizando as alteracoes, enviando o valor final para os outros processos\n")
                    for k in range (4):
                        id_teste=k+1
                        if id_teste!= id:
                            conn = rpyc.connect('localhost',5000+id_teste)
                            conn.root.exposed_modificar_variavel_global(id,x)
                            conn.close()
                    a = False
                    break                       
                else:
                    c = int(c)
                    copia_primaria.exposed_modificar_variavel_local(copia_primaria,c)
        #encerrando a aplicação
        if f == 4:
            print("Encerrando a aplicacao")
            os._exit(1)
    

class copia_primaria(rpyc.Service):
    
    #Função responsavel por fazer a tomada de chapeu
    def exposed_pegar_chapeu(self,id_chapeu):
        global p
        conn = rpyc.connect('localhost',5000+id_chapeu)
        conn.root.exposed_tira_chapeu()
        conn.close()
        p = True
    
    #função que indica se a função atual está em uma fila
    def exposed_fila(self):
        global fila
        return fila
    
    #função que atualiza a fila dos outros processos
    def exposed_atualizar_fila(self,id_retirado):
        global fila
        try:
            fila.remove(id_retirado)
        except:
            pass 
                    
    #Função responsavel por modificar o valor de x nas replicas após a replica com chapeu finalizar suas modificações
    def exposed_modificar_variavel_global(self,id,mod):
        global x
        global h
        x = mod
        aux1 = []
        aux2 = {}
        try:
            for i in h[id]:
                aux1.append(i)
        except:
            pass
        aux1.append(x)
        aux2[id] = aux1
        h.update(aux2) 
        
    #Função responsavel por remover o chapeu da replica que o possui                
    def exposed_tira_chapeu(self):
        global p
        p = False
    
    #Função responsavel por tomar o valor local do chapeu de um processo para fins de teste    
    def exposed_tem_chapeu(self):
        global p
        return p
    
    #Função responsavel por tomar o valor local a da variavel que possui o chapeu, para checar se ela esta realizando uma escrita no momento
    def exposed_esta_escrevendo(self):
        global a
        return a
                        
    #Função responsavel por modificar a variavel x localmente    
    def exposed_modificar_variavel_local(self,novo_valor):
        global x
        global id
        global p 
        x = novo_valor
        aux1 = []
        aux2 = {}
        try:
            for i in h[id]:
                aux1.append(i)
        except:
            pass
        aux1.append(x)
        aux2[id] = aux1
        h.update(aux2) 

#inicializando o servidor e a interface simultaneamente
t1 = threading.Thread(target = interface,args=())
t1.start()
server = ThreadedServer(copia_primaria,port = porta)
server.start()                                    
