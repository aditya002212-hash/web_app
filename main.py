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
    def load_data():
        with open('physics.txt','r') as f:
            return f.read()
    def search_query(query,context):
        lines=context.split('\n')
        relvant=[]
        for line in lines :
            if query.lower()  in line.lower():
                relvant.append(line)
        return '\n'.join(relvant[:5])
    knowledge=load_data()
    context=search_query(query,knowledge)
    if context:
        prompt=f'''

Use the following study material to answer:

{context}

Student doubt:
{query}

Answer clearly and exam-focused.
'''
        response=client.models.generate_content(model='gemini-2.5-flash',contents=prompt)
        return {'answer':response}
    prompt = f"""

You are a top Kota mentor for {subject}.

Student Profile:
Class: {student['current_class']}
Target Exam: {student['target_exam']}
Weak Subject: {student['weak_subject']}

Mode: {mode}

Task:
1. Teach like a mentor, not just answer
2. Keep explanation clear and structured
3. Focus on exam relevance
4. Guide the student on what to do next

Student doubt:
{query}

Output format:

📘 Concept:
🧠 Explanation:
📊 Example:
⚠️ Common Mistake:
🎯 Exam Tip:
➡️ Next Step:
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

class follow(BaseModel):
    need:str
    name:str
@web_app.post('/followup')
def followup(need:follow):
    user_response=need.need
    name=need.name
    prompt=f'''based on previous history {profiledata[name]['history'][-1]}
    and the user_response --{user_response} guide the answer 
    constraints----
    1. be straight forward and do not add noise 
    2. do not make up answer 
    3. if you do not found info or any relevancy admit it 
    4. answer must be allign with the user need in user_response---{user_response}
    '''
    response=client.models.generate_content(model='gemini-2.5-flash',contents=prompt)
    return {'answer':response}


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



