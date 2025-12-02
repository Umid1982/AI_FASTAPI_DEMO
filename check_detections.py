#!/usr/bin/env python3
"""Check detections in database."""

from app.database.connection import SessionLocal
from app.database.models import Detection

session_id = 'd8e22871-a1c2-4c7e-b357-f63cf37c1423'

db = SessionLocal()
detections = db.query(Detection).filter(Detection.session_id == session_id).count()
print(f'Session {session_id}: {detections} detections')

# Check all sessions
all_detections = db.query(Detection).count()
print(f'Total detections in DB: {all_detections}')

if detections > 0:
    first = db.query(Detection).filter(Detection.session_id == session_id).first()
    print(f'\nFirst detection: frame {first.frame_number}, class={first.class_name}, confidence={first.confidence:.2f}')

db.close()
