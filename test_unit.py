import unittest
import os
import shutil
import tempfile
import io
import sys
import sbac

class TestSBACUnit(unittest.TestCase):

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

    def test_init_repo(self):
        """verifica que init crea la estructura de carpetas correcta"""
        sbac.init_repo()
        
        self.assertTrue(os.path.exists(sbac.REPO_DIR), "No se creó la carpeta .sbac")
        self.assertTrue(os.path.exists(sbac.METADATA_FILE), "No se creó el metadata.json")
        self.assertTrue(os.path.exists(sbac.SNAPSHOTS_DIR), "No se creó la carpeta de snapshots")

    def test_add_file(self):
        """verifica que add registra el archivo en el json"""
        sbac.init_repo()
        
        # creamos un archivo dummy real en el directorio temporal
        with open("archivo.txt", "w") as f:
            f.write("Hola")
            
        sbac.add_file("archivo.txt")
        metadata = sbac.load_metadata()
        
        self.assertIn("archivo.txt", metadata["tracked_files"], "El archivo no se añadió al tracking")

    def test_baseline(self):
        """verifica que se asigne correctamente una linea base"""
        sbac.init_repo()
        with open("app.py", "w") as f: f.write("print('hola')")
        sbac.add_file("app.py")
        sbac.create_commit("Commit inicial")
        
        sbac.mark_baseline("Produccion")
        metadata = sbac.load_metadata()
        
        self.assertEqual(metadata["baselines"]["Produccion"], "v1", "La línea base no apuntó a v1")

    def test_add_nonexistent_file(self):
        """verifica el manejo de error al intentar agregar un archivo que no existe"""
        sbac.init_repo()
        
        captured_output = io.StringIO()
        sys.stdout = captured_output
        sbac.add_file("no_existo.txt")
        sys.stdout = sys.__stdout__
        
        output = captured_output.getvalue()
        self.assertIn("Error. El archivo", output, "No se mostró el error adecuado")

    def test_commit_without_tracked_files(self):
        """verifica que no se pueda hacer commit si no hay archivos en seguimiento"""
        sbac.init_repo()
        
        captured_output = io.StringIO()
        sys.stdout = captured_output
        sbac.create_commit("Commit vacío")
        sys.stdout = sys.__stdout__
        
        output = captured_output.getvalue()
        self.assertIn("No hay archivos bajo seguimiento", output, "El sistema intentó hacer un commit vacío")

    def test_double_init(self):
        """verifica que inicializar un repositorio existente no borre los datos"""
        sbac.init_repo()
        metadata = sbac.load_metadata()
        metadata["head"] = "v_test"
        sbac.save_metadata(metadata)
        
        captured_output = io.StringIO()
        sys.stdout = captured_output
        sbac.init_repo() 
        sys.stdout = sys.__stdout__
        
        metadata_after = sbac.load_metadata()
        self.assertEqual(metadata_after["head"], "v_test", "La doble inicialización borró los metadatos")

    def test_repo_not_initialized_errors(self):
        """verifica que los comandos se detengan de forma segura si no hay repositorio"""
        # no inicializamos el repositorio a proposito
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        sbac.show_status()
        sbac.create_commit("msg")
        sbac.show_history()
        sbac.mark_baseline("base")
        sbac.list_baselines()
        sbac.show_diff("v1", "v2")
        sbac.checkout_version("v1")
        
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        
        # verificamos que todos los comandos imprimieron la advertencia
        self.assertEqual(output.count("Repositorio no inicializado"), 7)

if __name__ == "__main__": # pragma: no cover
    unittest.main(verbosity=2)