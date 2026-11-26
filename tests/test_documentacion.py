"""Pruebas de la documentación. Igual que los demás tests cubren el código, estos
comprueban que todo el código está explicado.

- Cada archivo de código sale en docs/como-funciona.md, con su ruta.
- Cada módulo, clase y función pública tiene su explicación (docstring).
- Los enlaces a archivos del README y de docs/ llevan a algo que existe.
"""

import ast
import re
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
GUIA = RAIZ / "docs" / "como-funciona.md"
DOCUMENTOS = [RAIZ / "README.md", GUIA, RAIZ / "docs" / "decisiones.md"]


def archivos_de_codigo() -> list[Path]:
    """Todos los .py y .sh del proyecto, sin los modelos, los datos ni el entorno."""
    archivos = [RAIZ / "main.py", *RAIZ.glob("*.sh")]
    for carpeta in ("temple", "herramientas", "tests"):
        archivos += (RAIZ / carpeta).rglob("*.py")
    return sorted(archivos)


def sin_explicar(ruta: Path) -> list[str]:
    """El módulo, las clases y las funciones públicas de un archivo sin docstring."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    faltan = [] if ast.get_docstring(arbol) else ["el módulo"]
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.FunctionDef, ast.ClassDef)) and not nodo.name.startswith("_"):
            # Los tests se explican con su nombre (test_cinco_dias_suben_y_cuatro_no),
            # y setUp y tearDown son los de siempre de unittest
            if ruta.parent.name == "tests" and nodo.name.startswith(("test", "Test", "setUp",
                                                                     "tearDown")):
                continue
            if not ast.get_docstring(nodo):
                faltan.append(f"{nodo.name} (línea {nodo.lineno})")
    return faltan


class TestDocumentacion(unittest.TestCase):
    def test_cada_archivo_sale_en_la_guia(self):
        guia = GUIA.read_text(encoding="utf-8")
        for ruta in archivos_de_codigo():
            relativa = ruta.relative_to(RAIZ).as_posix()
            with self.subTest(archivo=relativa):
                self.assertTrue(f"`{relativa}`" in guia, "falta explicarlo en docs/como-funciona.md")

    def test_cada_funcion_tiene_su_explicacion(self):
        for ruta in archivos_de_codigo():
            if ruta.suffix != ".py":
                continue
            with self.subTest(archivo=ruta.relative_to(RAIZ).as_posix()):
                self.assertEqual(sin_explicar(ruta), [])

    def test_los_enlaces_no_estan_rotos(self):
        enlace = re.compile(r'(?:\]\(|src=")([^)"#\s]+)')
        for doc in DOCUMENTOS:
            for destino in enlace.findall(doc.read_text(encoding="utf-8")):
                if destino.startswith(("http://", "https://", "mailto:")):
                    continue
                with self.subTest(documento=doc.name, enlace=destino):
                    self.assertTrue((doc.parent / destino).exists())


if __name__ == "__main__":
    unittest.main()
