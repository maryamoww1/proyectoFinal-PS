import unittest
import os
import shutil
import tempfile
import io
import sys
import sbac

class TestSBACRegression(unittest.TestCase):

    def setUp(self):
        """
        se ejecuta antes de cada prueba.
        crea un entorno de trabajo temporal y limpio para no ensuciar los archivos reales
        """
        # crear un directorio temporal
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
        # movemos la ejecucion al directorio temporal
        os.chdir(self.test_dir)

        # redirigimos las constantes de sbac para que apunten al entorno temporal
        sbac.REPO_DIR = ".sbac"
        sbac.METADATA_FILE = os.path.join(sbac.REPO_DIR, "metadata.json")
        sbac.SNAPSHOTS_DIR = os.path.join(sbac.REPO_DIR, "snapshots")

    def tearDown(self):
        """
        se ejecuta despues de cada prueba.
        limpia y elimina el directorio temporal
        """
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_checkout_regression(self):
        """
        verifica el flujo: inicializar, guardar v1, modificar, guardar v2,
        y regresar a v1. garantiza que el sistema viaja en el tiempo sin romper archivos
        """
        sbac.init_repo()
        
        # crear v1
        with open("config.txt", "w") as f: 
            f.write("DEBUG=True")
        sbac.add_file("config.txt")
        sbac.create_commit("Version 1")
        
        # modificar y crear v2
        with open("config.txt", "w") as f: 
            f.write("DEBUG=False")
        sbac.create_commit("Version 2")
        
        # regresar a v1 (checkout)
        sbac.checkout_version("v1")
        
        # verificar que el archivo regreso a su estado original
        with open("config.txt", "r") as f:
            contenido = f.read()
            
        self.assertEqual(contenido, "DEBUG=True", "El checkout no restauró el archivo correctamente")
        
        metadata = sbac.load_metadata()
        self.assertEqual(metadata["head"], "v1", "El HEAD no regresó a v1 después del checkout")

    def test_empty_states(self):
        """verifica el comportamiento del sistema cuando los registros existen pero estan vacios"""
        sbac.init_repo()
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        sbac.show_history()
        sbac.list_baselines()
        sbac.mark_baseline("Base_Vacia") 
        
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        
        self.assertIn("No hay historial de versiones aún", output)
        self.assertIn("No hay líneas base registradas", output)
        self.assertIn("No hay ninguna versión registrada para marcar", output)

    def test_file_already_tracked_and_missing_physical(self):
        """verifica el intento de seguir un archivo ya rastreado y el manejo de archivos borrados fisicamente"""
        sbac.init_repo()
        with open("doble.txt", "w") as f: 
            f.write("contenido")
        
        sbac.add_file("doble.txt")
        
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        # intento de doble tracking
        sbac.add_file("doble.txt")
        
        # borramos el archivo fisicamente para forzar la advertencia en el commit
        os.remove("doble.txt")
        sbac.create_commit("Commit sin archivo físico")
        
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        
        self.assertIn("ya está bajo seguimiento", output)
        self.assertIn("Advertencia, el archivo", output)

    def test_invalid_diff_and_checkout(self):
        """verifica el manejo de errores al pedir comparaciones o checkouts de versiones que no existen"""
        sbac.init_repo()
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        sbac.show_diff("v99", "v100")
        sbac.checkout_version("v99")
        
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        
        self.assertIn("no existen", output)
        self.assertIn("no existe en el historial", output)

    def test_extreme_edge_cases(self):
        """cubre estados anomalos como metadatos borrados y snapshots corruptos en el sistema de archivos"""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        # intento de agregar archivo sin inicializar repositorio
        sbac.add_file("test.txt")
        
        sbac.init_repo()
        
        # forzar lectura de metadatos eliminando el archivo fisico json
        os.remove(sbac.METADATA_FILE)
        empty_meta = sbac.load_metadata()
        self.assertEqual(empty_meta["tracked_files"], [])
        
        # restaurar metadatos para continuar con la prueba
        sbac.save_metadata(empty_meta)
        
        # imprimir estado cuando no hay archivos bajo seguimiento
        sbac.show_status()
        
        # forzar corrupcion en snapshots para probar protecciones en diff y checkout
        with open("fantasma.txt", "w") as f: 
            f.write("datos")
        
        sbac.add_file("fantasma.txt")
        sbac.create_commit("v1")
        
        # borramos el archivo directamente del directorio de snapshots interno
        snapshot_file = os.path.join(sbac.SNAPSHOTS_DIR, "v1", "fantasma.txt")
        if os.path.exists(snapshot_file):
            os.remove(snapshot_file)
            
        # ejecutar comandos sobre el snapshot corrupto para asegurar que no se rompa la ejecucion
        sbac.show_diff("v1", "v1")
        sbac.checkout_version("v1")
        
        sys.stdout = sys.__stdout__

if __name__ == "__main__": # pragma: no cover
    unittest.main(verbosity=2)