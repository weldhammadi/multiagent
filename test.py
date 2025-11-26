import os
from dotenv import load_dotenv

# Charger les variables de .env
load_dotenv()

from output.write_last_30_gmail_subjects_to_sheet import   write_last_30_gmail_subjects_to_sheet
def main():
    try:
        result =  write_last_30_gmail_subjects_to_sheet()
        if result:
            print("✔️ Les 10 derniers emails non lus ont été marqués comme lus.")
        else:
            print("❌ La fonction a retourné False.")
    except Exception as e:
        print("❌ Erreur :", e)

if __name__ == "__main__":
    main()
