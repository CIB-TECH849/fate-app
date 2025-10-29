import os
from dotenv import load_dotenv

load_dotenv()

from web_app.app import app, db, IChingHexagram, IChingLine

HEXAGRAM_TO_CLEAR = "乾"

with app.app_context():
    print(f"Attempting to clear data for hexagram: {HEXAGRAM_TO_CLEAR}")

    hexagram = IChingHexagram.query.filter_by(name=HEXAGRAM_TO_CLEAR).first()

    if hexagram:
        # Delete associated lines first due to foreign key constraint
        IChingLine.query.filter_by(hexagram_id=hexagram.id).delete()
        db.session.delete(hexagram)
        db.session.commit()
        print(f"Successfully cleared data for hexagram: {HEXAGRAM_TO_CLEAR} and its lines.")
    else:
        print(f"Hexagram '{HEXAGRAM_TO_CLEAR}' not found in the database.")
