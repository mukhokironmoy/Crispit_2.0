crispit_bot/
│
├── app/
│ ├── bot/
│ │ ├── handlers/
│ │ │ ├── home.py
│ │ │ ├── transcript.py
│ │ │ ├── notes.py
│ │ │ ├── batch.py
│ │ │ ├── modes.py
│ │ │ ├── help.py
│ │ │ ├── errors.py
│ │ │ └── debug.py
│ │ ├── keyboards/
│ │ │ ├── home_kb.py
│ │ │ ├── notes_kb.py
│ │ │ ├── batch_kb.py
│ │ │ └── navigation_kb.py
│ │ ├── state/
│ │ │ ├── machine.py
│ │ │ └── constants.py
│ │ ├── router.py
│ │ └── app.py
│ │
│ ├── services/
│ │ ├── youtube_service.py
│ │ ├── transcript_service.py
│ │ ├── notes_service.py
│ │ ├── batch_service.py
│ │ ├── pdf_service.py
│ │ ├── llm_service.py
│ │ ├── text_limit.py
│ │ └── storage_service.py
│ │
│ ├── db/
│ │ ├── database.py
│ │ ├── models.py
│ │ └── migrations.sql (optional)
│ │
│ ├── config/
│ │ ├── settings.py
│ │ └── logging.py
│ │
│ ├── utils/
│ │ ├── validators.py
│ │ ├── formatting.py
│ │ └── helpers.py
│ │
│ └── storage/
│ ├── transcripts/
│ ├── summaries/
│ ├── pdf/
│ └── batch/
│
├── run.py
├── requirements.txt
├── .env
└── README.md
