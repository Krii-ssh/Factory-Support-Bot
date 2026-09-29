# Factory Accident Support Bot: complete setup guide

**For someone setting this up for the first time on a Windows laptop who has
never run a Python project before.**

Read it top to bottom and do not skip steps. The total time is about 30 to 40
minutes, most of it waiting for downloads.

---

## What you are setting up

A chatbot that answers legal questions for families of factory accident victims
in Punjab. It only answers from a checked collection of current Indian law, and
it refuses when it is not sure.

There are **two ways** to use it:

| | What it is | Difficulty |
|---|---|---|
| **Web chat** | A page in your browser | Easy, so start here |
| **WhatsApp** | Real messages to a real phone | Harder, needs extra setup |

**Do the web chat first.** It proves everything works. WhatsApp has its own
guide, [whatsapp-setup.md](whatsapp-setup.md), and you can skip it entirely.

---

# Part 1: Install Python

Python is the programming language this is written in. Your laptop probably does
not have it.

### 1.1 Check if you already have it

Press the **Windows key**, type `powershell` and press **Enter**. A blue or black
window opens. This is the **terminal**, and you will use it a lot. It is just a
place to type commands.

Type this and press Enter:

```
python --version
```

- If it prints `Python 3.14` or higher, **skip to Part 2**.
- If it prints an older version, says "not recognized" or opens the Microsoft
  Store, continue. The pinned packages in this project were measured on Python
  3.14.

### 1.2 Download Python

1. Go to **python.org/downloads**.
2. Click the big yellow **Download Python 3.x.x** button.
3. Open the downloaded file.

### 1.3 Install it, with one critical step

On the first install screen there is a checkbox at the bottom:

> ☑ **Add python.exe to PATH**

**You must tick this box.** It is easy to miss and everything fails without it.

Then click **Install Now** and wait. Click **Close** when it finishes.

### 1.4 Check it worked

**Close the PowerShell window and open a new one.** It will not notice Python
until you do.

```
python --version
```

You should see a version number. If it still fails, reinstall and make sure that
checkbox is ticked.

---

# Part 2: Get the project onto the laptop

You need the project folder. Clone the repository with Git, or download the ZIP
from GitHub and extract it.

**Put it somewhere with a simple path.** Good: `C:\factory-bot`. Avoid folders
with accents in the name, and avoid spaces if you can.

### 2.1 Check the folder is complete

Open it. You should see files including:

- `server.py`, `query.py` and `ingest.py`
- `run_demo.bat`
- a folder called `knowledge_base`
- `.env.example`

If `knowledge_base` is missing, you have an incomplete copy, so get it again.

### 2.2 Learn this one trick

You will need to open a terminal **inside** the project folder repeatedly.

**How:** open the folder in File Explorer, click the address bar at the top
(where the path is shown), type `powershell` and press **Enter**.

A terminal opens already pointing at that folder. Do this every time this guide
says "open a terminal in the project folder".

---

# Part 3: Install the packages

The project needs a handful of add-ons, all listed in `requirements.txt`. Open a
terminal in the project folder and run this **one command**:

```
pip install -r requirements.txt
```

Press Enter and wait. **This takes 5 to 15 minutes** and downloads about 2 GB.
You will see a lot of scrolling text, and that is normal.

It has finished when you see `Successfully installed ...` and get your prompt
back.

### If `pip` is not recognised

Try:

```
python -m pip install -r requirements.txt
```

### What these are, briefly

- **chromadb** stores the law so it can be searched by meaning.
- **sentence-transformers** and **torch** turn text into numbers so searching
  works.
- **fastapi** and **uvicorn** run the web page and the WhatsApp connection.
- **python-multipart** is needed for one of the message formats.

---

# Part 4: Set up the keys

The bot needs an API key to use the AI model. It is free.

### 4.1 Get a Groq key

1. Go to **console.groq.com**.
2. Sign up (Google sign-in is fine and no card is needed).
3. In the left sidebar choose **API Keys**.
4. Click **Create API Key**, give it any name and click **Submit**.
5. **Copy it immediately.** It is shown once and never again.

It looks like `gsk_` followed by a long string.

### 4.2 Create the `.env` file

This file holds the key. It has no filename, just an extension, and that is
normal.

**The reliable way** (Notepad likes to break this):

1. In the project folder, find **`.env.example`**.
2. Copy it (Ctrl+C, Ctrl+V), which gives you `.env - Copy.example`.
3. Rename that copy to exactly **`.env`**, with no `.txt` and no `.example`.
4. Windows warns about changing the extension, so click **Yes**.

> **If you cannot see file extensions:** in File Explorer, click **View** and
> tick **File name extensions**. Do this, or you will create `.env.txt` by
> accident and nothing will work.

### 4.3 Put the key in

Right-click `.env`, choose **Open with** and then **Notepad**.

Find the line starting `GROQ_API_KEY=` and put your key after the `=`:

```
GROQ_API_KEY=gsk_your_actual_key_here
```

**Rules:**

- No spaces around the `=`.
- No quotes around the key.
- Everything on one line.

Save (Ctrl+S) and close.

> **Leave all the `WHATSAPP_` lines empty for now.** They are only needed for
> [whatsapp-setup.md](whatsapp-setup.md). The web chat works fine without them.

---

# Part 5: Build the search index

This reads all the law files and prepares them for searching. **You only do this
once**, and again whenever you edit anything in `knowledge_base/`.

Open a terminal in the project folder:

```
python ingest.py
```

**The first run downloads an AI model (about 90 MB), so give it 2 to 5
minutes.**

When it is done you will see a summary of the chunks that were parsed and
embedded, along with two lines naming the store location and the embedder. The
embedder line should say `SentenceTransformerEmbeddingFunction`. If it says
`DefaultEmbeddingFunction  <-- FALLBACK`, the packages in Part 3 did not install
properly and the index has been built with a weaker model. Fix Part 3 and run
this again.

A new folder called `chroma` appears. That is the search index, so do not delete
it.

### If it says "no module named chromadb"

Part 3 did not finish. Run the pip command again and watch for errors.

---

# Part 6: Run it (the web version)

**Double-click `run_demo.bat`** in the project folder.

A terminal window opens, and after about 15 seconds your browser opens at
`http://localhost:8000`.

**Leave that terminal window open.** Closing it stops the bot.

### Test it

Type into the chat box:

> the owner is offering us money to sign a paper

You should get a long warning about not signing anything, ending with a legal
aid phone number and a reference number like `LDH-1001`.

Then try:

> my husband died in a factory accident, what are we owed?

The panel on the right shows which law was used and which safety rules fired.
That panel is the most interesting part of the whole project.

### If `run_demo.bat` does not work

Run it manually instead. In a terminal in the project folder:

```
python -m uvicorn server:app --port 8000
```

Wait for `Application startup complete`, then open **http://localhost:8000** in
your browser yourself.

### To stop it

Click the terminal window and press **Ctrl+C**, or just close the window.

---

# Part 7: WhatsApp (optional, harder)

**Skip this unless you specifically need WhatsApp.** The web chat does
everything except deliver to a phone.

It needs a Meta developer account, four credentials and a tunnel so that Meta
can reach your laptop. All of it is in
[whatsapp-setup.md](whatsapp-setup.md).

---

# Part 8: When something goes wrong

### "python is not recognized"

Python is not installed, or the PATH box was not ticked. Redo Part 1.

### "No module named chromadb" or "fastapi"

Part 3 did not complete. Run the pip command again.

### The browser page will not load

The terminal from Part 6 is not running, or it crashed. Look at it for red text.

### Every answer says "I don't have reliable information"

The Groq key is missing or wrong. Check `.env`:

- Is the filename exactly `.env` and not `.env.txt`?
- Are there any spaces or quotes around the key?
- Is the key still valid at console.groq.com?

Check by opening **http://localhost:8000/health**, which shows where the key came
from.

### A stale key overrides `.env`

If `/health` says `environment (overriding .env)`, Windows is holding an old copy
of the key that beats the file. Fix: press the Windows key, type
`environment variables`, choose **Edit environment variables for your account**,
find `GROQ_API_KEY` in the top box, click **Delete**, click OK and restart the
terminals.

### WhatsApp problems

See the troubleshooting table in [whatsapp-setup.md](whatsapp-setup.md).

---

# Quick reference

**Every time you want to run it:**

```
Double-click run_demo.bat
```

That is it, for the web version.

**Useful addresses:**

| | |
|---|---|
| Chat page | http://localhost:8000 |
| Status check | http://localhost:8000/health |

**Files you should never delete:**

- `knowledge_base\`, which holds the law
- `chroma\`, which is the search index (it can be rebuilt with `python ingest.py`)
- `.env`, which holds your keys
- any `.py` file

**Safe to delete:** `__pycache__\`, and `cases.db` (which wipes saved cases).

---

# Important things to know

**This is not finished software.** The compensation calculator is switched off on
purpose. Two government notifications are missing, so the bot explains how
compensation is worked out but refuses to state an amount. That is deliberate,
not a bug.

**It has not been reviewed by a lawyer**, and it must not be used with a real
family until it has been. This is the single most important open item.

**It only works while the terminal is open** and the laptop is on. It is not
hosted anywhere yet.

**English only.** The bot understands and answers in English. Hindi and Punjabi
are not built yet, because translating answers would bypass the safety checks
that make it trustworthy.
