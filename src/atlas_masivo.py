"""
Extractor corporativo multi-ruta para el Sistema ATLAS.
Hereda la infraestructura de AtlasDataExtractor y agrega:
  - Auto-descubrimiento de todas las oficinas y rutas del sistema
  - Organización jerárquica Data Lake: data/raw/OFI_{id}/RTA_{id}/
  - Filtro anti-ceros: _validar_presencia_de_abonos()
  - Checkpoint de resiliencia (reinicio desde cualquier punto)
  - Maratón extractora: triple bucle Oficina → Ruta → Tiempo
"""

import json
import os
import shutil
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.insert(0, str(Path(__file__).parent))
from atlas_extractor import AtlasDataExtractor

# ------------------------------------------------------------------ #
# Configuración global                                                #
# ------------------------------------------------------------------ #

FECHA_INICIO_GLOBAL = "01/01/2020"
PAUSA_ENTRE_RUTAS   = 10  # segundos de pausa entre rutas

_RAIZ              = Path(__file__).parent.parent
_DIR_RAW           = _RAIZ / "data" / "raw"
ARCHIVO_CHECKPOINT = _DIR_RAW / ".checkpoint.json"

# Vacío = auto-descubrir todas las oficinas y rutas del sistema.
# Poblado manualmente actúa como filtro (solo extrae lo especificado).
# Ejemplo de uso manual: {"23": ["83", "84"], "24": ["90", "91"]}
MAPA_CORPORATIVO: dict[str, list[str]] = {
    # OFI_23 = 01. SAO PAULO   (RTA_82 = JUAN SP ya descargada por atlas_extractor.py)
    "23": ["82", "96", "423", "136", "367", "448", "494"],
    # OFI_31 = 04. SOCIEDADES BRASIL
    "31": ["415", "68", "338", "347", "389"],
    # OFI_44 = 02. CABO FRIO
    "44": ["114", "439", "396", "420", "511"],
}


# ------------------------------------------------------------------ #
# Clase principal                                                     #
# ------------------------------------------------------------------ #

class AtlasMasivoExtractor(AtlasDataExtractor):
    """
    Extractor corporativo que recorre todas las oficinas y rutas del Sistema
    ATLAS, organiza los archivos en un Data Lake jerárquico y soporta
    reanudación desde checkpoints ante cortes de sesión.
    """

    # ------------------------------------------------------------------ #
    # Descubrimiento del mapa corporativo                                #
    # ------------------------------------------------------------------ #

    def _descubrir_mapa_rutas(self) -> dict[str, list[str]]:
        """
        Lee dinámicamente todas las oficinas y rutas disponibles en el
        formulario activo (mainFrame). Dispara el AJAX de cmbRutas por cada
        oficina y recolecta los IDs de las rutas disponibles.

        Returns:
            {"id_oficina": ["id_ruta1", "id_ruta2", ...], ...}
        """
        espera = WebDriverWait(self.driver, 20)

        oficinas = [
            (o.get_attribute("value"), o.text.strip())
            for o in self.driver.find_elements(By.CSS_SELECTOR, "#sltOficina option")
            if o.get_attribute("value") and o.get_attribute("value").strip()
        ]
        self.logger.info("Oficinas detectadas en el sistema: %d.", len(oficinas))

        mapa: dict[str, list[str]] = {}
        for id_ofi, nombre_ofi in oficinas:
            self.driver.execute_script(
                "var s=document.getElementById('sltOficina');"
                "s.value=arguments[0];"
                "s.dispatchEvent(new Event('change',{bubbles:true}));",
                id_ofi,
            )
            espera.until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "#cmbRutas option")) > 1
            )
            time.sleep(0.5)

            rutas = [
                o.get_attribute("value")
                for o in self.driver.find_elements(By.CSS_SELECTOR, "#cmbRutas option")
                if o.get_attribute("value") and o.get_attribute("value").strip()
            ]
            mapa[id_ofi] = rutas
            self.logger.info(
                "  OFI %s (%s) → %d rutas: %s",
                id_ofi, nombre_ofi, len(rutas), rutas,
            )

        return mapa

    # ------------------------------------------------------------------ #
    # Utilidades de rutas y archivos                                     #
    # ------------------------------------------------------------------ #

    def _ruta_jerarquica(self, id_ofi: str, id_rta: str) -> Path:
        """Crea y retorna data/raw/OFI_{id_ofi}/RTA_{id_rta}/"""
        dest = _DIR_RAW / f"OFI_{id_ofi}" / f"RTA_{id_rta}"
        dest.mkdir(parents=True, exist_ok=True)
        return dest

    def _esperar_renombrar_mover(
        self,
        fecha_desde: date,
        fecha_hasta: date,
        dir_destino: Path,
        timeout: int = 90,
    ) -> bool:
        """
        Vigila data/raw/ (staging area de Chrome) esperando un nuevo xlsx.
        Al completar la descarga, mueve el archivo al directorio jerárquico.

        Returns:
            True si la descarga fue exitosa, False si timeout.
        """
        nombre_destino = (
            f"planilla_abonos_"
            f"{fecha_desde.strftime('%Y%m%d')}_"
            f"{fecha_hasta.strftime('%Y%m%d')}.xlsx"
        )
        ruta_final = dir_destino / nombre_destino

        if ruta_final.exists():
            self.logger.info("[YA EXISTE] %s — bloque omitido.", nombre_destino)
            return True

        archivos_previos = set(_DIR_RAW.glob("*.xls*"))

        inicio = time.time()
        while time.time() - inicio < timeout:
            parciales = (
                list(_DIR_RAW.glob("*.crdownload"))
                + list(_DIR_RAW.glob("*.tmp"))
            )
            nuevos = set(_DIR_RAW.glob("*.xls*")) - archivos_previos

            if nuevos and not parciales:
                mas_reciente = max(nuevos, key=lambda f: f.stat().st_mtime)
                shutil.move(str(mas_reciente), str(ruta_final))
                self.logger.info(
                    "  [OK] %s", ruta_final.relative_to(_RAIZ)
                )
                return True

            time.sleep(1)

        self.logger.warning(
            "  [TIMEOUT] Bloque %s → %s. Verifica %s manualmente.",
            fecha_desde, fecha_hasta, dir_destino,
        )
        return False

    # ------------------------------------------------------------------ #
    # Control del formulario                                             #
    # ------------------------------------------------------------------ #

    def _seleccionar_oficina_y_ruta(self, id_ofi: str, id_rta: str) -> None:
        """
        Navega ao menu e reabre o formulário para a oficina/ruta indicada.

        Re-navegar é necessário porque SELECT2 (widget de cmbRutas) ignora
        eventos nativos e o jQuery ($) não está disponível no contexto do
        mainFrame. Na inicialização do formulário fresco, SELECT2 lê o valor
        do <select> subjacente — então Select().select_by_value() funciona
        corretamente logo após a repopulação AJAX das opções.

        Reintentos: hasta 3 intentos ante StaleElementReferenceException,
        con 3 s de pausa entre cada uno (el AJAX de rutas puede no haber
        terminado cuando el SELECT ya fue encontrado pero aún no estabilizado).
        """
        MAX_INTENTOS = 3

        for intento in range(1, MAX_INTENTOS + 1):
            try:
                espera = WebDriverWait(self.driver, 20)

                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(0)
                espera.until(EC.frame_to_be_available_and_switch_to_it("leftFrame"))

                def _js_click(xpath: str) -> None:
                    el = espera.until(EC.presence_of_element_located((By.XPATH, xpath)))
                    self.driver.execute_script("arguments[0].click();", el)

                _js_click("//op[normalize-space()='Reportes']")
                _js_click("//op[normalize-space()='Recaudador']")
                _js_click("//a[contains(@href,'ReportePlanillaReacudadorConAbono')]")

                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(0)
                espera.until(EC.frame_to_be_available_and_switch_to_it("mainFrame"))
                espera.until(EC.presence_of_element_located((By.ID, "sltOficina")))

                # Pausa extra para que el AJAX de rutas se estabilice antes de interactuar
                time.sleep(2)

                Select(self.driver.find_element(By.ID, "sltOficina")).select_by_value(id_ofi)

                espera.until(
                    lambda d: any(
                        o.get_attribute("value") == id_rta
                        for o in d.find_elements(By.CSS_SELECTOR, "#cmbRutas option")
                    )
                )

                time.sleep(1)  # margen para que SELECT2 termine de inicializar

                Select(self.driver.find_element(By.ID, "cmbRutas")).select_by_value(id_rta)
                Select(self.driver.find_element(By.ID, "cmbFiltro")).select_by_value("2")

                self.logger.info(
                    "  Selects → OFI %s | RTA %s | Detallado", id_ofi, id_rta
                )
                return  # éxito

            except StaleElementReferenceException:
                if intento < MAX_INTENTOS:
                    self.logger.warning(
                        "  [STALE] OFI %s / RTA %s — intento %d/%d, reintentando en 3 s...",
                        id_ofi, id_rta, intento, MAX_INTENTOS,
                    )
                    time.sleep(3)
                else:
                    raise  # agota reintentos → el caller lo captura como ERROR-SELECT

    def _validar_presencia_de_abonos(self) -> bool:
        """
        El reporte se renderiza como un PDF embebido en <object id="ebReportePantalla">.
        Cuando hay datos: style="display: inline-block" y data apunta a un .pdf real.
        Cuando no hay datos: el objeto está oculto o su data está vacía.
        """
        try:
            objs = self.driver.find_elements(By.ID, "ebReportePantalla")
            if not objs:
                return False
            data_attr = objs[0].get_attribute("data") or ""
            style     = objs[0].get_attribute("style") or ""
            return ".pdf" in data_attr and "inline-block" in style
        except Exception:
            return False

    # ------------------------------------------------------------------ #
    # Checkpoint de resiliencia                                          #
    # ------------------------------------------------------------------ #

    def _cargar_checkpoint(self) -> dict | None:
        """Lee el checkpoint de sesión anterior. Retorna None si no existe."""
        if ARCHIVO_CHECKPOINT.exists():
            try:
                return json.loads(
                    ARCHIVO_CHECKPOINT.read_text(encoding="utf-8")
                )
            except (json.JSONDecodeError, OSError):
                return None
        return None

    def _guardar_checkpoint(
        self, id_ofi: str, id_rta: str, fecha_str: str
    ) -> None:
        """Persiste el estado actual para permitir reanudación."""
        ARCHIVO_CHECKPOINT.write_text(
            json.dumps(
                {"id_oficina": id_ofi, "id_ruta": id_rta, "fecha": fecha_str},
                indent=2,
            ),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------ #
    # Maratón extractora                                                 #
    # ------------------------------------------------------------------ #

    def ejecutar_maraton_extractora(
        self,
        id_oficina_inicio: str | None = None,
        id_ruta_inicio: str | None = None,
    ) -> None:
        """
        Triple bucle Oficina → Ruta → Tiempo que extrae el histórico completo
        de todas las rutas del sistema.

        Args:
            id_oficina_inicio: ID de la oficina donde reanudar (None = inicio).
            id_ruta_inicio:    ID de la ruta donde reanudar en esa oficina.
                               Si id_oficina_inicio es None, este parámetro
                               se ignora.
        """
        # Con dos sesiones simultáneas el frameset puede tardar más — reintenta 3 veces
        for intento in range(1, 4):
            try:
                self._navegar_a_planilla_abonos()
                break
            except Exception as exc:
                if intento == 3:
                    raise
                self.logger.warning(
                    "Intento %d/3 fallido navegando al formulario: %s. Reintentando en 10 s...",
                    intento, exc,
                )
                time.sleep(10)

        mapa = MAPA_CORPORATIVO if MAPA_CORPORATIVO else self._descubrir_mapa_rutas()
        if not mapa:
            self.logger.error("Mapa de rutas vacío. Abortando maratón.")
            return

        total_rutas = sum(len(v) for v in mapa.values())
        self.logger.info(
            "Maratón extractora: %d oficinas | %d rutas totales.",
            len(mapa), total_rutas,
        )

        # Determinar si arrancamos desde el inicio o reanudamos
        activado = id_oficina_inicio is None

        # Fecha de reanudación desde checkpoint (solo para la primera ruta)
        checkpoint       = self._cargar_checkpoint()
        fecha_reanudacion: date | None = None
        if checkpoint and id_oficina_inicio:
            if (
                checkpoint.get("id_oficina") == id_oficina_inicio
                and checkpoint.get("id_ruta") == id_ruta_inicio
                and checkpoint.get("fecha")
            ):
                fecha_reanudacion = date.fromisoformat(checkpoint["fecha"])
                self.logger.info(
                    "Checkpoint detectado → reanudando desde %s (OFI %s / RTA %s).",
                    fecha_reanudacion, id_oficina_inicio, id_ruta_inicio,
                )

        fecha_hoy         = date.today()
        rutas_procesadas  = 0

        for id_ofi in sorted(mapa.keys()):
            for id_rta in mapa[id_ofi]:

                # ── Saltar hasta el punto de reinicio ──────────────────
                if not activado:
                    if id_ofi == id_oficina_inicio and id_rta == id_ruta_inicio:
                        activado = True
                    else:
                        self.logger.debug(
                            "[INICIO-SKIP] OFI %s RTA %s", id_ofi, id_rta
                        )
                        continue

                rutas_procesadas += 1
                dir_destino = self._ruta_jerarquica(id_ofi, id_rta)

                # Cursor temporal: checkpoint si aplica, inicio global si no
                if (
                    fecha_reanudacion
                    and id_ofi == id_oficina_inicio
                    and id_rta == id_ruta_inicio
                ):
                    cursor = fecha_reanudacion
                    fecha_reanudacion = None  # solo para la primera ruta
                else:
                    cursor = datetime.strptime(
                        FECHA_INICIO_GLOBAL, "%d/%m/%Y"
                    ).date()

                bloques_totales = -(-((fecha_hoy - cursor).days + 1) // 10)
                self.logger.info(
                    "══ OFI %s | RTA %s | %s → %s | %d bloques ══",
                    id_ofi, id_rta,
                    cursor.strftime("%d/%m/%Y"),
                    fecha_hoy.strftime("%d/%m/%Y"),
                    bloques_totales,
                )

                # ── Configurar selects para esta ruta ───────────────────
                try:
                    self._seleccionar_oficina_y_ruta(id_ofi, id_rta)
                except Exception as exc:
                    self.logger.error(
                        "[ERROR-SELECT] OFI %s / RTA %s: %s. Saltando ruta.",
                        id_ofi, id_rta, exc,
                    )
                    continue

                # ── Bucle temporal ──────────────────────────────────────
                espera        = WebDriverWait(self.driver, 20)
                numero_bloque = 0

                while cursor <= fecha_hoy:
                    fecha_hasta = min(cursor + timedelta(days=9), fecha_hoy)
                    numero_bloque += 1

                    self.logger.info(
                        "  [%d/%d] %s → %s",
                        numero_bloque, bloques_totales,
                        cursor.strftime("%d/%m/%Y"),
                        fecha_hasta.strftime("%d/%m/%Y"),
                    )

                    try:
                        # Early-exit: si el archivo ya existe, saltar sin
                        # tocar el formulario ni descargar nada.
                        nombre_bloque = (
                            f"planilla_abonos_"
                            f"{cursor.strftime('%Y%m%d')}_"
                            f"{fecha_hasta.strftime('%Y%m%d')}.xlsx"
                        )
                        if (dir_destino / nombre_bloque).exists():
                            self.logger.info(
                                "[YA EXISTE] %s — bloque omitido.", nombre_bloque
                            )
                            cursor = fecha_hasta + timedelta(days=1)
                            continue

                        self._cerrar_modal_si_existe()

                        campo_fecha = espera.until(
                            EC.presence_of_element_located((By.ID, "dtFechaIni"))
                        )
                        self.driver.execute_script(
                            "arguments[0].value=arguments[1];"
                            "arguments[0].dispatchEvent("
                            "  new Event('change',{bubbles:true}));",
                            campo_fecha,
                            cursor.strftime("%Y-%m-%d"),
                        )

                        self.driver.execute_script(
                            "document.getElementById('btnAceptar').click();"
                        )
                        time.sleep(10)
                        self._cerrar_modal_si_existe()

                        if not self._validar_presencia_de_abonos():
                            self.logger.info(
                                "    [SKIP] Sin actividad real — bloque omitido."
                            )
                            cursor = fecha_hasta + timedelta(days=1)
                            continue

                        self.driver.execute_script(
                            "document.getElementById('btnExcel').click();"
                        )
                        ok = self._esperar_renombrar_mover(
                            cursor, fecha_hasta, dir_destino
                        )
                        if ok:
                            self._guardar_checkpoint(
                                id_ofi, id_rta, str(cursor)
                            )

                    except Exception as exc:
                        self.logger.error(
                            "    [ERROR] %s → %s: %s. Continuando.",
                            cursor.strftime("%d/%m/%Y"),
                            fecha_hasta.strftime("%d/%m/%Y"),
                            exc,
                        )

                    cursor = fecha_hasta + timedelta(days=1)

                self.logger.info(
                    "[RUTA COMPLETA] OFI %s | RTA %s", id_ofi, id_rta
                )
                time.sleep(PAUSA_ENTRE_RUTAS)

        self.logger.info(
            "══ MARATÓN COMPLETADA: %d rutas procesadas. ══", rutas_procesadas
        )
        if ARCHIVO_CHECKPOINT.exists():
            ARCHIVO_CHECKPOINT.unlink()
            self.logger.info("Checkpoint eliminado.")


# ------------------------------------------------------------------ #
# Punto de entrada                                                    #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    load_dotenv(Path(__file__).parent.parent / ".env")

    usuario    = os.getenv("ATLAS_USER")
    contrasena = os.getenv("ATLAS_PASS")
    ruta       = os.getenv("ATLAS_RUTA", "01.01. JUAN SP - JJ")

    if not usuario or not contrasena:
        raise ValueError(
            "Variables ATLAS_USER y ATLAS_PASS no encontradas. "
            "Crea un archivo .env en la raíz del proyecto."
        )

    extractor = AtlasMasivoExtractor()
    try:
        extractor.login(AtlasDataExtractor.URL_ATLAS, usuario, contrasena, ruta)
        time.sleep(8)  # margen extra para que el frameset cargue con sesiones simultáneas
        extractor.ejecutar_maraton_extractora(
            # OFI_23 completa (1.630 arch.) | OFI_31 completa (1.163 arch.)
            # OFI_44 completa salvo RTA_114 que falló por stale element.
            id_oficina_inicio="44",
            id_ruta_inicio="114",
        )
    finally:
        extractor.cerrar()
