from fastapi import FastAPI
from pydantic import BaseModel
import os 
from dotenv import load_dotenv
from google import genai
from fastapi.middleware.cors import CORSMiddleware
load_dotenv()
client=genai.Client(api_key=os.getenv('Api_Key'))

web_app=FastAPI()

web_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


profiledata = {}

@web_app.get("/")
def home():
    return {"message": "AI Mentor API "}

class Doubt(BaseModel):
    query: str
    mode: str
    subject: str
    name: str

@web_app.post("/ask-doubt")
def ask_doubt(data: Doubt):
    subject = data.subject
    query = data.query
    mode = data.mode
    name=data.name
    if name not in profiledata:
        return {'response':'profile not found make your profile first'}
    student=profiledata[name]

    prompt = f"""
Role: doubt solver

Act: you are a top kota faculty of subject {subject} and you have taught many top rankers in JEE and NEET.
student profile :
name={name}
currentclass:{student['current_class']}
target_exam:{student['target_exam']}



Mode selected: {mode}

Rules:
1. exam mode → guide for near exams, high-weightage topics, syllabus strategy
2. depth mode → detailed answer, tips, tricks, similar problems
3. quick doubt mode → short and concise answer

Constraints:
- be concise and straightforward
- do not add noise
- if you do not know, admit it
- if subject is physics, focus on intuition and derivation
- if subject is chemistry, focus on reactions and mechanisms
- if subject is maths, focus on formulas and tricks
- if subject is biology, focus on flowcharts and concise theory

Student doubt:
{query}

Output format:
greetings:
answer:
motivation:
exam tips:
"""
    if len(data.query.lower())<=10:
        return {"response": "Please provide a more detailed doubt for better assistance."}
    
    

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt)

    
    profiledata[name]['history'].append({
        "query": query,
        "response": response.text,
        "subject": subject,
        "mode": mode
    })
    return {'answer': response.text}

class Profile(BaseModel):
    name: str
    current_class: str
    target_exam: str
    weak_subject: str
@web_app.get('/askprofile')
def greet():
    return{'WELCOME': 'Hello HOW ARE YOU !!'}
    

@web_app.post("/addprofile")
def add_profile(profile: Profile):
    profiledata[profile.name] = {'weak_subject': profile.weak_subject,
                                 'current_class': profile.current_class,
                                 'target_exam': profile.target_exam,
                                 'history': []}
    return {"message": "Profile added successfully"}

@web_app.get('/student_history/{name}')
def student_profile(name:str):
    if name not in profiledata:
        return{'response ': 'profile not found'}
    else:
        return{'history':profiledata[name]['history']}


@web_app.get('/weak_topic/{name}')
def weak_topic(name:str):
    count={}
    if name not in profiledata:
        return {'response':'add your profile '}
    for item in profiledata[name]['history']:
        sub=item['subject']
        count[sub]=count.get(sub,0)+1
    if not count:
        return 'no data availabe'
    weak=max(count,key=count.get)
    return{'weak_subject':weak,
           'details':count}
@web_app.get('/progress/{name}')
def progress(name:str):
    if name not in profiledata:
        return{'response': 'add your profile'}
    history=profiledata[name]['history']
    total=len(history)
    subjects={}
    for item in history:
        sub=item['subject']
        subjects[sub]=subjects.get(sub,0)+1
    return { 'total_doubt':
            total,
            'subjectwise':
            subjects}



