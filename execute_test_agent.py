import os
import sys
import ast
import subprocess
import tempfile
import json
from typing import Dict, List, Any
from datetime import datetime


class AgentTestExecuteur:
    """
    Agent de test SIMPLE qui:
    1. Vérifie la syntaxe du code
    2. Exécute le code localement
    3. Renvoie les erreurs en JSON (liste)
    
    PAS DE CORRECTION - juste détection des erreurs.
    PAS D'API - exécution locale uniquement.
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialise l'agent de test.
        
        Args:
            timeout: Timeout en secondes pour l'exécution
        """
        self.timeout = timeout
        print(f"✅ AgentTestExecuteur initialisé (timeout: {timeout}s)")
    
    def tester_code(self, code: str, description: str = "") -> Dict[str, Any]:
        """
        Teste le code: installe les imports, vérifie la syntaxe, puis exécute.
        """
        resultat = {
            "statut": "OK",
            "erreurs": [],
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "etape_echouee": None
        }

        print(f"\n{'='*60}")
        print("🔍 TEST DU CODE")
        print(f"{'='*60}\n")

        # Étape 0: Installer les imports nécessaires
        print("🔎 Étape 0: Détection et installation des imports...")
        try:
            modules = self._extraire_imports(code)
            if modules:
                print(f"📦 Modules détectés: {modules}")
                self._installer_modules(modules)
            else:
                print("📦 Aucun import externe détecté.")
        except Exception as e:
            resultat["statut"] = "ERREUR"
            resultat["erreurs"] = [f"Erreur lors de l'installation des modules: {str(e)}"]
            resultat["etape_echouee"] = "import"
            return resultat

        # Étape 1: Vérifier la syntaxe
        print("📝 Étape 1: Vérification syntaxe...")
        erreurs_syntaxe = self._verifier_syntaxe(code)

        if erreurs_syntaxe:
            resultat["statut"] = "ERREUR"
            resultat["erreurs"] = erreurs_syntaxe
            resultat["etape_echouee"] = "syntaxe"
            print(f"❌ {len(erreurs_syntaxe)} erreur(s) de syntaxe")
            return resultat

        print("✅ Syntaxe OK")

        # Étape 2: Exécuter le code
        print("\n⚡ Étape 2: Exécution du code...")
        erreurs_execution = self._executer_code(code)

        if erreurs_execution:
            resultat["statut"] = "ERREUR"
            resultat["erreurs"] = erreurs_execution
            resultat["etape_echouee"] = "execution"
            print(f"❌ {len(erreurs_execution)} erreur(s) d'exécution")
            return resultat

        print("✅ Exécution OK")
        print(f"\n✅ CODE VALIDE - Aucune erreur")

        return resultat
    
    def _extraire_imports(self, code: str) -> List[str]:
        """
        Extrait les modules importés dans le code (import X, from X import Y).
        Ne retourne que les modules de premier niveau (pas les sous-modules).
        """
        import ast
        modules = set()
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        modules.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        modules.add(node.module.split('.')[0])
        except Exception:
            pass
        # Exclure les modules standards connus (liste simple, pas exhaustive)
        stdlib = {
            'os', 'sys', 'math', 'json', 'datetime', 'time', 're', 'random', 'subprocess', 'tempfile', 'traceback',
            'typing', 'collections', 'itertools', 'functools', 'pathlib', 'shutil', 'logging', 'ast', 'enum', 'threading',
            'unittest', 'doctest', 'inspect', 'platform', 'copy', 'csv', 'argparse', 'pprint', 'heapq', 'bisect', 'array',
            'struct', 'socket', 'signal', 'weakref', 'types', 'uuid', 'base64', 'hashlib', 'hmac', 'getopt', 'glob', 'zipfile',
            'tarfile', 'pickle', 'queue', 'email', 'http', 'urllib', 'xml', 'html', 'codecs', 'ctypes', 'configparser', 'statistics',
            'string', 'site', 'builtins', 'warnings', 'dataclasses', 'abc', 'numbers', 'fractions', 'decimal', 'selectors', 'ssl',
            'asyncio', 'concurrent', 'multiprocessing', 'bz2', 'lzma', 'gzip', 'calendar', 'locale', 'gettext', 'token', 'tokenize',
            'symtable', 'tabnanny', 'trace', 'cProfile', 'pstats', 'doctest', 'unittest', 'venv', 'ensurepip', 'distutils', 'site',
            'runpy', 'importlib', 'imp', 'marshal', 'sysconfig', 'faulthandler', 'atexit', 'gc', 'resource', 'fcntl', 'termios',
            'tty', 'pty', 'pipes', 'select', 'selectors', 'signal', 'mmap', 'readline', 'rlcompleter', 'code', 'codeop', 'bz2',
            'lzma', 'zipapp', 'shlex', 'cmd', 'gettext', 'locale', 'calendar', 'mailbox', 'mimetypes', 'smtplib', 'ssl', 'asyncore',
            'asynchat', 'socketserver', 'http', 'cgi', 'cgitb', 'wsgiref', 'urllib', 'xmlrpc', 'xml', 'html', 'plistlib', 'uuid',
            'secrets', 'zoneinfo', 'graphlib', 'dataclasses', 'contextvars', 'importlib', 'typing_extensions', 'typing'
        }
        return [m for m in modules if m not in stdlib]
    
    def _installer_modules(self, modules: List[str]):
        """
        Installe les modules via pip si non déjà installés.
        """
        import importlib
        import subprocess
        import sys
        to_install = []
        for mod in modules:
            try:
                importlib.import_module(mod)
            except ImportError:
                to_install.append(mod)
        if to_install:
            print(f"➡️ Installation via pip: {to_install}")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', *to_install])
        else:
            print("✅ Tous les modules sont déjà installés.")
    
    def tester_fichier(self, chemin_fichier: str) -> Dict[str, Any]:
        """
        Teste un fichier Python.
        
        Args:
            chemin_fichier: Chemin vers le fichier .py
        
        Returns:
            Dict JSON avec les erreurs
        """
        resultat = {
            "statut": "ERREUR",
            "erreurs": [],
            "timestamp": datetime.now().isoformat(),
            "fichier": chemin_fichier,
            "etape_echouee": None
        }
        
        # Vérifier que le fichier existe
        if not os.path.exists(chemin_fichier):
            resultat["erreurs"] = [f"Fichier non trouvé: {chemin_fichier}"]
            resultat["etape_echouee"] = "fichier"
            return resultat
        
        # Lire le fichier
        try:
            with open(chemin_fichier, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            resultat["erreurs"] = [f"Erreur lecture fichier: {str(e)}"]
            resultat["etape_echouee"] = "lecture"
            return resultat
        
        print(f"📂 Fichier: {chemin_fichier} ({len(code)} caractères)")
        
        # Tester le code
        resultat_test = self.tester_code(code, description=f"Fichier: {chemin_fichier}")
        resultat_test["fichier"] = chemin_fichier
        
        return resultat_test
    
    def _verifier_syntaxe(self, code: str) -> List[str]:
        """
        Vérifie la syntaxe du code Python avec ast.parse().
        
        Returns:
            Liste des erreurs de syntaxe (vide si OK)
        """
        erreurs = []
        
        try:
            ast.parse(code)
        except SyntaxError as e:
            erreur = {
                "type": "SyntaxError",
                "ligne": e.lineno,
                "colonne": e.offset,
                "message": e.msg,
                "code_ligne": e.text.strip() if e.text else None
            }
            erreurs.append(json.dumps(erreur, ensure_ascii=False))
        except Exception as e:
            erreurs.append(f"ParseError: {str(e)}")
        
        return erreurs
    
    def _executer_code(self, code: str) -> List[str]:
        """
        Exécute le code dans un subprocess et capture TOUTES les erreurs runtime.
        
        Returns:
            Liste des erreurs d'exécution (vide si OK)
        """
        erreurs = []
        
        # Créer fichier temporaire
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            encoding='utf-8'
        ) as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        
        try:
            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env={**os.environ}  # Passer les variables d'environnement
            )
            
            if result.returncode != 0:
                stderr = result.stderr.strip()
                if stderr:
                    # Capturer le traceback complet pour le contexte
                    full_traceback = stderr
                    
                    # Extraire les erreurs importantes
                    lignes = stderr.split('\n')
                    
                    # Trouver la dernière ligne d'erreur (la plus importante)
                    derniere_erreur = None
                    for ligne in reversed(lignes):
                        ligne = ligne.strip()
                        if ligne and ('Error' in ligne or 'Exception' in ligne):
                            derniere_erreur = ligne
                            break
                    
                    # Trouver les localisations de fichiers et lignes
                    for i, ligne in enumerate(lignes):
                        ligne_strip = ligne.strip()
                        
                        # Détecter "File ..., line X"
                        if ligne_strip.startswith('File') and 'line' in ligne_strip:
                            erreur_info = {
                                "localisation": ligne_strip,
                                "code": lignes[i + 1].strip() if i + 1 < len(lignes) else "",
                                "erreur": derniere_erreur or "Erreur inconnue"
                            }
                            erreurs.append(json.dumps(erreur_info, ensure_ascii=False))
                    
                    # Si on a trouvé une erreur finale mais pas de localisation
                    if derniere_erreur and not erreurs:
                        erreurs.append(derniere_erreur)
                    
                    # Si aucune erreur structurée, ajouter le stderr complet
                    if not erreurs:
                        erreurs.append(full_traceback)
        
        except subprocess.TimeoutExpired:
            erreurs.append(f"TimeoutError: Exécution dépassée ({self.timeout}s) - le code peut attendre une entrée ou être bloqué")
        except Exception as e:
            erreurs.append(f"ExecutionError: {str(e)}")
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass
        
        return erreurs
    
    def sauvegarder_resultat(self, resultat: Dict[str, Any], fichier: str = "resultat_test.json") -> str:
        """Sauvegarde le résultat en JSON."""
        with open(fichier, 'w', encoding='utf-8') as f:
            json.dump(resultat, f, indent=2, ensure_ascii=False)
        print(f"💾 Sauvegardé: {fichier}")
        return fichier


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    agent = AgentTestExecuteur(timeout=60)  # 60s pour les appels API
    
    if len(sys.argv) > 1:
        # Tester le fichier passé en argument
        resultat = agent.tester_fichier(sys.argv[1])
    elif os.path.exists("tmp.py"):
        # Tester tmp.py par défaut
        resultat = agent.tester_fichier("tmp.py")
    else:
        # Code de démo
        code = """
def test():
    print("Hello")
test()
"""
        resultat = agent.tester_code(code, "Code de test")
    
    print("\n" + "=" * 60)
    print("📊 RÉSULTAT JSON")
    print("=" * 60)
    print(json.dumps(resultat, indent=2, ensure_ascii=False))
    
    agent.sauvegarder_resultat(resultat)


