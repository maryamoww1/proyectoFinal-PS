import unittest
import os
import shutil
import tempfile
import io
import sys
import sbac

class TestSBAC(unittest.TestCase):

    def setUp(self):
        """
        Se ejecuta ANTES de cada prueba.
        Crea un entorno de trabajo temporal y limpio para no ensuciar los archivos reales
        """
        #crear un directorio temporal
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
        #movemos la ejecucion al directorio temporal
        os.chdir(self.test_dir)

        #redirigimos las constantes de sbac para que apunten al entorno temporal
        sbac.REPO_DIR = ".sbac"
        sbac.METADATA_FILE = os.path.join(sbac.REPO_DIR, "metadata.json")
        sbac.SNAPSHOTS_DIR = os.path.join(sbac.REPO_DIR, "snapshots")

    def tearDown(self):
        """
        Se ejecuta despsues de cada prueba
        Limpia y elimina el directorio temporal
        """
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    #PRUEBAS UNITARIAS

    def test_init_repo(self):
        """Verifica que init crea la estructura de carpetas correcta"""
        sbac.init_repo()
        
        self.assertTrue(os.path.exists(sbac.REPO_DIR), "No se creó la carpeta .sbac")
        self.assertTrue(os.path.exists(sbac.METADATA_FILE), "No se creó el metadata.json")
        self.assertTrue(os.path.exists(sbac.SNAPSHOTS_DIR), "No se creó la carpeta de snapshots")

    def test_add_file(self):
        """Verifica que add registra el archivo en el JSON"""
        sbac.init_repo()
        
        #creamos un archivo dummy real en el directorio temporal
        with open("archivo.txt", "w") as f:
            f.write("Hola")
            
        sbac.add_file("archivo.txt")
        metadata = sbac.load_metadata()
        
        self.assertIn("archivo.txt", metadata["tracked_files"], "El archivo no se añadió al tracking")

    def test_baseline(self):
        """Verifica que se asigne correctamente una linea base"""
        sbac.init_repo()
        with open("app.py", "w") as f: f.write("print('hola')")
        sbac.add_file("app.py")
        sbac.create_commit("Commit inicial")
        
        sbac.mark_baseline("Produccion")
        metadata = sbac.load_metadata()
        
        self.assertEqual(metadata["baselines"]["Produccion"], "v1", "La línea base no apuntó a v1")


    #PRUEBAS DE INTEGRACION

    def test_create_commit(self):
        """Verifica el flujo integrado de init -> add -> commit y el copiado fisico de archivos"""
        sbac.init_repo()
        
        with open("script.py", "w") as f:
            f.write("def suma(a,b): return a+b")
            
        sbac.add_file("script.py")
        sbac.create_commit("Primer feature")
        
        metadata = sbac.load_metadata()
        snapshot_path = os.path.join(sbac.SNAPSHOTS_DIR, "v1", "script.py")
        
        self.assertIn("v1", metadata["commits"], "No se registró el commit v1 en metadata")
        self.assertEqual(metadata["head"], "v1", "El HEAD no se actualizó")
        self.assertTrue(os.path.exists(snapshot_path), "No se hizo la copia física del archivo al snapshot")

    def test_diff_versions(self):
        """Verifica que diff encuentre los cambios entre dos versiones de un archivo"""
        sbac.init_repo()
        
        #version 1
        with open("codigo.py", "w") as f:
            f.write("print('Hola')\n")
        sbac.add_file("codigo.py")
        sbac.create_commit("V1")
        
        #version 2 (modificada)
        with open("codigo.py", "w") as f:
            f.write("print('Hola Mundo')\n")
        sbac.create_commit("V2")
        
        #capturamos el print en memoria para verificar que imprime diff
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        #ejecutamos el diff
        sbac.show_diff("v1", "v2")
        
        #restauramos la salida estandar
        sys.stdout = sys.__stdout__
        
        output = captured_output.getvalue()
        
        #verificamos que la salida detecte la eliminacion de la linea vieja y la agregacion de la nueva
        self.assertIn("-print('Hola')", output, "No detectó la línea eliminada")
        self.assertIn("+print('Hola Mundo')", output, "No detectó la línea agregada")


    #PRUEBAS DE REGRESION

    def test_checkout_regression(self):
        """
        verifica el flujo: inicializar, guardar v1, modificar, guardar v2,
        y regresar a v1. Garantiza que el sistema viaja en el tiempo sin romper archivos
        """
        sbac.init_repo()
        
        #crear v1
        with open("config.txt", "w") as f: 
            f.write("DEBUG=True")
        sbac.add_file("config.txt")
        sbac.create_commit("Version 1")
        
        #modificar y crear v2
        with open("config.txt", "w") as f: 
            f.write("DEBUG=False")
        sbac.create_commit("Version 2")
        
        #regresar a v1 (checkout)
        sbac.checkout_version("v1")
        
        #verificar que el archivo regreso a su estado original
        with open("config.txt", "r") as f:
            contenido = f.read()
            
        self.assertEqual(contenido, "DEBUG=True", "El checkout no restauró el archivo correctamente")
        
        metadata = sbac.load_metadata()
        self.assertEqual(metadata["head"], "v1", "El HEAD no regresó a v1 después del checkout")

if __name__ == "__main__":
    unittest.main(verbosity=2)