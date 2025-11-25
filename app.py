import streamlit as st
from pydub import AudioSegment
from pydub.utils import which
import tempfile
import os
import whisper
import sys
# Vérification FFmpeg
if which("ffmpeg") is None:
    st.error("FFmpeg introuvable ! Veuillez l’installer et l’ajouter au PATH. "
             "Téléchargez ici : https://www.gyan.dev/ffmpeg/builds/")
    st.stop()  # Stoppe le script si FFmpeg n’est pas trouvé
st.set_page_config(page_title="Transcription Audio → Texte", layout="centered")
st.title("🎧➡️📝 Transcription audio vers texte (Streamlit + Whisper)")
st.markdown("""Téléchargez un fichier audio (MP3, WAV, M4A, OGG...) et l'application le convertira en texte.
""")
uploaded_file = st.file_uploader("Choisissez un fichier audio", type=["mp3", "wav", "m4a", "ogg", "flac", "aac"])
model_option = st.selectbox(
    "Choisissez le modèle Whisper (plus petit = plus rapide, plus grand = plus précis)",
    ["base", "small", "medium", "large"],
    index=1
)
if uploaded_file is not None:
    st.audio(uploaded_file, format="audio/*")
    if st.button("Lancer la transcription"):
        with st.spinner("Traitement en cours... Cela peut prendre un moment selon le modèle et la taille du fichier."):
            # Sauvegarde temporaire du fichier uploadé
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tf:
                tf.write(uploaded_file.read())
                temp_input_path = tf.name
            # Conversion en WAV 16k (recommandé)
            try:
                audio = AudioSegment.from_file(temp_input_path)
                wav_path = temp_input_path + ".wav"
                audio.export(wav_path, format="wav")
            except Exception as e:
                st.error(f"Erreur lors de la conversion audio : {e}")
                st.stop()
            # Chargement du modèle
            try:
                model = whisper.load_model(model_option)
            except Exception as e:
                st.error(f"Erreur lors du chargement du modèle Whisper : {e}")
                st.stop()
            # Transcription
            try:
                result = model.transcribe(wav_path)
                text = result.get("text", "").strip()
            except Exception as e:
                st.error(f"Erreur pendant la transcription : {e}")
                text = ""
            # Nettoyage des fichiers temporaires
            try:
                os.remove(temp_input_path)
                os.remove(wav_path)
            except:
                pass
        if text:
            st.success("Transcription réussie ✅")
            st.text_area("Texte transcrit :", value=text, height=300)
            # Téléchargement du fichier texte
            filename = os.path.splitext(uploaded_file.name)[0] + ".txt"
            st.download_button(
                "Télécharger le texte (.txt)",
                data=text,
                file_name=filename,
                mime="text/plain"
            )
        else:
            st.warning("Aucun texte n’a été extrait. Essayez un modèle plus grand ou un audio plus clair.")