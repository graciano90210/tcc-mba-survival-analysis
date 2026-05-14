"""
Extractor automatizado del Sistema LISTO para el pipeline ETL del TCC.
Descarga reportes de cartera hacia data/raw/ para el modelo de supervivencia.
"""

import os
import time
import logging
from datetime import date, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

URL_REPORTE = (
    "https://listo11.listoonline.co/Golden/caja/frm/"
    "frmReportes.php?action=ReportePlanillaReacudadorConAbono"
)


class ListoDataExtractor:
    """Robot de extracción web para el Sistema LISTO (riesgo crediticio)."""

    URL_LISTO = "https://listo11.listoonline.co/Golden/index.php"

    # Valores fijos de los selects del formulario de reporte
    _OFICINA_VALOR = "23"    # 01. SAO PAULO
    _RUTA_VALOR = "82"       # 01.01. JUAN SP - JJ
    _FILTRO_DETALLADO = "2"  # cmbFiltro value=2 → Detallado

    def __init__(self):
        self._configurar_logging()
        self.driver = self._inicializar_driver()
        self._ruta_descarga = Path(__file__).parent.parent / "data" / "raw"

    # ------------------------------------------------------------------ #
    # Infraestructura                                                     #
    # ------------------------------------------------------------------ #

    def _configurar_logging(self):
        """Configura el logger de auditoría en consola con formato estándar."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.logger = logging.getLogger(__name__)

    def _inicializar_driver(self) -> webdriver.Chrome:
        """
        Inicializa Chrome via webdriver-manager y configura la carpeta de
        descarga automática apuntando a data/raw/ relativo a este script.
        """
        ruta_descarga = str(Path(__file__).parent.parent / "data" / "raw")

        opciones = Options()
        opciones.add_experimental_option(
            "prefs",
            {
                "download.default_directory": ruta_descarga,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False,
                # Permite múltiples descargas sin el popup "¿Descargar varios archivos?"
                "profile.default_content_setting_values.automatic_downloads": 1,
                # Desactiva el gestor de contraseñas para evitar el popup
                # "Cambia la contraseña" de Google durante la automatización
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "profile.password_manager_leak_detection": False,
            },
        )
        opciones.add_argument("--disable-features=PasswordCheck,SafeBrowsingEnhancedProtection")

        servicio = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=servicio, options=opciones)

        self.logger.info(
            "Driver Chrome inicializado. Directorio de descarga: %s", ruta_descarga
        )
        return driver

    # ------------------------------------------------------------------ #
    # Login                                                               #
    # ------------------------------------------------------------------ #

    def login(
        self,
        url: str,
        user: str,
        password: str,
        ruta: str = "01.01. JUAN SP - JJ",
    ) -> None:
        """
        Login en dos fases:
          Fase 1 → usuario + clave + clic en 'Validar'
          Fase 2 → selección de ruta (select2 vía DOM nativo) + clic en 'Ingresar'
        """
        self.logger.info("Navegando a: %s", url)
        self.driver.get(url)

        espera = WebDriverWait(self.driver, 15)

        # El formulario de login vive dentro de un iframe
        espera.until(EC.frame_to_be_available_and_switch_to_it(0))
        self.logger.info("Iframe de autenticación detectado y activo.")

        # Fase 1: credenciales
        campo_usuario = espera.until(
            EC.presence_of_element_located((By.ID, "txtLogin"))
        )
        campo_usuario.clear()
        campo_usuario.send_keys(user)
        self.logger.info("Usuario ingresado correctamente.")

        campo_contrasena = espera.until(
            EC.presence_of_element_located((By.ID, "txtClave"))
        )
        campo_contrasena.clear()
        campo_contrasena.send_keys(password)
        self.logger.info("Contraseña ingresada correctamente.")

        espera.until(EC.element_to_be_clickable((By.ID, "btnAutenticar"))).click()
        self.logger.info("Botón 'Validar' presionado. Esperando selector de ruta...")

        # Fase 2: selección de ruta
        # cmbRutas usa select2; se activa vía DOM nativo para disparar el change
        espera.until(EC.visibility_of_element_located((By.ID, "cmbRutas")))

        valor_ruta = self.driver.execute_script(
            "var opts = document.querySelectorAll('#cmbRutas option');"
            "for(var o of opts){"
            "  if(o.text.trim().indexOf(arguments[0]) !== -1) return o.value;"
            "}"
            "return null;",
            ruta,
        )
        if not valor_ruta:
            raise ValueError(f"Ruta '{ruta}' no encontrada en el dropdown cmbRutas.")

        self.driver.execute_script(
            "var sel = document.getElementById('cmbRutas');"
            "sel.value = arguments[0];"
            "sel.dispatchEvent(new Event('change', {bubbles: true}));",
            valor_ruta,
        )
        self.logger.info("Ruta seleccionada: %s (value=%s)", ruta, valor_ruta)

        espera.until(EC.element_to_be_clickable((By.ID, "btnAutenticar"))).click()
        self.logger.info("Botón 'Ingresar' presionado. Esperando modal de bienvenida...")

        # El modal bootbox-confirm "¡Bienvenido!" se renderiza DENTRO del iframe[0]
        # (body.i18n de frmAutenticacion.php). Esperamos que el servidor responda
        # antes de buscarlo — el sleep es indispensable para estabilizar el DOM.
        time.sleep(5)

        # Usar find_elements (sin excepción si no existe) + clic via JS
        btns = self.driver.find_elements(
            By.CSS_SELECTOR, "button[data-bb-handler='confirm']"
        )
        if btns:
            btns[0].click()
            self.logger.info("Modal de bienvenida cerrado correctamente.")
        else:
            self.logger.warning("Botón 'Aceptar' del modal no encontrado; continuando.")

        # Salir del iframe y dar tiempo al frameset para cargar
        self.driver.switch_to.default_content()
        time.sleep(4)

    # ------------------------------------------------------------------ #
    # Métodos privados de soporte                                        #
    # ------------------------------------------------------------------ #

    def _navegar_a_planilla_abonos(self) -> None:
        """
        Navega al módulo 'Planilla de recaudador con abonos' usando la estructura
        real de frames:
          index2.php → leftFrame (menú) → clic en menú → mainFrame (formulario)

        Configura también los filtros estáticos (Oficina, Ruta, Filtro=Detallado)
        que no cambian entre iteraciones del bucle batch.
        """
        espera = WebDriverWait(self.driver, 20)

        # Entrar al frameset dentro del iframe principal
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(0)  # index2.php

        # Entrar al frame del menú lateral y esperar que cargue
        espera.until(EC.frame_to_be_available_and_switch_to_it("leftFrame"))
        self.logger.info("leftFrame (menú) activo.")

        # Desplegar menú: Reportes → Recaudador → Planilla de recaudador con abonos
        # El menú usa etiquetas <op> para los textos; is_displayed() falla en ellas
        # por eso se usa presence_of_element_located + clic vía JS.
        def _js_click(xpath):
            el = espera.until(EC.presence_of_element_located((By.XPATH, xpath)))
            self.driver.execute_script("arguments[0].click();", el)

        _js_click("//op[normalize-space()='Reportes']")
        self.logger.info("Clic en 'Reportes'.")

        _js_click("//op[normalize-space()='Recaudador']")
        self.logger.info("Clic en 'Recaudador'.")

        # Se usa el href como selector inequívoco del enlace correcto
        _js_click("//a[contains(@href,'ReportePlanillaReacudadorConAbono')]")
        self.logger.info("Clic en 'Planilla de recaudador con abonos'.")

        # Cambiar al frame de contenido y esperar que el formulario esté listo
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(0)
        espera.until(EC.frame_to_be_available_and_switch_to_it("mainFrame"))
        espera.until(EC.presence_of_element_located((By.ID, "sltOficina")))
        self.logger.info("Formulario 'Planilla de recaudador con abonos' cargado en mainFrame.")

        # Filtros estáticos: se configuran una sola vez antes del bucle batch
        Select(self.driver.find_element(By.ID, "sltOficina")).select_by_value(
            self._OFICINA_VALOR
        )
        # Esperar AJAX que repopula cmbRutas después de cambiar la oficina
        espera.until(
            lambda d: any(
                o.get_attribute("value") == self._RUTA_VALOR
                for o in d.find_elements(By.CSS_SELECTOR, "#cmbRutas option")
            )
        )
        Select(self.driver.find_element(By.ID, "cmbRutas")).select_by_value(
            self._RUTA_VALOR
        )
        Select(self.driver.find_element(By.ID, "cmbFiltro")).select_by_value(
            self._FILTRO_DETALLADO
        )
        self.logger.info(
            "Filtros estáticos configurados → Oficina: %s | Ruta: %s | Filtro: Detallado.",
            self._OFICINA_VALOR,
            self._RUTA_VALOR,
        )

    def _cerrar_modal_si_existe(self) -> bool:
        """Cierra cualquier modal bootbox abierto en el frame activo. Retorna True si había modal."""
        btns = self.driver.find_elements(
            By.CSS_SELECTOR, ".bootbox.modal button, .modal.in button"
        )
        if btns:
            self.driver.execute_script("arguments[0].click();", btns[-1])
            time.sleep(0.8)
            return True
        return False

    def _esperar_y_renombrar_descarga(
        self,
        fecha_desde: date,
        fecha_hasta: date,
        timeout: int = 90,
    ) -> None:
        """
        Espera a que Chrome complete la descarga del Excel (sin archivos .crdownload)
        y renombra el archivo al formato: planilla_abonos_YYYYMMDD_YYYYMMDD.xlsx
        """
        nombre_destino = (
            f"planilla_abonos_"
            f"{fecha_desde.strftime('%Y%m%d')}_"
            f"{fecha_hasta.strftime('%Y%m%d')}.xlsx"
        )
        ruta_destino = self._ruta_descarga / nombre_destino

        # Snapshot de archivos Excel ya existentes antes de que llegue el nuevo
        archivos_previos = set(self._ruta_descarga.glob("*.xls*"))

        inicio = time.time()
        while time.time() - inicio < timeout:
            parciales = (
                list(self._ruta_descarga.glob("*.crdownload"))
                + list(self._ruta_descarga.glob("*.tmp"))
            )
            nuevos = set(self._ruta_descarga.glob("*.xls*")) - archivos_previos

            if nuevos and not parciales:
                # Nuevo Excel completamente descargado — tomar el más reciente
                mas_reciente = max(nuevos, key=lambda f: f.stat().st_mtime)
                mas_reciente.rename(ruta_destino)
                self.logger.info("Descarga completada y renombrada: %s", nombre_destino)
                return

            time.sleep(1)

        self.logger.warning(
            "Timeout esperando descarga del bloque %s → %s. "
            "Verifica data/raw/ manualmente.",
            fecha_desde,
            fecha_hasta,
        )

    # ------------------------------------------------------------------ #
    # Extracción batch                                                    #
    # ------------------------------------------------------------------ #

    def descargar_historico(self, fecha_inicio_str: str) -> None:
        """
        Extracción batch del histórico de 'Planilla de recaudador con abonos'.

        Itera desde fecha_inicio_str hasta hoy en bloques estrictos de 10 días,
        descargando un Excel por bloque y renombrándolo automáticamente.

        Args:
            fecha_inicio_str: Fecha de inicio en formato 'DD/MM/YYYY'
                              (ejemplo: '01/01/2020').
        """
        try:
            cursor = datetime.strptime(fecha_inicio_str, "%d/%m/%Y").date()
        except ValueError as exc:
            raise ValueError(
                f"Formato de fecha incorrecto: '{fecha_inicio_str}'. "
                "Use 'DD/MM/YYYY', ej: '01/01/2020'."
            ) from exc

        fecha_hoy = date.today()
        total_dias = (fecha_hoy - cursor).days + 1
        bloques_totales = -(-total_dias // 10)  # división techo (ceil)

        self.logger.info(
            "Extracción histórica: %s → %s | %d bloques de 10 días.",
            cursor.strftime("%d/%m/%Y"),
            fecha_hoy.strftime("%d/%m/%Y"),
            bloques_totales,
        )

        # Navegación al módulo (una sola vez; el bucle reutiliza el mainFrame)
        self._navegar_a_planilla_abonos()

        espera = WebDriverWait(self.driver, 20)
        numero_bloque = 0

        while cursor <= fecha_hoy:
            fecha_hasta = min(cursor + timedelta(days=9), fecha_hoy)
            numero_bloque += 1

            self.logger.info(
                "--- Bloque %d/%d: %s → %s ---",
                numero_bloque,
                bloques_totales,
                cursor.strftime("%d/%m/%Y"),
                fecha_hasta.strftime("%d/%m/%Y"),
            )

            try:
                # Si el bloque ya fue descargado en una sesión anterior, saltarlo
                nombre_bloque = (
                    f"planilla_abonos_"
                    f"{cursor.strftime('%Y%m%d')}_"
                    f"{fecha_hasta.strftime('%Y%m%d')}.xlsx"
                )
                if (self._ruta_descarga / nombre_bloque).exists():
                    self.logger.info(
                        "  [YA EXISTE] %s — saltado.", nombre_bloque
                    )
                    cursor = fecha_hasta + timedelta(days=1)
                    continue

                # Cerrar cualquier modal previo antes de interactuar
                self._cerrar_modal_si_existe()

                # Inyectar fecha vía JS para bypassar el datepicker (campo readonly)
                campo_fecha = espera.until(
                    EC.presence_of_element_located((By.ID, "dtFechaIni"))
                )
                self.driver.execute_script(
                    "arguments[0].value = arguments[1];"
                    "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                    campo_fecha,
                    cursor.strftime("%Y-%m-%d"),
                )
                self.logger.info("Fecha inyectada: %s", cursor.strftime("%Y-%m-%d"))

                # JS click en Generar (evita intercepciones de modales)
                self.driver.execute_script(
                    "document.getElementById('btnAceptar').click();"
                )
                # Esperar a que el servidor procese y renderice el reporte
                time.sleep(10)

                # Cerrar el modal de resultado (puede ser "no hay datos" o confirmación)
                self._cerrar_modal_si_existe()

                # JS click en Excel → Chrome descarga directamente a data/raw/
                self.driver.execute_script(
                    "document.getElementById('btnExcel').click();"
                )
                self.logger.info("Botón 'Excel' presionado.")

                self._esperar_y_renombrar_descarga(cursor, fecha_hasta)

            except Exception as exc:
                self.logger.error(
                    "Error en bloque %s → %s: %s. Continuando con el siguiente bloque.",
                    cursor.strftime("%d/%m/%Y"),
                    fecha_hasta.strftime("%d/%m/%Y"),
                    exc,
                )

            cursor = fecha_hasta + timedelta(days=1)

        self.logger.info(
            "Extracción histórica completada. Archivos disponibles en: %s",
            self._ruta_descarga,
        )

    # ------------------------------------------------------------------ #
    # [Deprecado] descarga puntual vía URL directa                       #
    # ------------------------------------------------------------------ #

    def descargar_reporte(
        self,
        fecha_inicio: str | None = None,
        oficina_valor: str = "23",
        ruta_valor: str = "82",
        estado_valor: str = "-999999",
        filtro_valor: str = "2",
    ) -> None:
        """
        [Deprecado — usar descargar_historico]
        Descarga puntual navegando vía URL directa al reporte.
        """
        if fecha_inicio is None:
            fecha_inicio = date.today().strftime("%Y-%m-%d")

        self.logger.info("(descargar_reporte) Abriendo reporte vía URL directa.")
        self.driver.get(URL_REPORTE)

        espera = WebDriverWait(self.driver, 15)
        espera.until(EC.presence_of_element_located((By.ID, "sltOficina")))

        Select(self.driver.find_element(By.ID, "sltOficina")).select_by_value(oficina_valor)
        espera.until(
            lambda d: any(
                o.get_attribute("value") == ruta_valor
                for o in d.find_elements(By.CSS_SELECTOR, "#cmbRutas option")
            )
        )
        Select(self.driver.find_element(By.ID, "cmbRutas")).select_by_value(ruta_valor)

        campo_fecha = self.driver.find_element(By.ID, "dtFechaIni")
        self.driver.execute_script(
            "arguments[0].value = arguments[1];"
            "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
            campo_fecha,
            fecha_inicio,
        )
        Select(self.driver.find_element(By.ID, "cmbEstado")).select_by_value(estado_valor)
        Select(self.driver.find_element(By.ID, "cmbFiltro")).select_by_value(filtro_valor)

        self.driver.find_element(By.ID, "btnAceptar").click()
        time.sleep(5)
        self.driver.find_element(By.ID, "btnExcel").click()
        self.logger.info("(descargar_reporte) Botón 'Excel' presionado.")

        fecha_obj = date.fromisoformat(fecha_inicio)
        self._esperar_y_renombrar_descarga(fecha_obj, fecha_obj)

    def cerrar(self) -> None:
        """Cierra el navegador y libera recursos."""
        if self.driver:
            self.driver.quit()
            self.logger.info("Navegador cerrado.")


# ------------------------------------------------------------------ #
# Punto de entrada                                                    #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    load_dotenv(Path(__file__).parent.parent / ".env")

    usuario = os.getenv("LISTO_USER")
    contrasena = os.getenv("LISTO_PASS")
    ruta = os.getenv("LISTO_RUTA", "01.01. JUAN SP - JJ")

    if not usuario or not contrasena:
        raise ValueError(
            "Variables LISTO_USER y LISTO_PASS no encontradas. "
            "Crea un archivo .env en la raíz del proyecto con esas claves."
        )

    extractor = ListoDataExtractor()
    try:
        extractor.login(ListoDataExtractor.URL_LISTO, usuario, contrasena, ruta)
        extractor.descargar_historico("19/04/2024")
    finally:
        extractor.cerrar()
