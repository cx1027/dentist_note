import asyncio
import eel
import sys
import threading
import logging
import requests
import json
import ollama
import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client = Groq(api_key = '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')
# print("client", client)

from faster_whisper import WhisperModel
from .audio_transcriber import AppOptions
from .audio_transcriber import AudioTranscriber
from .utils.audio_utils import get_valid_input_devices, base64_to_audio
from .utils.file_utils import read_json, write_json, write_audio
from .websoket_server import WebSocketServer
from .openai_api import OpenAIAPI
from .ollama_api import OllamaAPI
# from .. consumers import TranscriptionConsumer

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# eel.init("/Users/xiu/Documents/audio-example/dental_notes/dental_notes/webapp/templates/webapp")
eel.init(f'{os.path.dirname(os.path.realpath(__file__))}/web')

transcriber: AudioTranscriber = None
event_loop: asyncio.AbstractEventLoop = None
thread: threading.Thread = None
websocket_server: WebSocketServer = None
openai_api: OpenAIAPI = None
ollama_api: OllamaAPI = None

# RunPod API configuration
RUNPOD_API_URL = "https://ipm1wipet51hbz-8008.proxy.runpod.net/"
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")

# from openai import OpenAI
# client = OpenAI(
#     base_url="https://ipm1wipet51hbz-8008.proxy.runpod.net/v1",
#     api_key=os.getenv("HUGGINGFACE_TOKEN"),
# )

@eel.expose
def get_valid_devices():
    devices = get_valid_input_devices()
    return [
        {
            "index": d["index"],
            "name": f"{d['name']} {d['host_api_name']} ({d['max_input_channels']} in)",
        }
        for d in devices
    ]


@eel.expose
def get_dropdown_options():
    data_types = ["model_sizes", "compute_types", "languages"]

    dropdown_options = {}
    for data_type in data_types:
        data = read_json("assets", data_type)
        dropdown_options[data_type] = data[data_type]

    return dropdown_options


@eel.expose
def get_user_settings():
    data_types = ["app_settings", "model_settings", "transcribe_settings"]
    user_settings = {}

    try:
        data = read_json("settings", "user_settings")
        for data_type in data_types:
            user_settings[data_type] = data[data_type]
    except Exception as e:
        eel.on_recive_message(str(e))

    return user_settings


@eel.expose
def start_as_transcription():
    global transcriber, event_loop, thread, websocket_server, openai_api
    try:
        logger.info("开始转录进程...")
        (
            filtered_app_settings,
            filtered_model_settings,
            filtered_transcribe_settings,
        ) = extracting_each_setting()
        
        logger.info(f"加载Whisper模型，设置: {filtered_model_settings}")
        whisper_model = WhisperModel(**filtered_model_settings)
        
        app_settings = AppOptions(**filtered_app_settings)
        event_loop = asyncio.new_event_loop()

        if app_settings.use_websocket_server:
            logger.info("初始化WebSocket服务器...")
            websocket_server = WebSocketServer(event_loop)
            asyncio.run_coroutine_threadsafe(
                websocket_server.start_server(), event_loop
            )

        if app_settings.use_openai_api:
            logger.info("初始化OpenAI API...")
            openai_api = OpenAIAPI()
        
        # consumer = TranscriptionConsumer()

        logger.info("初始化音频转录器...")
        transcriber = AudioTranscriber(
            event_loop,
            whisper_model,
            filtered_transcribe_settings,
            app_settings,
            websocket_server,
            openai_api,
        )
        asyncio.set_event_loop(event_loop)
        thread = threading.Thread(target=event_loop.run_forever, daemon=True)
        thread.start()

        asyncio.run_coroutine_threadsafe(transcriber.start_transcription(), event_loop)
    except Exception as e:
        logger.error(f"转录启动失败: {str(e)}")
        eel.on_recive_message(str(e))


@eel.expose
def stop_as_transcription():
    global transcriber, event_loop, thread, websocket_server, openai_api
    logger.info("停止转录进程...")
    if transcriber is None:
        logger.info("转录器未运行")
        # eel.transcription_stoppd()
        return
    transcriber_future = asyncio.run_coroutine_threadsafe(
        transcriber.stop_transcription(), event_loop
    )
    transcriber_future.result()

    if websocket_server is not None:
        websocket_server_future = asyncio.run_coroutine_threadsafe(
            websocket_server.stop_server(), event_loop
        )
        websocket_server_future.result()

    if thread.is_alive():
        event_loop.call_soon_threadsafe(event_loop.stop)
        thread.join()
    event_loop.close()
    transcriber = None
    event_loop = None
    thread = None
    websocket_server = None
    openai_api = None

    logger.info("转录进程已完全停止")
    # eel.transcription_stoppd()


@eel.expose
def audio_transcription(user_settings, base64data):
    global transcriber, openai_api
    try:
        logger.info("开始音频文件转录...")
        (
            filtered_app_settings,
            filtered_model_settings,
            filtered_transcribe_settings,
        ) = extracting_each_setting(user_settings)

        whisper_model = WhisperModel(**filtered_model_settings)
        app_settings = AppOptions(**filtered_app_settings)

        if app_settings.use_openai_api:
            openai_api = OpenAIAPI()

        # consumer = TranscriptionConsumer()
        
        transcriber = AudioTranscriber(
            event_loop,
            whisper_model,
            filtered_transcribe_settings,
            app_settings,
            None,
            openai_api
            # consumer
        )

        audio_data = base64_to_audio(base64data)
        if len(audio_data) > 0:
            logger.info("保存音频文件并开始转录...")
            write_audio("web", "voice", audio_data)
            transcriber.batch_transcribe_audio(audio_data)
            logger.info("音频文件转录完成")

    except Exception as e:
        logger.error(f"音频转录失败: {str(e)}")
        eel.on_recive_message(str(e))

    openai_api = None


def get_filtered_app_settings(settings):
    valid_keys = AppOptions.__annotations__.keys()
    return {k: v for k, v in settings.items() if k in valid_keys}


def get_filtered_model_settings(settings):
    valid_keys = WhisperModel.__init__.__annotations__.keys()
    return {k: v for k, v in settings.items() if k in valid_keys}


def get_filtered_transcribe_settings(settings):
    valid_keys = WhisperModel.transcribe.__annotations__.keys()
    return {k: v for k, v in settings.items() if k in valid_keys}


def extracting_each_setting():
    print("extracting_each_setting")
    
    with open("/Users/xiu/Documents/audio-example/dental_notes/dental_notes/webapp/speech_to_text/settings/user_settings.json", 'r') as f:
        user_settings = json.load(f)
    print("afafdas")
    filtered_app_settings = get_filtered_app_settings(user_settings["app_settings"])
    filtered_model_settings = get_filtered_model_settings(
        user_settings["model_settings"]
    )
    filtered_transcribe_settings = get_filtered_transcribe_settings(
        user_settings["transcribe_settings"]
    )

    write_json(
        "settings",
        "user_settings",
        {
            "app_settings": filtered_app_settings,
            "model_settings": filtered_model_settings,
            "transcribe_settings": filtered_transcribe_settings,
        },
    )
    print("finish extracting_each_setting")
    return filtered_app_settings, filtered_model_settings, filtered_transcribe_settings


def on_close(page, sockets):
    print(page, "was closed")

    if transcriber and transcriber.transcribing:
        stop_as_transcription()
    sys.exit()


@eel.expose
def initialize_ollama():
    global ollama_api
    try:
        ollama_api = OllamaAPI()
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Ollama API: {str(e)}")
        return False


@eel.expose
def generate_summary(text):
    try:
        if ollama_api is None:
            initialize_ollama()
        
        summary = ollama_api.generate_summary(text)
        return summary
    except Exception as e:
        logger.error(f"Failed to generate summary: {str(e)}")
        return str(e)


@eel.expose
def load_conversation_data():
    try:
        with open("summary/meeting_transcript.json") as f:
            json_file = json.load(f)
            extraction = lambda x: f"{x['speaker']}: {x['text']}"
            conversation = list(map(extraction, json_file))
            conversation_string = "\n".join(conversation)
            return conversation_string
    except Exception as e:
        print(f"Error loading conversation data: {str(e)}")
        return ""

@eel.expose
def meeting_summary():
    try:
        conversation_string = load_conversation_data()
        response = ollama.chat(model='gemma:2b', messages=[
            {
                'role': 'system',
                'content': 'Your goal is to summarize the text that is given to you in roughly 300 words. It is from a meeting between one or more people. Only output the summary without any additional text. Focus on providing a summary in freeform text with a summary of what people said and the action items coming out of it.'
            },
            {
                'role': 'user',
                'content': conversation_string,
            },
        ])
        return response['message']['content']
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        return "Error generating summary"

@eel.expose
def meeting_summary_rest(conversation_string):
    try:
        if not conversation_string:
            return "No transcription data available"

        prompt = """As a doctor, analyze this medical consultation transcript and return ONLY a single-level JSON object. 
        For multiple points in any field, use numbered format (1. 2. 3.) within the same string. You need to use as much as the patient description for your notes.
        
        Required JSON format:
        {
            "Patient_Name": "patient name or N/A",
            "Date": "date or N/A",
            "Reason_for_Meeting": "main reason or N/A",
            "History": "patient history or N/A (if multiple points: 1. First point 2. Second point)",
            "Examination": "examination details or N/A (if multiple points: 1. First finding 2. Second finding)",
            "Discussion": "discussion points or N/A (if multiple points: 1. First topic 2. Second topic)",
            "Plan": "treatment plan or N/A (if multiple points: 1. First step 2. Second step)",
            "Follow_up": "follow up details or N/A",
            "Teeth_Description": {
                "1": "Upper right central incisor: description or N/A",
                "2": "Upper right lateral incisor: description or N/A",
                "3": "Upper right canine: description or N/A",
                "4": "Upper right first molar: description or N/A",
                "5": "Upper right second molar: description or N/A",
                "6": "Upper right third molar: description or N/A",
                "7": "Upper left third molar: description or N/A",
                "8": "Upper left second molar: description or N/A",
                "9": "Upper left first molar: description or N/A",
                "10": "Upper left canine: description or N/A",
                "11": "Upper left lateral incisor: description or N/A",
                "12": "Upper left central incisor: description or N/A",
                "13": "Lower left central incisor: description or N/A",
                "14": "Lower left lateral incisor: description or N/A",
                "15": "Lower left canine: description or N/A",
                "16": "Lower left first molar: description or N/A",
                "17": "Lower left second molar: description or N/A",
                "18": "Lower left third molar: description or N/A",
                "19": "Lower right third molar: description or N/A",
                "20": "Lower right second molar: description or N/A",
                "21": "Lower right first molar: description or N/A",
                "22": "Lower right canine: description or N/A",
                "23": "Lower right lateral incisor: description or N/A",
                "24": "Lower right central incisor: description or N/A",
                "25": "Lower right central incisor: description or N/A",
                "26": "Lower right lateral incisor: description or N/A",
                "27": "Lower right canine: description or N/A",
                "28": "Lower right first molar: description or N/A",
                "29": "Lower right second molar: description or N/A",
                "30": "Lower right third molar: description or N/A",
                "31": "Lower left third molar: description or N/A",
                "32": "Lower left second molar: description or N/A"
            }
        }

        Rules:
        1. Return ONLY the JSON object, no additional text
        2. Use "N/A" for missing information in Patient_Name, Date, Reason_for_Meeting, History, Examination, Discussion, Plan, Follow_up.
        3. Keep all points for each field in a single string
        4. Use numbered format (1. 2. 3.) for multiple points within the same string
        5. Do not create nested objects or arrays
        6. For teeth description, if not mention any teeth specifically, mark as N/A for missing information.
        
        Here's the transcript to analyze: {conversation_string}"""

        # OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"

        # OLLAMA_PROMPT = f"{prompt}: {conversation_string}"
        # OLLAMA_DATA = {
        #     "model": "gemma:2b",
        #     # "model": "llama3.1:70b",
        #     "prompt": OLLAMA_PROMPT,
        #     "stream": False,
        #     "keep_alive": "1m",
        # }

        # response = requests.post(OLLAMA_ENDPOINT, json=OLLAMA_DATA)
        # print("response",response.json()["response"])
        # return response.json()["response"]
    
        # completion = client.chat.completions.create(
        #     model="llama-3.3-70b-versatile",
        #     messages=[{"role": "user", "content":prompt}],
        #     temperature=1,
        #     max_completion_tokens=1024,
        #     top_p=1,
        #     stream=True,
        #     stop=None,)
        
        # response = completion.choices[0].message
        # print("response",response.content)
        # return response.content
    
        completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content":prompt}]
                )
            
        response = completion.choices[0].message
        print("response",response.content)
        return response.content
    except Exception as e:
        print(f"Error generating summary via REST: {str(e)}")
        return "Error generating summary"
    
@eel.expose
def meeting_template_summary_rest(TemplateText, conversation_string):
    try:
        if not conversation_string:
            return "No transcription data available"
        if not TemplateText:
            return "No Template data available"
        
        # 将 TemplateText 转换为 JSON
        template_json = text_to_json(TemplateText)
        print("template_json:", template_json)
        
        # 更新 prompt_temp，传递 template_json 和 conversation_string
        prompt = f"""As a doctor, analyze this medical consultation transcript and return ONLY a single-level JSON object. 
        For multiple points in any field, use numbered format (1. 2. 3.) within the same string. You need to use as much as the patient description for your notes.
        
        Required JSON format: {template_json}
        
        Rules:
        1. Return ONLY the JSON object, no additional text
        2. Use "N/A" for missing information in Patient_Name, Date, Reason_for_Meeting, History, Examination, Discussion, Plan, Follow_up.
        3. Keep all points for each field in a single string
        4. Use numbered format (1. 2. 3.) for multiple points within the same string
        5. Do not create nested objects or arrays
        6. For teeth description, if not mention any teeth specifically, mark as N/A for missing information.
        
        Here's the transcript to analyze: {conversation_string}"""

        # OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"

        # OLLAMA_DATA = {
        #     "model": "gemma:2b",
        #     "prompt": prompt_temp,
        #     "stream": False,
        #     "keep_alive": "1m",
        # }

        # response = requests.post(OLLAMA_ENDPOINT, json=OLLAMA_DATA)
        # print("response", response.json()["response"])
        # return response.json()["response"]
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content":prompt}])
            # temperature=1,
            # max_completion_tokens=1024,
            # top_p=1,
            # stream=True,
            # stop=None,)
        
        response = completion.choices[0].message
        print("response",response.content)
        return response.content
    except Exception as e:
        print(f"Error generating summary via REST: {str(e)}")
        return "Error generating summary"
    
@eel.expose
def meeting_summary_rest_runpod(conversation_string):
    logger.info(f'meeting_summary_rest_runpod: {conversation_string}')
    try:
        if not conversation_string:
            return "No transcription data available"

        # Prepare the input for the model
        prompt = """As a doctor, analyze this medical consultation transcript and return ONLY a single-level JSON object. 
        For multiple points in any field, use numbered format (1. 2. 3.) within the same string. You need to use as much as the patient description for your notes.
        
        Required JSON format:
        {
            "Patient_Name": "patient name or N/A",
            "Date": "date or N/A",
            "Reason_for_Meeting": "main reason or N/A",
            "History": "patient history or N/A (if multiple points: 1. First point 2. Second point)",
            "Examination": "examination details or N/A (if multiple points: 1. First finding 2. Second finding)",
            "Discussion": "discussion points or N/A (if multiple points: 1. First topic 2. Second topic)",
            "Plan": "treatment plan or N/A (if multiple points: 1. First step 2. Second step)",
            "Follow_up": "follow up details or N/A",
            "Teeth_Description": {
                "1": "Upper right central incisor: description or N/A",
                "2": "Upper right lateral incisor: description or N/A",
                "3": "Upper right canine: description or N/A",
                "4": "Upper right first molar: description or N/A",
                "5": "Upper right second molar: description or N/A",
                "6": "Upper right third molar: description or N/A",
                "7": "Upper left third molar: description or N/A",
                "8": "Upper left second molar: description or N/A",
                "9": "Upper left first molar: description or N/A",
                "10": "Upper left canine: description or N/A",
                "11": "Upper left lateral incisor: description or N/A",
                "12": "Upper left central incisor: description or N/A",
                "13": "Lower left central incisor: description or N/A",
                "14": "Lower left lateral incisor: description or N/A",
                "15": "Lower left canine: description or N/A",
                "16": "Lower left first molar: description or N/A",
                "17": "Lower left second molar: description or N/A",
                "18": "Lower left third molar: description or N/A",
                "19": "Lower right third molar: description or N/A",
                "20": "Lower right second molar: description or N/A",
                "21": "Lower right first molar: description or N/A",
                "22": "Lower right canine: description or N/A",
                "23": "Lower right lateral incisor: description or N/A",
                "24": "Lower right central incisor: description or N/A",
                "25": "Lower right central incisor: description or N/A",
                "26": "Lower right lateral incisor: description or N/A",
                "27": "Lower right canine: description or N/A",
                "28": "Lower right first molar: description or N/A",
                "29": "Lower right second molar: description or N/A",
                "30": "Lower right third molar: description or N/A",
                "31": "Lower left third molar: description or N/A",
                "32": "Lower left second molar: description or N/A"
            }
        }

        Rules:
        1. Return ONLY the JSON object, no additional text
        2. Use "N/A" for missing information in Patient_Name, Date, Reason_for_Meeting, History, Examination, Discussion, Plan, Follow_up.
        3. Keep all points for each field in a single string
        4. Use numbered format (1. 2. 3.) for multiple points within the same string
        5. Do not create nested objects or arrays
        6. For teeth description, if not mention any teeth specifically, mark as N/A for missing information.
        
        Here's the transcript to analyze: """+f'{conversation_string}'
        print(prompt)
        
        completion = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-70B-Instruct",
            messages=[{"role": "user", "content":prompt}])
        
        response = completion.choices[0].message
        print("response",response.content)
        return response.content
    except Exception as e:
        print(f"Error generating summary via REST: {str(e)}")
        return "Error generating summary"
        

def text_to_json(text):
    lines = text.strip().split('\n')
    result = {}
    current_key = None

    for line in lines:
        line = line.strip()
        if line.endswith(':'):
            current_key = line[:-1]  # Remove the colon
            result[current_key] = ""
        elif line.startswith('- '):
            if current_key:
                result[current_key] = line[2:]  # Remove the '- ' at the beginning

    return json.dumps(result, indent=2)

