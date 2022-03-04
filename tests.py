import time
from threading import Thread

from MappingClass import MappingClass
from VoiceInput import VoiceInput


class Z:
    def __init__(self):

        # the control concept is based on the unreal engine:
        # first mapping action names to specific functions
        self.mappingObject = MappingClass()
        self.mappingObject.map_standard_action("test", lambda: print("test"))
        self.mappingObject.map_standard_action("movement", lambda x, y: print(f"move, {x}, {y}"))
        # self.mappingObject.map_standard_action("swap", lambda:)

        self.voice_input = VoiceInput(self.mappingObject, '9l0KIfkApY6TbTOsrhP5g_TdI3V6d0_-qa66IEJyrOsd',
                                      'https://api.eu-de.speech-to-text.watson.cloud.ibm.com/instances/8206897f'
                                      '-1878-440b-b329-d9fa922e132e')

        self.voice_input.bind_sentence("test", ["test"])
        self.voice_input.bind_sentence("movement", ["for word", "forward"], args=[0, 1])

        self.listen_to_voice_input = False

    def runZebulon(self):
        self.voice_input.start_voice_input()

        # self.body.getUp()
        while True:
            if self.listen_to_voice_input:
                if not self.voice_input.recognize_thread.is_alive():
                    self.voice_input.recognize_thread.start()

                if self.voice_input.stop or self.voice_input.total_stop:
                    self.voice_input.audio_source.completed_recording()
                    self.voice_input.stream.stop_stream()

                    if self.voice_input.action_to_execute is not None:
                        self.voice_input.action_to_execute()
                    while self.voice_input.recognize_thread.is_alive():
                        pass

                    self.voice_input.action_to_execute = None
                    self.voice_input.stop = False

                    if self.voice_input.total_stop:
                        self.voice_input.stream.close()
                        print("terminating!!!!!!!!!!!!!!!!!!!!!!!")
                        self.voice_input.audio.terminate()
                        self.voice_input.total_stop = False
                    else:
                        self.voice_input.stream.start_stream()
                        self.voice_input.recognize_thread = Thread(
                            target=self.voice_input.recognize_using_weboscket, args=())
                        self.voice_input.recognize_thread.start()

            time.sleep(0.02)

    def switch_voice_input(self):
        self.listen_to_voice_input = not self.listen_to_voice_input

        if not self.listen_to_voice_input:
            self.voice_input.stream.close()
            self.voice_input.audio.terminate()
            self.voice_input.action_to_execute = None
            self.voice_input.stop = False
            self.voice_input.total_stop = False

            while self.voice_input.recognize_thread.is_alive():
                pass


if __name__ == '__main__':
    listen_to_voice_input = True

    mappingObject = MappingClass()
    mappingObject.map_standard_action("test", lambda: print("test"))
    mappingObject.map_standard_action("movement", lambda x, y: print(f"move, {x}, {y}"))

    voiceInput = VoiceInput(mappingObject, '9l0KIfkApY6TbTOsrhP5g_TdI3V6d0_-qa66IEJyrOsd',
                            'https://api.eu-de.speech-to-text.watson.cloud.ibm.com/instances/8206897f'
                            '-1878-440b-b329-d9fa922e132e'
                            )

    voiceInput.bind_sentence("test", ["test"])
    voiceInput.bind_sentence("movement", ["for word", "forward"], args=[0, 1])



    while True:
        if listen_to_voice_input:
            if not voiceInput.recognize_thread.is_alive():
                voiceInput.recognize_thread.start()

            if voiceInput.stop or voiceInput.total_stop:
                voiceInput.audio_source.completed_recording()
                voiceInput.stream.stop_stream()

                if voiceInput.action_to_execute is not None:
                    voiceInput.action_to_execute()

                while voiceInput.recognize_thread.is_alive():
                    pass

                voiceInput.action_to_execute = None
                voiceInput.stop = False

                if voiceInput.total_stop:
                    voiceInput.stream.close()
                    print("terminating!!!!!!!!!!!!!!!!!!!!!!!")
                    voiceInput.audio.terminate()
                    voiceInput.total_stop = False
                else:
                    voiceInput.stream.start_stream()
                    voiceInput.recognize_thread = Thread(
                        target=voiceInput.recognize_using_weboscket, args=())
                    voiceInput.recognize_thread.start()
