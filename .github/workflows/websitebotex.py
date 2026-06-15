import psutil
import os
import sys
import time

os.system("pkill -9 chrome")  # Forcefully kill all Chrome processes

def kill_chrome():
    for process in psutil.process_iter(attrs=["pid", "name"]):
        if "chrome" in process.info["name"].lower():
            try:
                p = psutil.Process(process.info["pid"])
                p.terminate()  # Terminate gracefully
            except psutil.NoSuchProcess:
                pass  # Process already closed

kill_chrome()

# --- CAMBIO PRINCIPAL AQUÍ ---
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Chrome Options (Usando la clase de undetected_chromedriver)
options = uc.ChromeOptions()

# Persistent user profile
USER_DATA_DIR = "/tmp/seedloaf-session"
options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
options.add_argument("--profile-directory=Default") 

# Configuración obligatoria para GitHub Actions
options.headless = True  # Modo Headless integrado en UC
options.add_argument("--window-size=1920,1080") 
options.add_argument("--disable-gpu") 
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-popup-blocking")

# Bypass detection extra (UC ya maneja la mayoría, pero aseguramos la ventana gráfica)
options.add_argument("--disable-blink-features=AutomationControlled")

# Initialize WebDriver con UC (no requiere Service, lo busca automáticamente)
print("Iniciando navegador indetectable...")
driver = uc.Chrome(options=options)

driver.get("https://accounts.seedloaf.com/sign-in")

# Wait for page to fully load
WebDriverWait(driver, 10).until(lambda driver: driver.execute_script("return document.readyState") == "complete")

# Login flow function
def run_loginflow(usernamesec, passwordsec):
    #---------------------------
    try:
        # Wait for the username field to be visible
        username = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "identifier-field"))
        )
        print("After waiting for username:\n" + driver.current_url)
        
        driver.execute_script("arguments[0].scrollIntoView(true);", username)
        driver.execute_script("arguments[0].click();", username)
        username.send_keys(usernamesec)
        username.send_keys(Keys.RETURN)
        
        time.sleep(5)
        print("entered username")
        global ran_loginflow
        ran_loginflow = 1
    except Exception as e:
        print(f"Error occurred(username): {e}")
        print("After waiting for username:\n" + driver.current_url)
        
    #---------------------------
    
    try:
        try: # Check if username is incorrect
            wait = WebDriverWait(driver, 5)
            error_elem = wait.until(EC.visibility_of_element_located((By.ID, "error-identifier")))
            if error_elem:
                print("Username is incorrect")
                driver.quit()
                sys.exit()  
        except Exception as e:
            pass
            
        # Wait for the password field to be visible
        password = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "password-field"))
        )
        print("After waiting for password:\n" + driver.current_url)
        
        # Now enter password  
        global old_url
        old_url = driver.current_url
        driver.execute_script("arguments[0].scrollIntoView(true);", password)
        driver.execute_script("arguments[0].click();", password)
        password.send_keys(passwordsec)
        password.send_keys(Keys.RETURN)
        
        time.sleep(8)
        print("entered password")
        ran_loginflow = 2
    except Exception as e:
        print(f"Error occurred(password): {e}")
        print("After waiting for password:\n" + driver.current_url)


# Cleanup old marker
MARKER_FILE = "/tmp/seedloaf-session/.valid_session"
try:
    os.remove(MARKER_FILE)
except FileNotFoundError:
    pass
    
# Check dashboard
try:
    WebDriverWait(driver, 10).until(
        lambda d: "dashboard" in d.current_url
    )
    print("✅ Already logged in, at dashboard")
except:
    print("🔐 Not logged in — need to re-run login flow:\n" + driver.current_url)
    try: 
        ran_loginflow = 0
        usernamesec = os.getenv("USERNAME")
        passwordsec = os.getenv("PASSWORD")
        run_loginflow(usernamesec, passwordsec)
    except Exception as e:
        print("something wrong with secrets")
        
    # Write that Login flow has occured
    with open(MARKER_FILE, "w") as f:
        f.write("session valid")

# Extra delay crucial para evadir la pantalla "Checking your browser" de Cloudflare
print("Esperando 7 segundos para chequeos de Cloudflare...")
time.sleep(7)

#---------------------------
try:
    # Wait for the start button to be visible
    try:
        wait = WebDriverWait(driver, 20)
        startworld = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-primary")))
        print("After waiting for start:\n" + driver.current_url)
    except:
        try: # Check if password is incorrect or stop button is already present
            if ran_loginflow and driver.current_url == old_url:
                error_elem = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "error-password")))
                if error_elem:
                    print("Password is incorrect")
                    driver.quit()
                    sys.exit()
            else:
                try:
                    stopworld = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((By.XPATH, "//button[contains(@class, 'btn-error')]"))
                    )
                    print("Stop button found — world already running.")
                    driver.quit()
                    sys.exit()
                except Exception as e:
                    print(f"Neither Start nor Stop button found. Something might be wrong: {e}")
                    driver.quit()
                    exit()
        except Exception as inner_exc:
            print(f"Unexpected error during start/stop button checks: {inner_exc}")
            print("After waiting for start/stop:\n" + driver.current_url)
            driver.quit()
            sys.exit()
            
    # Now ensure it’s clickable
    driver.execute_script("arguments[0].scrollIntoView(true);", startworld)
    driver.execute_script("arguments[0].click();", startworld)
    print("Clicked start")
    time.sleep(2)

except Exception as e:
    print(f"Error occurred(start): {e}")

driver.quit()
