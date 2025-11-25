import sys
import os
import traceback
from dotenv import load_dotenv

# 🔐 Charger les variables du fichier .env
load_dotenv()

# 📌 Ajouter la racine du projet au PYTHONPATH
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

# ⚠️ Importer ici la fonction générée par ton Agent
from output.get_last_3_subjects import get_last_3_subjects


def test_get_last_3_subjects():
    print("\n📬 Test de récupération des 3 objets d’emails...")

    try:
        subjects = get_last_3_subjects()

        # ✔️ Vérifier que la sortie est bien une liste
        if not isinstance(subjects, list):
            raise TypeError("La fonction doit retourner une liste Python")

        # ✔️ Vérifier qu'il y a exactement 3 éléments
        if len(subjects) != 3:
            raise ValueError("La fonction doit retourner exactement 3 objets d’emails")

        # ✔️ Vérifier que chaque élément est une string
        if not all(isinstance(s, str) for s in subjects):
            raise TypeError("Chaque objet d’email doit être une string")

        print("✅ Succès ! Les 3 derniers objets ont été récupérés correctement :")
        for i, sub in enumerate(subjects, 1):
            print(f"   {i}. {sub}")

    except Exception as e:
        print("❌ Erreur pendant la récupération des objets d’emails :")
        print(e)
        print("\n📌 Traceback :")
        traceback.print_exc()


if __name__ == "__main__":
    test_get_last_3_subjects()
