import RPi.GPIO as GPIO  
import time
import MySQLdb
import datetime
from gpiozero import MCP3008
  
### DECLARAÇõES DE VARIAVEIS / CONFIGURAÇÕES INICIAIS ###  
TempoInsert    = 60 # 60 Segundos
ultimoInsert   = datetime.datetime.now()
data_atual     = datetime.datetime.now()
DiferencaTempo = None
higro          = MCP3008(0) #canal 0 para leitura analogica de umidade
nivelUmidade   = 0;

pinoRele = 12

GPIO.setmode(GPIO.BCM)  
GPIO.setup(pinoRele, GPIO.OUT)
GPIO.output(pinoRele, 0)
GPIO.cleanup()

statusRele = "D"  
#print("Rele DESLIGADO")


conexao = MySQLdb.connect(host= "localhost",
                          user="root",
                          passwd="1234",
                          db="soil_analyser")

cursor = conexao.cursor()  

##########PROCEDIMENTOS#############
def gravaUmidade(umidade):
    try:
       global data_atual
       data_atual = datetime.datetime.now()
       
       global tempo_insert
       DiferencaTempo = round((data_atual-ultimoInsert).total_seconds())
       
       if  DiferencaTempo >= TempoInsert:           
           cursor = conexao.cursor()        
           cursor.execute("insert into soil_analyser.umidades(valor, id_sensor) values(%s, 1)", [umidade])
           conexao.commit();
           
           global ultimoInsert
           ultimoInsert = datetime.datetime.now()
           
    except Exception as e:    
       conexao.rollback()
       print(e)
       
def InsereIrrigacao(id_area):
    try:
       
       if  id_area > 0 :           
           cursor = conexao.cursor()        
           cursor.execute("insert into soil_analyser.irrigacoes(id_area) values(%s)", [id_area])           
           conexao.commit();
           
    except Exception as e:    
       conexao.rollback()
       print(e)
       
def FinalizaIrrigacao(id_area):
    try:
       
       if  id_area > 0 :           
           cursor = conexao.cursor()        
           cursor.execute("update soil_analyser.irrigacoes set irrigacoes.data_inicio = irrigacoes.data_inicio where irrigacoes.id_area = %s and irrigacoes.data_fim is null", [id_area])
           
           
           conexao.commit();
           
    except Exception as e:    
       conexao.rollback()
       print(e)       
       
def ligaRele():
    try:
       
       GPIO.setmode(GPIO.BCM)
       GPIO.setup(pinoRele, GPIO.OUT)        
       GPIO.output(pinoRele, 1)
       #print("BOMBA D'AGUA LIGADA")  
       
       global statusRele
       statusRele = "L"     
               
    except Exception as e:    
       #GPIO.cleanup() 
       print(e)
       
def desligaRele():
    try:      

       GPIO.setmode(GPIO.BCM)
       GPIO.setup(pinoRele, GPIO.OUT)         
       GPIO.output(pinoRele, 0)
       #print("BOMBA D'AGUA DESLIGADA")
       GPIO.cleanup()
       
       global statusRele       
       statusRele = "D"      
       
              
    except Exception as e:    
       #GPIO.cleanup() 
       print(e)        
    
def analisaUmidade(umidade):
    try:      
       cursor.execute("select ideal_menor from soil_analyser.areas where id_sensor = 1")
       
       data = cursor.fetchone()
       
       #print("Umidade Atual: {0}".format(umidade))
       #print("Ideal: {0}".format(int(data[0])))
       #print("Status Rele: " + statusRele)

       if ((int(umidade) < int(data[0])) and (statusRele == "D")):                    
          ligaRele()
          id_area = RetornaIdArea()
          InsereIrrigacao(id_area)
    
       if ((int(umidade) >= int(data[0])) and (statusRele == "L")):                  
          desligaRele()
          id_area = RetornaIdArea()
          FinalizaIrrigacao(id_area)
       
    except Exception as e:    
       print(e)
       
def leUmidade():
    try:
        
       higro_perc = round((1 - higro.value) * 100)
       
    except Exception as e:    
       print(e)
       
    return higro_perc

def RetornaIdArea():
    try:
        
       cursor.execute("select id_area from soil_analyser.areas where id_sensor = 1")
       
       data = cursor.fetchone()
       
    except Exception as e:    
       print(e)
       
    return int(data[0]) 

##########FIM_PROCEDIMENTOS##########


##########LOOP PRINCIPAL##########

try:

    while True:        

        global nivelUmidade;
        nivelUmidade = leUmidade()


        if (nivelUmidade < 0):
           nivelUmidade = 0
           
        #Grava umidade no banco
        gravaUmidade(nivelUmidade)
       
        #Analisa Umidade e aciona bomba caso necessário
        analisaUmidade(nivelUmidade)                    

      
        #Faz com que o loop seja a cada 1 segundo   
        time.sleep(2);     
   
except KeyboardInterrupt:  
  print("Finalizado!")
  GPIO.cleanup()  
  
##########FIM LOOP PRINCIPAL##########