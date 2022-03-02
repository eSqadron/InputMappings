from dataclasses import dataclass
from typing import Dict, List, Any

import pyaudio
from ibm_watson import SpeechToTextV1
from ibm_watson.websocket import RecognizeCallback, AudioSource
from threading import Thread
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

from MappingClass import MappingClass, Mapping

try:
    from Queue import Queue, Full
except ImportError:
    from queue import Queue, Full


# define callback for the speech to text service
# TODO - zmergować tą klasę z klasą VoiceInput
class MyRecognizeCallback(RecognizeCallback):
    def __init__(self, VoiceInputInstance):
        RecognizeCallback.__init__(self)
        self.VoiceInputInstance = VoiceInputInstance
        self.old_trans = None

    def on_transcription(self, transcript):
        pass
        # print("  ", transcript['results'][0]['alternatives'][0]['transcript'])

    def on_connected(self):
        print('Connection was successful')

    def on_error(self, error):
        print('Error received: {}'.format(error))

    def on_inactivity_timeout(self, error):
        print('Inactivity timeout: {}'.format(error))

    def on_listening(self):
        print('Service is listening')

    def on_hypothesis(self, hypothesis):
        pass
        # print("hypo:", hypothesis)

    def on_data(self, data):
        # 5) podczas rozpoznawania on_data otrzymuje obecny stan transkrypcji, od początku recognize_using_websocket
        trans = data['results'][0]['alternatives'][0]['transcript']
        if trans != self.old_trans:  # zabezpieczenie aby nie rozpoznawało ciszy
            print(trans)
            # 6) transkrypcja jest przekazywana do checkAndExecute aby sprawdzić czy pojawiło się jakieś słowo klucz
            # i wywołać daną funkcję
            self.VoiceInputInstance.checkAndExecute(trans)
            self.old_trans = trans

    def on_close(self):
        print("Connection closed")


@dataclass
class VoiceBind:
    action_name: str
    voice_inputs: List[str]
    action_map: Mapping
    args: List[Any]
    kwargs: Dict[str, Any]


class VoiceInput:
    def __init__(self, mapping_object: MappingClass, APIKEY: str, URL: str, model: str = "en-GB_BroadbandModel"):
        self.CHUNK = 1024

        # TODO - dodać settera BUF_MAX_SIZE, aby dało się zmienić dla instancji klasy, powinien też updejtować queue
        self.BUF_MAX_SIZE = self.CHUNK * 10
        self.q = Queue(maxsize=int(round(self.BUF_MAX_SIZE / self.CHUNK)))

        # Create an instance of AudioSource
        self.audio_source = AudioSource(self.q, True, True)

        # initialize variables for recording the speech
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 48000

        # initialize speech to text service
        self.authenticator = IAMAuthenticator(APIKEY)
        self.speech_to_text = SpeechToTextV1(authenticator=self.authenticator)
        self.speech_to_text.set_service_url(URL)
        self.model = model
        # TODO - dodać własny model

        self.stream = None
        self.audio = None
        self.recognize_thread = Thread(target=self.recognize_using_weboscket, args=())

        # initlialize mapping
        self.mapping_object = mapping_object
        self.voice_binds: Dict[str, VoiceBind] = {}

        self.stop = False
        self.total_stop = False
        self.stop_words = ['exit']  # TODO - stop_words ładniej by chyba z geterami seterami działało

        self.action_to_execute = None

        # this function will initiate the recognize service and pass in the AudioSource

    def recognize_using_weboscket(self, *args):
        # 3) mycallback jest instancją klasy która mówi co ma się dziać w przypadku wystąpienia pewnych wydarzeń podczas
        # rozpoznawania
        mycallback = MyRecognizeCallback(self)
        # 4) rozpoczynam rozpoznawania
        # audio source to efektywnie kolejka z kolejnymi nagranymi fragmentami. Kolejka ta po wysłaniu kolejnego
        # fragmentu CHYBA usuwa go "z siebie". Podaje się też mycallback. Jest tam funkcja on data, czyli co ma się
        # dziać kiedy otrzyma i rozpozna kolejny fragment
        self.speech_to_text.recognize_using_websocket(audio=self.audio_source,
                                                      content_type=f'audio/l16; rate={self.RATE}',
                                                      recognize_callback=mycallback,
                                                      interim_results=True,
                                                      model=self.model)

    # define callback for pyaudio to store the recording in queue
    def pyaudio_callback(self, in_data, frame_count, time_info, status):
        try:
            self.q.put(in_data)
        except Full:
            pass  # discard
        return None, pyaudio.paContinue

    def start_voice_input(self):
        # TODO - aby po rozpoznaniu polecenia czyściło bufor (aby to polecenie nie wykonywało się bez przerwy)

        self.stop = False
        self.total_stop = False

        # while not self.total_stop:
        # instantiate pyaudio
        self.audio = pyaudio.PyAudio()
        try:
            self.RATE = int(self.audio.get_default_input_device_info()['defaultSampleRate'])
        except OSError:
            pass

        # TODO - ogarnąć ustawianie audio i ratea w inicie i setter podstawowego urządzenia (list devices i set device)

        # open stream using callback
        # 1) otwieram stream z mikrofonu, co self.CHUNK ramek będzie się wywoływała funkcja self.pyaudio_callback.
        # Funkcja ta dodaje kolejny nagrany fragment do kolejki
        # TODO - jakiesz poszukiwanie mikrofonu

        self.stream = self.audio.open(
            format=self.FORMAT,
            channels=1,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
            stream_callback=self.pyaudio_callback,
            start=False,
            input_device_index=1
        )

        self.stream.start_stream()
        self.recognize_thread.start()

    def checkAndExecute(self, transcript):
        print("checkAndExecute")
        if not self.stop:
            # 7) w pierwszej kolejności sprawdza słowa "zupełnego" stopu, w tym momencie nie działa
            # ponieważ jakiekolwiek słowo klucz jest zupełnym stopem
            for i in self.stop_words:
                if i in transcript:
                    self.total_stop = True
            # 8) później przeszukuje słownik voice_binds i sprawdza czy w transkrypcji
            # pojawiły się słowa klucze znajdujące się w tym słowniku. Jeżeli tak to wykonuje odpowiednią akcję i
            # wychodzi z rozpoznawania
            for i, v_c in self.voice_binds.items():
                print(transcript)
                if i in transcript:
                    self.action_to_execute = lambda: v_c.action_map.executeAction(*v_c.args, **v_c.kwargs)
                    self.stop = True

    def bind_sentence(self, action_name: str, voice_inputs: List[str], args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        if action_name in self.mapping_object.standard_mappings.keys():
            voice_bind = VoiceBind(action_name, voice_inputs, self.mapping_object.standard_mappings[action_name], args=args,
                                   kwargs=kwargs)
            for i in voice_inputs:
                self.voice_binds[i] = voice_bind
        else:
            raise IndexError(f"First map the action named {action_name}!")

