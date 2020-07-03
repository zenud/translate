#Speech To Text 
from pydub import AudioSegment

from google.cloud import translate_v2 as translate
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
import wave
import mutagen
#Text to Speech 
from google.cloud import texttospeech
#Storage
from google.cloud import storage

import html
import io
import os 

FILEPATH = ""     #Input audio file path
OUTPUT_FILEPATH = "Transcript/" #Final transcript path
BUCKETNAME = "transcrib_01" #Name of the bucket created in the step before`

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="/home/nouro/transcrib-0001-074be7447961.json"

def Traduit(text, target):
    #translate_client = translate.Client()
    translate_client=translate.Client()
    translation=translate_client.translate(
                    text,
                    target_language=target)
    return (html.unescape(translation['translatedText']))


def Frame_Rate_Channel(audio_file_name):
    with wave.open(audio_file_name, "rb") as wave_file:
        frame_rate = wave_file.getframerate()
        channels = wave_file.getnchannels()
        return frame_rate,channels

def FrameRate_Channel (audio_file_name):
    f = mutagen.File(audio_file_name)
    return (f.info.bitrate,f.info.channels)

def Upload_Blob(bucket_name, source_file_name, destination_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print("File {} uploaded to {}.".format(
           source_file_name, destination_blob_name))

def G_Transcribe(audio_file_name, language):
    file_name = FILEPATH + audio_file_name
    frame_rate, channels = Frame_Rate_Channel(file_name)
    if channels > 1:
        stereo_to_mono(file_name)
    source_file_name = FILEPATH + audio_file_name
    destination_blob_name = audio_file_name
    #Upload file in cloud to translate 
    Upload_Blob(BUCKETNAME, source_file_name, destination_blob_name)
    gcs_uri = 'gs://' + BUCKETNAME + '/' + audio_file_name
    transcript = ''
    client = speech.SpeechClient()
    audio = types.RecognitionAudio(uri=gcs_uri)
    # The use case of the audio, e.g. PHONE_CALL, DISCUSSION, PRESENTATION, et al.
    interaction_type = enums.RecognitionMetadata.InteractionType.PRESENTATION
    # The kind of device used to capture the audio
    recording_device_type = enums.RecognitionMetadata.RecordingDeviceType.RECORDING_DEVICE_TYPE_UNSPECIFIED
    microphone_distance =enums.RecognitionMetadata.MicrophoneDistance.NEARFIELD
    # The device used to make the recording.
    # Arbitrary string, e.g. 'Pixel XL', 'VoIP', 'Cardioid Microphone', or other
    # value.
    #recording_device_name = "Pixel 3"
    metadata = {
        "interaction_type": interaction_type,
        "recording_device_type": recording_device_type,
        #recording_device_name": recording_device_name,
        "microphone_distance": microphone_distance
    }
    config = types.RecognitionConfig(
        #enableAutomaticPunctuation = True,
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=frame_rate,
        language_code= language,
        enable_automatic_punctuation=True,
        model="video",
        metadata = metadata
        )
    # Detects speech in the audio file
    operation = client.long_running_recognize(config, audio)
    response = operation.result(timeout=10000)

    for result in response.results:
        transcript += result.alternatives[0].transcript
        
    return (transcript)

def Write_Transcripts(transcript_filename,transcript):
    f=open(OUTPUT_FILEPATH + transcript_filename,"w+")
    f.write(transcript)
    f.close()

def chunkstring(string, length):
    return (string[0+i:length+i] for i in range(0, len(string), length))

def chunkNB (t,nb):
    lines = (i.strip() for i in t.splitlines())
    list=[]
    for line in lines:
        for chunk in chunkstring(line, nb):
            list.append(chunk)
    return list

def Synthesize_Text(text,file_name,language):
    """
    Synthesizes speech from the input string of text.
    """
    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.types.SynthesisInput(text=text)
    if language == 'FR':
        language_code='fr-FR'
        name = 'fr-FR-Wavenet-B'
    else:
        language_code='es-ES'
        name = 'es-ES-Wavenet-B'
    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    voice = texttospeech.types.VoiceSelectionParams(
            language_code=language_code,
            name=name,
            ssml_gender=texttospeech.enums.SsmlVoiceGender.MALE
            )
    audio_config = texttospeech.types.AudioConfig(
                audio_encoding=texttospeech.enums.AudioEncoding.MP3
            )
    response = client.synthesize_speech(input_text, voice, audio_config)
    file_name=file_name+".mp3"
    # The response's audio_content is binary.
    with open(file_name, 'wb') as out:
        out.write(response.audio_content)
        print('Audio content written to file ',file_name)

def Transcription (audio_file_name, language):
    client = speech.SpeechClient()
    file_name = FILEPATH + audio_file_name
    # The name of the audio file to transcribe
    frame_rate, channels = frame_rate_channel(file_name)
    #frame_rate, channels = frameRate_Channel (file_name)
    if channels > 1:
        stereo_to_mono(file_name)
    """
    with io.open(file_name, 'rb') as audio_file:
        content = audio_file.read()
    """
    audio = speech.types.RecognitionAudio(uri=file_name)
    config = speech.types.RecognitionConfig(
            encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=frame_rate,
            language_code=language,
            # Enable automatic punctuation
            enable_automatic_punctuation=True)
   #response = client.recognize(config, audio)
    operation = client.long_running_recognize(config, audio)
    response = operation.result(timeout=10000)
    for i, result in enumerate(response.results):
        alternative = result.alternatives[0]
        print('-' * 20)
        print('First alternative of result {}'.format(i))
        print('Transcript: {}'.format(alternative.transcript))
    return (alternative)

