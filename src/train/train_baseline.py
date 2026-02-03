# src/train/train_baseline.py
import os
from pathlib import Path
import pandas as pd

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report
import joblib

# ---------------- Config ----------------
DATA_PATH = "data/custom_generated.csv"   # หรือ "data/train_all.csv"
MODEL_PATH = "models/baseline.joblib"
TEST_SIZE = 0.2
RANDOM_STATE = 42
# ----------------------------------------

# ensure model dir
Path("models").mkdir(exist_ok=True)

# load data
df = pd.read_csv(DATA_PATH)

# ปรับชื่อคอลัมน์ให้เป็นมาตรฐาน text/label หากมาจากไฟล์อื่น
rename_map = {}
if "ข้อความ" in df.columns and "text" not in df.columns:
    rename_map["ข้อความ"] = "text"
df = df.rename(columns=rename_map)

# ตรวจคอลัมน์จำเป็น
if "label" not in df.columns:
    raise SystemExit("❌ ไม่พบคอลัมน์ 'label' ในไฟล์ข้อมูล")
if "text" not in df.columns:
    raise SystemExit("❌ ไม่พบคอลัมน์ 'text' ในไฟล์ข้อมูล")

# ทำความสะอาดขั้นต้น
df = df.dropna(subset=["text", "label"])
df["text"] = df["text"].astype(str).str.strip()
df = df[df["text"] != ""].drop_duplicates(subset=["text"]).reset_index(drop=True)

# แยก train/test
X_train, X_test, y_train, y_test = train_test_split(
    df["text"], df["label"],
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=df["label"]
)

# Pipeline: สำหรับภาษาไทยชุดเล็ก ลองใช้ char-ngrams จะจับ pattern ได้ดีขึ้น
pipe = Pipeline([
    ("tfidf", TfidfVectorizer(
        analyzer="char_wb",      # ลองแบบอิงตัวอักษรในขอบคำ ช่วยกับภาษาไทยได้ดี
        ngram_range=(3,5),       # ลอง 3–5 ตัวอักษร
        min_df=2,                # ตัดคำ/สตริงที่โผล่น้อยมาก
        max_features=30000
    )),
    ("clf", LogisticRegression(max_iter=500, n_jobs=None))
])

# เทรน
pipe.fit(X_train, y_train)

# ประเมิน
pred = pipe.predict(X_test)
print("\nClassification report (test set):")
print(classification_report(y_test, pred, digits=3))

# cross-val (ประเมินรวมๆ เพิ่มเติม)
scores = cross_val_score(pipe, df["text"], df["label"], cv=5)
print(f"\nCross-val accuracy (5-fold): {scores.mean():.3f} ± {scores.std():.3f}")

# เซฟโมเดล
joblib.dump(pipe, MODEL_PATH)
print(f"\n✅ saved → {MODEL_PATH}")
