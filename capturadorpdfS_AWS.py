import asyncio
import os
import re
from urllib.parse import unquote
from playwright.async_api import async_playwright

# --- CONFIGURACIÓN ---
OUTPUT_DIR = "MIS_PDFS_AWS"

async def handle_response(response):
    try:
        # Detectamos PDFs por Content-Type o por extensión en la URL
        is_pdf = "application/pdf" in response.headers.get("content-type", "").lower()
        url = response.url.lower()
        
        if is_pdf or url.endswith(".pdf") or "contentcontroller.com/vault" in url:
            # 1. Extraer y limpiar el nombre del archivo
            full_url = response.url
            raw_name = full_url.split("/")[-1].split("?")[0]
            filename = unquote(raw_name) # Decodifica %20 por espacios
            
            if not filename.lower().endswith(".pdf"):
                filename += ".pdf"
            
            # Limpiar caracteres prohibidos en Windows
            filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
            save_path = os.path.join(OUTPUT_DIR, filename)

            # 2. Si ya existe, no lo bajamos de nuevo
            if os.path.exists(save_path):
                return

            # 3. Descargar el binario
            print(f"📥 Detectado: {filename}")
            content = await response.body()
            
            with open(save_path, "wb") as f:
                f.write(content)
            
            print(f"✅ ¡Guardado!: {filename}")
            # Sonido de éxito (solo Windows)
            if os.name == 'nt':
                import winsound
                winsound.Beep(1000, 200)

    except Exception:
        pass # Ignorar errores de peticiones que no son archivos

async def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    async with async_playwright() as p:
        print("🔗 Conectando al navegador en puerto 9222...")
        try:
            # Conexión al Chrome que abrimos manualmente
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]

            def monitor_page(page):
                print(f"👀 Vigilando pestaña nueva: {page.url[:40]}...")
                page.on("response", lambda res: asyncio.create_task(handle_response(res)))

            # Vigilar pestañas actuales y las que abras después
            for page in context.pages:
                monitor_page(page)
            context.on("page", lambda page: monitor_page(page))

            print("\n🚀 SCRAPPING PASIVO ACTIVO")
            print("Instrucciones: Navega por el curso de AWS. Cada PDF que veas se bajará solo.")
            print("Presiona Ctrl+C para cerrar el script cuando acabes.\n")

            while True:
                await asyncio.sleep(1)

        except Exception as e:
            print(f"❌ ERROR: {e}")
            print("\nCONSEJO: Asegúrate de que Chrome está abierto con el puerto 9222.")

if __name__ == "__main__":
    asyncio.run(main())