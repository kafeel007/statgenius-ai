"""StatGenius AI - FastAPI backend. Run: uvicorn main:app --reload --port 8000  (from the backend folder)"""
import os, uuid, hmac, hashlib, base64, time, secrets, logging
from datetime import datetime, timedelta, date
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
import database, models, schemas, assessment as A, competency as C, quiz_generator as QG, learning_engine as LE
import document_processor as DP, ai_service, igot_demo, stats_lab
from models import *

BASE = os.path.dirname(os.path.abspath(__file__)); UPLOADS = os.path.join(BASE, "uploads"); os.makedirs(UPLOADS, exist_ok=True)
SECRET = os.getenv("SECRET_KEY") or secrets.token_hex(32)  # set SECRET_KEY in .env to keep sessions across restarts
log = logging.getLogger("statgenius")
app = FastAPI(title="StatGenius AI", version="1.0", description="AI-powered statistical learning assistant (prototype)")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000").split(",")],
                   allow_methods=["*"], allow_headers=["*"])

# ---------- auth ----------
def hash_pw(pw, salt=None):
    salt = salt or secrets.token_hex(16); h = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200_000).hex(); return f"{salt}${h}"
def check_pw(pw, stored):
    salt, _ = stored.split("$"); return hmac.compare_digest(hash_pw(pw, salt), stored)
def make_token(uid):
    p = f"{uid}:{int(time.time()) + 7*86400}"; s = hmac.new(SECRET.encode(), p.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{p}:{s}".encode()).decode()
def current_user(authorization: str = Header(default=""), db: Session = Depends(database.get_db)):
    try:
        uid, exp, sig = base64.urlsafe_b64decode(authorization.replace("Bearer ", "").encode()).decode().split(":")
        good = hmac.new(SECRET.encode(), f"{uid}:{exp}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, good) or int(exp) < time.time(): raise ValueError
    except Exception: raise HTTPException(401, "Please sign in")
    u = db.get(User, int(uid))
    if not u: raise HTTPException(401, "Please sign in")
    return u
def user_out(u): return dict(id=u.id, name=u.name, email=u.email, role=u.role, goals=u.goals, thresholds=u.thresholds, is_demo=u.is_demo)

# ---------- data helpers ----------
def scores_of(db, uid): return {c.topic: c.score for c in db.query(Competency).filter_by(user_id=uid)}
def set_score(db, uid, topic, score):
    c = db.query(Competency).filter_by(user_id=uid, topic=topic).first()
    if c: c.score, c.updated = score, datetime.utcnow()
    else: db.add(Competency(user_id=uid, topic=topic, score=score))
def log_activity(db, uid, topic, kind, minutes=0, detail=""):
    db.add(Activity(user_id=uid, topic=topic, kind=kind, minutes=minutes, detail=detail))
def history_by_topic(db, uid):
    h = {}
    for a in db.query(AssessmentAttempt).filter_by(user_id=uid).order_by(AssessmentAttempt.created):
        for t, v in a.topic_scores.items(): h.setdefault(t, []).append(v["pct"])
    return h
def get_doc(db, u, did):
    d = db.get(Document, did)
    if not d or d.user_id != u.id: raise HTTPException(404, "Document not found")
    return d

# ---------- seed / init ----------
def seed(db):
    if not db.query(Question).count():
        for q in A.BANK: db.add(Question(id=q["id"], topic=q["topic"], difficulty=q["difficulty"], text=q["question"], options=q["options"], correct=q["correct"]))
    if not db.query(User).filter_by(email="demo@statgenius.local").first():
        u = User(email="demo@statgenius.local", password_hash=hash_pw(secrets.token_hex(8)), name="Demo Learner (sample data)",
                 role="Statistical Officer (demo)", goals=["Sampling Techniques", "Hypothesis Testing"], is_demo=True)
        db.add(u); db.flush()
        prev = {"Descriptive Statistics": 70, "Probability": 40, "Sampling Techniques": 25, "Statistical Inference": 55, "Hypothesis Testing": 50,
                "Regression Analysis": 60, "Data Visualization": 65, "Survey Methodology": 45, "Data Quality and Validation": 60}
        db.add(AssessmentAttempt(user_id=u.id, created=datetime.utcnow() - timedelta(days=14), accuracy=round(sum(prev.values()) / 9, 1), correct=0, total=0,
                                 topic_scores={t: {"correct": 0, "total": 0, "pct": v} for t, v in prev.items()}, answers=[], is_sample=True))
        for t, v in prev.items(): set_score(db, u.id, t, v)
        for d, (t, k, m) in enumerate([("Descriptive Statistics", "notes", 20), ("Probability", "practice", 15), ("Data Visualization", "practice", 15)]):
            db.add(Activity(user_id=u.id, topic=t, kind=k, minutes=m, detail="sample data", created=datetime.utcnow() - timedelta(days=2 - d // 2)))
    db.commit()
def init_db():
    database.Base.metadata.create_all(database.engine)
    with database.SessionLocal() as db: seed(db)
@app.on_event("startup")
def _startup(): init_db()

# ---------- auth endpoints ----------
@app.post("/api/auth/register")
def register(b: schemas.Register, db: Session = Depends(database.get_db)):
    if db.query(User).filter_by(email=b.email.lower()).first(): raise HTTPException(409, "Email already registered")
    u = User(email=b.email.lower(), password_hash=hash_pw(b.password), name=b.name, role=b.role, goals=b.goals); db.add(u); db.commit()
    return dict(token=make_token(u.id), user=user_out(u))
@app.post("/api/auth/login")
def login(b: schemas.Login, db: Session = Depends(database.get_db)):
    u = db.query(User).filter_by(email=b.email.lower()).first()
    if not u or u.is_demo or not check_pw(b.password, u.password_hash): raise HTTPException(401, "Invalid email or password")
    return dict(token=make_token(u.id), user=user_out(u))
@app.post("/api/auth/demo")
def demo_login(db: Session = Depends(database.get_db)):
    u = db.query(User).filter_by(is_demo=True).first(); return dict(token=make_token(u.id), user=user_out(u), notice="Demo account with SAMPLE data")
@app.get("/api/me")
def me(u: User = Depends(current_user)): return user_out(u)
@app.put("/api/me/thresholds")
def set_thresholds(b: schemas.Thresholds, u: User = Depends(current_user), db: Session = Depends(database.get_db)):
    try: u.thresholds = C.check_thresholds(b.model_dump())
    except ValueError as e: raise HTTPException(422, str(e))
    db.commit(); return u.thresholds
@app.get("/api/status")
def status(): return dict(ai_available=ai_service.available(), mode="AI" if ai_service.available() else "demo", igot=igot_demo.INTEGRATION_MODE)

# ---------- assessment ----------
@app.get("/api/assessment/questions")
def questions(per_topic: int = 3, u: User = Depends(current_user)):
    per_topic = max(1, min(per_topic, 3)); return [A.public(q) for q in A.select_questions(per_topic)]
@app.post("/api/assessment/submit")
def submit(b: schemas.AssessmentSubmit, u: User = Depends(current_user), db: Session = Depends(database.get_db)):
    try: g = A.grade([a.model_dump() for a in b.answers])
    except ValueError as e: raise HTTPException(422, str(e))
    prev = scores_of(db, u.id)
    for t in g["topic_scores"]:  # follow-up credit if practice was done for this topic earlier
        if db.query(Activity).filter_by(user_id=u.id, topic=t, kind="practice").first() and not db.query(Activity).filter_by(user_id=u.id, topic=t, kind="followup").first():
            log_activity(db, u.id, t, "followup", 10, "assessment")
    db.add(AssessmentAttempt(user_id=u.id, accuracy=g["accuracy"], correct=g["correct"], total=g["total"], topic_scores=g["topic_scores"], answers=g["results"]))
    for t, v in g["topic_scores"].items(): set_score(db, u.id, t, v["pct"])
    log_activity(db, u.id, "Assessment", "assessment", max(5, g["total"]), f"{g['correct']}/{g['total']}")
    db.commit(); cur = scores_of(db, u.id)
    return dict(g, report=C.gap_report({t: v["pct"] for t, v in g["topic_scores"].items()}, u.thresholds), insights=C.confidence_insights(g["results"]),
                comparison=C.compare(prev, {t: v["pct"] for t, v in g["topic_scores"].items()}),
                review=[dict(question_id=r["question_id"], question=A.BY_ID[r["question_id"]]["question"], options=A.BY_ID[r["question_id"]]["options"], **{k: r[k] for k in ("selected", "correct_index", "is_correct")}) for r in g["results"]])
@app.get("/api/competency/report")
def report(u: User = Depends(current_user), db: Session = Depends(database.get_db)):
    sc = scores_of(db, u.id); hist = db.query(AssessmentAttempt).filter_by(user_id=u.id).order_by(AssessmentAttempt.created.desc()).all()
    last = hist[0] if hist else None; prev = {t: v["pct"] for t, v in hist[1].topic_scores.items()} if len(hist) > 1 else {}
    return dict(report=C.gap_report(sc, u.thresholds), overall=C.overall(sc), comparison=C.compare(prev, sc) if prev else [],
                insights=C.confidence_insights(last.answers) if last else [], disclaimer="Assessment-based scores from short quizzes; recommendations are rule-based/AI suggestions, not a measure of professional competency.")

# ---------- documents / notes / quiz ----------
@app.post("/api/documents/upload")
async def upload(file: UploadFile = File(...), u: User = Depends(current_user), db: Session = Depends(database.get_db)):
    data = await file.read(DP.MAX_BYTES + 1)
    try: DP.validate_pdf_bytes(data, file.filename or ""); pages = DP.extract_pages(data)
    except DP.DocumentError as e: raise HTTPException(422, str(e))
    stored = uuid.uuid4().hex + ".pdf"
    with open(os.path.join(UPLOADS, stored), "wb") as f: f.write(data)
    d = Document(user_id=u.id, filename=os.path.basename(file.filename)[:200], stored_name=stored, pages=pages, topics=QG.detect_topics(pages)); db.add(d); db.commit()
    return dict(id=d.id, filename=d.filename, page_count=len(pages), topics=d.topics, preview=DP.preview(pages))
@app.post("/api/documents/sample")
def use_sample(u: User = Depends(current_user), db: Session = Depends(database.get_db)):
    path = os.path.join(BASE, "sample_data", "sampling_basics.pdf")
    data = open(path, "rb").read(); pages = DP.extract_pages(data)
    d = Document(user_id=u.id, filename="sampling_basics.pdf (SAMPLE)", stored_name="sample", pages=pages, topics=QG.detect_topics(pages)); db.add(d); db.commit()
    return dict(id=d.id, filename=d.filename, page_count=len(pages), topics=d.topics, preview=DP.preview(pages))
@app.post("/api/notes/generate")
def notes(b: schemas.NotesReq, u: User = Depends(current_user), db: Session = Depends(database.get_db)):
    d = get_doc(db, u, b.document_id); n = QG.generate_notes([tuple(p) for p in d.pages])
    if n["topics"]: log_activity(db, u.id, n["topics"][0], "notes", 15, d.filename); db.commit()
    return n
@app.post("/api/quiz/generate")
def quiz_generate(b: schemas.QuizReq, u: User = Depends(current_user), db: Session = Depends(database.get_db)):
    pages = [tuple(p) for p in get_doc(db, u, b.document_id).pages] if b.document_id else []
    try: qs = QG.generate_quiz(pages, b.topic, b.n, b.difficulty, b.format)
    except ValueError as e: raise HTTPException(500, str(e))
    topic = b.topic if b.topic != "Any" else (qs[0]["topic"] if qs else "Any")
    q = Quiz(user_id=u.id, document_id=b.document_id, topic=topic, difficulty=b.difficulty, questions=qs); db.add(q); db.commit()
    return dict(quiz_id=q.id, topic=topic, questions=[QG.public_question(x) for x in qs])
@app.post("/api/quiz/{quiz_id}/submit")
def quiz_submit(quiz_id: int, b: schemas.QuizSubmit, u: User = Depends(current_user), db: Session = Depends(database.get_db)):
    q = db.get(Quiz, quiz_id)
    if not q or q.user_id != u.id: raise HTTPException(404, "Quiz not found")
    if db.query(QuizAttempt).filter_by(quiz_id=q.id).first(): raise HTTPException(409, "Quiz already submitted")
    res = []
    for x in q.questions:
        given = b.answers.get(str(x["id"])); ok = QG.check_answer(x, given)
        shown = x["options"][x["answer"]] if x["type"] in ("mcq", "tf") else x["answer"]
        res.append(dict(id=x["id"], question=x["question"], topic=x["topic"], type=x["type"], is_correct=ok, given=given,
                        given_text=(x["options"][given] if x["type"] in ("mcq", "tf") and isinstance(given, int) and 0 <= given < len(x["options"]) else given),
                        correct_answer=shown, explanation=x["explanation"], source=x.get("source")))
    s = sum(r["is_correct"] for r in res); acc = round(100 * s / len(res), 1)
    db.add(QuizAttempt(user_id=u.id, quiz_id=q.id, score=s, total=len(res), accuracy=acc, topic=q.topic))
    topics = {}
    for r in res: topics.setdefault(r["topic"], []).append(r["is_correct"])
    for t, v in topics.items():
        if t in A.TOPICS and len(v) >= 2:  # blend practice into the competency profile (needs >=2 items)
            set_score(db, u.id, t, C.blend(scores_of(db, u.id).get(t), 100 * sum(v) / len(v)))
    log_activity(db, u.id, q.topic, "practice", 15, f"quiz {s}/{len(res)}"); db.commit()
    nxt = LE.build_path(scores_of(db, u.id), {(a.topic, a.kind) for a in db.query(Activity).filter_by(user_id=u.id)}, u.thresholds, u.goals, history_by_topic(db, u.id))["next"]
    return dict(score=s, total=len(res), accuracy=acc, results=res, next_step=nxt)

@app.post("/api/mistake/explain")
def explain(b: schemas.MistakeReq, u: User = Depends(current_user), db: Session = Depends(database.get_db)):
    if b.source == "assessment":
        q = A.BY_ID.get(b.question_id)
        if not q: raise HTTPException(404, "Question not found")
        sel = q["options"][b.selected] if isinstance(b.selected, int) and 0 <= b.selected < len(q["options"]) else "(no answer)"
        topic, correct, text, expl, concept, bid = q["topic"], q["options"][q["correct"]], q["question"], q["explanation"], q["concept"], q["id"]
    else:
        qz = db.get(Quiz, b.quiz_id or 0)
        if not qz or qz.user_id != u.id: raise HTTPException(404, "Quiz not found")
        if not db.query(QuizAttempt).filter_by(quiz_id=qz.id).first(): raise HTTPException(403, "Submit the quiz before requesting explanations")
        q = next((x for x in qz.questions if x["id"] == b.question_id), None)
        if not q: raise HTTPException(404, "Question not found")
        isopt = q["type"] in ("mcq", "tf")
        sel = q["options"][b.selected] if isopt and isinstance(b.selected, int) and 0 <= b.selected < len(q["options"]) else (b.selected if b.selected not in (None, "") else "(no answer)")
        topic, correct, text, expl, concept, bid = q["topic"], (q["options"][q["answer"]] if isopt else q["answer"]), q["question"], q["explanation"], q["topic"], q.get("bank_id")
    kb = QG.KB.get(topic, {})
    ai = ai_service.complete(ai_service.TUTOR_SYSTEM, f"Question: {text}\nLearner chose: {sel}\nCorrect: {correct}\nVerified explanation: {expl}\nIn 3 short sentences in simple English, explain why the learner's choice is wrong and the key idea. Do not change the correct answer.", 300)
    log_activity(db, u.id, topic, "example", 5, "Explain My Mistake"); db.commit()
    return dict(your_answer=sel, correct_answer=correct, why_wrong=ai or f'You chose "{sel}", but the correct answer is "{correct}". {expl}', concept=concept, simple_explanation=expl,
                worked_example=kb.get("example"), formula=kb.get("formula"), practice_question=QG.similar_practice(topic, bid), study_material=kb.get("notes"), ai_generated=bool(ai),
                study_material_source="general knowledge")

@app.post("/api/practice/check")
def practice_check(b: schemas.PracticeCheck, u: User = Depends(current_user), db: Session = Depends(database.get_db)):
    q = A.BY_ID.get(b.bank_id)
    if not q or not 0 <= b.selected < len(q["options"]): raise HTTPException(422, "Invalid practice answer")
    ok = b.selected == q["correct"]; log_activity(db, u.id, q["topic"], "example", 3, "practice question"); db.commit()
    return dict(is_correct=ok, correct_answer=q["options"][q["correct"]], explanation=q["explanation"])

# ---------- path, progress, courses, lab, chat ----------
def _path(db, u):
    return LE.build_path(scores_of(db, u.id), {(a.topic, a.kind) for a in db.query(Activity).filter_by(user_id=u.id)}, u.thresholds, u.goals, history_by_topic(db, u.id))
@app.get("/api/recommendations")
def recs(u: User = Depends(current_user), db: Session = Depends(database.get_db)):
    p = _path(db, u); p["courses"] = [c for it in p["path"] if it["level"] != "strong" for c in igot_demo.fetch_courses(it["topic"])][:3]; p["rules"] = LE.__doc__; return p
@app.post("/api/activities/complete")
def complete_act(b: schemas.ActivityReq, u: User = Depends(current_user), db: Session = Depends(database.get_db)):
    if b.topic not in A.TOPICS: raise HTTPException(422, "Unknown topic")
    log_activity(db, u.id, b.topic, b.kind, b.minutes, "manual"); db.commit(); return _path(db, u)
@app.get("/api/progress")
def progress(u: User = Depends(current_user), db: Session = Depends(database.get_db)):
    sc = scores_of(db, u.id); acts = db.query(Activity).filter_by(user_id=u.id).order_by(Activity.created).all()
    qa = db.query(QuizAttempt).filter_by(user_id=u.id).order_by(QuizAttempt.created.desc()).all()
    att = db.query(AssessmentAttempt).filter_by(user_id=u.id).order_by(AssessmentAttempt.created).all()
    days = sorted({a.created.date() for a in acts}, reverse=True); streak, d = 0, date.today()
    if days and days[0] in (d, d - timedelta(days=1)):
        d = days[0]
        for x in days:
            if x == d: streak += 1; d -= timedelta(days=1)
            else: break
    per_day = {}
    for a in acts: per_day[a.created.date().isoformat()] = per_day.get(a.created.date().isoformat(), 0) + a.minutes
    tq, tc = sum(q.total for q in qa), sum(q.score for q in qa); p = _path(db, u)
    return dict(user=user_out(u), overall=C.overall(sc), scores=sc, report=C.gap_report(sc, u.thresholds),
                completed_activities=len({(a.topic, a.kind) for a in acts if a.kind != "assessment"}), minutes=sum(a.minutes for a in acts),
                quiz_accuracy=round(100 * tc / tq, 1) if tq else None, quizzes_taken=len(qa), streak=streak,
                history=[dict(date=a.created.date().isoformat(), accuracy=a.accuracy, sample=a.is_sample) for a in att],
                minutes_per_day=per_day, recent_quizzes=[dict(topic=q.topic, score=q.score, total=q.total, accuracy=q.accuracy, date=q.created.date().isoformat()) for q in qa[:5]],
                next=p["next"], goals=u.goals, completed=[dict(topic=a.topic, kind=a.kind) for a in acts if a.kind not in ("assessment",)][-8:],
                ai_mode=ai_service.available())
@app.get("/api/igot/courses")
def courses(topic: str, u: User = Depends(current_user)):
    return dict(mode=igot_demo.INTEGRATION_MODE, disclaimer=igot_demo.DISCLAIMER, courses=igot_demo.fetch_courses(topic))
@app.post("/api/igot/track")
def track(b: schemas.CourseTrack, u: User = Depends(current_user), db: Session = Depends(database.get_db)):
    db.add(CourseRec(user_id=u.id, topic=b.topic, title=b.title)); db.commit(); return dict(tracked=True, note="Recorded locally only; not sent to iGOT Karmayogi.")
@app.get("/api/igot/tracked")
def tracked(u: User = Depends(current_user), db: Session = Depends(database.get_db)):
    return [dict(topic=c.topic, title=c.title, status=c.status) for c in db.query(CourseRec).filter_by(user_id=u.id)]
@app.post("/api/lab/{calc}")
def lab(calc: str, body: dict, u: User = Depends(current_user)):
    f = stats_lab.CALCS.get(calc)
    if not f: raise HTTPException(404, "Unknown calculator")
    try: return f(body)
    except (ValueError, KeyError, TypeError, ZeroDivisionError) as e: raise HTTPException(422, f"Invalid input: {e}")
@app.post("/api/chat")
def chat(b: schemas.ChatReq, u: User = Depends(current_user), db: Session = Depends(database.get_db)):
    txt = None
    if b.document_id: txt = "\n".join(f"[Page {p}] {t}" for p, t in get_doc(db, u, b.document_id).pages)
    return ai_service.tutor(b.message, b.history, txt)

frontend = os.path.join(BASE, "..", "frontend")
if os.path.isdir(frontend): app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
