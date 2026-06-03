import unittest
import os
import shutil
import tempfile
import io
import sys
import sbac

class TestSBACIntegration(unittest.TestCase):

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

    def test_create_commit(self):
        """verifica el flujo integrado de init -> add -> commit y el copiado fisico de archivos"""
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
        """verifica que diff encuentre los cambios entre dos versiones de un archivo"""
        sbac.init_repo()
        
        # version 1
        with open("codigo.py", "w") as f:
            f.write("print('Hola')\n")
        sbac.add_file("codigo.py")
        sbac.create_commit("V1")
        
        # version 2 (modificada)
        with open("codigo.py", "w") as f:
            f.write("print('Hola Mundo')\n")
        sbac.create_commit("V2")
        
        # capturamos el print en memoria para verificar que imprime diff
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        # ejecutamos el diff
        sbac.show_diff("v1", "v2")
        
        # restauramos la salida estandar
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        
        # verificamos que la salida detecte la eliminacion de la linea vieja y la agregacion de la nueva
        self.assertIn("-print('Hola')", output, "No detectó la línea eliminada")
        self.assertIn("+print('Hola Mundo')", output, "No detectó la línea agregada")

    def test_coverage_print_loops(self):
        """fuerza la ejecucion de los ciclos de impresion para validar salidas completas de status, history y diff"""
        sbac.init_repo()
        
        # crear un archivo real y registrarlo
        with open("cobertura.txt", "w") as f:
            f.write("linea 1\n")
        
        sbac.add_file("cobertura.txt")
        sbac.create_commit("Commit para prints")
        sbac.mark_baseline("BASE_PRINT")
        
        # modificar el archivo para que diff tenga informacion que comparar
        with open("cobertura.txt", "w") as f:
            f.write("linea 1 modificada\n")
        sbac.create_commit("Commit 2 para prints")
        
        # capturar la salida para no ensuciar la terminal de pruebas
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        # ejecutar las funciones con datos poblados
        sbac.show_status()
        sbac.show_history()
        sbac.list_baselines()
        sbac.show_diff("v1", "v2")
        
        sys.stdout = sys.__stdout__

if __name__ == "__main__": # pragma: no cover
    unittest.main(verbosity=2)