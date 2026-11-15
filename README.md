# knowledgehub-ai-server

The backend that powers KnowledgeHub AI.

## High-level design

An upload saves the original file, extracts passages, embeds them, and stores the passages in Postgres. A question searches those passages and either returns a cited answer or refuses.

### Upload

```mermaid
flowchart TD
  UI[Web page]
  API[API]
  Ingest[Upload handler]
  Files[Folder of original files]
  Embed[Embedding API]
  DB[(Postgres)]

  UI -->|1. the file| API
  API -->|2. the file| Ingest
  Ingest -->|3. save the original| Files
  Ingest -->|4. text of each passage| Embed
  Embed -->|5. numbers for each passage| Ingest
  Ingest -->|6. passages and numbers| DB
  Ingest -->|7. finished| API
  API -->|8. confirmation| UI
```

### Question

```mermaid
flowchart TD
  UI[Web page]
  API[API]
  Search[Search]
  Embed[Embedding API]
  DB[(Postgres)]
  Decide{Strong match?}
  Writer[Answer writer]
  LLM[Chat model]

  UI -->|1. the question| API
  API -->|2. the question| Search
  Search -->|3. the question text| Embed
  Embed -->|4. numbers for the question| Search
  Search -->|5. those numbers, plus keywords| DB
  DB -->|6. the closest passages| Search
  Search --> Decide
  Decide -->|7a. yes, send those passages| Writer
  Writer -->|8. only those passages| LLM
  LLM -->|9. the written answer| Writer
  Writer -->|10. answer, file, and page| API
  Decide -->|7b. no, stop| API
  API -->|11. answer, or not in your documents| UI
```

## Low-level design

### Modules

```mermaid
flowchart TD
  api[api.py]
  files[files.py]
  extract[extract.py]
  chunk[chunk.py]
  embed[embed.py]
  search[search.py]
  answer[answer.py]
  db[db.py]
  config[config.py]
  eval[eval/run.py]
  disk[storage/]
  pg[(Postgres)]
  openai[OpenAI]

  api --> files
  api --> extract
  api --> chunk
  api --> embed
  api --> search
  api --> answer
  api --> db
  eval --> search
  eval --> answer
  files --> disk
  embed --> openai
  search --> embed
  search --> db
  answer --> openai
  db --> pg
  config --> api
  config --> db
```

`config.py` and `db.py` read settings and create the tables. `upload.py` runs the upload steps. `search.py` and `answer.py` run the question steps. `api.py` only handles HTTP.

### Tables

```mermaid
erDiagram
  documents ||--o{ chunks : contains
  documents {
    uuid id
    text filename
    text media_type
    text storage_path
    timestamptz created_at
  }
  chunks {
    uuid id
    uuid document_id
    int ordinal
    text text
    int page
    vector embedding
    tsvector tsv
  }
```

Deleting a document deletes its passages. The original PDF or DOCX stays in `storage/`, not in these tables.
