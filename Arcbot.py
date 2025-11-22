from flask import Flask, request, jsonify, render_template, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import json, os
from datetime import datetime, timedelta

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")  # CHANGE THIS IN PRODUCTION!

USER_DB = "users.json"
HISTORY_DB = "history.json"
SESSIONS = {}

GUEST_SESSION_MINUTES = 5
USER_SESSION_MINUTES = 15

# -- User management --
def load_users():
    if not os.path.exists(USER_DB):
        return {}
    with open(USER_DB, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_DB, "w") as f:
        json.dump(users, f, indent=2)

# -- History management --
def load_history():
    if not os.path.exists(HISTORY_DB):
        return {}
    with open(HISTORY_DB, "r") as f:
        return json.load(f)

def save_history(history):
    with open(HISTORY_DB, "w") as f:
        json.dump(history, f, indent=2)

def add_to_history(username, message, reply):
    history = load_history()
    if username not in history:
        history[username] = []
    history[username].append({
        "timestamp": datetime.utcnow().isoformat(),
        "message": message,
        "reply": reply
    })
    save_history(history)

# -- Bot logic --
import random

greetings = [
    "Hello! how can i help you today?",
    "hii, glad to meet you, hope you are doing well, How can I help you?",
    "I'm glad you are here, what would u like to talk about?",
    "Hii, glad you decided to take help, I'm all ears! (;",
    "Hellooo, Welcomeeee!! How can I help you today",
    "Hii, I'm glad you are asking for help!",
    "Heyyy, what brings you here today?",
    "hellooo, how are you feeling today?",
    "Yoo, how can i help you today?",
    "Look who's here, hellooo it's nice to meet you, hope you are doing well!",
    "Hii, I'm here to listen to youu, what's on your mind today?",
    "Heyyy, I'm so glad you reached out today, how can I help you?",
    "Helloo buddy, it seems you have some issues, let's fix them like a og",
    "Hello! How are you feeling today?",
    "Hi there! What’s on your mind?",
    "Hey! Glad you stopped by. How can I help?",
    "Welcome! I’m here to listen whenever you’re ready.",
    "It’s great to see you. How are you doing?",
    "Hey, friend! Tell me what’s going on.",
    "Hi, I’m always here to listen. What brings you here?",
    "Hey, welcome back! How can I support you today?",
    "Hello there! What would you like to talk about?",
    "Hi! I’m so glad you reached out today.",
    "Hey! You matter. How can I help?",
    "Hello! Whenever you’re ready, I’m here.",
    "Hi! Let’s chat. How can I support you?",
    "Hey there! Ready when you are.",
    "Hi! You’re not alone. Let’s talk.",
    "Hey there, what’s up?",
    "Hello, how are you holding up?",
    "Hi! I’m happy to connect with you today.",
    "Hello! Tell me about your day.",
    "Hey! I’m here for you, no matter what.",
    "Hi! How’s things?",
    "Hello! Is there something on your mind?",
    "Hey! Just checking in on you.",
    "Hi! Whatever you want to talk about, I’m here.",
    "Hello! Take your time, I’m here to listen.",
    "Hey! How has your day been so far?",
    "Hi there, I’m always here to help.",
    "Hello! I’m all ears.",
    "Hey! You’re doing great by reaching out.",
    "Hi! I hope you find comfort here."
]

goodBye = [
    "Glad you asked for help, I'm always here if you need me again! :)",
    "Hope you are feeling better after talking, come again if you need someone to listen to you!! (:",
    "I hope you are doing fine after talking, hope you won't have to come again :)",
    "Hope you had a good time, Bye!!",
    "Take care! I’m always here if you want to talk.",
    "Goodbye! Remember, tough times don’t last.",
    "Bye! Reach out anytime – you’re never alone.",
    "Stay strong! Wishing you peace and comfort.",
    "Goodbye for now. Come back whenever you need.",
    "See you soon! You’re doing great.",
    "Take care of yourself, you deserve kindness.",
    "Bye! I’ll be here whenever you need me.",
    "Stay safe, and don’t forget to take care of yourself.",
    "Signing off for now, but always a message away.",
    "Hope you feel a bit lighter today. Goodbye!",
    "It was nice chatting. Remember, you matter.",
    "Have a gentle day! Take things one step at a time.",
    "Goodbye! Sending you lots of positive energy.",
    "Take care! You’re important.",
    "Until next time, take care of your heart.",
    "Bye for now! You’re stronger than you think.",
    "Hope to talk soon. Remember, it’s okay to ask for help.",
    "Goodbye! You’re not alone on this journey.",
    "Wishing you well until our next chat.",
    "Have a peaceful day ahead!",
    "You did great by reaching out. Take care!",
    "Be kind to yourself. See you soon!",
    "Stay hopeful, I’m always here.",
    "Bye! You’ve got this.",
    "See you! Feel free to come back anytime.",
    "Take it easy. You are valued.",
    "Remember, you're doing the best you can.",
    "Hope the rest of your day goes well.",
    "Goodbye, and remember you’re loved.",
    "Signing off, stay positive!",
    "Enjoy the little moments today. Bye!",
    "I’ll be here if you need to talk again.",
    "Remember to breathe and take care.",
    "Reach out anytime! Wishing you better days."
]

default_response = [
    "I hear you. Can you share more about that?",
    "That sounds difficult. Want to tell me more?",
    "I'm here for you, no judgment.",
    "It's okay to feel that way. How can I support you?",
    "I'm listening – please go on.",
    "You’re not alone in this. Let’s talk through it.",
    "Would you like to tell me more?",
    "I understand. What helps you in moments like this?",
    "It’s important to share. How can I help right now?",
    "Thank you for sharing this with me.",
    "That must be tough. I’m here for you.",
    "Your feelings are valid. Would you like to talk more?",
    "Let’s work through this together.",
    "What can I do to make things easier for you?",
    "I’m so sorry you’re feeling this way. I’m here.",
    "If you’d like, you can tell me more.",
    "It’s okay to open up. Take your time.",
    "I’m always here to chat if you need me.",
    "Every feeling matters.",
    "If you want to talk about something else, that’s okay too.",
    "How long have you been feeling this way?",
    "Want to explore what’s causing this?",
    "Let’s take it one step at a time.",
    "Do you have someone nearby who supports you?",
    "Thank you for trusting me.",
    "It’s okay to take a break if you need.",
    "What do you wish could be different right now?",
    "I'm glad you’re talking to me.",
    "Even little steps count.",
    "Whatever you’re facing, you don’t have to face it alone.",
    "How do you usually cope with this?",
    "Let’s try to understand these feelings together.",
    "Is there something that might make you feel better?",
    "If you feel stuck, that's okay. I'm here.",
    "Would expressing more help you feel lighter?",
    "You can talk to me about anything.",
    "Everyone goes through difficult days – you’re not alone.",
    "Is there a small thing you’d like to do right now?",
    "It's okay if you don't have all the answers.",
    "I respect your courage for reaching out.",
    "Sometimes just talking helps.",
    "If you could change one thing today, what would it be?",
    "No topic is too small.",
    "There’s no pressure, share only what feels right.",
    "Is there something you look forward to?",
    "Would a piece of advice help, or just listening?"
]

sad_responses = [
    "I'm sorry you're feeling sad. Want to talk about what's weighing on you?",
    "Sadness is something everyone feels sometimes. How long have you felt this way?",
    "It's okay to be sad. Would sharing more help?",
    "I understand that sadness can feel overwhelming. You're not alone.",
    "Sometimes, just talking can lift a little of that sadness. Would you like that?",
    "Remember to be gentle with yourself during sad days.",
    "Has something happened recently to make you feel this way?",
    "Even on sad days, reaching out is a strong thing to do.",
    "Your feelings matter. Can I help in some way?",
    "Have you been able to talk to anyone else about your sadness?",
    "It’s okay to let emotions out; tears are a way of healing.",
    "Would you like to tell me if anything's helped you in the past?",
    "Do you have a favorite memory that can make you smile, even a little?",
    "Crying is not a weakness; it's an expression of emotion.",
    "Are there things that used to bring you joy, even if they don’t right now?",
    "Sometimes small acts of self-care can help – is there something soothing you could do?",
    "It's okay to rest. Emotional fatigue is real.",
    "You’re allowed to feel what you feel. I’m here.",
    "Would you like suggestions for activities when feeling down?",
    "Can I help you find positive distractions?",
    "Remember, all feelings are temporary.",
    "Self-compassion can be powerful. Try to be kind to yourself.",
    "I’m here, no matter how many sad days come.",
    "Could you describe your sadness, or what triggers it?",
    "Sadness sometimes hides behind routine. Has your routine changed recently?",
    "It's okay if you can’t explain it. Sometimes sadness is just there.",
    "Have you felt supported by people around you?",
    "Would it help to write your feelings or try a creative activity?",
    "Is your sadness tied to memories or worries about the future?",
    "Would it help to list positive things, even if they’re small?",
    "Let’s focus on one small thing you can do gently for yourself.",
    "Sometimes music or art can lighten sadness. Is that true for you?",
    "You don’t have to fake a smile with me.",
    "Would talking to someone in person help? I’m here to help you figure it out.",
    "What do you wish people understood about your sadness?",
    "Let this chat be a safe place for your feelings.",
    "Sadness can be exhausting, please rest if you need.",
]

# ANXIOUS / ANXIETY (50)
anxious_responses = [
    "It's okay to feel anxious; I'm here for you.",
    "Let's take a deep breath together.",
    "Would it help to talk through your worries?",
    "Anxiety doesn't define you. You're stronger than you think.",
    "Is there something specific making you anxious today?",
    "Try to focus on the present moment.",
    "Remember, anxious thoughts aren't always facts.",
    "How have you managed anxiety before?",
    "Even a tiny step forward is progress.",
    "Let's name three things you can see right now.",
    "You aren't alone – many feel just like you.",
    "Would soothing music help you relax?",
    "It's brave to share when you're feeling anxious.",
    "Anxiety is your body's way of looking out for you.",
    "You are safe here.",
    "This feeling will pass, even if it's tough now.",
    "Would it help to write your thoughts down?",
    "Try telling yourself: 'I'm doing the best I can.'",
    "I'm proud of you for reaching out.",
    "Imagine a place where you feel peaceful and safe.",
    "What comfort routine helps when you're anxious?",
    "Would a short walk or movement help ease the tension?",
    "You're allowed to slow down and take breaks.",
    "Let's count backwards from ten together.",
    "Your sensitivity is a strength.",
    "It's okay if it takes time to calm down.",
    "Fear and worry are just feelings; they don't control you.",
    "Try to name your anxiety out loud.",
    "Would repeating a positive phrase to yourself feel good?",
    "What would you say to a friend feeling this way?",
    "Some days will feel better than others."
    "Is it mostly physical symptoms or thoughts?",
    "You can be proud of yourself for facing anxiety.",
    "Try to notice sounds or colors around you.",
    "Would you like to try a short breathing exercise?",
    "Trust in the process – relief will come.",
    "Everyone worries sometimes, but it won't last forever.",
    "Even if anxiety returns, you have new tools now.",
    "Taking care of yourself isn't selfish.",
    "Would it help to distract with something you enjoy?",
    "You get through every anxious moment, one at a time.",
    "Try to stretch or unclench your jaw and hands.",
    "Is there a loved one you can reach out to?",
    "You are enough, even if you're worried.",
    "Small comforts count – wrap up in a blanket or sip something warm.",
    "I'm glad you're here talking about this.",
    "You can always take a short break from whatever is causing anxiety.",
    "Would journaling or doodling help you right now?",
    "Healing isn't linear, and that's okay.",
    "I'm listening as long as you want to talk."
]

# STRESSED / STRESS (50)
stressed_responses = [
    "Stress is tough, but you’re tougher.",
    "Let’s break things down into smaller steps.",
    "What’s the biggest thing on your mind today?",
    "You can ask for help if you need it.",
    "It's okay to take a break.",
    "Progress is progress, even if it's slow.",
    "Sometimes, resting is the most productive thing you can do.",
    "Do you want to talk about what's stressing you out?",
    "You’re not alone – stress is a common feeling.",
    "A deep breath and a cup of tea can work wonders.",
    "You don’t have to handle it all at once.",
    "Would writing a to-do list help clear your mind?",
    "Remember to be gentle with yourself.",
    "Is there something you’ve been putting off that’s adding stress?",
    "It’s okay if you can’t do everything perfectly.",
    "Would a five-minute pause help you reset?",
    "Setbacks don’t erase your effort.",
    "Everyone feels stressed sometimes.",
    "Let’s focus on what you can control right now.",
    "Your best is enough.",
    "Would listening to some favorite music help?",
    "You’re allowed to say ‘no’ to things that feel overwhelming.",
    "Taking care of yourself is important.",
    "Can you delegate or delay anything on your plate?",
    "There’s no shame in feeling overloaded.",
    "Tiny victories matter – celebrate every one.",
    "Rest is productive.",
    "Who can you reach out to for support?",
    "Would moving your body or stretching help?",
    "Give yourself credit for all you’ve managed.",
    "Let’s focus on today, one hour at a time.",
    "You can take tasks one at a time.",
    "It's okay to walk away and return later.",
    "Be proud of what you've accomplished.",
    "Would jotting down your worries make them less heavy?",
    "How can I support you right now?",
    "Try some slow, deliberate breaths.",
    "You are more than your stress.",
    "Let’s think of three things you’re grateful for.",
    "Even superstars need rest days.",
    "You’re not expected to do it all alone.",
    "Sometimes, laughing at a silly video helps.",
    "Stressful times don't last forever.",
    "What brings you a sense of relief?",
    "Let’s aim for progress, not perfection.",
    "Would venting about it for a bit help?",
    "Give yourself permission to step back.",
    "You’re a human being, not a machine.",
    "Remember to check in with your body’s needs.",
    "It’s enough to do your best."
]

# LONELY / ALONE / ISOLATION (50)
lonely_responses = [
    "You’re not as alone as you feel—I'm here for you.",
    "Would it help to talk about what’s making you feel isolated?",
    "Your feelings are valid.",
    "Even small connections count.",
    "Is there someone you could reach out to for a quick hello?",
    "Would a favorite book or movie help keep you company?",
    "It’s normal to feel lonely at times.",
    "Would you like to share your favorite memory?",
    "Pets, music, or nature can offer a sense of companionship.",
    "You matter to me.",
    "Solitude can be gentle, but too much feels heavy.",
    "You’re welcome here for as long as you need.",
    "Would sending a text to a friend help?",
    "Online communities count, too.",
    "What’s something you've always enjoyed doing alone?",
    "Let yourself be kind to you today.",
    "What would help you feel less alone right now?",
    "I appreciate your honesty.",
    "Small talk still matters.",
    "Would listening to calming music or a podcast help?",
    "Would journaling help you process your feelings?",
    "You’re braver than you believe.",
    "Is there a place—a café, park, or garden—where you feel connected?",
    "You can always message here when you need to.",
    "What’s one comfort you can give yourself right now?",
    "Your presence is valuable.",
    "It’s okay to crave connection.",
    "People care about you, even if it’s hard to see it.",
    "Would doodling or creating art help express things?",
    "You deserve to feel seen.",
    "Have you ever tried a new hobby to meet people?",
    "It’s okay to rest in your own company.",
    "Would joining a club or virtual meetup help?",
    "Connecting with yourself is valuable too.",
    "Would calling a family member feel comforting?",
    "Would writing a letter (even unsent) help?",
    "You are worthy of friendship and love.",
    "Would volunteering help you feel more connected?",
    "Feeling lonely isn’t your fault.",
    "Everyone feels alone sometimes.",
    "Let’s brainstorm ways to add connection to your day.",
    "If you need to talk, I’m always here.",
    "Honor your feelings; they’ll pass in time.",
    "You bring light to someone’s life, even if you can’t see it.",
    "Keep showing up, for yourself—it's enough.",
    "Would a pet or plant offer some company?",
    "Loneliness is a feeling, not a permanent state.",
    "Remember, you matter.",
    "I’m glad you reached out."
]

# OVERWHELMED / OVERWHELM (50)
overwhelmed_responses = [
    "Feeling overwhelmed is a sign you care deeply.",
    "Let's take it step by step.",
    "You don’t have to do everything right now.",
    "Would a break help clear your mind?",
    "It’s okay to pause and rest.",
    "Even a small task is still progress.",
    "Would it help to talk out what's on your plate?",
    "You’re doing more than enough.",
    "What’s something you can set aside today?",
    "Rest is a valid option.",
    "Would prioritizing your tasks make things clearer?",
    "You’re allowed to slow down.",
    "Let’s focus on just the next thing.",
    "Would a change of scenery help you reset?",
    "Try deep breathing or a short walk.",
    "You don’t have to carry it all alone.",
    "What would you say to a friend who felt this way?",
    "Being overwhelmed is honest and human.",
    "Would you feel better asking for support?",
    "Your best is all anyone can ask.",
    "List your concerns; we’ll tackle them one by one.",
    "Perfection isn’t required.",
    "Breaks help your brain process things.",
    "Can you let go of just one thing?",
    "You’re doing your best.",
    "Would focusing on what’s urgent help?",
    "Celebrate any little victories.",
    "Would some fun or laughter be a welcome break?",
    "You’re not alone in feeling this way.",
    "How can I support you?",
    "Would it help to delegate or postpone something?",
    "Even brief rest matters.",
    "Try to do one thing at a time.",
    "Breathe in, breathe out—start with that.",
    "Let’s make time for you, not just your tasks.",
    "Would turning off notifications help reduce stress?",
    "Saying ‘no’ to more is really saying ‘yes’ to yourself.",
    "Nobody can pour from an empty cup.",
    "Today doesn’t have to be perfect.",
    "Sometimes just getting by is enough.",
    "What’s been weighing on you most?",
    "Try a mini dance or stretch break.",
    "What would be the gentlest next step?",
    "You can get through this.",
    "Take as much time as you need.",
    "You’re important, with or without achievements.",
    "Some days, rest is winning.",
    "Would a comfort snack help?",
    "You matter, more than anything on your to-do list.",
    "Your pace is just right."
]

# ANGRY / ANGER (50)
angry_responses = [
    "Feeling angry is totally okay; it's a natural emotion.",
    "Would you like to talk about what made you upset?",
    "Anger is sometimes a signal that your boundaries matter.",
    "Try taking a few deep breaths together with me.",
    "Sometimes a walk or movement helps release built-up anger.",
    "It's okay to step back and give yourself time to cool down.",
    "Expressing anger safely is healthy.",
    "Do you want to talk, write, or even draw your feelings?",
    "It's okay if you don't want to talk about it right away.",
    "Anger doesn’t make you a bad person.",
    "Let’s focus on what you can control in this moment.",
    "Who or what are you feeling upset with today?",
    "It's normal to feel mad sometimes.",
    "Try to notice where you feel the anger in your body.",
    "Sometimes, anger hides sadness or fear underneath.",
    "Would releasing this feeling help right now?",
    "Is there a way to express it without harm?",
    "Journaling or scribbling can sometimes help.",
    "Would a pillow or stress ball help you vent safely?",
    "There’s no need to apologize for how you feel.",
    "If you could say anything to the person or thing that made you mad, what would it be?",
    "Let yourself cool off before reacting if you can.",
    "Your feelings are valid.",
    "It’s okay if anger comes and goes.",
    "Try not to judge yourself for feeling this way.",
    "What would help you feel calmer right now?",
    "Sometimes, a little humor can break the spell.",
    "You are not alone in being frustrated.",
    "Small things may trigger big anger, and that's okay.",
    "Is there something you wish could change about the situation?",
    "Are there other ways you’d like to process this?",
    "Talking to a supportive friend might help.",
    "Breathe in...and let some tension out.",
    "It’s okay to take a break from the situation.",
    "Would music or movement offer some relief?",
    "Let yourself feel and then let go, at your own pace.",
    "You are in charge of your reactions.",
    "Everyone gets angry sometimes — it's part of being human.",
    "Would giving yourself space help things feel easier?",
    "How do you usually soothe anger?",
    "What do you want most right now?",
    "Let’s find a way to bring you some peace.",
    "I'm here, no matter how strong your feelings are.",
    "Anger can be an invitation to care for yourself.",
    "Try to forgive yourself for any strong emotions.",
    "Is there an action you could safely take to release energy?",
    "Would you like a listening ear or advice?",
    "You can always return when you’re ready to talk.",
    "Take your time — I'm not judging.",
    "It's powerful that you can name your anger.",
    "You're doing great just by reaching out."
]

# HOPELESS / DESPAIR (50)
hopeless_responses = [
    "It’s tough feeling hopeless. I’m here for you.",
    "Even on the darkest days, the light can return.",
    "Would you like to talk about what’s weighing you down?",
    "Remember, feelings pass—even the deepest despair.",
    "You matter, even when you feel empty.",
    "Is there something that usually helps, even just a little?",
    "I believe hope can return, one gentle step at a time.",
    "Would it help to share your story?",
    "Let’s take today one gentle moment at a time.",
    "You’re not alone; I’m here whenever you want to talk.",
    "Is there anyone in your life you can lean on right now?",
    "What would make things feel even a bit lighter for you?",
    "Your courage to reach out matters.",
    "Even the smallest hope counts.",
    "It’s valid to feel this way; your feelings matter.",
    "Would it help to focus on a tiny good thing today?",
    "Hope can be fragile, but it’s still possible.",
    "No darkness is total, even if it feels that way.",
    "Try to rest if you can—the heart needs rest to heal.",
    "You are valued no matter how you’re feeling.",
    "It’s okay to cry or release emotions.",
    "Would gentle music or poetry offer comfort?",
    "Sometimes, hope is just a slow return of light.",
    "What’s one little thing you wish could change?",
    "Talk at your pace; I’ll listen.",
    "Feelings of despair don’t last forever.",
    "I believe in you, even when you don’t.",
    "What has helped you in hard times before?",
    "If the weight feels too much, reach out for extra support.",
    "Would shifting focus to a distraction help for a bit?",
    "You deserve care, especially on the hardest days.",
    "Sometimes, hope comes from places we don’t expect.",
    "Are there signs of hope or beauty where you are?",
    "Let’s look for a small spark together.",
    "Your presence is meaningful in this world.",
    "Tell me what brings you the tiniest comfort.",
    "Would repeating a gentle phrase offer a little solace?",
    "You are important, even if you can’t see it now.",
    "Tomorrow can bring something new.",
    "Can we imagine together a soft, safe space?",
    "What would you tell someone else feeling this way?",
    "You have survived hard days before.",
    "Hold on for now — I’ll stay with you.",
    "Even on low days, you’re worthy.",
    "Rest if you need; the world can wait.",
    "Would a positive memory help anchor you?",
    "Despair doesn’t define you.",
    "Let yourself breathe; that is enough for now.",
    "I care about what happens to you."
]

# TIRED / EXHAUSTED (50)
tired_responses = [
    "It's okay to feel tired – you deserve to rest.",
    "Rest is a basic need, not a luxury.",
    "Would a break or nap help replenish you?",
    "You’ve been carrying a lot; no wonder you feel exhausted.",
    "Take things slow; your pace is enough.",
    "Have you had a chance to sleep or relax today?",
    "You’re allowed to say ‘no’ so you can recharge.",
    "Gentle movement or stretches might help your body relax.",
    "It’s strong to admit you need rest.",
    "Would you like tips for winding down?",
    "You don't have to be productive to be valuable.",
    "Let your mind and body recover.",
    "Sometimes, just sitting quietly can help.",
    "Would a soothing drink, like tea, help you unwind?",
    "Everyone needs breaks.",
    "Try closing your eyes for a minute and just breathing.",
    "Your energy will return with time.",
    "Sleep can be medicine for the soul.",
    "If you can, let yourself slow your schedule today.",
    "Forgive yourself for needing a pause.",
    "You’ve earned a rest.",
    "Sometimes, exhaustion means it’s time for real self-care.",
    "Could dimming lights or turning off screens help?",
    "Would a warm bath or shower help you relax?",
    "You’re not alone in feeling wiped out.",
    "Would journaling or brain-dumping your thoughts help?",
    "Nothing lasts forever—your tiredness will pass too.",
    "It’s okay not to have energy for everything.",
    "You’re still worthy, even without accomplishments.",
    "Be kind to your tired self.",
    "How can you make your environment a little more restful?",
    "Would nature sounds or gentle music help you rest?",
    "You deserve a soft pillow and some quiet time.",
    "Sometimes, exhaustion hints at deeper needs.",
    "Taking care of yourself is powerful.",
    "Know that it’s okay to tune out for a while.",
    "Try to let go of what isn’t urgent.",
    "Would you prefer encouragement or just a quiet space?",
    "I’m glad you’re here, even if you’re weary.",
    "Do you want to talk about why you’re feeling so tired?",
    "Your only job now is rest.",
    "You’re making it through, one slow step at a time.",
    "Thank you for sharing your feelings.",
    "You can return here whenever you want.",
    "Would a few deep breaths help you recharge?",
    "You owe yourself gentleness.",
    "Take the day slow—it's perfectly okay.",
    "I believe your energy will return in time.",
    "You’re allowed to rest — it’s good for you."
]

# SCARED / AFRAID / FEAR (50)
scared_responses = [
    "It’s okay to be scared. Your feelings are real.",
    "Would it help to talk about your fears?",
    "You're safe here with me.",
    "Fear can be powerful, but so is reaching out.",
    "Naming your fears out loud can make them less strong.",
    "What is making you feel afraid or uneasy?",
    "Try breathing deeply—you're in a safe space.",
    "Would focusing on something familiar help comfort you?",
    "Even brave people get scared sometimes.",
    "Let’s focus on what you can control.",
    "You’re not alone in feeling fear.",
    "What helps you feel grounded or safe?",
    "Would a calming image or memory help?",
    "Is there anything that usually brings you comfort?",
    "Let someone you trust know how you’re feeling.",
    "It's okay to seek reassurance.",
    "Would soft lighting or blankets help you feel cozy?",
    "Give yourself time—there’s no rush to stop being scared.",
    "Remind yourself: the feeling of fear will pass.",
    "Would distracting yourself with something fun help?",
    "Small comfort routines can help manage fear.",
    "Talk to me as much as you want—I’ll listen.",
    "You’re allowed to be afraid and still be strong.",
    "No one expects you to be unbreakably brave.",
    "If it helps, hold onto something soft or familiar.",
    "You matter, scared feelings and all.",
    "Sometimes, fear is your mind asking for protection.",
    "Would guided imagery help you feel calm?",
    "What do you wish someone would say to comfort you?",
    "You can work through fear step by step.",
    "Has breathing slowly helped before?",
    "Would hearing a reassuring quote help?",
    "Listening to a comforting song might soothe you.",
    "Sometimes, being scared lets you learn something new.",
    "Thank you for sharing; sharing makes you braver.",
    "Let’s create a mini action plan for what scares you.",
    "Would you like to hear how others cope with fear?",
    "Trust that the feeling will fade eventually.",
    "You’ve made it through scary times before.",
    "Your courage brought you here today.",
    "Would looking at trusted photos or messages calm you?",
    "If your fear grows, reach out to a loved one in your life.",
    "No feeling is permanent.",
    "You’re not judged for being afraid.",
    "I'm here for you till you feel safer.",
    "Let’s take it one moment at a time.",
    "Your fear matters."
]

# LOST / EMPTY / POINTLESS (50)
lost_responses = [
    "It’s normal to feel lost sometimes, even if it’s hard.",
    "Would you like to talk about what’s making you feel directionless?",
    "Your journey still matters.",
    "Small steps still move you forward.",
    "Feeling empty isn’t forever.",
    "Is there anything that gives you a sense of purpose?",
    "The hardest journeys can reveal the brightest destinations.",
    "Would a simple routine help create structure today?",
    "You are valuable, even when you feel adrift.",
    "Sometimes, doing something kind for yourself is a good start.",
    "It's okay not to know your next step.",
    "Would setting a very small goal for today help?",
    "You're not defined by your confusion.",
    "Would writing your feelings down help make sense of them?",
    "You can always begin again.",
    "Let yourself feel these emotions—they will shift in time.",
    "Would you like inspiration or just a friendly ear?",
    "Have you felt this way before—and what helped last time?",
    "You are enough even without a clear plan.",
    "Gentle activities can help fill emptiness.",
    "What’s something small that brings you comfort?",
    "Remember, every life has ebbs and flows.",
    "Finding meaning can take time—you’re not behind.",
    "Would you like to brainstorm ways to bring back meaning?",
    "Trying something new, no matter how small, might help.",
    "You're worthwhile just by being here.",
    "If you want, share a favorite memory.",
    "Talk to yourself like you would talk to a friend.",
    "Emptiness can be a sign it’s time to rest and reflect.",
    "Would making or creating something bring joy today?",
    "Structure, like eating at the same time, can help.",
    "You have a place in this world.",
    "Would imagining a peaceful space help you feel less adrift?",
    "Take a break; you can return whenever you want.",
    "Your thoughts and feelings are important.",
    "One small act of self-kindness is enough.",
    "It's okay if you don’t have it figured out.",
    "Would connecting with someone help bring some clarity?",
    "You can always find support here.",
    "Empty patches are just that—patches, not forever.",
    "I care about what happens to you.",
    "Let's brainstorm together if you want.",
    "Start with what’s right in front of you.",
    "Try to trust that feelings shift and change."
]

# UNMOTIVATED / STUCK (50)
unmotivated_responses = [
    "Everyone feels unmotivated sometimes; it's part of being human.",
    "Would you like to talk about what's making you feel stuck?",
    "Small accomplishments count, even on low-energy days.",
    "Try to set the bar as low as possible today—tiny wins matter.",
    "Taking a break isn’t the same as giving up.",
    "What task feels like a mountain today?",
    "Is your lack of motivation tied to stress or something else?",
    "You can restart at any time.",
    "Is there something you usually enjoy that feels doable?",
    "Let’s set just one single goal for now.",
    "You don’t have to be productive every day.",
    "Would music or movement help shift your energy?",
    "Sometimes, going slow is the bravest choice.",
    "It's okay to leave things unfinished.",
    "Would kind words to yourself help?",
    "Just planning to try is enough for now.",
    "What usually sparks your energy?",
    "Would a change of perspective or scenery help?",
    "You made it here—even that’s a step.",
    "Some days are for resting, not running.",
    "Is there a gentle activity you could start with?",
    "Your best looks different every day.",
    "Let someone know how you’re feeling if you want to.",
    "Would encouragement or just a listening ear help?",
    "Would a mini reward help motivate you?",
    "Try not to compare yourself to others.",
    "It’s okay to do less.",
    "Sometimes motivation returns slowly.",
    "Small wins count, too.",
    "You’re enough just by trying.",
    "Is there a gentle affirmation you’d like to try?",
    "Doing your best is progress, even if it’s hard to see.",
    "You’re not your productivity.",
    "Let yourself rest if you need to.",
    "Try a new song or video for a burst of energy.",
    "Having off days is part of everyone’s journey.",
    "Would creative expression help you feel unstuck?",
    "You’re not alone in feeling this way.",
    "You can always try again later.",
    "Would a pep-talk help right now?",
    "I've got your back.",
    "Don’t forget to breathe and be kind to yourself.",
    "You are not falling behind.",
    "Even the smallest step is a victory."
]

# GRIEF / GRIEVING (30)
grief_responses = [
    "Grief is difficult—I'm here to listen if you'd like to share.",
    "Would it help to talk about your loved one or your loss?",
    "There is no right or wrong way to grieve.",
    "Take all the time you need to heal.",
    "Emotions come in waves—let them come and go.",
    "It’s okay to laugh, cry, or feel both at once.",
    "Would sharing a memory bring comfort?",
    "Your loved one would want you to take care of yourself.",
    "Are there comforting rituals that help you remember them?",
    "You don’t have to grieve alone.",
    "Every feeling is valid in grief.",
    "Would photos, letters, or music help process these feelings?",
    "Tears can be healing.",
    "Sometimes, grief doesn’t make sense—be gentle with yourself.",
    "What do you wish you could say to your loved one?",
    "Rest and nourishment are important in grief.",
    "Would writing a letter to your loved one help?",
    "Keeping their memory alive in little ways is meaningful.",
    "You're not bothering anyone by needing support.",
    "Grief takes its own time.",
    "Would it help to honor your loved one with a candle or walk?",
    "It’s okay if it still hurts.",
    "Even sad memories are part of healing.",
    "Let yourself feel everything, without judgment.",
    "No one grieves in exactly the same way.",
    "I care about the pain you’re carrying.",
    "Would talking about the future bring any peace?",
    "A small comfort, like a warm blanket, can help.",
    "Remember, loved ones are never truly gone from your heart.",
    "Thank you for sharing your feelings here."
]

# PANIC / PANIC ATTACK (30)
panic_responses = [
    "Try slow, deep breaths: in for 4, out for 6.",
    "I’m here with you—panic can’t hurt you, even if it feels scary.",
    "This moment will pass.",
    "Would describing what you’re experiencing help?",
    "Place your hand on your chest and focus on your breath.",
    "Try to feel your feet on the ground.",
    "It’s okay to sit or lie down until you feel steadier.",
    "Would cool water on your wrists help calm you?",
    "Name five things you can see.",
    "Talk through your sensations—sometimes this helps.",
    "Try not to fight the feeling—let it move through you.",
    "Have you had panic before? What helped then?",
    "Would you like to hear a calming affirmation?",
    "You are not alone; I'm here until it passes.",
    "Your breath is your anchor—focus on that.",
    "Panic attacks end, even if it takes a while.",
    "Would closing your eyes and counting help?",
    "You’re safe, right now, in this space.",
    "Sometimes, holding something cool or soft helps.",
    "Would gentle movement like rocking comfort you?",
    "It’s okay if you can only focus on breathing.",
    "Being patient with yourself helps, too.",
    "Remind yourself: this is just anxiety, it will go away.",
    "Would you like to talk about what may have triggered this?",
    "There’s no rush to feel okay.",
    "Each breath is a step closer to calm.",
    "Try humming to regulate your breathing.",
    "Be proud for reaching out in a hard moment.",
    "After the panic fades, be gentle with yourself.",
    "Any step toward comfort is enough."
]

# WORTHLESS / NOT ENOUGH (30)
worthless_responses = [
    "You are valuable, just as you are.",
    "Feeling this way doesn't make it true.",
    "Would it help to list your strengths together?",
    "Your presence makes a difference.",
    "Self-worth doesn’t depend on achievements.",
    "Would a gentle affirmation help?",
    "You have reasons to be proud, even if they're small.",
    "Everyone matters, including you.",
    "What would you tell a friend feeling like this?",
    "Mistakes don’t erase your worth.",
    "I'm always here to remind you—you matter.",
    "It’s okay to acknowledge if you need support.",
    "You're important, even when you can't see it.",
    "Try to be as kind to yourself as you are to others.",
    "Who would miss you if you weren’t here?",
    "Let’s list three things you’re grateful for within yourself.",
    "Your best is enough.",
    "You can try again tomorrow.",
    "Tiny steps count as progress.",
    "You’re not defined by your struggles.",
    "Would you like some encouragement?",
    "You're needed, even if you don’t always feel it.",
    "This feeling will pass, even if it feels strong now.",
    "Would a comforting routine help today?",
    "Let yourself be human—you are enough.",
    "Thank you for talking—it takes courage.",
    "Would listening to a positive song remind you of your value?",
    "I'm glad you’re here.",
    "You are worthy of love and acceptance.",
    "Be gentle with yourself today."
]

# GUILT / GUILTY (30)
guilt_responses = [
    "Guilt is a sign you care, but don’t let it overwhelm you.",
    "Would talking through what happened help?",
    "Making mistakes is human.",
    "Self-forgiveness is healing.",
    "You did the best you could at the time.",
    "Is there any way to make amends?",
    "Small actions toward change matter.",
    "Would a letter to yourself offer new perspective?",
    "Carrying guilt alone is heavy—let’s share the load.",
    "Try to hold yourself with compassion.",
    "You are not alone in this feeling.",
    "Would it help to apologize or reach out to someone?",
    "Perfection isn’t possible; effort is enough.",
    "You still deserve kindness.",
    "Learning from mistakes brings healing.",
    "Are you holding yourself to a higher standard than others?",
    "Let yourself feel and then release the guilt.",
    "Small acts of repair are valuable.",
    "Guilt doesn’t erase your worth.",
    "Change happens step by step.",
    "Thank you for trusting me with your story.",
    "Atonement means growth, not punishment.",
    "Would writing out your feelings help lighten the burden?",
    "You can make new choices each day.",
    "Self-compassion matters too.",
    "Growth comes from reflection, not self-hate.",
    "Your story isn’t over yet.",
    "You are allowed to learn and heal.",
    "Would talking more bring clarity?",
    "Mistakes do not make you unlovable."
]

# SHAME / ASHAMED (30)
shame_responses = [
    "You are worthy of love, even when you feel shame.",
    "Would sharing what happened help you heal?",
    "Everyone trips up—nobody is perfect.",
    "Shame is a heavy load—you don’t have to hold it alone.",
    "Mistakes do not define you.",
    "Would self-kindness feel possible today?",
    "Try to separate who you are from what happened.",
    "Talking is a step toward letting shame go.",
    "Thank you for trusting me—it takes courage.",
    "Compassion is healing. You deserve it.",
    "Would it help to hear a story about someone who overcame shame?",
    "Shame fades with time and openness.",
    "You have overcome challenges before.",
    "Your feelings are valid, but don't have to control you.",
    "Would it help to write about your feelings?",
    "Imagine how you’d comfort a friend in your place.",
    "Light can reach every part of you.",
    "Would forgiveness—of self or others—feel helpful?",
    "You still belong here.",
    "Your past does not cancel out your goodness.",
    "Being honest with yourself is powerful.",
    "You are more than any mistake.",
    "Each day is a chance to begin again.",
    "Healing happens bit by bit.",
    "You are not alone with these feelings.",
    "You’re brave for showing up.",
    "Are you carrying judgments that don’t belong to you?",
    "You are more than what you've been through.",
    "Would a warm bath or comforting environment help soften self-judgment?",
    "You can always start again."
]

# Fallbacks for generic/unmatched situations
fallback_responses = [
    "That's interesting! Would you like to talk more about how that makes you feel?",
    "Thank you for sharing. What would you like to discuss next?",
    "I'm here to listen to anything you'd like to share.",
    "Tell me more about that!",
    "Would you like support with your feelings, or just someone to listen?"
]

# Example: contextual/branching follow-ups (template)
topic_followups = {
    "movie": [
        "That sounds like a fun movie!",
        "Movies can really be comforting! Do you watch it often?",
        "I love hearing about people's favorites. Thanks for sharing!"
    ],
    "food": [
        "Yum! That sounds delicious.",
        "Food can be so comforting. Nice choice!",
        "Love that! Do you cook it yourself?"
    ],
    "music": [
        "That's a great song! Does it bring back memories?",
        "Music can change the mood instantly.",
        "Thanks for sharing! Why do you love it?"
    ]
}

def get_emotion_response(emotion):
    # Map emotion to their lists
    responses = {
        'anxious': anxious_responses,
        'anxiety': anxious_responses,
        'stressed': stressed_responses,
        'stress': stressed_responses,
        'lonely': lonely_responses,
        'alone': lonely_responses,
        'isolation': lonely_responses,
        'overwhelmed': overwhelmed_responses,
        'overwhelm': overwhelmed_responses,
        'angry': angry_responses,
        'anger': angry_responses,
        'hopeless': hopeless_responses,
        'despair': hopeless_responses,
        'tired': tired_responses,
        'exhausted': tired_responses,
        'scared': scared_responses,
        'afraid': scared_responses,
        'fear': scared_responses,
        'lost': lost_responses,
        'empty': lost_responses,
        'pointless': lost_responses,
        'unmotivated': unmotivated_responses,
        'stuck': unmotivated_responses,
        'grief': grief_responses,
        'grieving': grief_responses,
        'panic': panic_responses,
        'panic attack': panic_responses,
        'worthless': worthless_responses,
        'not enough': worthless_responses,
        'guilt': guilt_responses,
        'guilty': guilt_responses,
        'shame': shame_responses,
        'ashamed': shame_responses
    }
    resp_list = responses.get(emotion)
    if resp_list:
        return random.choice(resp_list)
    return random.choice(fallback_responses)

def get_followup_response(topic):
    # For pending topics, like after the bot asks "What's your favorite movie?"
    repo = topic_followups.get(topic)
    if repo:
        return random.choice(repo)
    return random.choice(fallback_responses)

def respond(user_input):
    text = user_input.lower()
    if "hello" in text or "hi" in text or "hey" in text:
        return random.choice(greetings)
    elif "bye" in text or "goodbye" in text or "see you" in text:
        return random.choice(goodBye)
    elif "sad" in text or "depressed" in text:
        return random.choice([
            "I'm sorry to hear that but now you have me, lets make you feel better",
            "Don't be sad, I'm here to help you!"
        ])
    elif "anxious" in text or "grief" in text:
        return "Don't worry, you can talk to me about it"
    elif "help" in text or "support" in text:
        return "Don't worry you have me here"
    elif "talk" in text or "speak" in text:
        return "I'm here to listen, tell me what's on your mind"
    else:
        return random.choice(default_response)

# -- Helpers for session control --

def set_session(username=None):
    """Set the session timer and session['username']."""
    if username:
        duration = USER_SESSION_MINUTES
        session['username'] = username
        session['guest'] = False
    else:
        duration = GUEST_SESSION_MINUTES
        session['username'] = None
        session['guest'] = True
    session['start_time'] = datetime.utcnow().isoformat()
    session['expire_time'] = (datetime.utcnow() + timedelta(minutes=duration)).isoformat()
    session.permanent = True  # So browser remembers the session between requests

def session_remaining():
    expire_time = session.get('expire_time')
    if not expire_time:
        return 0
    expire_dt = datetime.fromisoformat(expire_time)
    delta = expire_dt - datetime.utcnow()
    return max(int(delta.total_seconds()), 0)

def is_logged_in():
    return session.get('username') is not None and not session.get("guest", True)

# -- Routes --

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/home.html")
def index():
    return render_template("home.html")

@app.route("/chatcopy.html")
def chatcopy():
    return render_template("chatcopy.html")

@app.route("/features.html")
def feautures():
    return render_template("features.html")

@app.route("/history.html")
def history():
    return render_template("history.html")

@app.route("/homecopy.html")
def homecopy():
    return render_template("homecopy.html")

@app.route("/loginpage.html")
def loginpage():
    return render_template("loginpage.html")

@app.route("/chat.html")
def chat():
    return render_template("chat.html")

@app.route("/contact.html")
def contact():
    return render_template("contact.html")

@app.route("/offline.html")
def offline():
    return render_template("offline.html")

# Users API - login
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"success": False, "error": "username and password required"}), 400

    users = load_users()
    user = users.get(username)
    if user:
        if not check_password_hash(user["password_hash"], password):
            return jsonify({"success": False, "error": "incorrect password"}), 401
    else:
        users[username] = {
            "password_hash": generate_password_hash(password),
            "created": datetime.utcnow().isoformat()
        }
    save_users(users)
    set_session(username=username)
    return jsonify({"success": True, "username": username, "expires_in_minutes": USER_SESSION_MINUTES})

# Session status
@app.route("/api/status")
def api_status():
    remaining = session_remaining()
    if is_logged_in():
        return jsonify({"logged_in": True, "username": session["username"], "remaining_seconds": remaining, "guest": False})
    elif session.get("guest", False) and remaining > 0:
        return jsonify({"logged_in": False, "guest": True, "remaining_seconds": remaining})
    else:
        return jsonify({"logged_in": False})

# Start or continue guest session (use this endpoint for guests before chat)
@app.route("/api/guest", methods=["POST"])
def api_guest():
    set_session(username=None)
    return jsonify({"success": True, "expires_in_minutes": GUEST_SESSION_MINUTES})

# Chat messages
@app.route("/api/chat", methods=["POST"])
def api_chat():
    if not session.get("expire_time"):
        # No session, treat as guest
        set_session(username=None)
    remaining = session_remaining()
    if remaining <= 0:
        session.clear()
        return jsonify({"success": False, "error": "session_expired"}), 403
    data = request.get_json() or {}
    msg = data.get("message", "").strip()
    if not msg:
        return jsonify({"success": False, "error": "empty message"}), 400
    reply = respond(msg)
    # Save chat to history if logged in
    if is_logged_in():
        add_to_history(session['username'], msg, reply)
    return jsonify({"success": True, "reply": reply, "remaining_seconds": remaining, "guest": session.get("guest", False)})

# Chat history for logged in user
@app.route("/api/history", methods=["GET"])
def api_history():
    if not is_logged_in():
        return jsonify({"success": False, "error": "not logged in"}), 401
    history = load_history()
    user_history = history.get(session['username'], [])
    return jsonify({"success": True, "history": user_history})

# To serve manifest and icons (keep at root url)
@app.route('/<path:filename>')
def serve_static_files(filename):
    # Allows things like /manifest.json or /icon-192.png to still work
    return send_from_directory('static', filename)


if __name__ == '__main__':
    # Init files
    if not os.path.exists(USER_DB):
        with open(USER_DB, "w") as f:
            json.dump({}, f)
    if not os.path.exists(HISTORY_DB):
        with open(HISTORY_DB, "w") as f:
            json.dump({}, f)
    app.run(debug=True)