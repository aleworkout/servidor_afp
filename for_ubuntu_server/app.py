import os
import time
from flask import Flask, render_template, request, send_from_directory
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_DIR = os.path.join(os.getcwd(), UPLOAD_FOLDER)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def validate_rut(rut):
    return len(rut) >= 8 and rut[-1].isalnum()

def generate_with_selenium(rut):
    chrome_options = Options()
    # Mantenha o modo headless comentado para depuração
    # chrome_options.add_argument("--headless")
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True
    })

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # 1. Listar arquivos existentes antes do download
        existing_files = set(os.listdir(DOWNLOAD_DIR))
        
        # 2. Executar o processo de geração
        print("Acessando a página...")
        driver.get("https://www.spensiones.cl/apps/certificados/formCertificadoAfiliacion.php")
        wait = WebDriverWait(driver, 20)  # Aumentado para 20 segundos

        # Preencher RUT Afiliado
        print("Preenchendo RUT Afiliado:", rut)
        wait.until(EC.presence_of_element_located((By.ID, "rutAfiliado"))).send_keys(rut.replace('.', '').replace('-', ''))
        
        # Selecionar opção de pesquisa
        print("Selecionando 'Aceito' para pesquisa")
        driver.find_element(By.ID, "optionsRadios1").click()

        # Preencher dados do consultor (fictícios)
        print("Preenchendo Nome: Cyber Cafe Generico")
        driver.find_element(By.ID, "nombre").send_keys("Cyber Cafe Generico")
        
        print("Preenchendo Email: cyber@example.com")
        driver.find_element(By.ID, "email1").send_keys("cyber@example.com")
        driver.find_element(By.ID, "email2").send_keys("cyber@example.com")
        
        print("Preenchendo Telefone: +56912345678")
        driver.find_element(By.ID, "telefono1").send_keys("+56912345678")
        driver.find_element(By.ID, "telefono2").send_keys("+56912345678")

        # 3. Registrar o momento exato antes do clique
        start_time = time.time()
        
        print("Clicando em 'Generar Certificado'")
        driver.find_element(By.ID, "btn_buscar").click()

        # 4. Aguardar exclusivamente pelo NOVO arquivo
        downloaded_file = wait_for_download_to_complete(existing_files)
        
        # 5. Renomear apenas o novo arquivo
        new_filename = rename_downloaded_file(downloaded_file, rut, start_time)

        print("Certificado gerado com sucesso:", new_filename)
        return new_filename

    except TimeoutException as e:
        print("Elemento não encontrado:", str(e))
        raise
    finally:
        driver.quit()

def wait_for_download_to_complete(existing_files, timeout=40):
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Verificar apenas por NOVOS arquivos PDF
        current_files = set(os.listdir(DOWNLOAD_DIR))
        new_files = current_files - existing_files
        
        pdf_files = [f for f in new_files if f.lower().endswith('.pdf')]
        
        if pdf_files:
            # Obter o arquivo mais recente dentre os novos
            latest_file = max(
                [os.path.join(DOWNLOAD_DIR, f) for f in pdf_files],
                key=os.path.getctime
            )
            return os.path.basename(latest_file)

        # Verificar por arquivos temporários
        temp_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".crdownload")]
        if temp_files:
            print("Download em andamento...")
            time.sleep(1)
            continue
            
        time.sleep(1)
    
    raise Exception("Download do PDF não foi concluído a tempo")

def rename_downloaded_file(filename, rut, timestamp):
    # Gerar nome base com timestamp para evitar conflitos
    base_name = f"certificado_afp_{rut}_{int(timestamp)}.pdf"
    new_filepath = os.path.join(DOWNLOAD_DIR, base_name)
    
    # Renomear o arquivo baixado
    os.rename(os.path.join(DOWNLOAD_DIR, filename), new_filepath)
    
    print(f"Arquivo renomeado para: {base_name}")
    return base_name

@app.route('/')
def index():
    return render_template('afp_form.html')

@app.route('/generate', methods=['POST'])
def generate_certificate():
    rut = request.form['rut'].replace('.', '').replace('-', '').upper()
    
    if not validate_rut(rut):
        return "RUT inválido. Formato correto: 12345678K", 400
    
    try:
        pdf_path = generate_with_selenium(rut)
        return render_template('result.html', 
                            rut=rut,
                            pdf_path=pdf_path)
    
    except WebDriverException as e:
        return f"Erro no navegador: {str(e)}", 500
    except Exception as e:
        return f"Erro inesperado: {str(e)}", 500

@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
