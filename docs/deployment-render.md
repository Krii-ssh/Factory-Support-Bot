# Deploying to Render

Render Standard, 2 GB and 1 CPU, $25 a month, with a 1 GB disk at `/var/data`.

**Why not the free tier.** Memory was never the problem, since peak RSS measured
126 MB. The free tier has no disk and cannot hold PyTorch, which forces chroma's
bundled ONNX encoder. That model truncates at **128** tokens, which is not the
256 an old docstring claimed and was read off the model's own `tokenizer.json`.
28 of the 31 chunks are longer than that. **66% of the corpus is never embedded** and the safety gate's margin drops from 0.048 to 0.006. Full numbers
are in `ingest.embedder()`.

Everything below needs your GitHub and Render accounts, so it is written as
steps to follow and not as something already done. The bot has not been
deployed.

---

## 1. Push to GitHub

`.env`, `chroma/`, `cases.db` and `refusals.jsonl` are gitignored. Before you
push, confirm that no credential or personal identifier is in any tracked file or
in the git history:

```bash
git grep -nE "gsk_|EAA[A-Za-z0-9]{20,}"
git log --all -p | grep -nE "gsk_|EAA[A-Za-z0-9]{20,}"
```

Neither command should print anything. If a real credential ever reached a
commit, rotate it at the provider first, then remove it from history.

To create the repository:

1. Go to <https://github.com/new>.
2. Choose a repository name, for example `factory-accident-support-bot`.
3. Select **Private** until the legal review is done.
4. Do **not** tick "Add a README", ".gitignore" or a licence. The repository
   already has them, and an extra commit would make the first push conflict.
5. Click **Create repository**.
6. Back in the project folder, run:

```bash
git remote add origin https://github.com/<your-username>/factory-accident-support-bot.git
git branch -M main
git push -u origin main
```

GitHub will ask for credentials. Use a **personal access token** as the password,
not your account password: <https://github.com/settings/tokens>, then **Generate
new token (classic)**, tick **repo** and copy it.

---

## 2. Create the Render service

`render.yaml` is a blueprint, so Render can read the whole configuration (plan,
disk, start command and env vars) from the repository.

1. Go to <https://dashboard.render.com/>.
2. Choose **New** and then **Blueprint**.
3. Connect the GitHub account and pick the repository.
4. Render reads `render.yaml` and shows a service named
   **factory-accident-support-bot** on plan **standard** with a 1 GB disk.
5. It prompts for the five secret values. They are `sync: false` in the
   blueprint, so they are never in the repository. Paste them from your local
   `.env`:

   | Key | Where it comes from |
   |---|---|
   | `GROQ_API_KEY` | console.groq.com, then API Keys |
   | `WHATSAPP_PHONE_NUMBER_ID` | Meta, then WhatsApp, then API Setup |
   | `WHATSAPP_ACCESS_TOKEN` | A System User token, see the warning below |
   | `WHATSAPP_APP_SECRET` | Meta, then App Settings, then Basic |
   | `WHATSAPP_VERIFY_TOKEN` | The string you invented |

6. Click **Apply**.

**The token on Meta's API Setup page expires in 24 hours.** For anything that has
to keep working, use a System User token: business.facebook.com, then Business
Settings, Users, System Users, Add, Generate token. Tick **both**
`whatsapp_business_messaging` and `whatsapp_business_management`, and set the
expiry to **Never**.

The first build installs torch and sentence-transformers and takes several
minutes.

---

## 3. Build the index, once, from the shell

`render.yaml` deliberately does **not** run `ingest.py` in the build. A build
writes to the ephemeral filesystem and not the mounted disk, so the index would
vanish on the next restart. Rebuilding on every deploy would also re-embed 31
chunks for no reason.

Once the first deploy is live:

1. Open the service in the Render dashboard.
2. Click the **Shell** tab.
3. Run:

```bash
python ingest.py
```

**Check the two lines it prints before anything else:**

```
store    -> /var/data/chroma
embedder -> SentenceTransformerEmbeddingFunction
```

`store` must be under `/var/data`, or the index is on the ephemeral disk.

`embedder` must say `SentenceTransformerEmbeddingFunction`. If it says
`DefaultEmbeddingFunction  <-- FALLBACK`, torch did not install and the index has
been built with the 128-token ONNX model. The bot will still answer, which is why
this is worth checking. The only symptom is handing off to legal aid more often
than it should. Fix the build and then re-run `ingest.py`.

Until this runs the service is healthy but cannot answer a question, because
retrieval raises "Collection does not exist".

---

## 4. Verify

```
https://<service>.onrender.com/health
```

Expect `"ok": true`, with `"groq_key"` and `"whatsapp_token"` reporting
`environment`. On Render they come from the dashboard and not from a `.env` file.

Then, from the Shell tab:

```bash
python query.py --test
```

Compare against the sentence-transformers baseline: case 1 is about 0.77, case 3
about 0.75, case 4 about 0.72 and case 8 about 0.78. A whole-table shift downward
means the fallback encoder built the index.

**Restart persistence.** In the dashboard choose **Manual Deploy** and then
**Restart service**. After it comes back, `/health` should still report the same
`cases_logged` count, and `python tracker.py` should list the same case IDs. The
index should still be there, so `python ingest.py` should not need re-running.

---

## 5. The Meta webhook

Leave the webhook pointing at your tunnel until this deployment is proven, so
that the tunnel stays as the working fallback. When you want to switch it:

1. Open the Meta dashboard, choose your app and then **WhatsApp**, then
   **Configuration**.
2. **Callback URL:** `https://<service>.onrender.com/meta`
3. **Verify token:** the same `WHATSAPP_VERIFY_TOKEN` you set in Render.
4. Click **Verify and save**.

Meta sends a GET to the URL once and expects the challenge echoed back. If it
says "callback URL could not be validated", the verify tokens do not match.

---

## Notes

- **Region** is set to `singapore`, the closest of Render's regions to Ludhiana.
  Change it in `render.yaml` if you would rather be elsewhere.
- **Disk size** is 1 GB. The index is a few MB and `cases.db` grows slowly. 1 GB
  is the smallest Render offers and is far more than needed.
- **Local runs are unaffected.** `CHROMA_PATH` and `CASES_DB_PATH` default to the
  project folder when unset, exactly as they behaved before.
- `.python-version` pins 3.14.5 to match the machine the pins were measured on.
  `requirements.txt` pins `torch==2.13.0+cpu` from the PyTorch CPU index, because
  plain `torch` on Linux pulls the CUDA build, which is several GB for a box with
  no GPU. The wheel `torch-2.13.0+cpu-cp314-cp314-manylinux_2_28_x86_64.whl` was
  confirmed to exist before pinning.
